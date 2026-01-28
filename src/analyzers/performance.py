"""
Performance analyzer.
"""
from typing import List, Dict, Optional
from .base import BaseAnalyzer, AnalysisResult


class PerformanceAnalyzer(BaseAnalyzer):
    """Analyzer for performance issues."""

    def get_name(self) -> str:
        """Get analyzer name."""
        return "Performance"

    def get_analysis_prompt(self) -> str:
        """Get performance analysis prompt."""
        return """You are a performance optimization expert reviewing code for efficiency issues. Analyze the provided code/diff.

Focus on identifying:
1. Inefficient algorithms
   - O(n²) loops where O(n) or O(n log n) is possible
   - Unnecessary nested loops
   - Inefficient searching/sorting

2. Memory issues
   - Memory leaks
   - Excessive allocations
   - Large object creation in loops
   - Missing resource cleanup

3. Database performance
   - N+1 query problems
   - Missing database indexes
   - Inefficient queries (SELECT *)
   - Large result sets without pagination

4. Async/concurrency issues
   - Blocking operations in async code
   - Missing await keywords
   - Unnecessary synchronous calls
   - Inefficient thread usage

5. I/O performance
   - Reading large files into memory
   - Missing streaming for large data
   - Inefficient file operations
   - Unnecessary disk writes

6. Caching opportunities
   - Repeated expensive computations
   - Missing memoization
   - Inefficient cache usage

7. Network performance
   - Multiple sequential API calls (could be parallel)
   - Missing request batching
   - Large payload sizes

For each issue found, provide:
- Severity: high, medium, low, or info
- Title: Brief description
- Description: Detailed explanation of the performance impact
- Line number: Where issue occurs
- Suggestion: How to optimize

Return results in JSON format:
{
  "issues": [
    {
      "severity": "high",
      "title": "N+1 query problem",
      "description": "This code makes a database query inside a loop, resulting in N+1 queries instead of a single query with JOIN",
      "line_number": 78,
      "suggestion": "Use a single query with JOIN or eager loading to fetch all related data at once"
    }
  ]
}

If no performance issues are found, return: {"issues": []}
"""

    def analyze(self, code: str, filename: str, context: Optional[Dict] = None) -> List[AnalysisResult]:
        """
        Analyze code for performance issues.

        Args:
            code: Code or diff to analyze
            filename: File being analyzed
            context: Additional context

        Returns:
            List of performance findings
        """
        if not self.enabled:
            return []

        # Actual analysis happens via AI in review_engine
        return []

    def get_performance_patterns(self, language: Optional[str]) -> List[Dict]:
        """
        Get performance anti-patterns to look for.

        Args:
            language: Programming language

        Returns:
            List of pattern dictionaries
        """
        patterns = []

        if language == 'python':
            patterns.extend([
                {
                    'name': 'List comprehension in loop',
                    'description': 'List comprehension inside loop can be inefficient',
                    'severity': 'medium'
                },
                {
                    'name': 'String concatenation in loop',
                    'description': 'Use join() instead of += for strings in loops',
                    'severity': 'medium'
                }
            ])
        elif language in ['javascript', 'typescript']:
            patterns.extend([
                {
                    'name': 'Synchronous forEach with async',
                    'description': 'Using forEach with async functions does not wait',
                    'severity': 'high'
                },
                {
                    'name': 'Missing Promise.all',
                    'description': 'Sequential awaits could be parallelized',
                    'severity': 'medium'
                }
            ])

        return patterns
