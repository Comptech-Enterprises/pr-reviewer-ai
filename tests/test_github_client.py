"""
Tests for GitHub client.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.github_client import GitHubClient


class TestGitHubClient:
    """Test cases for GitHubClient."""

    @patch('src.github_client.Github')
    def test_initialization(self, mock_github):
        """Test client initialization."""
        mock_github.return_value.get_repo.return_value = Mock()

        client = GitHubClient(token="test_token", repository="owner/repo")

        assert client.repository == "owner/repo"
        mock_github.assert_called_once_with("test_token")

    @patch('src.github_client.Github')
    def test_get_pr_details(self, mock_github):
        """Test getting PR details."""
        # Setup mock PR
        mock_pr = Mock()
        mock_pr.number = 123
        mock_pr.title = "Test PR"
        mock_pr.body = "Test description"
        mock_pr.user.login = "testuser"
        mock_pr.base.ref = "main"
        mock_pr.head.ref = "feature"
        mock_pr.state = "open"
        mock_pr.changed_files = 5
        mock_pr.additions = 100
        mock_pr.deletions = 50

        mock_repo = Mock()
        mock_repo.get_pull.return_value = mock_pr
        mock_github.return_value.get_repo.return_value = mock_repo

        client = GitHubClient(token="test_token", repository="owner/repo")
        details = client.get_pr_details(123)

        assert details['number'] == 123
        assert details['title'] == "Test PR"
        assert details['author'] == "testuser"
        assert details['changed_files'] == 5

    @patch('src.github_client.Github')
    def test_get_pr_files(self, mock_github):
        """Test getting PR files."""
        # Setup mock files
        mock_file1 = Mock()
        mock_file1.filename = "file1.py"
        mock_file1.status = "modified"
        mock_file1.additions = 10
        mock_file1.deletions = 5
        mock_file1.changes = 15
        mock_file1.patch = "@@ -1,5 +1,10 @@"
        mock_file1.sha = "abc123"

        mock_pr = Mock()
        mock_pr.get_files.return_value = [mock_file1]

        mock_repo = Mock()
        mock_repo.get_pull.return_value = mock_pr
        mock_github.return_value.get_repo.return_value = mock_repo

        client = GitHubClient(token="test_token", repository="owner/repo")
        files = client.get_pr_files(123)

        assert len(files) == 1
        assert files[0]['filename'] == "file1.py"
        assert files[0]['status'] == "modified"
        assert files[0]['additions'] == 10

    @patch('src.github_client.Github')
    def test_should_skip_file(self, mock_github):
        """Test file exclusion logic."""
        mock_github.return_value.get_repo.return_value = Mock()

        client = GitHubClient(token="test_token", repository="owner/repo")

        exclusions = ["*.lock", "node_modules/*", "*.min.js"]

        assert client.should_skip_file("package-lock.json", exclusions) is True
        assert client.should_skip_file("node_modules/test.js", exclusions) is True
        assert client.should_skip_file("app.min.js", exclusions) is True
        assert client.should_skip_file("src/main.py", exclusions) is False

    @patch('src.github_client.Github')
    def test_post_review_comment(self, mock_github):
        """Test posting review comment."""
        mock_commit = Mock()
        mock_pr = Mock()
        mock_pr.get_commits.return_value = [mock_commit]
        mock_pr.commits = 1
        mock_pr.create_review_comment.return_value = Mock()

        mock_repo = Mock()
        mock_repo.get_pull.return_value = mock_pr
        mock_github.return_value.get_repo.return_value = mock_repo

        client = GitHubClient(token="test_token", repository="owner/repo")
        success = client.post_review_comment(
            pr_number=123,
            body="Test comment",
            commit_id="abc123",
            path="test.py",
            line=42
        )

        assert success is True
        mock_pr.create_review_comment.assert_called_once()

    @patch('src.github_client.Github')
    def test_post_issue_comment(self, mock_github):
        """Test posting issue comment."""
        mock_pr = Mock()
        mock_pr.create_issue_comment.return_value = Mock()

        mock_repo = Mock()
        mock_repo.get_pull.return_value = mock_pr
        mock_github.return_value.get_repo.return_value = mock_repo

        client = GitHubClient(token="test_token", repository="owner/repo")
        success = client.post_issue_comment(
            pr_number=123,
            body="Summary comment"
        )

        assert success is True
        mock_pr.create_issue_comment.assert_called_once_with("Summary comment")
