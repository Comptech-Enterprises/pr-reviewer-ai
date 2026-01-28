"""
Format review comments for GitHub.
"""
from typing import List, Dict
from analyzers.base import AnalysisResult, Severity
import logging

logger = logging.getLogger(__name__)


class CommentFormatter:
    """Format analysis results as GitHub comments."""

    def __init__(self, config: Dict = None):
        """
        Initialize comment formatter.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.include_severity_emoji = self.config.get('severity_emoji', True)
        self.include_category_labels = self.config.get('category_labels', True)

    def format_inline_comment(self, result: AnalysisResult) -> str:
        """
        Format a single analysis result as an inline comment.

        Args:
            result: Analysis result

        Returns:
            Formatted comment text
        """
        parts = []

        # Severity emoji
        if self.include_severity_emoji:
            emoji = self._get_severity_emoji(result.severity)
            parts.append(f"{emoji} **{result.severity.value.upper()}**")

        # Category label
        if self.include_category_labels:
            parts.append(f"[{result.category}]")

        # Title
        parts.append(f"**{result.title}**")

        comment = " ".join(parts) + "\n\n"

        # Description
        comment += result.description + "\n"

        # Suggestion
        if result.suggestion:
            comment += f"\n💡 **Suggestion:**\n{result.suggestion}\n"

        # Code snippet if provided
        if result.code_snippet:
            comment += f"\n```\n{result.code_snippet}\n```\n"

        return comment

    def format_summary_comment(
        self,
        results_by_category: Dict[str, List[AnalysisResult]],
        pr_details: Dict,
        stats: Dict = None
    ) -> str:
        """
        Format a summary comment for the entire PR review.

        Args:
            results_by_category: Results grouped by analyzer category
            pr_details: PR metadata
            stats: Optional statistics about the review

        Returns:
            Formatted summary comment
        """
        lines = ["## 🤖 AI Code Review Summary\n"]

        # PR info
        lines.append(f"**PR:** {pr_details.get('title', 'N/A')}")
        lines.append(f"**Author:** @{pr_details.get('author', 'unknown')}")
        lines.append(
            f"**Changes:** {pr_details.get('changed_files', 0)} files, "
            f"+{pr_details.get('additions', 0)} -{pr_details.get('deletions', 0)}\n"
        )

        # Overall statistics
        total_issues = sum(len(results) for results in results_by_category.values())

        if total_issues == 0:
            lines.append("### ✅ No Issues Found\n")
            lines.append("Great work! No significant issues were detected in this PR.\n")
            return "\n".join(lines)

        lines.append(f"### 📊 Found {total_issues} issue(s) across {len(results_by_category)} categories\n")

        # Breakdown by severity
        severity_counts = self._count_by_severity(results_by_category)
        if severity_counts:
            lines.append("**By Severity:**")
            for severity, count in sorted(
                severity_counts.items(),
                key=lambda x: self._severity_order(x[0]),
                reverse=True
            ):
                emoji = self._get_severity_emoji(severity)
                lines.append(f"- {emoji} {severity.value.title()}: {count}")
            lines.append("")

        # Breakdown by category
        lines.append("**By Category:**")
        for category, results in results_by_category.items():
            if results:
                lines.append(f"- {category}: {len(results)} issue(s)")
        lines.append("")

        # Critical/High severity issues highlighted
        critical_high = self._get_critical_high_issues(results_by_category)
        if critical_high:
            lines.append("### 🚨 Critical & High Priority Issues\n")
            for result in critical_high[:5]:  # Show top 5
                lines.append(
                    f"- **{result.title}** ({result.category}) "
                    f"in `{result.filename}`"
                )
                if result.line_number:
                    lines.append(f"  Line {result.line_number}")
            if len(critical_high) > 5:
                lines.append(f"\n_...and {len(critical_high) - 5} more_")
            lines.append("")

        # Category summaries
        for category, results in results_by_category.items():
            if results:
                lines.append(f"### {self._get_category_emoji(category)} {category}\n")
                lines.append(f"Found {len(results)} issue(s):\n")

                # Group by severity
                by_severity = {}
                for result in results:
                    by_severity.setdefault(result.severity, []).append(result)

                for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]:
                    if severity in by_severity:
                        emoji = self._get_severity_emoji(severity)
                        lines.append(f"**{emoji} {severity.value.title()}:**")
                        for result in by_severity[severity][:3]:  # Show top 3 per severity
                            lines.append(f"- {result.title} (`{result.filename}`)")
                        if len(by_severity[severity]) > 3:
                            lines.append(f"  _...and {len(by_severity[severity]) - 3} more_")
                        lines.append("")

        # Footer
        lines.append("---")
        lines.append("*This review was generated by AI using Mistral Devstral-2-123b via NVIDIA NIM*")
        lines.append("*Please review suggestions carefully and use your judgment*")

        return "\n".join(lines)

    def format_file_summary(
        self,
        filename: str,
        results: List[AnalysisResult]
    ) -> str:
        """
        Format a summary for a specific file.

        Args:
            filename: File name
            results: Analysis results for the file

        Returns:
            Formatted file summary
        """
        if not results:
            return f"### {filename}\n\n✅ No issues found\n"

        lines = [f"### {filename}\n"]
        lines.append(f"Found {len(results)} issue(s):\n")

        for i, result in enumerate(results, 1):
            emoji = self._get_severity_emoji(result.severity)
            lines.append(
                f"{i}. {emoji} **{result.title}** "
                f"({result.severity.value})"
            )
            if result.line_number:
                lines.append(f"   Line: {result.line_number}")
            lines.append(f"   {result.description[:100]}...")
            lines.append("")

        return "\n".join(lines)

    def _get_severity_emoji(self, severity: Severity) -> str:
        """Get emoji for severity level."""
        emoji_map = {
            Severity.CRITICAL: "🔴",
            Severity.HIGH: "🟠",
            Severity.MEDIUM: "🟡",
            Severity.LOW: "🔵",
            Severity.INFO: "ℹ️"
        }
        return emoji_map.get(severity, "⚪")

    def _get_category_emoji(self, category: str) -> str:
        """Get emoji for review category."""
        emoji_map = {
            "Security": "🔒",
            "Code Quality": "✨",
            "Performance": "⚡",
            "Testing": "🧪"
        }
        return emoji_map.get(category, "📝")

    def _count_by_severity(
        self,
        results_by_category: Dict[str, List[AnalysisResult]]
    ) -> Dict[Severity, int]:
        """Count issues by severity across all categories."""
        counts = {}
        for results in results_by_category.values():
            for result in results:
                counts[result.severity] = counts.get(result.severity, 0) + 1
        return counts

    def _get_critical_high_issues(
        self,
        results_by_category: Dict[str, List[AnalysisResult]]
    ) -> List[AnalysisResult]:
        """Get all critical and high severity issues."""
        critical_high = []
        for results in results_by_category.values():
            critical_high.extend([
                r for r in results
                if r.severity in [Severity.CRITICAL, Severity.HIGH]
            ])
        return sorted(
            critical_high,
            key=lambda x: self._severity_order(x.severity),
            reverse=True
        )

    def _severity_order(self, severity: Severity) -> int:
        """Get numeric order for severity (higher = more severe)."""
        order_map = {
            Severity.CRITICAL: 4,
            Severity.HIGH: 3,
            Severity.MEDIUM: 2,
            Severity.LOW: 1,
            Severity.INFO: 0
        }
        return order_map.get(severity, 0)

    def should_post_comment(
        self,
        result: AnalysisResult,
        min_severity: Severity = Severity.LOW
    ) -> bool:
        """
        Determine if a comment should be posted based on severity threshold.

        Args:
            result: Analysis result
            min_severity: Minimum severity to post

        Returns:
            True if comment should be posted
        """
        return self._severity_order(result.severity) >= self._severity_order(min_severity)

    def truncate_long_comment(self, comment: str, max_length: int = 65536) -> str:
        """
        Truncate comment if it exceeds GitHub's limit.

        Args:
            comment: Comment text
            max_length: Maximum length (GitHub limit is 65536)

        Returns:
            Truncated comment if needed
        """
        if len(comment) <= max_length:
            return comment

        truncated = comment[:max_length - 100]
        truncated += "\n\n---\n*[Comment truncated due to length]*"
        return truncated
