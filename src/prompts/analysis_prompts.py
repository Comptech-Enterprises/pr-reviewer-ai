"""
Analysis-specific prompts for different review categories.
"""


def get_analysis_prompt(category: str, language: str = None) -> str:
    """
    Get the analysis prompt for a specific category.

    Args:
        category: Review category (security, quality, performance, testing)
        language: Programming language (optional)

    Returns:
        Analysis prompt string
    """
    prompts = {
        'security': get_security_prompt(language),
        'quality': get_quality_prompt(language),
        'performance': get_performance_prompt(language),
        'testing': get_testing_prompt(language)
    }

    return prompts.get(category.lower(), get_general_prompt())


def get_security_prompt(language: str = None) -> str:
    """Get security analysis prompt."""
    base_prompt = """Analyze this code for security vulnerabilities.

Look for:
1. Injection flaws (SQL, XSS, command injection, LDAP, etc.)
2. Broken authentication and session management
3. Sensitive data exposure
4. XML external entities (XXE)
5. Broken access control
6. Security misconfiguration
7. Cross-Site Scripting (XSS)
8. Insecure deserialization
9. Using components with known vulnerabilities
10. Insufficient logging and monitoring
11. Server-side request forgery (SSRF)
12. Hardcoded credentials or secrets

For each vulnerability:
- Assess exploitability and impact
- Provide specific remediation steps
- Reference relevant security standards (OWASP, CWE)
"""

    language_specific = {
        'python': """

Python-specific security concerns:
- Pickle deserialization vulnerabilities
- Use of eval(), exec(), or compile() with user input
- SQL injection via string formatting in database queries
- Command injection via os.system() or subprocess with shell=True
- Path traversal in file operations
- Unsafe YAML loading (yaml.load vs yaml.safe_load)
- Missing input validation in Flask/Django views
""",
        'javascript': """

JavaScript-specific security concerns:
- XSS via innerHTML, dangerouslySetInnerHTML
- Prototype pollution
- ReDoS (Regular Expression Denial of Service)
- Unsafe use of eval(), Function(), setTimeout/setInterval with strings
- Missing CSRF protection
- Insecure JWT validation
- Missing input sanitization in React/Vue/Angular
""",
        'java': """

Java-specific security concerns:
- SQL injection in JDBC queries
- XML injection and XXE attacks
- Deserialization vulnerabilities
- Path traversal in file operations
- Missing input validation
- Improper exception handling exposing sensitive info
"""
    }

    if language and language.lower() in language_specific:
        return base_prompt + language_specific[language.lower()]

    return base_prompt


def get_quality_prompt(language: str = None) -> str:
    """Get code quality analysis prompt."""
    return """Analyze this code for quality and maintainability issues.

Review for:
1. Code smells (long methods, large classes, duplicate code, etc.)
2. SOLID principle violations
3. Poor naming conventions
4. High complexity (cyclomatic complexity, nesting depth)
5. Missing or poor documentation
6. Inadequate error handling
7. Tight coupling and low cohesion
8. Magic numbers and hardcoded values
9. Inconsistent code style
10. Dead code or unused variables

Provide:
- Specific refactoring suggestions
- Better naming alternatives where applicable
- How to simplify complex logic
- Where to add documentation
"""


def get_performance_prompt(language: str = None) -> str:
    """Get performance analysis prompt."""
    base_prompt = """Analyze this code for performance issues and optimization opportunities.

Look for:
1. Inefficient algorithms (O(n²) where O(n) possible, etc.)
2. Unnecessary loops or iterations
3. Memory leaks or excessive allocations
4. Database query inefficiencies (N+1 queries, missing indexes)
5. Blocking operations in async code
6. Missing caching opportunities
7. Inefficient I/O operations
8. Unnecessary computations
9. Suboptimal data structures
10. Resource leaks (unclosed files, connections, etc.)

For each issue:
- Explain the performance impact
- Suggest specific optimizations
- Estimate complexity improvement where applicable
"""

    language_specific = {
        'python': """

Python-specific performance concerns:
- List comprehensions vs generator expressions
- String concatenation in loops (use join())
- Global variable lookups
- Missing __slots__ in classes with many instances
- Inefficient use of pandas operations
- GIL implications for threading
""",
        'javascript': """

JavaScript-specific performance concerns:
- Unnecessary re-renders in React
- Missing memoization (useMemo, useCallback)
- Inefficient DOM manipulation
- Missing debouncing/throttling
- Synchronous loops with async operations (use Promise.all)
- Memory leaks from event listeners
"""
    }

    if language and language.lower() in language_specific:
        return base_prompt + language_specific[language.lower()]

    return base_prompt


def get_testing_prompt(language: str = None) -> str:
    """Get testing analysis prompt."""
    return """Analyze this code change for testing requirements and gaps.

Assess:
1. What new functionality needs testing
2. What edge cases are not covered
3. What error paths need tests
4. Whether existing tests need updates
5. Missing integration tests
6. Test quality issues
7. Over-reliance on mocks (should be integration tests)
8. Missing assertions or unclear test intent

Suggest:
- Specific test cases to add
- Edge cases to cover
- Test improvements for clarity
- Where to use mocks vs real dependencies
- Test organization improvements
"""


def get_general_prompt() -> str:
    """Get general review prompt."""
    return """Analyze this code comprehensively for any issues or improvements.

Consider:
1. Correctness and logic errors
2. Security vulnerabilities
3. Performance issues
4. Code quality and maintainability
5. Testing needs
6. Documentation quality

Provide actionable, specific feedback.
"""


def get_diff_review_prompt() -> str:
    """Get prompt specifically for reviewing diffs."""
    return """You are reviewing a code change (diff). Focus on:

1. What changed and why
2. Potential bugs introduced by the change
3. Security implications of the change
4. Performance impact
5. Breaking changes or compatibility issues
6. Missing tests for the change
7. Documentation updates needed

Context matters:
- Consider how changes integrate with existing code
- Look for incomplete refactoring
- Check for missing related changes

Be specific about line numbers in your feedback.
"""


def get_summary_prompt(
    pr_title: str,
    pr_description: str,
    files_changed: int,
    additions: int,
    deletions: int
) -> str:
    """
    Get prompt for generating PR summary.

    Args:
        pr_title: PR title
        pr_description: PR description
        files_changed: Number of files changed
        additions: Lines added
        deletions: Lines deleted

    Returns:
        Summary generation prompt
    """
    return f"""Generate a concise summary of this pull request review.

PR Details:
- Title: {pr_title}
- Description: {pr_description}
- Files changed: {files_changed}
- Lines added: {additions}
- Lines deleted: {deletions}

Include:
1. Overall assessment (approve, request changes, or comment)
2. Key security concerns (if any)
3. Major quality issues (if any)
4. Performance concerns (if any)
5. Testing gaps (if any)
6. Positive aspects worth highlighting

Keep summary under 500 words.
"""
