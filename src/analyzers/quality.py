"""
Code quality analyzer.
"""
from typing import List, Dict, Optional
from .base import BaseAnalyzer, AnalysisResult


class QualityAnalyzer(BaseAnalyzer):
    """Analyzer for code quality and best practices."""

    def get_name(self) -> str:
        """Get analyzer name."""
        return "Code Quality"

    def get_analysis_prompt(self) -> str:
        """Get code quality analysis prompt."""
        return """You are a code quality expert reviewing code for best practices and maintainability. Analyze the provided code/diff.

Focus on:
1. Code smells and anti-patterns
   - Long methods/functions (>50 lines)
   - Large classes (>300 lines)
   - Duplicate code
   - Magic numbers and strings
   - God objects/classes

2. SOLID principles violations
   - Single Responsibility Principle
   - Open/Closed Principle
   - Liskov Substitution Principle
   - Interface Segregation Principle
   - Dependency Inversion Principle

3. Naming conventions
   - Unclear variable/function names
   - Inconsistent naming styles
   - Misleading names

4. Code complexity
   - High cyclomatic complexity
   - Deeply nested conditionals
   - Complex boolean expressions

5. Documentation quality
   - Missing docstrings/comments
   - Outdated documentation
   - Unclear comments

6. Error handling practices
   - Bare except clauses
   - Swallowed exceptions
   - Missing error handling
   - Overly broad exception catching

7. Code organization
   - Poor module structure
   - Circular dependencies
   - Tight coupling

For each issue found, provide:
- Severity: high, medium, low, or info
- Title: Brief description
- Description: Detailed explanation
- Line number: Where issue occurs
- Suggestion: How to improve

Return results in JSON format:
{
  "issues": [
    {
      "severity": "medium",
      "title": "Function too complex",
      "description": "This function has cyclomatic complexity of 15, making it hard to test and maintain",
      "line_number": 25,
      "suggestion": "Break this function into smaller, focused functions with single responsibilities"
    }
  ]
}

If no quality issues are found, return: {"issues": []}
"""

    def analyze(self, code: str, filename: str, context: Optional[Dict] = None) -> List[AnalysisResult]:
        """
        Analyze code for quality issues.

        Args:
            code: Code or diff to analyze
            filename: File being analyzed
            context: Additional context

        Returns:
            List of quality findings
        """
        if not self.enabled:
            return []

        # Actual analysis happens via AI in review_engine
        return []

    def get_complexity_threshold(self) -> int:
        """
        Get cyclomatic complexity threshold.

        Returns:
            Maximum acceptable complexity
        """
        return self.config.get('max_complexity', 10)

    def get_function_length_threshold(self) -> int:
        """
        Get maximum acceptable function length.

        Returns:
            Maximum lines per function
        """
        return self.config.get('max_function_length', 50)

    def get_class_length_threshold(self) -> int:
        """
        Get maximum acceptable class length.

        Returns:
            Maximum lines per class
        """
        return self.config.get('max_class_length', 300)
