"""
LLM API Usage Analyzer - Detects and analyzes LLM/AI API calls in code.
"""
from typing import List, Dict, Optional
import re
from .base import BaseAnalyzer, AnalysisResult, Severity


class LLMUsageAnalyzer(BaseAnalyzer):
    """Analyzer for detecting LLM API calls and estimating costs."""

    # Pricing per 1K tokens (input/output) - approximate as of 2024
    MODEL_PRICING = {
        # OpenAI
        'gpt-4': {'input': 0.03, 'output': 0.06},
        'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
        'gpt-4o': {'input': 0.005, 'output': 0.015},
        'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
        'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015},
        'o1': {'input': 0.015, 'output': 0.06},
        'o1-mini': {'input': 0.003, 'output': 0.012},
        
        # Anthropic
        'claude-3-opus': {'input': 0.015, 'output': 0.075},
        'claude-3-sonnet': {'input': 0.003, 'output': 0.015},
        'claude-3-haiku': {'input': 0.00025, 'output': 0.00125},
        'claude-3.5-sonnet': {'input': 0.003, 'output': 0.015},
        
        # Google
        'gemini-pro': {'input': 0.00025, 'output': 0.0005},
        'gemini-1.5-pro': {'input': 0.00125, 'output': 0.005},
        'gemini-1.5-flash': {'input': 0.000075, 'output': 0.0003},
        
        # Mistral
        'mistral-large': {'input': 0.004, 'output': 0.012},
        'mistral-medium': {'input': 0.0027, 'output': 0.0081},
        'mistral-small': {'input': 0.001, 'output': 0.003},
        'codestral': {'input': 0.001, 'output': 0.003},
        'devstral': {'input': 0.001, 'output': 0.003},
        
        # Embeddings
        'text-embedding-3-small': {'input': 0.00002, 'output': 0},
        'text-embedding-3-large': {'input': 0.00013, 'output': 0},
        'text-embedding-ada-002': {'input': 0.0001, 'output': 0},
        
        # Cohere
        'command-r-plus': {'input': 0.003, 'output': 0.015},
        'command-r': {'input': 0.0005, 'output': 0.0015},
        
        # Default fallback
        'default': {'input': 0.002, 'output': 0.006},
    }

    # Patterns to detect LLM SDK usage
    LLM_PATTERNS = {
        'openai': {
            'patterns': [
                r'openai\.ChatCompletion\.create',
                r'openai\.Completion\.create',
                r'client\.chat\.completions\.create',
                r'client\.completions\.create',
                r'OpenAI\s*\(',
                r'AsyncOpenAI\s*\(',
                r'openai\.Client\s*\(',
                r'from\s+openai\s+import',
                r'import\s+openai',
            ],
            'provider': 'OpenAI',
            'severity': Severity.INFO
        },
        'anthropic': {
            'patterns': [
                r'anthropic\.messages\.create',
                r'client\.messages\.create',
                r'Anthropic\s*\(',
                r'AsyncAnthropic\s*\(',
                r'from\s+anthropic\s+import',
                r'import\s+anthropic',
            ],
            'provider': 'Anthropic',
            'severity': Severity.INFO
        },
        'litellm': {
            'patterns': [
                r'litellm\.completion',
                r'litellm\.acompletion',
                r'litellm\.embedding',
                r'from\s+litellm\s+import',
                r'import\s+litellm',
            ],
            'provider': 'LiteLLM',
            'severity': Severity.INFO
        },
        'langchain': {
            'patterns': [
                r'ChatOpenAI\s*\(',
                r'ChatAnthropic\s*\(',
                r'ChatGoogleGenerativeAI\s*\(',
                r'LLMChain\s*\(',
                r'ConversationChain\s*\(',
                r'from\s+langchain',
                r'from\s+langchain_openai',
                r'from\s+langchain_anthropic',
                r'from\s+langchain_google',
            ],
            'provider': 'LangChain',
            'severity': Severity.INFO
        },
        'azure_openai': {
            'patterns': [
                r'AzureOpenAI\s*\(',
                r'AsyncAzureOpenAI\s*\(',
                r'azure\.ai\.inference',
                r'AzureKeyCredential',
            ],
            'provider': 'Azure OpenAI',
            'severity': Severity.INFO
        },
        'google_ai': {
            'patterns': [
                r'genai\.GenerativeModel',
                r'vertexai\.generative_models',
                r'google\.generativeai',
                r'from\s+google\.generativeai',
                r'import\s+google\.generativeai',
            ],
            'provider': 'Google AI',
            'severity': Severity.INFO
        },
        'huggingface': {
            'patterns': [
                r'transformers\.pipeline',
                r'AutoModelForCausalLM',
                r'AutoTokenizer',
                r'from\s+transformers\s+import',
                r'HfApi\s*\(',
                r'InferenceClient\s*\(',
            ],
            'provider': 'Hugging Face',
            'severity': Severity.INFO
        },
        'cohere': {
            'patterns': [
                r'cohere\.Client',
                r'co\.generate',
                r'co\.chat',
                r'from\s+cohere\s+import',
                r'import\s+cohere',
            ],
            'provider': 'Cohere',
            'severity': Severity.INFO
        },
        'aws_bedrock': {
            'patterns': [
                r'bedrock-runtime',
                r'invoke_model',
                r'BedrockRuntime',
                r'boto3.*bedrock',
            ],
            'provider': 'AWS Bedrock',
            'severity': Severity.INFO
        },
        'llamaindex': {
            'patterns': [
                r'llama_index\.llms',
                r'from\s+llama_index',
                r'ServiceContext',
                r'VectorStoreIndex',
            ],
            'provider': 'LlamaIndex',
            'severity': Severity.INFO
        },
        'replicate': {
            'patterns': [
                r'replicate\.run',
                r'replicate\.stream',
                r'from\s+replicate\s+import',
                r'import\s+replicate',
            ],
            'provider': 'Replicate',
            'severity': Severity.INFO
        },
    }

    # Patterns that indicate potential issues
    ISSUE_PATTERNS = {
        'no_max_tokens': {
            'check': lambda code: 'max_tokens' not in code and 'max_completion_tokens' not in code,
            'message': 'No max_tokens set - could lead to unexpected high costs',
            'severity': Severity.MEDIUM,
            'suggestion': 'Set max_tokens to limit response length and control costs'
        },
        'no_timeout': {
            'check': lambda code: 'timeout' not in code,
            'message': 'No timeout configured - API calls could hang indefinitely',
            'severity': Severity.LOW,
            'suggestion': 'Add timeout parameter to prevent hanging requests'
        },
        'hardcoded_key': {
            'patterns': [
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'OPENAI_API_KEY\s*=\s*["\'][^"\']+["\']',
                r'sk-[a-zA-Z0-9]{32,}',
            ],
            'message': 'Potential hardcoded API key detected',
            'severity': Severity.CRITICAL,
            'suggestion': 'Use environment variables for API keys'
        },
        'no_retry': {
            'check': lambda code: 'retry' not in code.lower() and 'tenacity' not in code and 'backoff' not in code,
            'message': 'No retry logic detected - API calls may fail silently',
            'severity': Severity.LOW,
            'suggestion': 'Add retry logic with exponential backoff for resilience'
        },
        'no_streaming': {
            'check': lambda code: 'stream' not in code.lower(),
            'message': 'No streaming detected - long responses may cause timeouts',
            'severity': Severity.INFO,
            'suggestion': 'Consider using streaming for better UX and avoiding timeouts'
        },
        'sync_in_async': {
            'patterns': [
                r'async\s+def.*\n.*(?:openai|anthropic|litellm)\.(?!a)',
            ],
            'message': 'Synchronous LLM call in async function - may block event loop',
            'severity': Severity.MEDIUM,
            'suggestion': 'Use async version (acompletion, async client) in async functions'
        },
    }

    def get_name(self) -> str:
        """Get analyzer name."""
        return "LLM Usage"

    def get_analysis_prompt(self) -> str:
        """Get LLM usage analysis prompt."""
        return """You are an expert in LLM/AI API usage patterns. Analyze the provided code/diff for LLM API calls.

Detect and report on:
1. **LLM SDK Usage**: OpenAI, Anthropic, LiteLLM, LangChain, Azure OpenAI, Google AI, Cohere, AWS Bedrock, Hugging Face, LlamaIndex, Replicate
2. **Model Detection**: Identify which models are being used (gpt-4, claude-3, etc.)
3. **Cost Estimation**: Based on typical usage patterns
4. **Best Practices Issues**:
   - Missing max_tokens limits
   - No timeout configuration
   - Hardcoded API keys
   - Missing retry logic
   - Sync calls in async context
   - No streaming for long responses
   - No error handling
   - No rate limiting

For each LLM call found, provide:
- Severity: critical (security issues), high (cost/reliability), medium (best practices), low (optimization), info (informational)
- Title: Brief description
- Description: What was found and why it matters
- Line number: Where the issue occurs
- Suggestion: How to improve
- Provider: Which LLM provider (OpenAI, Anthropic, etc.)
- Model: Detected model name if available
- Estimated cost per call: If determinable

Return results in JSON format:
{
  "issues": [
    {
      "severity": "medium",
      "title": "OpenAI API call without max_tokens",
      "description": "GPT-4 call on line 42 has no token limit, which could lead to unexpectedly high costs",
      "line_number": 42,
      "suggestion": "Add max_tokens=4096 to limit response length and control costs",
      "provider": "OpenAI",
      "model": "gpt-4",
      "estimated_cost_per_call": "$0.03-0.12"
    }
  ],
  "summary": {
    "total_llm_calls": 3,
    "providers": ["OpenAI", "Anthropic"],
    "estimated_monthly_cost": "$50-200 (based on 1000 calls/day)"
  }
}

If no LLM API calls are found, return: {"issues": [], "summary": {"total_llm_calls": 0, "providers": [], "estimated_monthly_cost": "$0"}}
"""

    def analyze(self, code: str, filename: str, context: Optional[Dict] = None) -> List[AnalysisResult]:
        """
        Analyze code for LLM API usage.

        Args:
            code: Code or diff to analyze
            filename: File being analyzed
            context: Additional context

        Returns:
            List of LLM usage findings
        """
        if not self.enabled:
            return []

        results = []
        
        # Quick pattern-based detection for common issues
        results.extend(self._detect_llm_patterns(code, filename))
        results.extend(self._detect_issues(code, filename))
        
        return results

    def _detect_llm_patterns(self, code: str, filename: str) -> List[AnalysisResult]:
        """Detect LLM SDK patterns in code."""
        results = []
        detected_providers = set()
        
        lines = code.split('\n')
        
        for sdk_name, sdk_info in self.LLM_PATTERNS.items():
            for pattern in sdk_info['patterns']:
                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        provider = sdk_info['provider']
                        if provider not in detected_providers:
                            detected_providers.add(provider)
                            
                            # Detect model if possible
                            model = self._detect_model(code)
                            cost_info = self._get_cost_estimate(model)
                            
                            results.append(AnalysisResult(
                                severity=Severity.INFO,
                                category="LLM Usage",
                                title=f"{provider} API usage detected",
                                description=f"Found {provider} LLM API call. {cost_info}",
                                filename=filename,
                                line_number=line_num,
                                suggestion=f"Ensure proper error handling, rate limiting, and cost monitoring for {provider} API calls"
                            ))
                        break
        
        return results

    def _detect_model(self, code: str) -> Optional[str]:
        """Try to detect which model is being used."""
        model_patterns = [
            r'model\s*=\s*["\']([^"\']+)["\']',
            r'model_name\s*=\s*["\']([^"\']+)["\']',
            r'model_id\s*=\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in model_patterns:
            match = re.search(pattern, code)
            if match:
                return match.group(1)
        
        return None

    def _get_cost_estimate(self, model: Optional[str]) -> str:
        """Get cost estimate for a model."""
        if not model:
            return "Cost varies by model - monitor usage carefully"
        
        # Normalize model name
        model_lower = model.lower()
        
        for model_key, pricing in self.MODEL_PRICING.items():
            if model_key in model_lower:
                input_cost = pricing['input']
                output_cost = pricing['output']
                # Estimate based on average 1K input, 500 output tokens
                est_per_call = (input_cost * 1) + (output_cost * 0.5)
                return f"Estimated cost: ${est_per_call:.4f} per call (based on avg token usage)"
        
        return "Cost varies - check provider pricing"

    def _detect_issues(self, code: str, filename: str) -> List[AnalysisResult]:
        """Detect potential issues with LLM usage."""
        results = []
        
        # Only check for issues if LLM usage is detected
        has_llm_usage = any(
            re.search(pattern, code, re.IGNORECASE)
            for sdk_info in self.LLM_PATTERNS.values()
            for pattern in sdk_info['patterns']
        )
        
        if not has_llm_usage:
            return results
        
        for issue_name, issue_info in self.ISSUE_PATTERNS.items():
            triggered = False
            line_num = None
            
            if 'patterns' in issue_info:
                for pattern in issue_info['patterns']:
                    match = re.search(pattern, code, re.IGNORECASE | re.MULTILINE)
                    if match:
                        triggered = True
                        # Try to find line number
                        line_num = code[:match.start()].count('\n') + 1
                        break
            elif 'check' in issue_info:
                triggered = issue_info['check'](code)
            
            if triggered:
                results.append(AnalysisResult(
                    severity=issue_info['severity'],
                    category="LLM Usage",
                    title=issue_info['message'],
                    description=issue_info['message'],
                    filename=filename,
                    line_number=line_num,
                    suggestion=issue_info['suggestion']
                ))
        
        return results

    def get_supported_providers(self) -> List[str]:
        """Get list of supported LLM providers."""
        return [info['provider'] for info in self.LLM_PATTERNS.values()]

    def get_model_pricing(self, model: str) -> Dict[str, float]:
        """Get pricing for a specific model."""
        model_lower = model.lower()
        for model_key, pricing in self.MODEL_PRICING.items():
            if model_key in model_lower:
                return pricing
        return self.MODEL_PRICING['default']
