"""
Testing coverage and quality analyzer.
"""
from typing import List, Dict, Optional
from .base import BaseAnalyzer, AnalysisResult


class TestingAnalyzer(BaseAnalyzer):
    """Analyzer for testing coverage and quality."""

    def get_name(self) -> str:
        """Get analyzer name."""
        return "Testing"

    def get_analysis_prompt(self) -> str:
        """Get testing analysis prompt."""
        return """You are a testing expert reviewing code for test coverage and quality. Analyze the provided code/diff.

Focus on:
1. Missing test cases
   - New functions without tests
   - Changed logic without updated tests
   - Untested edge cases
   - Missing error path tests

2. Edge cases not covered
   - Null/undefined inputs
   - Empty collections
   - Boundary values
   - Invalid inputs
   - Concurrent access

3. Test quality issues
   - Tests that don't actually test anything
   - Overly complex tests
   - Brittle tests (too coupled to implementation)
   - Missing assertions
   - Tests that test multiple things

4. Mock/stub opportunities
   - External dependencies not mocked
   - Database calls in unit tests
   - Network calls in unit tests
   - File I/O in unit tests

5. Test organization
   - Missing test fixtures
   - Duplicate test setup code
   - Poor test naming
   - Tests in wrong location

6. Integration vs unit test balance
   - Missing integration tests
   - Integration tests that should be unit tests
   - Missing end-to-end tests for critical flows

7. Test maintainability
   - Magic values in tests
   - Unclear test intent
   - Missing test documentation

For each suggestion, provide:
- Severity: medium, low, or info (testing suggestions are usually not critical)
- Title: Brief description
- Description: What should be tested and why
- Line number: Code that needs testing
- Suggestion: Specific test case recommendations

Return results in JSON format:
{
  "issues": [
    {
      "severity": "medium",
      "title": "Missing edge case tests",
      "description": "New authentication function lacks tests for invalid credentials and expired tokens",
      "line_number": 45,
      "suggestion": "Add test cases for: 1) Invalid username, 2) Invalid password, 3) Expired token, 4) Null credentials"
    }
  ]
}

If code changes don't require new tests, return: {"issues": []}
"""

    def analyze(self, code: str, filename: str, context: Optional[Dict] = None) -> List[AnalysisResult]:
        """
        Analyze code for testing needs.

        Args:
            code: Code or diff to analyze
            filename: File being analyzed
            context: Additional context

        Returns:
            List of testing suggestions
        """
        if not self.enabled:
            return []

        # Actual analysis happens via AI in review_engine
        return []

    def is_test_file(self, filename: str) -> bool:
        """
        Check if file is a test file.

        Args:
            filename: File name

        Returns:
            True if test file
        """
        test_indicators = [
            'test_',
            '_test.',
            '.test.',
            '.spec.',
            '/tests/',
            '/test/',
            '__tests__',
        ]

        return any(indicator in filename.lower() for indicator in test_indicators)

    def get_test_frameworks(self, language: Optional[str]) -> List[str]:
        """
        Get common test frameworks for a language.

        Args:
            language: Programming language

        Returns:
            List of framework names
        """
        frameworks = {
            'python': ['pytest', 'unittest', 'nose', 'doctest'],
            'javascript': ['jest', 'mocha', 'jasmine', 'vitest'],
            'typescript': ['jest', 'mocha', 'jasmine', 'vitest'],
            'java': ['junit', 'testng', 'mockito'],
            'go': ['testing', 'testify'],
            'rust': ['cargo test'],
            'ruby': ['rspec', 'minitest'],
            'php': ['phpunit'],
        }

        return frameworks.get(language, [])
