"""
Tests for the LLM Usage Analyzer.
"""
import pytest
from src.analyzers.llm_usage import LLMUsageAnalyzer
from src.analyzers.base import Severity


class TestLLMUsageAnalyzer:
    """Test cases for LLMUsageAnalyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = LLMUsageAnalyzer({'enabled': True})

    def test_analyzer_name(self):
        """Test analyzer name."""
        assert self.analyzer.get_name() == "LLM Usage"

    def test_detect_openai_usage(self):
        """Test detection of OpenAI API usage."""
        code = '''
from openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
'''
        results = self.analyzer.analyze(code, "test.py")
        
        # Should detect OpenAI usage
        assert len(results) > 0
        providers = [r.title for r in results if "OpenAI" in r.title]
        assert len(providers) > 0

    def test_detect_anthropic_usage(self):
        """Test detection of Anthropic API usage."""
        code = '''
import anthropic

client = Anthropic()
message = client.messages.create(
    model="claude-3-sonnet",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
)
'''
        results = self.analyzer.analyze(code, "test.py")
        
        # Should detect Anthropic usage
        assert len(results) > 0
        providers = [r.title for r in results if "Anthropic" in r.title]
        assert len(providers) > 0

    def test_detect_litellm_usage(self):
        """Test detection of LiteLLM usage."""
        code = '''
import litellm

response = litellm.completion(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello"}]
)
'''
        results = self.analyzer.analyze(code, "test.py")
        
        # Should detect LiteLLM usage
        assert len(results) > 0
        providers = [r.title for r in results if "LiteLLM" in r.title]
        assert len(providers) > 0

    def test_detect_langchain_usage(self):
        """Test detection of LangChain usage."""
        code = '''
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4")
response = llm.invoke("Hello")
'''
        results = self.analyzer.analyze(code, "test.py")
        
        # Should detect LangChain usage
        assert len(results) > 0
        providers = [r.title for r in results if "LangChain" in r.title]
        assert len(providers) > 0

    def test_detect_hardcoded_api_key(self):
        """Test detection of hardcoded API keys."""
        code = '''
from openai import OpenAI

client = OpenAI(api_key="sk-1234567890abcdefghijklmnopqrstuvwxyz")
'''
        results = self.analyzer.analyze(code, "test.py")
        
        # Should detect hardcoded key with CRITICAL severity
        critical_issues = [r for r in results if r.severity == Severity.CRITICAL]
        assert len(critical_issues) > 0

    def test_detect_missing_max_tokens(self):
        """Test detection of missing max_tokens."""
        code = '''
from openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
'''
        results = self.analyzer.analyze(code, "test.py")
        
        # Should detect missing max_tokens
        token_issues = [r for r in results if "max_tokens" in r.title.lower()]
        assert len(token_issues) > 0

    def test_no_issues_without_llm_code(self):
        """Test that no issues are reported for non-LLM code."""
        code = '''
def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
'''
        results = self.analyzer.analyze(code, "test.py")
        
        # Should not detect any LLM issues
        assert len(results) == 0

    def test_detect_model_name(self):
        """Test model detection from code."""
        code = '''
response = client.chat.completions.create(
    model="gpt-4-turbo",
    messages=[{"role": "user", "content": "Hello"}]
)
'''
        model = self.analyzer._detect_model(code)
        assert model == "gpt-4-turbo"

    def test_get_cost_estimate(self):
        """Test cost estimation for known models."""
        # GPT-4 should have a cost estimate
        cost = self.analyzer._get_cost_estimate("gpt-4")
        assert "0.0600" in cost or "per call" in cost
        
        # Unknown model should return generic message
        cost = self.analyzer._get_cost_estimate(None)
        assert "varies" in cost.lower()

    def test_model_pricing_lookup(self):
        """Test model pricing lookup."""
        pricing = self.analyzer.get_model_pricing("gpt-4")
        assert pricing['input'] == 0.03
        assert pricing['output'] == 0.06
        
        pricing = self.analyzer.get_model_pricing("claude-3-sonnet")
        assert pricing['input'] == 0.003
        assert pricing['output'] == 0.015

    def test_supported_providers(self):
        """Test listing of supported providers."""
        providers = self.analyzer.get_supported_providers()
        
        expected_providers = [
            'OpenAI', 'Anthropic', 'LiteLLM', 'LangChain',
            'Azure OpenAI', 'Google AI', 'Hugging Face',
            'Cohere', 'AWS Bedrock', 'LlamaIndex', 'Replicate'
        ]
        
        for provider in expected_providers:
            assert provider in providers

    def test_disabled_analyzer(self):
        """Test that disabled analyzer returns no results."""
        disabled_analyzer = LLMUsageAnalyzer({'enabled': False})
        
        code = '''
from openai import OpenAI
client = OpenAI()
'''
        results = disabled_analyzer.analyze(code, "test.py")
        assert len(results) == 0

    def test_azure_openai_detection(self):
        """Test detection of Azure OpenAI usage."""
        code = '''
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key="xxx",
    api_version="2024-02-15-preview",
    azure_endpoint="https://xxx.openai.azure.com"
)
'''
        results = self.analyzer.analyze(code, "test.py")
        
        # Should detect Azure OpenAI usage
        assert len(results) > 0
        azure_issues = [r for r in results if "Azure" in r.title or "azure" in r.description.lower()]
        assert len(azure_issues) > 0

    def test_google_ai_detection(self):
        """Test detection of Google AI usage."""
        code = '''
import google.generativeai as genai

genai.configure(api_key="xxx")
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("Hello")
'''
        results = self.analyzer.analyze(code, "test.py")
        
        # Should detect Google AI usage
        assert len(results) > 0
        google_issues = [r for r in results if "Google" in r.title]
        assert len(google_issues) > 0


# Sample code snippets for manual testing
SAMPLE_OPENAI_CODE = '''
from openai import OpenAI

# Initialize client
client = OpenAI()

def chat_with_gpt(prompt: str) -> str:
    """Chat with GPT-4."""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content
'''

SAMPLE_LITELLM_CODE = '''
import litellm
from litellm import completion

# Using LiteLLM for multi-provider support
def query_llm(prompt: str, model: str = "gpt-3.5-turbo"):
    response = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000
    )
    return response.choices[0].message.content
'''

SAMPLE_INSECURE_CODE = '''
from openai import OpenAI

# BAD: Hardcoded API key
client = OpenAI(api_key="sk-proj-abc123xyz789")

def unsafe_chat(prompt):
    # BAD: No max_tokens limit
    # BAD: No timeout
    # BAD: No error handling
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
'''


if __name__ == "__main__":
    # Run basic test
    analyzer = LLMUsageAnalyzer({'enabled': True})
    
    print("Testing OpenAI detection:")
    results = analyzer.analyze(SAMPLE_OPENAI_CODE, "openai_example.py")
    for r in results:
        print(f"  - [{r.severity.name}] {r.title}")
    
    print("\nTesting LiteLLM detection:")
    results = analyzer.analyze(SAMPLE_LITELLM_CODE, "litellm_example.py")
    for r in results:
        print(f"  - [{r.severity.name}] {r.title}")
    
    print("\nTesting insecure code detection:")
    results = analyzer.analyze(SAMPLE_INSECURE_CODE, "insecure_example.py")
    for r in results:
        print(f"  - [{r.severity.name}] {r.title}: {r.suggestion}")
