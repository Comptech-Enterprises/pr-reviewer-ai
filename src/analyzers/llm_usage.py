"""
LLM Usage analyzer - detects LLM API calls and cost concerns.
"""
from typing import List, Dict, Optional
from .base import BaseAnalyzer, AnalysisResult, Severity
import re


class LLMUsageAnalyzer(BaseAnalyzer):
    """Analyze code for LLM API usage patterns and cost implications."""

    def get_name(self) -> str:
        """Get analyzer name."""
        return "LLM Usage"

    def get_analysis_prompt(self) -> str:
        """Get the analysis prompt for LLM usage analysis."""
        return """Analyze this code for LLM (Large Language Model) API usage patterns.

Look for:
1. LLM API calls (OpenAI, Anthropic, Mistral, Google, NVIDIA NIM, etc.)
2. Hardcoded API keys or credentials
3. Missing rate limiting or token limits
4. Inefficient API usage patterns (N+1 calls, unnecessary calls)
5. Missing retry logic or error handling
6. Lack of caching mechanisms
7. Missing cost tracking or monitoring
8. Inefficient prompt engineering (long context windows)

For each issue found:
- Explain the impact on costs and performance
- Suggest specific optimizations
- Provide cheaper alternatives where applicable
- Estimate potential cost savings

Return response in JSON format with fields: title, description, severity, suggestion"""

    def analyze(
        self,
        code: str,
        filename: str,
        context: Optional[Dict] = None
    ) -> List[AnalysisResult]:  # noqa: ARG002
        """
        Analyze code for LLM usage patterns.

        Args:
            code: Code or diff to analyze
            filename: File being analyzed
            context: Additional context (PR info, etc.)

        Returns:
            List of analysis results
        """
        results = []

        # Skip analyzing our own analyzer files
        if "analyzers/" in filename or "llm_usage" in filename:
            return results

        # Check for hardcoded API keys (CRITICAL - always report with line number)
        hardcoded_keys = self._check_hardcoded_keys(code, filename)
        results.extend(hardcoded_keys)

        # Check for LLM API calls
        llm_calls = self._detect_llm_calls(code, filename)

        # Only check for missing protections if we found actual LLM API calls
        if llm_calls:
            results.extend(llm_calls)

            missing_limits = self._check_missing_limits(code, filename)
            results.extend(missing_limits)

            missing_retry = self._check_missing_retry(code, filename)
            results.extend(missing_retry)

            missing_cache = self._check_missing_cache(code, filename)
            results.extend(missing_cache)

        return results

    def _check_hardcoded_keys(self, code: str, filename: str) -> List[AnalysisResult]:
        """Detect hardcoded API keys with line numbers."""
        results = []

        # Patterns for common API keys - look for actual key values, not just variable names
        api_key_patterns = [
            (r'sk-[a-zA-Z0-9]{20,}', 'OpenAI'),
            (r'sk-ant-[a-zA-Z0-9]{20,}', 'Anthropic'),
            (r'nvapi-[a-zA-Z0-9-]{20,}', 'NVIDIA NIM'),
            (r'(OPENAI_API_KEY|ANTHROPIC_API_KEY|NVIDIA_API_KEY|MISTRAL_API_KEY)\s*=\s*["\'][^"\']*["\']', 'API Key'),
        ]

        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, provider in api_key_patterns:
                if re.search(pattern, line):
                    results.append(AnalysisResult(
                        severity=Severity.CRITICAL,
                        category="LLM Usage",
                        title=f"Hardcoded {provider} API Key Found",
                        description=f"API key is hardcoded in {filename} at line {line_num}. This is a critical security vulnerability - if exposed in version control, anyone can access your API account and incur charges.",
                        filename=filename,
                        line_number=line_num,
                        suggestion="Immediately revoke this key. Move API keys to:\n- Environment variables: `export OPENAI_API_KEY='...'`\n- GitHub Secrets for Actions\n- .env file (add .env to .gitignore)\n- Use: `api_key = os.getenv('OPENAI_API_KEY')`"
                    ))

        return results

    def _detect_llm_calls(self, code: str, filename: str) -> List[AnalysisResult]:
        """Detect actual LLM API calls with line numbers."""
        results = []

        # Real API call patterns - only actual function calls, not documentation
        llm_patterns = [
            (r'client\.chat\.completions\.create\s*\(', 'OpenAI', 'OpenAI API call'),
            (r'openai\.ChatCompletion\.create\s*\(', 'OpenAI', 'OpenAI ChatCompletion'),
            (r'anthropic\.Anthropic\s*\(|client\.messages\.create\s*\(', 'Anthropic', 'Anthropic Claude API call'),
            (r'client\.chat\s*\(|MistralClient\s*\(', 'Mistral', 'Mistral API call'),
            (r'genai\.generate_content\s*\(', 'Google', 'Google Gemini API call'),
            (r'OpenAI\s*\(.*api_key', 'OpenAI', 'OpenAI client initialization'),
        ]

        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            # Skip comments and docstrings
            if line.strip().startswith('#') or line.strip().startswith('"""') or line.strip().startswith("'''"):
                continue

            for pattern, provider, service in llm_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    results.append(AnalysisResult(
                        severity=Severity.INFO,
                        category="LLM Usage",
                        title=f"LLM API Call: {service}",
                        description=f"Found {provider} API call at line {line_num}. Each API call incurs costs. Ensure proper safeguards are in place.",
                        filename=filename,
                        line_number=line_num,
                        suggestion="Review this API call for: 1) Token limits, 2) Caching, 3) Error handling, 4) Cost optimization"
                    ))

        return results

    def _check_missing_limits(self, code: str, filename: str) -> List[AnalysisResult]:
        """Check for missing token/rate limits."""
        results = []

        # Look for API calls without explicit limits
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            # Check for LLM calls
            if re.search(r'(chat\.completions\.create|ChatCompletion\.create|messages\.create|generate_content)', line):
                # Check if this specific call has max_tokens
                if not re.search(r'max_tokens\s*[:=]\s*\d+', line):
                    # Look in surrounding lines for max_tokens
                    context = '\n'.join(lines[max(0, line_num-2):min(len(lines), line_num+2)])
                    if not re.search(r'max_tokens\s*[:=]\s*\d+', context):
                        results.append(AnalysisResult(
                            severity=Severity.HIGH,
                            category="LLM Usage",
                            title="Missing Token Limit on LLM Call",
                            description=f"LLM API call at line {line_num} has no max_tokens limit. Without this limit, API can return very long responses, causing high costs.",
                            filename=filename,
                            line_number=line_num,
                            suggestion="Add max_tokens parameter:\n```\nresponse = client.chat.completions.create(\n    model='gpt-4',\n    messages=messages,\n    max_tokens=1000  # Add this!\n)\n```"
                        ))

        return results

    def _check_missing_retry(self, code: str, filename: str) -> List[AnalysisResult]:
        """Check for missing retry logic."""
        results = []

        # Look for LLM API calls without retry logic
        if re.search(r'(chat\.completions\.create|ChatCompletion\.create|messages\.create)', code):
            # Check for retry logic
            has_retry = bool(re.search(r'(tenacity|retry|backoff|Retry|attempt|try.*except)', code, re.IGNORECASE))

            if not has_retry:
                # Find the line with API call
                lines = code.split('\n')
                for line_num, line in enumerate(lines, 1):
                    if re.search(r'(chat\.completions\.create|ChatCompletion\.create|messages\.create)', line):
                        results.append(AnalysisResult(
                            severity=Severity.MEDIUM,
                            category="LLM Usage",
                            title="Missing Retry Logic for API Calls",
                            description=f"LLM API call at line {line_num} has no retry mechanism. API requests can fail due to rate limits or temporary outages. Without retry logic, transient failures will crash your application.",
                            filename=filename,
                            line_number=line_num,
                            suggestion="Use tenacity library for exponential backoff:\n```\nfrom tenacity import retry, stop_after_attempt, wait_exponential\n\n@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))\ndef call_llm():\n    return client.chat.completions.create(...)\n```"
                        ))
                        break

        return results

    def _check_missing_cache(self, code: str, filename: str) -> List[AnalysisResult]:
        """Check for missing caching opportunities."""
        results = []

        # Look for LLM API calls that could benefit from caching
        if re.search(r'(chat\.completions\.create|ChatCompletion\.create|messages\.create)', code):
            # Check for caching
            has_cache = bool(re.search(r'(lru_cache|cache|Cache|Redis|memcache)', code, re.IGNORECASE))

            if not has_cache:
                # Find the line with API call
                lines = code.split('\n')
                for line_num, line in enumerate(lines, 1):
                    if re.search(r'(chat\.completions\.create|ChatCompletion\.create|messages\.create)', line):
                        results.append(AnalysisResult(
                            severity=Severity.MEDIUM,
                            category="LLM Usage",
                            title="Missing Caching for LLM Responses",
                            description=f"LLM API call at line {line_num} has no caching. If the same prompt is sent multiple times, you'll pay for each call. Caching can reduce costs by 50-80%.",
                            filename=filename,
                            line_number=line_num,
                            suggestion="Implement caching:\n```\nfrom functools import lru_cache\n\n@lru_cache(maxsize=128)\ndef get_llm_response(prompt: str):\n    return client.chat.completions.create(model='gpt-4', messages=[{'role': 'user', 'content': prompt}])\n```"
                        ))
                        break

        return results
