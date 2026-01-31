# LLM API Usage Analyzer

Automated GitHub PR reviewer that detects and optimizes LLM (Large Language Model) API usage in your code. Powered by Mistral's Devstral-2-123b model via NVIDIA NIM APIs.

## Overview

This tool analyzes pull requests for LLM/AI API usage patterns, security vulnerabilities, and cost optimization opportunities. It supports 10+ different LLM providers and includes pricing information to help estimate API costs.

## Features

- **🔍 Multi-Provider Detection**: Supports OpenAI, Anthropic, LiteLLM, LangChain, Azure OpenAI, Google AI, Cohere, AWS Bedrock, Hugging Face, LlamaIndex, Replicate, and more
- **💰 Cost Estimation**: Automatically estimates costs based on detected models and pricing data
- **🔑 Security Scanning**: Detects hardcoded API keys and credentials
- **⚡ Best Practices**: Identifies missing token limits, timeouts, retry logic, and streaming
- **🎯 Performance Analysis**: Detects sync calls in async contexts and other efficiency issues
- **📍 Precise Reporting**: Shows exact line numbers and file locations for each issue
- **💡 Actionable Suggestions**: Provides specific code examples and recommendations

## Detected Issues

### Critical
- **Hardcoded API Keys**: Exposed credentials (security risk)

### High/Medium
- **Missing Token Limits**: No `max_tokens` parameter (cost control)
- **No Timeout Configuration**: API calls could hang indefinitely
- **Missing Retry Logic**: No error handling for transient failures
- **Sync in Async Context**: Blocking calls in async functions

### Low/Info
- **No Streaming**: Long responses may cause timeouts or poor UX
- **LLM API Usage Detection**: Informational - tracks all LLM integrations

## Supported LLM Providers

| Provider | SDK | Models Supported |
|----------|-----|-----------------|
| **OpenAI** | openai | GPT-4, GPT-4 Turbo, GPT-4o, GPT-3.5 Turbo, o1 |
| **Anthropic** | anthropic | Claude 3 Opus, Sonnet, Haiku, 3.5 Sonnet |
| **Google** | google-generativeai | Gemini Pro, 1.5 Pro, 1.5 Flash |
| **Mistral** | mistralai | Large, Medium, Small, Codestral, Devstral |
| **LiteLLM** | litellm | Multi-provider proxy |
| **LangChain** | langchain | Framework for all providers |
| **Azure OpenAI** | azure-openai | Azure-hosted models |
| **Cohere** | cohere | Command R+, Command R |
| **Hugging Face** | transformers | Open-source models |
| **AWS Bedrock** | boto3 | Bedrock runtime models |
| **LlamaIndex** | llama-index | Vector indexing framework |
| **Replicate** | replicate | Community models |

## Model Pricing Reference

The analyzer includes current pricing for 30+ models:

**OpenAI:**
- GPT-4: $0.03/$0.06 per 1K tokens (input/output)
- GPT-3.5-Turbo: $0.0005/$0.0015 per 1K tokens
- GPT-4o-mini: $0.00015/$0.0006 per 1K tokens (cheapest)

**Anthropic:**
- Claude 3 Opus: $0.015/$0.075 per 1K tokens
- Claude 3 Haiku: $0.00025/$0.00125 per 1K tokens (cheapest)

**Google:**
- Gemini 1.5 Flash: $0.000075/$0.0003 per 1K tokens (cheapest)

**Mistral:**
- Mistral Small: $0.001/$0.003 per 1K tokens (very cheap)

## Example Output

Each issue appears as a **separate, detailed comment** on your PR:

```
🔴 **CRITICAL** [LLM Usage] - Potential hardcoded API key detected

File: `src/llm_service.py`
Line: 15

### Issue
Potential hardcoded API key detected. This is a critical security
vulnerability - if exposed in version control, anyone can access your
API account and incur charges.

### How to Resolve
Use environment variables for API keys

### Cost-Saving Alternatives
- Use environment variables to secure keys
- Implement key rotation policies
- Monitor key usage to detect unauthorized access

---
*Review powered by AI using Mistral Devstral-2-123b*
```

## Setup

### 1. Prerequisites

- Python 3.11 or higher
- GitHub repository with Actions enabled
- NVIDIA NIM API key ([Get one here](https://build.nvidia.com/mistralai/devstral))

### 2. Installation

```bash
git clone https://github.com/Comptech-Enterprises/pr-reviewer-ai.git
cd pr-reviewer-ai
pip install -r requirements.txt
```

### 3. Configure GitHub Secrets

1. Go to your repository **Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Add:
   - **Name:** `NVIDIA_API_KEY`
   - **Value:** Your NVIDIA NIM API key from https://build.nvidia.com/

The `GITHUB_TOKEN` is automatically provided by GitHub Actions.

### 4. Enable GitHub Actions

The workflow file is at `.github/workflows/pr-review.yml`. It triggers automatically on:
- Pull request opened
- New commits pushed to PR
- PR reopened

## Usage

### Option 1: Automatic (GitHub Actions)

Once configured:

1. Create or push to a pull request
2. GitHub Actions triggers automatically
3. AI analyzes LLM API usage
4. Individual comments posted for each issue

### Option 2: Reusable GitHub Action

Use in any repository:

```yaml
name: LLM API Usage Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  llm-review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read

    steps:
      - uses: Comptech-Enterprises/pr-reviewer-ai@main
        with:
          nvidia-api-key: ${{ secrets.NVIDIA_API_KEY }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

### Option 3: Manual CLI Review

```bash
python src/main.py \
  --pr-number 123 \
  --github-token $GITHUB_TOKEN \
  --nvidia-api-key $NVIDIA_API_KEY
```

## Configuration

Edit `config/default.yaml`:

```yaml
analyzers:
  llm_usage:
    enabled: true
    check_hardcoded_keys: true
    check_missing_limits: true
    check_retry_logic: true
    estimate_costs: true

min_severity_for_comments: "low"  # critical, high, medium, low, info
max_files_to_review: 50
max_tokens_per_file: 4096
```

## Cost Optimization Tips

| Issue | Impact | Solution | Savings |
|-------|--------|----------|---------|
| Hardcoded key | Security risk | Move to env var | Security |
| No max_tokens | Unbounded costs | Add limit | 20-40% |
| No caching | Repeated charges | Implement cache | 50-80% |
| Wrong model | High costs | Use cheaper model | 10-100x |
| No retry logic | Failed calls | Add exponential backoff | Reliability |
| No timeout | Hanging requests | Set timeout | Prevents hangs |

### Example: Model Cost Comparison

For the same task with 1K input + 500 output tokens:

- **GPT-4**: $0.045 per call
- **GPT-4o-mini**: $0.0004 per call (**112x cheaper**)
- **Claude 3 Opus**: $0.0225 per call
- **Claude 3 Haiku**: $0.0004 per call (**56x cheaper**)
- **Mistral Small**: $0.0035 per call (**13x cheaper**)

## Troubleshooting

### Review not running

1. Check GitHub Actions is enabled (Settings → Actions)
2. Verify `NVIDIA_API_KEY` secret is set
3. Check workflow logs in Actions tab
4. Ensure PR has code changes

### No LLM issues found

- Verify your code uses an LLM SDK
- Check supported providers list above
- Review logs for pattern matching details

### API errors

1. Verify NVIDIA API key is valid
2. Check endpoint is accessible
3. Ensure you have API quota

## Project Structure

```
pr-reviewer-ai/
├── .github/workflows/           # GitHub Actions
├── src/
│   ├── analyzers/
│   │   ├── llm_usage.py        # LLM analysis engine
│   │   └── base.py             # Base analyzer
│   ├── main.py                 # Entry point
│   ├── github_client.py        # GitHub API
│   ├── ai_reviewer.py          # NVIDIA NIM client
│   ├── review_engine.py        # Orchestration
│   ├── comment_formatter.py    # Formatting
│   └── prompts/                # AI prompts
├── config/default.yaml         # Configuration
├── action.yml                  # GitHub Action definition
└── requirements.txt            # Dependencies
```

## How It Works

1. **PR Triggered**: GitHub Actions workflow starts on PR events
2. **Code Fetched**: Changed files retrieved via GitHub API
3. **LLM Detection**: Analyzer scans for LLM SDK usage patterns
4. **Cost Analysis**: Models detected and pricing looked up
5. **Issue Detection**: Security, configuration, and best-practice issues identified
6. **AI Enhancement**: NVIDIA NIM AI provides additional insights
7. **Comments Posted**: Individual comments for each issue with suggestions
8. **Summary**: Optional summary comment with aggregated findings

## Security

⚠️ **Important:**

- **Never commit API keys** - Use environment variables or GitHub Secrets
- **Monitor key usage** - The analyzer detects exposure
- **Rotate keys regularly** - Best practice for API key management
- **Review suggestions** - AI recommendations should be validated before applying

## Dependencies

- `openai>=1.0.0` - OpenAI client (also works with NVIDIA NIM)
- `PyGithub>=2.1.1` - GitHub API client
- `pyyaml>=6.0` - Configuration
- `requests>=2.31.0` - HTTP client

## Contributing

Areas for improvement:

- Add more LLM providers
- Improve cost estimation accuracy
- Add token counting for better estimates
- Support more programming languages
- Add caching pattern detection

## License

[Add your license here]

## Support

For issues or questions:
- Open an issue on GitHub
- Check troubleshooting section
- Review logs for details

## Acknowledgments

- Powered by Mistral Devstral-2-123b via NVIDIA NIM
- Multi-provider LLM detection and cost analysis
- Built for optimizing LLM API usage and costs
