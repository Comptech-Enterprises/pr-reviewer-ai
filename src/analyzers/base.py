"""
Base analyzer class and common utilities.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class AnalysisResult:
    """Result from code analysis."""
    severity: Severity
    category: str
    title: str
    description: str
    filename: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None


class BaseAnalyzer(ABC):
    """Base class for all code analyzers."""

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize analyzer.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)

    @abstractmethod
    def get_name(self) -> str:
        """
        Get analyzer name.

        Returns:
            Analyzer name
        """
        pass

    @abstractmethod
    def get_analysis_prompt(self) -> str:
        """
        Get the analysis prompt for this analyzer.

        Returns:
            Prompt string
        """
        pass

    @abstractmethod
    def analyze(self, code: str, filename: str, context: Optional[Dict] = None) -> List[AnalysisResult]:
        """
        Analyze code and return findings.

        Args:
            code: Code or diff to analyze
            filename: File being analyzed
            context: Additional context (PR info, etc.)

        Returns:
            List of analysis results
        """
        pass

    def parse_ai_response(self, response: str, filename: str) -> List[AnalysisResult]:
        """
        Parse AI response into structured results.

        Args:
            response: AI response text
            filename: File being analyzed

        Returns:
            List of analysis results
        """
        # Default parser - can be overridden by subclasses
        results = []

        if not response or "No issues found" in response or "No concerns" in response:
            return results

        # Try to parse structured response
        import json
        try:
            # Attempt JSON parsing
            data = json.loads(response)
            if isinstance(data, list):
                for item in data:
                    results.append(self._dict_to_result(item, filename))
            elif isinstance(data, dict) and 'issues' in data:
                for item in data['issues']:
                    results.append(self._dict_to_result(item, filename))
        except json.JSONDecodeError:
            # Fallback: parse text format
            results = self._parse_text_response(response, filename)

        return results

    def _dict_to_result(self, data: Dict, filename: str) -> AnalysisResult:
        """Convert dictionary to AnalysisResult."""
        severity_map = {
            'critical': Severity.CRITICAL,
            'high': Severity.HIGH,
            'medium': Severity.MEDIUM,
            'low': Severity.LOW,
            'info': Severity.INFO
        }

        severity = severity_map.get(
            data.get('severity', 'info').lower(),
            Severity.INFO
        )

        return AnalysisResult(
            severity=severity,
            category=data.get('category', self.get_name()),
            title=data.get('title', 'Issue found'),
            description=data.get('description', ''),
            filename=filename,
            line_number=data.get('line_number'),
            suggestion=data.get('suggestion'),
            code_snippet=data.get('code_snippet')
        )

    def _parse_text_response(self, response: str, filename: str) -> List[AnalysisResult]:
        """Parse text-based AI response."""
        results = []
        lines = response.split('\n')

        current_issue = {}
        for line in lines:
            line = line.strip()

            # Look for severity indicators
            if any(s in line.lower() for s in ['critical:', 'high:', 'medium:', 'low:']):
                if current_issue:
                    results.append(self._create_result_from_text(current_issue, filename))
                    current_issue = {}

                # Extract severity
                for sev in ['critical', 'high', 'medium', 'low']:
                    if sev in line.lower():
                        current_issue['severity'] = sev
                        current_issue['description'] = line
                        break

            elif line and current_issue:
                # Append to description
                current_issue['description'] = current_issue.get('description', '') + '\n' + line

        # Add last issue
        if current_issue:
            results.append(self._create_result_from_text(current_issue, filename))

        return results

    def _create_result_from_text(self, issue_data: Dict, filename: str) -> AnalysisResult:
        """Create AnalysisResult from parsed text data."""
        severity_map = {
            'critical': Severity.CRITICAL,
            'high': Severity.HIGH,
            'medium': Severity.MEDIUM,
            'low': Severity.LOW,
            'info': Severity.INFO
        }

        severity = severity_map.get(
            issue_data.get('severity', 'info').lower(),
            Severity.INFO
        )

        description = issue_data.get('description', '')
        # Extract title from first line
        title = description.split('\n')[0] if description else 'Issue found'

        return AnalysisResult(
            severity=severity,
            category=self.get_name(),
            title=title,
            description=description,
            filename=filename
        )

    def filter_by_severity(
        self,
        results: List[AnalysisResult],
        min_severity: Severity
    ) -> List[AnalysisResult]:
        """
        Filter results by minimum severity.

        Args:
            results: Analysis results
            min_severity: Minimum severity to include

        Returns:
            Filtered results
        """
        severity_order = {
            Severity.INFO: 0,
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4
        }

        min_level = severity_order[min_severity]
        return [
            r for r in results
            if severity_order[r.severity] >= min_level
        ]

    def get_language_from_filename(self, filename: str) -> Optional[str]:
        """
        Detect programming language from filename.

        Args:
            filename: File name

        Returns:
            Language identifier or None
        """
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.sql': 'sql',
            '.sh': 'bash',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.xml': 'xml',
            '.html': 'html',
            '.css': 'css',
        }

        for ext, lang in extension_map.items():
            if filename.endswith(ext):
                return lang

        return None
