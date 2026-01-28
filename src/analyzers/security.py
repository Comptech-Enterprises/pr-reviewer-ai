"""
Security vulnerability analyzer.
"""
from typing import List, Dict, Optional
from .base import BaseAnalyzer, AnalysisResult


class SecurityAnalyzer(BaseAnalyzer):
    """Analyzer for security vulnerabilities."""

    def get_name(self) -> str:
        """Get analyzer name."""
        return "Security"

    def get_analysis_prompt(self) -> str:
        """Get security analysis prompt."""
        return """You are a security expert reviewing code for vulnerabilities. Analyze the provided code/diff for security issues.

Focus on detecting:
1. SQL Injection vulnerabilities (unsanitized SQL queries, string concatenation)
2. Cross-Site Scripting (XSS) - unsafe HTML rendering, unescaped user input
3. Authentication/Authorization issues (weak auth, missing access controls)
4. Hardcoded secrets and credentials (API keys, passwords, tokens)
5. Insecure dependencies and outdated libraries
6. CSRF vulnerabilities (missing CSRF tokens)
7. Path traversal risks (unsanitized file paths)
8. Command injection (unsafe system calls, shell execution)
9. Insecure cryptography (weak algorithms, hardcoded keys)
10. Information disclosure (verbose errors, exposed debug info)

For each issue found, provide:
- Severity: critical, high, medium, low, or info
- Title: Brief description (one line)
- Description: Detailed explanation of the vulnerability
- Line number: Specific line where issue occurs (if applicable)
- Suggestion: How to fix the issue

Return results in JSON format:
{
  "issues": [
    {
      "severity": "high",
      "title": "SQL Injection vulnerability",
      "description": "User input is directly concatenated into SQL query without sanitization",
      "line_number": 42,
      "suggestion": "Use parameterized queries or an ORM to prevent SQL injection"
    }
  ]
}

If no security issues are found, return: {"issues": []}
"""

    def analyze(self, code: str, filename: str, context: Optional[Dict] = None) -> List[AnalysisResult]:
        """
        Analyze code for security vulnerabilities.

        Args:
            code: Code or diff to analyze
            filename: File being analyzed
            context: Additional context

        Returns:
            List of security findings
        """
        if not self.enabled:
            return []

        # Language-specific checks could be added here
        language = self.get_language_from_filename(filename)

        # For now, return empty - actual analysis happens via AI in review_engine
        # This method is called by the review engine with AI results
        return []

    def get_security_patterns(self, language: Optional[str]) -> List[Dict]:
        """
        Get security patterns to look for based on language.

        Args:
            language: Programming language

        Returns:
            List of pattern dictionaries
        """
        patterns = []

        # Common patterns across languages
        common_patterns = [
            {
                'name': 'Hardcoded credentials',
                'patterns': [
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
                    r'secret\s*=\s*["\'][^"\']+["\']',
                    r'token\s*=\s*["\'][^"\']+["\']',
                ],
                'severity': 'critical'
            },
            {
                'name': 'Potential secrets in comments',
                'patterns': [
                    r'#.*password.*:.*',
                    r'//.*api.*key.*',
                ],
                'severity': 'medium'
            }
        ]

        patterns.extend(common_patterns)

        # Language-specific patterns
        if language == 'python':
            patterns.extend([
                {
                    'name': 'SQL Injection',
                    'patterns': [
                        r'execute\([^)]*%.*\)',
                        r'\.format\(.*\).*execute',
                        r'f["\'].*SELECT.*{.*}',
                    ],
                    'severity': 'critical'
                },
                {
                    'name': 'Command Injection',
                    'patterns': [
                        r'os\.system\(',
                        r'subprocess\.call\(.*shell=True',
                        r'eval\(',
                        r'exec\(',
                    ],
                    'severity': 'high'
                }
            ])
        elif language in ['javascript', 'typescript']:
            patterns.extend([
                {
                    'name': 'XSS vulnerability',
                    'patterns': [
                        r'innerHTML\s*=',
                        r'dangerouslySetInnerHTML',
                        r'document\.write\(',
                    ],
                    'severity': 'high'
                },
                {
                    'name': 'Eval usage',
                    'patterns': [
                        r'eval\(',
                        r'Function\(',
                        r'setTimeout\(["\']',
                        r'setInterval\(["\']',
                    ],
                    'severity': 'high'
                }
            ])
        elif language == 'sql':
            patterns.extend([
                {
                    'name': 'Dynamic SQL',
                    'patterns': [
                        r'EXECUTE.*\+',
                        r'EXEC.*CONCAT',
                    ],
                    'severity': 'critical'
                }
            ])

        return patterns
