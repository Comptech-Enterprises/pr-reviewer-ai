"""
Core review orchestration engine.
"""
from typing import List, Dict, Optional
import logging
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from github_client import GitHubClient
from ai_reviewer import AIReviewer
from diff_parser import DiffParser
from comment_formatter import CommentFormatter
from analyzers import (
    SecurityAnalyzer,
    QualityAnalyzer,
    PerformanceAnalyzer,
    TestingAnalyzer,
    LLMUsageAnalyzer,
    AnalysisResult,
    Severity
)
from prompts import get_system_prompt, get_analysis_prompt
from prompts.system_prompt import get_system_prompt_for_category

logger = logging.getLogger(__name__)


class ReviewEngine:
    """Orchestrates the PR review process."""

    def __init__(
        self,
        github_client: GitHubClient,
        ai_reviewer: AIReviewer,
        config: Dict
    ):
        """
        Initialize review engine.

        Args:
            github_client: GitHub API client
            ai_reviewer: AI reviewer instance
            config: Configuration dictionary
        """
        self.github = github_client
        self.ai = ai_reviewer
        self.config = config
        self.diff_parser = DiffParser()
        self.formatter = CommentFormatter(config.get('formatting', {}))

        # Initialize analyzers based on config
        self.analyzers = self._initialize_analyzers()

    def _initialize_analyzers(self) -> Dict:
        """Initialize analyzers based on configuration."""
        analyzers = {}

        analyzer_config = self.config.get('analyzers', {})

        if analyzer_config.get('security', {}).get('enabled', True):
            analyzers['security'] = SecurityAnalyzer(
                analyzer_config.get('security', {})
            )

        if analyzer_config.get('quality', {}).get('enabled', True):
            analyzers['quality'] = QualityAnalyzer(
                analyzer_config.get('quality', {})
            )

        if analyzer_config.get('performance', {}).get('enabled', True):
            analyzers['performance'] = PerformanceAnalyzer(
                analyzer_config.get('performance', {})
            )

        if analyzer_config.get('testing', {}).get('enabled', True):
            analyzers['testing'] = TestingAnalyzer(
                analyzer_config.get('testing', {})
            )

        if analyzer_config.get('llm_usage', {}).get('enabled', True):
            analyzers['llm_usage'] = LLMUsageAnalyzer(
                analyzer_config.get('llm_usage', {})
            )

        logger.info(f"Initialized {len(analyzers)} analyzers: {list(analyzers.keys())}")
        return analyzers

    def review_pull_request(self, pr_number: int) -> Dict:
        """
        Review a pull request.

        Args:
            pr_number: Pull request number

        Returns:
            Review results dictionary
        """
        logger.info(f"Starting review of PR #{pr_number}")

        # Step 1: Fetch PR details
        pr_details = self.github.get_pr_details(pr_number)
        logger.info(f"PR: {pr_details['title']} by {pr_details['author']}")

        # Step 2: Get changed files
        files = self.github.get_pr_files(pr_number)
        logger.info(f"Found {len(files)} changed file(s)")

        # Step 3: Filter files based on exclusions
        exclusions = self.config.get('exclusions', [])
        files_to_review = [
            f for f in files
            if not self._should_skip_file(f['filename'], exclusions)
        ]

        logger.info(f"Reviewing {len(files_to_review)} file(s) after filtering")

        # Step 4: Analyze files
        all_results = self._analyze_files(files_to_review, pr_details)

        # Step 5: Format and post comments
        self._post_review_comments(pr_number, all_results, pr_details)

        # Step 6: Post summary
        self._post_summary(pr_number, all_results, pr_details)

        return {
            'pr_number': pr_number,
            'files_reviewed': len(files_to_review),
            'total_issues': sum(len(r) for r in all_results.values()),
            'results_by_category': {
                cat: len(results) for cat, results in all_results.items()
            }
        }

    def _should_skip_file(self, filename: str, exclusions: List[str]) -> bool:
        """Check if file should be skipped."""
        # Check exclusion patterns
        if self.github.should_skip_file(filename, exclusions):
            logger.info(f"Skipping {filename} (matches exclusion pattern)")
            return True

        # Check if binary
        if self.diff_parser.is_binary_file(filename):
            logger.info(f"Skipping {filename} (binary file)")
            return True

        # Check if generated
        if self.diff_parser.is_generated_file(filename):
            logger.info(f"Skipping {filename} (generated file)")
            return True

        return False

    def _analyze_files(
        self,
        files: List[Dict],
        pr_details: Dict
    ) -> Dict[str, List[AnalysisResult]]:
        """
        Analyze files using all enabled analyzers.

        Args:
            files: List of file information
            pr_details: PR metadata

        Returns:
            Results grouped by analyzer category
        """
        results_by_category = {name: [] for name in self.analyzers.keys()}

        max_workers = self.config.get('max_workers', 3)

        # Analyze each file with each analyzer
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []

            for file_info in files:
                filename = file_info['filename']
                patch = file_info.get('patch', '')

                if not patch:
                    logger.warning(f"No patch for {filename}, skipping")
                    continue

                # Submit analysis tasks for each analyzer
                for analyzer_name, analyzer in self.analyzers.items():
                    future = executor.submit(
                        self._analyze_file_with_analyzer,
                        filename,
                        patch,
                        analyzer_name,
                        analyzer,
                        pr_details
                    )
                    futures.append((future, analyzer_name, filename))

            # Collect results
            for future, analyzer_name, filename in futures:
                try:
                    results = future.result(timeout=120)
                    if results:
                        results_by_category[analyzer_name].extend(results)
                        logger.info(
                            f"Found {len(results)} {analyzer_name} issue(s) in {filename}"
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to analyze {filename} with {analyzer_name}: {e}"
                    )

        return results_by_category

    def _analyze_file_with_analyzer(
        self,
        filename: str,
        patch: str,
        analyzer_name: str,
        analyzer,
        pr_details: Dict
    ) -> List[AnalysisResult]:
        """
        Analyze a single file with a specific analyzer.

        Args:
            filename: File name
            patch: Unified diff patch
            analyzer_name: Name of analyzer
            analyzer: Analyzer instance
            pr_details: PR metadata

        Returns:
            List of analysis results
        """
        # Get prompts
        system_prompt = get_system_prompt_for_category(analyzer_name)
        analysis_prompt = analyzer.get_analysis_prompt()

        # Prepare context
        context = {
            'pr_title': pr_details.get('title'),
            'pr_description': pr_details.get('description'),
            'author': pr_details.get('author')
        }

        # Call AI for analysis
        response = self.ai.analyze_diff(
            diff=patch,
            filename=filename,
            system_prompt=system_prompt,
            analysis_prompt=analysis_prompt,
            context=context,
            max_tokens=self.config.get('max_tokens_per_file', 4096)
        )

        if not response:
            logger.warning(f"No response from AI for {filename}")
            return []

        # Parse response
        results = self._parse_ai_response(response, filename, analyzer_name)

        return results

    def _parse_ai_response(
        self,
        response: str,
        filename: str,
        analyzer_name: str
    ) -> List[AnalysisResult]:
        """
        Parse AI response into structured results.

        Args:
            response: AI response text
            filename: File being analyzed
            analyzer_name: Analyzer category

        Returns:
            List of analysis results
        """
        results = []

        try:
            # Try JSON parsing first
            data = json.loads(response)

            issues = data.get('issues', [])
            for issue in issues:
                result = AnalysisResult(
                    severity=self._parse_severity(issue.get('severity', 'info')),
                    category=analyzer_name.title(),
                    title=issue.get('title', 'Issue found'),
                    description=issue.get('description', ''),
                    filename=filename,
                    line_number=issue.get('line_number'),
                    suggestion=issue.get('suggestion'),
                    code_snippet=issue.get('code_snippet')
                )
                results.append(result)

        except json.JSONDecodeError:
            # Fallback to text parsing
            logger.warning(f"Failed to parse JSON response for {filename}, using text parsing")
            results = self._parse_text_response(response, filename, analyzer_name)

        return results

    def _parse_severity(self, severity_str: str) -> Severity:
        """Parse severity string to Severity enum."""
        severity_map = {
            'critical': Severity.CRITICAL,
            'high': Severity.HIGH,
            'medium': Severity.MEDIUM,
            'low': Severity.LOW,
            'info': Severity.INFO
        }
        return severity_map.get(severity_str.lower(), Severity.INFO)

    def _parse_text_response(
        self,
        response: str,
        filename: str,
        analyzer_name: str
    ) -> List[AnalysisResult]:
        """Parse text-based response as fallback."""
        # Simple text parsing - look for severity indicators
        results = []
        lines = response.split('\n')

        current_issue = {}
        for line in lines:
            line = line.strip()

            # Look for severity indicators
            for sev in ['critical', 'high', 'medium', 'low', 'info']:
                if sev in line.lower() and ':' in line:
                    if current_issue:
                        results.append(self._create_result_from_dict(
                            current_issue, filename, analyzer_name
                        ))
                    current_issue = {
                        'severity': sev,
                        'title': line.split(':', 1)[1].strip() if ':' in line else line,
                        'description': ''
                    }
                    break
            else:
                # Append to current issue description
                if current_issue and line:
                    current_issue['description'] += line + '\n'

        # Add last issue
        if current_issue:
            results.append(self._create_result_from_dict(
                current_issue, filename, analyzer_name
            ))

        return results

    def _create_result_from_dict(
        self,
        issue_dict: Dict,
        filename: str,
        analyzer_name: str
    ) -> AnalysisResult:
        """Create AnalysisResult from dictionary."""
        return AnalysisResult(
            severity=self._parse_severity(issue_dict.get('severity', 'info')),
            category=analyzer_name.title(),
            title=issue_dict.get('title', 'Issue found'),
            description=issue_dict.get('description', '').strip(),
            filename=filename,
            line_number=issue_dict.get('line_number'),
            suggestion=issue_dict.get('suggestion')
        )

    def _post_review_comments(
        self,
        pr_number: int,
        results: Dict[str, List[AnalysisResult]],
        pr_details: Dict
    ):
        """Post inline review comments."""
        min_severity = self._parse_severity(
            self.config.get('min_severity_for_comments', 'low')
        )

        posted_count = 0
        for category_results in results.values():
            for result in category_results:
                # Check if should post
                if not self.formatter.should_post_comment(result, min_severity):
                    continue

                # Format comment
                comment_text = self.formatter.format_inline_comment(result)

                # Post if line number available
                if result.line_number:
                    commit_sha = self.github.get_latest_commit_sha(pr_number)
                    success = self.github.post_review_comment(
                        pr_number=pr_number,
                        body=comment_text,
                        commit_id=commit_sha,
                        path=result.filename,
                        line=result.line_number
                    )
                    if success:
                        posted_count += 1

        logger.info(f"Posted {posted_count} inline comment(s)")

    def _post_summary(
        self,
        pr_number: int,
        results: Dict[str, List[AnalysisResult]],
        pr_details: Dict
    ):
        """Post summary comment."""
        summary = self.formatter.format_summary_comment(
            results_by_category=results,
            pr_details=pr_details
        )

        # Truncate if too long
        summary = self.formatter.truncate_long_comment(summary)

        # Post as issue comment
        success = self.github.post_issue_comment(pr_number, summary)

        if success:
            logger.info("Posted summary comment")
        else:
            logger.error("Failed to post summary comment")
