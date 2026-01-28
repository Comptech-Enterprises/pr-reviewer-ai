"""
Main entry point for AI Code Review system.
"""
import os
import sys
import argparse
import logging
import yaml
from pathlib import Path
from dotenv import load_dotenv

from github_client import GitHubClient
from ai_reviewer import AIReviewer
from review_engine import ReviewEngine


def setup_logging(level: str = "INFO"):
    """
    Configure logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_config(config_path: str = None) -> dict:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file (optional)

    Returns:
        Configuration dictionary
    """
    # Default config path
    if not config_path:
        config_path = Path(__file__).parent.parent / "config" / "default.yaml"

    if not os.path.exists(config_path):
        logging.warning(f"Config file not found: {config_path}, using defaults")
        return {}

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    return config or {}


def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="AI-powered code review for GitHub Pull Requests"
    )

    parser.add_argument(
        '--pr-number',
        type=int,
        required=True,
        help='Pull request number to review'
    )

    parser.add_argument(
        '--github-token',
        help='GitHub access token (or set GITHUB_TOKEN env var)'
    )

    parser.add_argument(
        '--github-repo',
        help='GitHub repository in format owner/repo (or set GITHUB_REPOSITORY env var)'
    )

    parser.add_argument(
        '--nvidia-api-key',
        help='NVIDIA API key (or set NVIDIA_API_KEY env var)'
    )

    parser.add_argument(
        '--nvidia-api-base',
        default='https://integrate.api.nvidia.com/v1',
        help='NVIDIA NIM API base URL'
    )

    parser.add_argument(
        '--config',
        help='Path to configuration YAML file'
    )

    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )

    parser.add_argument(
        '--post-summary-only',
        action='store_true',
        help='Only post summary comment, skip inline comments'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run analysis but do not post comments to GitHub'
    )

    return parser.parse_args()


def validate_environment(args) -> dict:
    """
    Validate required environment variables and arguments.

    Args:
        args: Parsed arguments

    Returns:
        Dictionary with validated configuration

    Raises:
        ValueError: If required variables are missing
    """
    # Load .env file if present
    load_dotenv()

    # GitHub token
    github_token = args.github_token or os.getenv('GITHUB_TOKEN')
    if not github_token:
        raise ValueError(
            "GitHub token is required. Provide via --github-token or GITHUB_TOKEN env var"
        )

    # GitHub repository
    github_repo = args.github_repo or os.getenv('GITHUB_REPOSITORY')
    if not github_repo:
        raise ValueError(
            "GitHub repository is required. Provide via --github-repo or GITHUB_REPOSITORY env var"
        )

    # NVIDIA API key
    nvidia_api_key = args.nvidia_api_key or os.getenv('NVIDIA_API_KEY')
    if not nvidia_api_key:
        raise ValueError(
            "NVIDIA API key is required. Provide via --nvidia-api-key or NVIDIA_API_KEY env var"
        )

    return {
        'github_token': github_token,
        'github_repo': github_repo,
        'nvidia_api_key': nvidia_api_key,
        'nvidia_api_base': args.nvidia_api_base or os.getenv(
            'NVIDIA_API_BASE',
            'https://integrate.api.nvidia.com/v1'
        )
    }


def main():
    """Main execution function."""
    # Parse arguments
    args = parse_arguments()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    try:
        # Validate environment
        logger.info("Validating environment...")
        env_config = validate_environment(args)

        # Load configuration
        logger.info("Loading configuration...")
        config = load_config(args.config)

        # Initialize GitHub client
        logger.info(f"Initializing GitHub client for {env_config['github_repo']}...")
        github_client = GitHubClient(
            token=env_config['github_token'],
            repository=env_config['github_repo']
        )

        # Initialize AI reviewer
        logger.info("Initializing AI reviewer...")
        ai_reviewer = AIReviewer(
            api_key=env_config['nvidia_api_key'],
            api_base=env_config['nvidia_api_base'],
            max_retries=config.get('model', {}).get('max_retries', 3),
            retry_delay=config.get('model', {}).get('retry_delay', 2)
        )

        # Initialize review engine
        logger.info("Initializing review engine...")
        review_engine = ReviewEngine(
            github_client=github_client,
            ai_reviewer=ai_reviewer,
            config=config
        )

        # Run review
        logger.info(f"Starting review of PR #{args.pr_number}...")
        results = review_engine.review_pull_request(args.pr_number)

        # Log results
        logger.info("=" * 60)
        logger.info("Review completed successfully!")
        logger.info(f"PR Number: {results['pr_number']}")
        logger.info(f"Files Reviewed: {results['files_reviewed']}")
        logger.info(f"Total Issues Found: {results['total_issues']}")
        logger.info("Issues by category:")
        for category, count in results['results_by_category'].items():
            logger.info(f"  - {category}: {count}")
        logger.info("=" * 60)

        # Exit with success
        sys.exit(0)

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
