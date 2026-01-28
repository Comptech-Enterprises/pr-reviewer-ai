"""
Parser for unified diff format to extract changed lines with context.
"""
from typing import List, Dict, Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)


class DiffParser:
    """Parse unified diff format and extract structured change information."""

    def __init__(self):
        """Initialize diff parser."""
        self.file_header_pattern = re.compile(r'^--- a/(.+)$')
        self.new_file_pattern = re.compile(r'^\+\+\+ b/(.+)$')
        self.hunk_header_pattern = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$')

    def parse_diff(self, diff: str) -> List[Dict]:
        """
        Parse unified diff into structured format.

        Args:
            diff: Unified diff string

        Returns:
            List of file changes with metadata
        """
        if not diff or not diff.strip():
            return []

        files = []
        current_file = None
        current_hunk = None

        for line in diff.split('\n'):
            # Check for file header
            file_match = self.file_header_pattern.match(line)
            if file_match:
                if current_file:
                    files.append(current_file)
                current_file = {
                    'filename': file_match.group(1),
                    'hunks': [],
                    'additions': 0,
                    'deletions': 0
                }
                current_hunk = None
                continue

            # Check for new file header
            new_file_match = self.new_file_pattern.match(line)
            if new_file_match and current_file:
                # Confirm or update filename
                current_file['new_filename'] = new_file_match.group(1)
                continue

            # Check for hunk header
            hunk_match = self.hunk_header_pattern.match(line)
            if hunk_match and current_file:
                old_start = int(hunk_match.group(1))
                old_count = int(hunk_match.group(2) or 1)
                new_start = int(hunk_match.group(3))
                new_count = int(hunk_match.group(4) or 1)
                context = hunk_match.group(5).strip()

                current_hunk = {
                    'old_start': old_start,
                    'old_count': old_count,
                    'new_start': new_start,
                    'new_count': new_count,
                    'context': context,
                    'changes': []
                }
                current_file['hunks'].append(current_hunk)
                continue

            # Parse change lines
            if current_hunk is not None and line:
                change_type = None
                content = line[1:] if len(line) > 1 else ''

                if line.startswith('+'):
                    change_type = 'addition'
                    current_file['additions'] += 1
                elif line.startswith('-'):
                    change_type = 'deletion'
                    current_file['deletions'] += 1
                elif line.startswith(' '):
                    change_type = 'context'
                else:
                    # Sometimes diff includes metadata or empty lines
                    continue

                current_hunk['changes'].append({
                    'type': change_type,
                    'content': content,
                    'line': line
                })

        # Add the last file
        if current_file:
            files.append(current_file)

        return files

    def get_changed_lines(self, parsed_diff: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Extract changed lines by file.

        Args:
            parsed_diff: Parsed diff structure

        Returns:
            Dict mapping filename to list of changed line info
        """
        result = {}

        for file_info in parsed_diff:
            filename = file_info['filename']
            changes = []

            for hunk in file_info['hunks']:
                old_line = hunk['old_start']
                new_line = hunk['new_start']

                for change in hunk['changes']:
                    if change['type'] == 'addition':
                        changes.append({
                            'line_number': new_line,
                            'type': 'addition',
                            'content': change['content']
                        })
                        new_line += 1
                    elif change['type'] == 'deletion':
                        changes.append({
                            'line_number': old_line,
                            'type': 'deletion',
                            'content': change['content']
                        })
                        old_line += 1
                    else:  # context
                        old_line += 1
                        new_line += 1

            result[filename] = changes

        return result

    def get_additions_only(self, parsed_diff: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Get only added lines (new code to review).

        Args:
            parsed_diff: Parsed diff structure

        Returns:
            Dict mapping filename to list of additions
        """
        result = {}

        for file_info in parsed_diff:
            filename = file_info['filename']
            additions = []

            for hunk in file_info['hunks']:
                new_line = hunk['new_start']

                for change in hunk['changes']:
                    if change['type'] == 'addition':
                        additions.append({
                            'line_number': new_line,
                            'content': change['content']
                        })
                        new_line += 1
                    elif change['type'] != 'deletion':
                        new_line += 1

            result[filename] = additions

        return result

    def get_file_patch(self, diff: str, filename: str) -> Optional[str]:
        """
        Extract patch for a specific file from complete diff.

        Args:
            diff: Complete unified diff
            filename: File to extract

        Returns:
            Patch for the file, or None if not found
        """
        parsed = self.parse_diff(diff)

        for file_info in parsed:
            if file_info['filename'] == filename:
                # Reconstruct patch from parsed data
                return self._reconstruct_patch(file_info)

        return None

    def _reconstruct_patch(self, file_info: Dict) -> str:
        """
        Reconstruct unified diff patch from parsed structure.

        Args:
            file_info: Parsed file information

        Returns:
            Unified diff patch as string
        """
        lines = [
            f"--- a/{file_info['filename']}",
            f"+++ b/{file_info.get('new_filename', file_info['filename'])}"
        ]

        for hunk in file_info['hunks']:
            # Hunk header
            header = f"@@ -{hunk['old_start']},{hunk['old_count']} +{hunk['new_start']},{hunk['new_count']} @@"
            if hunk['context']:
                header += f" {hunk['context']}"
            lines.append(header)

            # Changes
            for change in hunk['changes']:
                lines.append(change['line'])

        return '\n'.join(lines)

    def extract_context_window(
        self,
        parsed_diff: List[Dict],
        filename: str,
        line_number: int,
        context_lines: int = 3
    ) -> Optional[str]:
        """
        Extract code context around a specific line.

        Args:
            parsed_diff: Parsed diff structure
            filename: File name
            line_number: Target line number
            context_lines: Number of lines before/after to include

        Returns:
            Context as string, or None if not found
        """
        for file_info in parsed_diff:
            if file_info['filename'] != filename:
                continue

            for hunk in file_info['hunks']:
                new_line = hunk['new_start']
                context = []

                for i, change in enumerate(hunk['changes']):
                    current_line = new_line if change['type'] != 'deletion' else None

                    if current_line and abs(current_line - line_number) <= context_lines:
                        context.append(change['content'])

                    if change['type'] != 'deletion':
                        new_line += 1

                if context:
                    return '\n'.join(context)

        return None

    def get_statistics(self, parsed_diff: List[Dict]) -> Dict:
        """
        Get statistics about the diff.

        Args:
            parsed_diff: Parsed diff structure

        Returns:
            Statistics dictionary
        """
        stats = {
            'files_changed': len(parsed_diff),
            'total_additions': 0,
            'total_deletions': 0,
            'files': []
        }

        for file_info in parsed_diff:
            stats['total_additions'] += file_info['additions']
            stats['total_deletions'] += file_info['deletions']
            stats['files'].append({
                'filename': file_info['filename'],
                'additions': file_info['additions'],
                'deletions': file_info['deletions'],
                'hunks': len(file_info['hunks'])
            })

        return stats

    def is_binary_file(self, filename: str) -> bool:
        """
        Check if file is likely binary (should skip analysis).

        Args:
            filename: File name

        Returns:
            True if likely binary file
        """
        binary_extensions = {
            '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip',
            '.tar', '.gz', '.exe', '.dll', '.so', '.dylib',
            '.woff', '.woff2', '.ttf', '.eot', '.ico'
        }

        return any(filename.endswith(ext) for ext in binary_extensions)

    def is_generated_file(self, filename: str) -> bool:
        """
        Check if file is likely generated (should skip analysis).

        Args:
            filename: File name

        Returns:
            True if likely generated file
        """
        generated_patterns = [
            'package-lock.json',
            'yarn.lock',
            'Pipfile.lock',
            'poetry.lock',
            '.min.js',
            '.min.css',
            '-lock.json',
            '.bundle.js',
            '.map'
        ]

        return any(pattern in filename for pattern in generated_patterns)
