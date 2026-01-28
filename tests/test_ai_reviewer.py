"""
Tests for AI reviewer.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.ai_reviewer import AIReviewer


class TestAIReviewer:
    """Test cases for AIReviewer."""

    @patch('src.ai_reviewer.OpenAI')
    def test_initialization(self, mock_openai):
        """Test AI reviewer initialization."""
        reviewer = AIReviewer(
            api_key="test_key",
            api_base="https://test.api.com/v1",
            model="test-model"
        )

        assert reviewer.model == "test-model"
        assert reviewer.max_retries == 3
        mock_openai.assert_called_once()

    @patch('src.ai_reviewer.OpenAI')
    def test_analyze_code_success(self, mock_openai):
        """Test successful code analysis."""
        # Setup mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"issues": []}'

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        reviewer = AIReviewer(api_key="test_key")
        result = reviewer.analyze_code(
            code="def test(): pass",
            filename="test.py",
            system_prompt="You are a reviewer",
            analysis_prompt="Analyze this code"
        )

        assert result == '{"issues": []}'
        mock_client.chat.completions.create.assert_called_once()

    @patch('src.ai_reviewer.OpenAI')
    def test_analyze_code_with_retry(self, mock_openai):
        """Test code analysis with retries on failure."""
        # Setup mock to fail first, then succeed
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"issues": []}'

        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = [
            Exception("API Error"),
            mock_response
        ]
        mock_openai.return_value = mock_client

        reviewer = AIReviewer(api_key="test_key", retry_delay=0)
        result = reviewer.analyze_code(
            code="def test(): pass",
            filename="test.py",
            system_prompt="You are a reviewer",
            analysis_prompt="Analyze this code"
        )

        assert result == '{"issues": []}'
        assert mock_client.chat.completions.create.call_count == 2

    @patch('src.ai_reviewer.OpenAI')
    def test_analyze_diff(self, mock_openai):
        """Test diff analysis."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"issues": []}'

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        reviewer = AIReviewer(api_key="test_key")
        result = reviewer.analyze_diff(
            diff="+def new_function(): pass",
            filename="test.py",
            system_prompt="You are a reviewer",
            analysis_prompt="Analyze this diff",
            context={'pr_title': 'Test PR'}
        )

        assert result is not None
        # Check that context was included in the call
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        assert 'Test PR' in messages[1]['content']

    @patch('src.ai_reviewer.OpenAI')
    def test_count_tokens_estimate(self, mock_openai):
        """Test token counting estimation."""
        reviewer = AIReviewer(api_key="test_key")

        text = "a" * 400  # 400 characters
        tokens = reviewer.count_tokens_estimate(text)

        # Should be approximately 100 tokens (4 chars per token)
        assert 90 <= tokens <= 110

    @patch('src.ai_reviewer.OpenAI')
    def test_chunk_large_file(self, mock_openai):
        """Test chunking of large files."""
        reviewer = AIReviewer(api_key="test_key")

        # Create large content
        lines = ["line " + str(i) for i in range(1000)]
        content = "\n".join(lines)

        chunks = reviewer.chunk_large_file(content, max_chunk_tokens=100)

        # Should create multiple chunks
        assert len(chunks) > 1

        # Each chunk should be smaller than max
        for chunk in chunks:
            tokens = reviewer.count_tokens_estimate(chunk)
            assert tokens <= 110  # Some tolerance

    @patch('src.ai_reviewer.OpenAI')
    def test_batch_analyze(self, mock_openai):
        """Test batch analysis of multiple files."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"issues": []}'

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        reviewer = AIReviewer(api_key="test_key")

        files = [
            {'filename': 'file1.py', 'content': 'def test1(): pass'},
            {'filename': 'file2.py', 'content': 'def test2(): pass'}
        ]

        results = reviewer.batch_analyze(
            files=files,
            system_prompt="You are a reviewer",
            analysis_prompt="Analyze this code"
        )

        assert len(results) == 2
        assert results[0]['filename'] == 'file1.py'
        assert results[1]['filename'] == 'file2.py'
