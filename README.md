# LLM API Usage Analyzer

Automated GitHub PR reviewer that detects and optimizes LLM (Large Language Model) API usage in your code. Powered by Mistral's Devstral-2-123b model via NVIDIA NIM APIs.

## Features

- **🔍 Detects LLM API Calls**: Identifies all LLM API usage (OpenAI, Anthropic, Mistral, Google, NVIDIA NIM, etc.)
- **🔑 Hardcoded Credentials**: Finds exposed API keys with line numbers
- **💰 Cost Optimization**: Suggests token limits, caching, and cheaper models
- **⚡ Performance Issues**: Detects missing retry logic, rate limiting, and inefficient patterns
- **💡 Detailed Suggestions**: Shows exact code examples for each issue
- **📍 Precise Location**: Reports exact line numbers and file locations
- **💵 Cost-Saving Alternatives**: Provides specific recommendations to reduce API costs

## What It Analyzes

### ✅ Detects:
1. **Hardcoded API Keys** (CRITICAL)
   - Exposed credentials in code
   - Recommendation: Move to environment variables/GitHub Secrets

2. **LLM API Calls** (INFO)
   - All LLM service integrations
   - Ensures safeguards are in place

3. **Missing Token Limits** (HIGH)
   - API calls without `max_tokens` parameter
   - Can lead to unexpectedly high costs

4. **Missing Retry Logic** (MEDIUM)
   - No error handling for transient failures
   - Suggestion: Use exponential backoff with tenacity

5. **Missing Caching** (MEDIUM)
   - No response caching for repeated queries
   - Potential 50-80% cost reduction with caching

## Example Output

Each issue appears as a **separate, detailed comment** on your PR:

```
🔴 **CRITICAL** [LLM Usage] - Hardcoded OpenAI API Key Found

File: `src/main.py`
Line: 15

### Issue
API key is hardcoded in src/main.py at line 15. This is a critical security
vulnerability - if exposed in version control, anyone can access your API
account and incur charges.

### How to Resolve
Immediately revoke this key. Move API keys to:
- Environment variables: `export OPENAI_API_KEY='...'`
- GitHub Secrets for Actions
- .env file (add .env to .gitignore)
- Use: `api_key = os.getenv('OPENAI_API_KEY')`

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

Clone this repository:

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

The workflow file is located at `.github/workflows/pr-review.yml`. It will automatically trigger on:
- Pull request opened
- New commits pushed to PR
- PR reopened

## Usage

### Option 1: Use in Your Own Repository

Once configured, the review runs automatically on every PR:

1. Create or push to a pull request
2. GitHub Action triggers automatically
3. AI analyzes LLM API usage
4. Individual comments posted for each issue

### Option 2: Use as a Reusable GitHub Action

Use this analyzer in any other repository:

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
          pr-number: ${{ github.event.pull_request.number }}
          log-level: INFO
```

### Option 3: Manual CLI Review

Run reviews locally:

```bash
python src/main.py \
  --pr-number 123 \
  --github-token $GITHUB_TOKEN \
  --nvidia-api-key $NVIDIA_API_KEY
```

## Configuration

Edit `config/default.yaml` to customize:

```yaml
analyzers:
  llm_usage:
    enabled: true
    check_hardcoded_keys: true
    check_missing_limits: true
    check_retry_logic: true
    estimate_costs: true

min_severity_for_comments: "low"  # Post comments for low, medium, high, critical
max_tokens_per_file: 4096
```

## Cost Optimization Tips

Based on the analyzer's suggestions:

| Issue | Solution | Savings |
|-------|----------|---------|
| Missing caching | Use functools.lru_cache or Redis | 50-80% |
| No token limits | Set max_tokens=1000-2000 | 20-40% |
| Wrong model | Use GPT-3.5 instead of GPT-4 | 10x cheaper |
| Long prompts | Optimize context windows | 10-30% |
| No batching | Batch requests together | 15-25% |

## Troubleshooting

### Review not running
1. Check GitHub Actions is enabled (Settings → Actions)
2. Verify `NVIDIA_API_KEY` secret is set
3. Check workflow logs in Actions tab

### No issues found
- Check if your code actually uses LLM APIs
- Ensure API calls match expected patterns
- Review logs for warnings

### API errors
1. Verify NVIDIA API key is valid
2. Check API endpoint accessibility
3. Ensure you have API quota remaining

## Project Structure

```
pr-reviewer-ai/
├── .github/workflows/      # GitHub Actions workflow
├── src/
│   ├── analyzers/
│   │   ├── llm_usage.py   # LLM API usage analyzer
│   │   └── base.py        # Base analyzer class
│   ├── main.py            # Entry point
│   ├── github_client.py   # GitHub API integration
│   ├── ai_reviewer.py     # NVIDIA NIM integration
│   ├── review_engine.py   # Core orchestration
│   ├── comment_formatter.py # GitHub comment formatting
│   └── prompts/           # AI prompts
├── config/                # Configuration files
├── tests/                 # Test suite
├── action.yml            # GitHub Action definition
└── requirements.txt      # Python dependencies
```

## Security

⚠️ **Important Security Notes:**

- **Never commit API keys** - Use environment variables or GitHub Secrets
- **Monitor key usage** - The analyzer helps detect exposure
- **Rotate keys regularly** - Best practice for API key management
- **Review suggestions carefully** - AI recommendations should be validated

## Dependencies

- `openai>=1.0.0` - OpenAI client (also used for NVIDIA NIM via OpenAI-compatible API)
- `PyGithub>=2.1.1` - GitHub API client
- `pyyaml>=6.0` - Configuration parsing
- `requests>=2.31.0` - HTTP requests

## Contributing

Contributions welcome! Areas for improvement:

- Add more LLM providers (Cohere, Replicate, etc.)
- Improve cost estimation accuracy
- Add caching pattern detection
- Support for more programming languages
- Performance optimizations

## License

[Add your license here]

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review troubleshooting section

## Acknowledgments

- Powered by Mistral Devstral-2-123b via NVIDIA NIM
- Built for optimizing LLM API usage and costs
- GitHub Actions integration for seamless CI/CD
