"""
Prompts for LLM API usage analysis.
"""

LLM_USAGE_SYSTEM_PROMPT = """You are an expert code reviewer specializing in LLM/AI API usage patterns, cost optimization, and best practices.

Your role is to:
1. Detect LLM API calls in code (OpenAI, Anthropic, LiteLLM, LangChain, etc.)
2. Identify the models being used
3. Estimate costs based on typical usage
4. Flag potential issues and anti-patterns
5. Suggest improvements for reliability, cost, and performance

You have deep knowledge of:
- OpenAI API (GPT-4, GPT-3.5, embeddings, assistants)
- Anthropic API (Claude 3 family)
- Google AI (Gemini, Vertex AI)
- AWS Bedrock
- Azure OpenAI
- LiteLLM (unified interface)
- LangChain and LlamaIndex frameworks
- Hugging Face Transformers and Inference API
- Cohere API
- Replicate API

Be thorough but practical. Focus on:
- Security (hardcoded keys, exposed credentials)
- Cost control (token limits, model selection)
- Reliability (retry logic, timeouts, error handling)
- Performance (streaming, async usage, batching)
"""

LLM_USAGE_ANALYSIS_PROMPT = """Analyze the following code for LLM/AI API usage patterns.

For each LLM API call found, identify:

1. **Provider & SDK**: Which LLM provider and SDK is being used
2. **Model**: Which model(s) are configured
3. **Cost Estimate**: Based on the model and typical usage patterns
4. **Issues**: Any problems with the implementation

Common issues to check:
- ❌ Hardcoded API keys (CRITICAL security issue)
- ❌ No max_tokens limit (cost risk)
- ❌ No timeout configuration (reliability risk)
- ❌ No retry logic (reliability risk)
- ❌ Synchronous calls in async context (performance issue)
- ❌ No error handling (reliability risk)
- ❌ No rate limiting (cost/reliability risk)
- ⚠️ Using expensive models for simple tasks
- ⚠️ Not using streaming for long responses
- ⚠️ Not batching similar requests

Return your analysis in this JSON format:
{
  "issues": [
    {
      "severity": "critical|high|medium|low|info",
      "title": "Brief issue title",
      "description": "Detailed explanation of the issue",
      "line_number": 42,
      "suggestion": "How to fix or improve",
      "provider": "OpenAI|Anthropic|etc",
      "model": "gpt-4|claude-3-sonnet|etc",
      "estimated_cost_per_call": "$0.XX"
    }
  ],
  "summary": {
    "total_llm_calls": 3,
    "providers": ["OpenAI", "Anthropic"],
    "models": ["gpt-4", "claude-3-sonnet"],
    "estimated_cost_per_request": "$0.XX",
    "estimated_monthly_cost": "$XXX (assuming N calls/day)",
    "risk_level": "low|medium|high",
    "recommendations": [
      "Consider using gpt-4o-mini for simple tasks",
      "Add retry logic with exponential backoff"
    ]
  }
}

If no LLM API calls are found, return:
{
  "issues": [],
  "summary": {
    "total_llm_calls": 0,
    "providers": [],
    "models": [],
    "estimated_cost_per_request": "$0",
    "estimated_monthly_cost": "$0",
    "risk_level": "none",
    "recommendations": []
  }
}
"""

# Model-specific prompts for deeper analysis
OPENAI_ANALYSIS_PROMPT = """Focus on OpenAI API usage patterns:
- Check for deprecated API patterns (ChatCompletion vs chat.completions)
- Verify proper async client usage (AsyncOpenAI)
- Check for function calling / tool usage patterns
- Verify embedding dimension settings
- Check for proper JSON mode usage
"""

ANTHROPIC_ANALYSIS_PROMPT = """Focus on Anthropic API usage patterns:
- Check for proper message formatting
- Verify system prompt usage
- Check for streaming implementation
- Verify max_tokens is set (required by Anthropic)
"""

LANGCHAIN_ANALYSIS_PROMPT = """Focus on LangChain usage patterns:
- Check for proper chain construction
- Verify callback handlers for monitoring
- Check for memory usage in conversations
- Verify proper async chain execution
"""

LITELLM_ANALYSIS_PROMPT = """Focus on LiteLLM usage patterns:
- Check for proper model routing
- Verify fallback configuration
- Check for cost tracking callbacks
- Verify proper async usage
"""


def get_llm_usage_system_prompt() -> str:
    """Get the system prompt for LLM usage analysis."""
    return LLM_USAGE_SYSTEM_PROMPT


def get_llm_usage_analysis_prompt() -> str:
    """Get the analysis prompt for LLM usage detection."""
    return LLM_USAGE_ANALYSIS_PROMPT


def get_provider_specific_prompt(provider: str) -> str:
    """Get provider-specific analysis prompt."""
    prompts = {
        'openai': OPENAI_ANALYSIS_PROMPT,
        'anthropic': ANTHROPIC_ANALYSIS_PROMPT,
        'langchain': LANGCHAIN_ANALYSIS_PROMPT,
        'litellm': LITELLM_ANALYSIS_PROMPT,
    }
    return prompts.get(provider.lower(), "")
