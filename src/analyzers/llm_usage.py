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

        # Check for hardcoded API keys
        hardcoded_keys = self._check_hardcoded_keys(code, filename)
        results.extend(hardcoded_keys)

        # Check for LLM API calls
        llm_calls = self._detect_llm_calls(code, filename)
        results.extend(llm_calls)

        # Check for missing protections
        if llm_calls:
            missing_limits = self._check_missing_limits(code, filename)
            results.extend(missing_limits)

            missing_retry = self._check_missing_retry(code, filename)
            results.extend(missing_retry)

            missing_cache = self._check_missing_cache(code, filename)
            results.extend(missing_cache)

        return results

    def _check_hardcoded_keys(self, code: str, filename: str) -> List[AnalysisResult]:
        """Detect hardcoded API keys."""
        results = []

        # Patterns for common API keys
        api_key_patterns = [
            (r'(OPENAI_API_KEY|openai_api_key)\s*=\s*["\']sk-[a-zA-Z0-9]+["\']', 'OpenAI'),
            (r'(ANTHROPIC_API_KEY|anthropic_api_key)\s*=\s*["\']sk-ant-[a-zA-Z0-9]+["\']', 'Anthropic'),
            (r'(NVIDIA_API_KEY|nvidia_api_key)\s*=\s*["\']nvapi-[a-zA-Z0-9-]+["\']', 'NVIDIA NIM'),
            (r'(MISTRAL_API_KEY|mistral_api_key)\s*=\s*["\'][a-zA-Z0-9]+["\']', 'Mistral'),
            (r'(api[_-]?key|apikey)\s*[:=]\s*["\'](?!YOUR|your|YOUR_API_KEY)[a-zA-Z0-9-]{20,}["\']', 'Generic'),
        ]

        for pattern, provider in api_key_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                results.append(AnalysisResult(
                    severity=Severity.CRITICAL,
                    category="LLM Usage",
                    title=f"Hardcoded {provider} API Key",
                    description=f"Found hardcoded {provider} API key in {filename}. This is a major security risk - keys can be compromised if exposed in version control.",
                    filename=filename,
                    suggestion="Move API keys to environment variables or GitHub Secrets. Use: import os; api_key = os.getenv('OPENAI_API_KEY')"
                ))

        return results

    def _detect_llm_calls(self, code: str, filename: str) -> List[AnalysisResult]:
        """Detect LLM API calls in code."""
        results = []

        # Patterns for LLM API calls
        llm_patterns = [
            (r'openai\.ChatCompletion\.create|client\.chat\.completions\.create', 'OpenAI', 'OpenAI ChatCompletion'),
            (r'claude-|messages\.create\(|anthropic\.Anthropic', 'Anthropic', 'Anthropic Claude'),
            (r'mistralai|mistral\.Mistral', 'Mistral', 'Mistral API'),
            (r'google\.generativeai|genai\.generate', 'Google', 'Google Gemini'),
            (r'nvidia\.nims|integrate\.api\.nvidia\.com', 'NVIDIA', 'NVIDIA NIM'),
        ]

        for pattern, provider, service in llm_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                results.append(AnalysisResult(
                    severity=Severity.INFO,
                    category="LLM Usage",
                    title=f"LLM API Call Detected: {service}",
                    description=f"Found {provider} API usage in {filename}. LLM API calls have associated costs - ensure they're optimized.",
                    filename=filename,
                    suggestion="Consider: 1) Caching responses, 2) Using cheaper models, 3) Token limit enforcement, 4) Batch processing"
                ))

        return results

    def _check_missing_limits(self, code: str, filename: str) -> List[AnalysisResult]:
        """Check for missing token/rate limits."""
        results = []

        # Look for API calls without explicit limits
        if re.search(r'(chat\.completions\.create|ChatCompletion\.create)', code):
            # Check if max_tokens is set
            if not re.search(r'max_tokens\s*[:=]\s*\d+', code):
                results.append(AnalysisResult(
                    severity=Severity.HIGH,
                    category="LLM Usage",
                    title="Missing Token Limit on LLM Call",
                    description=f"LLM API call in {filename} has no max_tokens limit. This can lead to unexpectedly high costs.",
                    filename=filename,
                    suggestion="Add max_tokens parameter: client.chat.completions.create(..., max_tokens=1000)"
                ))

            # Check if temperature is optimized for cost
            if not re.search(r'temperature\s*[:=]\s*0[.,](0|1|2)', code):
                results.append(AnalysisResult(
                    severity=Severity.LOW,
                    category="LLM Usage",
                    title="Temperature Not Optimized for Cost",
                    description=f"Temperature in {filename} not set to low value. Higher temperature increases computation costs.",
                    filename=filename,
                    suggestion="Use lower temperature (0.0-0.2) for deterministic tasks to reduce costs. Higher temp (0.7-1.0) only when needed."
                ))

        return results

    def _check_missing_retry(self, code: str, filename: str) -> List[AnalysisResult]:
        """Check for missing retry logic."""
        results = []

        if re.search(r'(chat\.completions\.create|ChatCompletion\.create)', code):
            # Check for retry logic
            has_retry = bool(re.search(r'(retry|Retry|backoff|Backoff|tenacity)', code))

            if not has_retry:
                results.append(AnalysisResult(
                    severity=Severity.MEDIUM,
                    category="LLM Usage",
                    title="Missing Retry Logic for API Calls",
                    description=f"LLM API calls in {filename} have no retry mechanism. Transient failures will cause errors.",
                    filename=filename,
                    suggestion="Implement exponential backoff: use tenacity library or implement retry with exponential backoff (e.g., 2s, 4s, 8s)"
                ))

        return results

    def _check_missing_cache(self, code: str, filename: str) -> List[AnalysisResult]:
        """Check for missing caching opportunities."""
        results = []

        if re.search(r'(chat\.completions\.create|ChatCompletion\.create)', code):
            # Check for caching
            has_cache = bool(re.search(r'(cache|Cache|lru_cache|Redis|sqlite)', code))

            if not has_cache:
                results.append(AnalysisResult(
                    severity=Severity.MEDIUM,
                    category="LLM Usage",
                    title="No Caching for LLM Responses",
                    description=f"LLM responses in {filename} are not cached. Identical queries will be charged multiple times.",
                    filename=filename,
                    suggestion="Implement caching:\n- Simple: functools.lru_cache for function results\n- Advanced: Redis/memcached for distributed caching\n- Cost savings: 50-80% reduction for repeated queries"
                ))

        return results
