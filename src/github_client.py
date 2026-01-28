"""
GitHub API client for PR review operations.
"""
from typing import List, Dict, Optional
from github import Github, GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository
import logging

logger = logging.getLogger(__name__)


class GitHubClient:
    """Client for interacting with GitHub API for PR reviews."""

    def __init__(self, token: str, repository: str):
        """
        Initialize GitHub client.

        Args:
            token: GitHub personal access token
            repository: Repository in format 'owner/repo'
        """
        self.github = Github(token)
        self.repo = self.github.get_repo(repository)
        self.repository = repository

    def get_pull_request(self, pr_number: int) -> PullRequest:
        """
        Get pull request object.

        Args:
            pr_number: Pull request number

        Returns:
            PullRequest object
        """
        try:
            return self.repo.get_pull(pr_number)
        except GithubException as e:
            logger.error(f"Failed to fetch PR #{pr_number}: {e}")
            raise

    def get_pr_details(self, pr_number: int) -> Dict:
        """
        Get PR details including title, description, and metadata.

        Args:
            pr_number: Pull request number

        Returns:
            Dictionary with PR details
        """
        pr = self.get_pull_request(pr_number)
        return {
            'number': pr.number,
            'title': pr.title,
            'description': pr.body or '',
            'author': pr.user.login,
            'base_branch': pr.base.ref,
            'head_branch': pr.head.ref,
            'state': pr.state,
            'changed_files': pr.changed_files,
            'additions': pr.additions,
            'deletions': pr.deletions,
        }

    def get_pr_files(self, pr_number: int) -> List[Dict]:
        """
        Get list of files changed in the PR.

        Args:
            pr_number: Pull request number

        Returns:
            List of file information dictionaries
        """
        pr = self.get_pull_request(pr_number)
        files = []

        for file in pr.get_files():
            files.append({
                'filename': file.filename,
                'status': file.status,  # 'added', 'removed', 'modified', 'renamed'
                'additions': file.additions,
                'deletions': file.deletions,
                'changes': file.changes,
                'patch': file.patch,  # unified diff format
                'sha': file.sha,
            })

        return files

    def get_pr_diff(self, pr_number: int) -> str:
        """
        Get complete PR diff in unified format.

        Args:
            pr_number: Pull request number

        Returns:
            Complete diff as string
        """
        files = self.get_pr_files(pr_number)
        diff_parts = []

        for file in files:
            if file['patch']:
                diff_parts.append(f"--- a/{file['filename']}")
                diff_parts.append(f"+++ b/{file['filename']}")
                diff_parts.append(file['patch'])
                diff_parts.append('')  # Empty line between files

        return '\n'.join(diff_parts)

    def post_review_comment(
        self,
        pr_number: int,
        body: str,
        commit_id: str,
        path: str,
        line: int
    ) -> bool:
        """
        Post a review comment on a specific line.

        Args:
            pr_number: Pull request number
            body: Comment text
            commit_id: Commit SHA
            path: File path
            line: Line number

        Returns:
            True if successful, False otherwise
        """
        try:
            pr = self.get_pull_request(pr_number)
            pr.create_review_comment(
                body=body,
                commit=pr.get_commits()[pr.commits - 1],  # Latest commit
                path=path,
                line=line
            )
            logger.info(f"Posted comment on {path}:{line}")
            return True
        except GithubException as e:
            logger.error(f"Failed to post comment: {e}")
            return False

    def post_review_summary(
        self,
        pr_number: int,
        body: str,
        event: str = "COMMENT"
    ) -> bool:
        """
        Post a review summary comment.

        Args:
            pr_number: Pull request number
            body: Review summary text
            event: Review event type ('APPROVE', 'REQUEST_CHANGES', 'COMMENT')

        Returns:
            True if successful, False otherwise
        """
        try:
            pr = self.get_pull_request(pr_number)
            pr.create_review(
                body=body,
                event=event
            )
            logger.info(f"Posted review summary with event: {event}")
            return True
        except GithubException as e:
            logger.error(f"Failed to post review summary: {e}")
            return False

    def post_issue_comment(self, pr_number: int, body: str) -> bool:
        """
        Post a general comment on the PR (not a review comment).

        Args:
            pr_number: Pull request number
            body: Comment text

        Returns:
            True if successful, False otherwise
        """
        try:
            pr = self.get_pull_request(pr_number)
            pr.create_issue_comment(body)
            logger.info("Posted issue comment")
            return True
        except GithubException as e:
            logger.error(f"Failed to post issue comment: {e}")
            return False

    def get_latest_commit_sha(self, pr_number: int) -> str:
        """
        Get the SHA of the latest commit in the PR.

        Args:
            pr_number: Pull request number

        Returns:
            Commit SHA
        """
        pr = self.get_pull_request(pr_number)
        commits = list(pr.get_commits())
        return commits[-1].sha if commits else ""

    def should_skip_file(self, filename: str, exclusions: List[str]) -> bool:
        """
        Check if file should be skipped based on exclusion patterns.

        Args:
            filename: File path
            exclusions: List of patterns to exclude

        Returns:
            True if file should be skipped
        """
        import fnmatch

        for pattern in exclusions:
            if fnmatch.fnmatch(filename, pattern):
                return True
        return False
