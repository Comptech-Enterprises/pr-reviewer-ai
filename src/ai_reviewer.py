"""
AI Reviewer using Mistral Devstral-2-123b via NVIDIA NIM APIs.
"""
from typing import Dict, List, Optional
import logging
import time
from openai import OpenAI

logger = logging.getLogger(__name__)


class AIReviewer:
    """AI-powered code reviewer using Devstral via NVIDIA NIM."""

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://integrate.api.nvidia.com/v1",
        model: str = "mistralai/devstral-2-123b-instruct-2512",
        max_retries: int = 3,
        retry_delay: int = 2
    ):
        """
        Initialize AI reviewer.

        Args:
            api_key: NVIDIA API key
            api_base: NVIDIA NIM API base URL
            model: Model identifier
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base
        )
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def analyze_code(
        self,
        code: str,
        filename: str,
        system_prompt: str,
        analysis_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096
    ) -> Optional[str]:
        """
        Analyze code using AI model.

        Args:
            code: Code to analyze
            filename: Name of the file being analyzed
            system_prompt: System prompt defining reviewer role
            analysis_prompt: Specific analysis instructions
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response

        Returns:
            Analysis result as string, or None if failed
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"{analysis_prompt}\n\nFile: {filename}\n\n```\n{code}\n```"
            }
        ]

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                result = response.choices[0].message.content
                logger.info(f"Successfully analyzed {filename}")
                return result

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"Failed to analyze {filename} after {self.max_retries} attempts")
                    return None

    def analyze_diff(
        self,
        diff: str,
        filename: str,
        system_prompt: str,
        analysis_prompt: str,
        context: Optional[Dict] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096
    ) -> Optional[str]:
        """
        Analyze code diff using AI model.

        Args:
            diff: Unified diff to analyze
            filename: Name of the file
            system_prompt: System prompt
            analysis_prompt: Analysis instructions
            context: Additional context (PR title, description, etc.)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            Analysis result as string, or None if failed
        """
        context_str = ""
        if context:
            context_str = f"\n\nContext:\n"
            if 'pr_title' in context:
                context_str += f"PR Title: {context['pr_title']}\n"
            if 'pr_description' in context:
                context_str += f"PR Description: {context['pr_description']}\n"

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"{analysis_prompt}{context_str}\n\nFile: {filename}\n\n```diff\n{diff}\n```"
            }
        ]

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                result = response.choices[0].message.content
                logger.info(f"Successfully analyzed diff for {filename}")
                return result

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                else:
                    logger.error(f"Failed to analyze diff for {filename} after {self.max_retries} attempts")
                    return None

    def batch_analyze(
        self,
        files: List[Dict[str, str]],
        system_prompt: str,
        analysis_prompt: str,
        max_tokens: int = 4096
    ) -> List[Dict]:
        """
        Analyze multiple files in batch.

        Args:
            files: List of dicts with 'filename' and 'content' keys
            system_prompt: System prompt
            analysis_prompt: Analysis instructions
            max_tokens: Maximum tokens per response

        Returns:
            List of analysis results with filename and result
        """
        results = []

        for file_info in files:
            filename = file_info.get('filename', 'unknown')
            content = file_info.get('content', '')

            if not content:
                logger.warning(f"Skipping {filename}: empty content")
                continue

            result = self.analyze_code(
                code=content,
                filename=filename,
                system_prompt=system_prompt,
                analysis_prompt=analysis_prompt,
                max_tokens=max_tokens
            )

            if result:
                results.append({
                    'filename': filename,
                    'analysis': result
                })

        return results

    def stream_analysis(
        self,
        code: str,
        filename: str,
        system_prompt: str,
        analysis_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096
    ):
        """
        Stream analysis results (generator).

        Args:
            code: Code to analyze
            filename: File name
            system_prompt: System prompt
            analysis_prompt: Analysis instructions
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Yields:
            Chunks of analysis text
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"{analysis_prompt}\n\nFile: {filename}\n\n```\n{code}\n```"
            }
        ]

        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield None

    def count_tokens_estimate(self, text: str) -> int:
        """
        Estimate token count (rough approximation).

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token
        return len(text) // 4

    def chunk_large_file(
        self,
        content: str,
        max_chunk_tokens: int = 6000
    ) -> List[str]:
        """
        Split large file into chunks for processing.

        Args:
            content: File content
            max_chunk_tokens: Maximum tokens per chunk

        Returns:
            List of content chunks
        """
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_tokens = 0

        for line in lines:
            line_tokens = self.count_tokens_estimate(line)

            if current_tokens + line_tokens > max_chunk_tokens and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_tokens = line_tokens
            else:
                current_chunk.append(line)
                current_tokens += line_tokens

        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks
