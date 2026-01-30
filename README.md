# AI Code Review System

Automated GitHub PR review system powered by Mistral's Devstral-2-123b model via NVIDIA NIM APIs. This system analyzes pull requests for security vulnerabilities, code quality issues, performance problems, and testing coverage.

## Features

- **🔒 Security Analysis**: Detect SQL injection, XSS, authentication issues, hardcoded secrets, and more
- **✨ Code Quality Review**: Check for code smells, SOLID violations, naming issues, and complexity
- **⚡ Performance Analysis**: Identify inefficient algorithms, memory issues, N+1 queries, and optimization opportunities
- **🧪 Testing Suggestions**: Recommend test cases for new code, edge cases, and test improvements
- **🤖 AI-Powered**: Uses Mistral Devstral-2-123b, a state-of-the-art code model via NVIDIA NIM
- **📊 Detailed Reports**: Inline comments and comprehensive PR summaries

## Architecture

```
GitHub PR Event → GitHub Action → Review Engine → Devstral AI → Comments on PR
```

#####
This is a test PR

#####
## Setup

### 1. Prerequisites

- Python 3.9 or higher
- GitHub repository with Actions enabled
- NVIDIA NIM API key ([Get one here](https://build.nvidia.com/mistralai/devstral))

### 2. Installation

Clone this repository or add files to your project:

```bash
git clone <your-repo>
cd code_assist
pip install -r requirements.txt
```

### 3. Configuration

#### GitHub Repository Setup

1. Go to your repository **Settings** → **Secrets and variables** → **Actions**
2. Add the following secret:
   - `NVIDIA_API_KEY`: Your NVIDIA NIM API key

The `GITHUB_TOKEN` is automatically provided by GitHub Actions.

#### Local Setup (for testing)

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPOSITORY=owner/repo
GITHUB_PR_NUMBER=1
NVIDIA_API_KEY=your_nvidia_api_key
```

### 4. Enable GitHub Actions

The workflow file is located at `.github/workflows/pr-review.yml`. It will automatically trigger on:
- Pull request opened
- New commits pushed to PR
- PR reopened

**Note:** GitHub Actions must be enabled in your repository settings. This is the default for most repositories.

## Usage

### Automated (GitHub Actions)

#### Option 1: Use in Your Own Repository

Once configured, the review runs automatically on every PR:

1. Create or update a pull request
2. GitHub Action triggers automatically
3. AI reviews the changed code
4. Comments posted to PR with findings
5. Summary comment added to PR

#### Option 2: Use as a Reusable Action

This repository is also published as a reusable GitHub Action. Use it in any other repository:

1. **Add the workflow file** to any repository (`.github/workflows/ai-review.yml`):

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  ai-review:
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

2. **Set up secrets** in the target repository:
   - Go to **Settings → Secrets and variables → Actions**
   - Add `NVIDIA_API_KEY` with your NVIDIA NIM API key

3. **Create a PR** - the action will automatically run and review your code!

**Action Inputs:**
- `nvidia-api-key` (required): Your NVIDIA NIM API key
- `github-token` (required): GitHub token for PR operations (use `${{ secrets.GITHUB_TOKEN }}`)
- `pr-number` (optional): PR number to review (defaults to current PR)
- `log-level` (optional): Logging level - `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`)

**Action Outputs:**
- `files-reviewed`: Number of files reviewed
- `total-issues`: Total number of issues found
- `review-complete`: Whether review completed successfully

### Manual (Command Line)

You can also run reviews manually:

```bash
python src/main.py \
  --pr-number 123 \
  --github-token $GITHUB_TOKEN \
  --github-repo owner/repo \
  --nvidia-api-key $NVIDIA_API_KEY
```

Options:
- `--pr-number`: PR number to review (required)
- `--github-token`: GitHub token (or use `GITHUB_TOKEN` env var)
- `--github-repo`: Repository in `owner/repo` format
- `--nvidia-api-key`: NVIDIA API key
- `--config`: Custom config file path
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `--dry-run`: Run without posting comments

## Configuration

### Main Configuration (`config/default.yaml`)

```yaml
analyzers:
  security:
    enabled: true
  quality:
    enabled: true
  performance:
    enabled: true
  testing:
    enabled: true

exclusions:
  - "*.lock"
  - "*.min.js"
  - "node_modules/*"
  - "dist/*"

max_files_to_review: 50
min_severity_for_comments: "low"
```

### Customization

You can customize:

1. **Enable/disable analyzers**: Toggle specific review categories
2. **Exclusion patterns**: Skip generated files, dependencies, etc.
3. **Severity thresholds**: Only post comments above certain severity
4. **Formatting**: Toggle emojis, category labels
5. **AI settings**: Temperature, max tokens, retries

## Example Output

### Inline Comment

```
🔴 **CRITICAL** [Security] **SQL Injection vulnerability**

User input is directly concatenated into SQL query without sanitization on line 42.

💡 **Suggestion:**
Use parameterized queries or an ORM to prevent SQL injection:
```python
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

### Summary Comment

```markdown
## 🤖 AI Code Review Summary

**PR:** Add user authentication
**Author:** @johndoe
**Changes:** 5 files, +234 -12

### 📊 Found 8 issue(s) across 3 categories

**By Severity:**
- 🔴 Critical: 1
- 🟠 High: 2
- 🟡 Medium: 3
- 🔵 Low: 2

**By Category:**
- Security: 3 issue(s)
- Code Quality: 3 issue(s)
- Testing: 2 issue(s)

### 🚨 Critical & High Priority Issues

- **SQL Injection vulnerability** (Security) in `src/auth.py` Line 42
- **Missing input validation** (Security) in `src/api.py` Line 128
- **N+1 query problem** (Performance) in `src/users.py` Line 56
```

## GitHub Actions Requirements

**Is GitHub Actions required?**

**For automation:** Yes. The GitHub Actions workflow (`.github/workflows/pr-review.yml`) is what triggers the review automatically when PRs are created or updated. Without it, you would need to run reviews manually.

**Alternatives to GitHub Actions:**
- Run manually via command line (see Manual Usage above)
- Set up webhooks to trigger reviews from another CI/CD system
- Use cron jobs to periodically check for new PRs

**GitHub Actions must be enabled** in your repository settings for automatic reviews. Check: Repository → Settings → Actions → Allow all actions and reusable workflows.

## Troubleshooting

### Review not running

1. Check GitHub Actions is enabled
2. Verify `NVIDIA_API_KEY` secret is set
3. Check workflow logs in Actions tab
4. Ensure repository has pull request permissions

### API rate limits

- GitHub API: 5000 requests/hour for authenticated requests
- NVIDIA NIM: Check your API plan limits
- Reduce `max_workers` in config if hitting rate limits

### Comments not posting

1. Verify `GITHUB_TOKEN` has write permissions
2. Check PR is not from a fork (restricted by default)
3. Review logs for error messages
4. Ensure `min_severity_for_comments` isn't too high

### AI not detecting issues

1. Check NVIDIA API key is valid
2. Verify API endpoint is accessible
3. Review prompts in `src/prompts/` for your use case
4. Check AI response in logs (use `--log-level DEBUG`)

## Development

### Project Structure

```
code_assist/
├── .github/workflows/     # GitHub Actions workflow
├── config/                # Configuration files
├── src/
│   ├── analyzers/         # Analysis modules (security, quality, etc.)
│   ├── prompts/           # AI prompts
│   ├── main.py           # Entry point
│   ├── github_client.py  # GitHub API client
│   ├── ai_reviewer.py    # AI integration
│   ├── review_engine.py  # Core orchestration
│   ├── diff_parser.py    # Diff parsing
│   └── comment_formatter.py  # Comment formatting
└── tests/                # Test suite
```

### Running Tests

```bash
pytest tests/
```

### Adding Custom Analyzers

1. Create new analyzer in `src/analyzers/`
2. Inherit from `BaseAnalyzer`
3. Implement required methods
4. Add to `review_engine.py`
5. Update config to enable/disable

## Cost Estimation

NVIDIA NIM API costs vary by plan. Approximate token usage:
- Small PR (5 files): ~10,000 tokens
- Medium PR (20 files): ~40,000 tokens
- Large PR (50 files): ~100,000 tokens

Check current pricing at https://build.nvidia.com/

## Security Considerations

- Store API keys in GitHub Secrets, never commit them
- Review AI suggestions before applying (AI can make mistakes)
- This tool performs **defensive security analysis only**
- Does not assist with offensive security or credential harvesting

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

[Add your license here]

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review troubleshooting section above

## Acknowledgments

- Powered by Mistral Devstral-2-123b via NVIDIA NIM
- Built for defensive security and code quality improvement
- Inspired by automated code review best practices
