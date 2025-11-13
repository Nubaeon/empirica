"""
Enhanced File Tools - Inspired by Mini-Agent
Token-aware file reading for large codebases during investigations

Integrates with Empirica's investigation framework to handle large files
intelligently during epistemic assessments.
"""

import tiktoken
from pathlib import Path
from typing import Optional, Tuple, Dict
import logging

logger = logging.getLogger(__name__)


class EnhancedFileTools:
    """File tools with token-aware truncation for large codebase investigations"""
    
    def __init__(self, encoding_name: str = "cl100k_base"):
        """
        Initialize enhanced file tools
        
        Args:
            encoding_name: Tiktoken encoding to use (cl100k_base for GPT-4/Claude)
        """
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.warning(f"Could not load tiktoken encoding {encoding_name}: {e}")
            self.encoding = None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.encoding is None:
            # Fallback: rough estimate
            return len(text) // 4
        return len(self.encoding.encode(text))
    
    def truncate_text_by_tokens(
        self, 
        text: str, 
        max_tokens: int,
        truncate_position: str = "end"
    ) -> Tuple[str, bool]:
        """
        Truncate text to fit within token limit
        
        Args:
            text: Text to truncate
            max_tokens: Maximum tokens allowed
            truncate_position: "start", "end", or "middle"
            
        Returns:
            (truncated_text, was_truncated)
        """
        if self.encoding is None:
            # Fallback: character-based truncation
            char_limit = max_tokens * 4
            if len(text) <= char_limit:
                return text, False
            if truncate_position == "end":
                return text[:char_limit] + "\n... [truncated]", True
            elif truncate_position == "start":
                return "... [truncated]\n" + text[-char_limit:], True
            else:  # middle
                half = char_limit // 2
                return text[:half] + "\n... [truncated]\n" + text[-half:], True
        
        tokens = self.encoding.encode(text)
        
        if len(tokens) <= max_tokens:
            return text, False
        
        if truncate_position == "end":
            truncated = tokens[:max_tokens]
            suffix = "\n... [truncated: exceeds token limit]"
        elif truncate_position == "start":
            truncated = tokens[-max_tokens:]
            suffix = ""
            text = "... [truncated: exceeds token limit]\n" + self.encoding.decode(truncated)
            return text, True
        else:  # middle
            half = max_tokens // 2
            truncated = tokens[:half] + tokens[-half:]
            text = self.encoding.decode(tokens[:half]) + "\n... [truncated: middle section removed]\n" + self.encoding.decode(tokens[-half:])
            return text, True
        
        return self.encoding.decode(truncated) + suffix, True
    
    def read_file_with_limits(
        self,
        path: Path,
        offset: int = 0,
        limit: Optional[int] = None,
        max_tokens: Optional[int] = None,
        add_line_numbers: bool = True
    ) -> Dict:
        """
        Read file with line and token limits
        
        Args:
            path: File path to read
            offset: Line number to start from (0-indexed)
            limit: Maximum number of lines to read
            max_tokens: Maximum tokens to return (truncates if exceeded)
            add_line_numbers: Prefix each line with line number
            
        Returns:
            {
                'content': str,
                'total_lines': int,
                'lines_shown': int,
                'was_truncated': bool,
                'truncation_reason': str or None,
                'token_count': int
            }
        """
        if not path.exists():
            return {
                'error': f"File not found: {path}",
                'content': '',
                'total_lines': 0,
                'lines_shown': 0,
                'was_truncated': False,
                'truncation_reason': None,
                'token_count': 0
            }
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            return {
                'error': f"Could not read file: {e}",
                'content': '',
                'total_lines': 0,
                'lines_shown': 0,
                'was_truncated': False,
                'truncation_reason': None,
                'token_count': 0
            }
        
        total_lines = len(lines)
        selected_lines = lines[offset:offset+limit] if limit else lines[offset:]
        
        if add_line_numbers:
            content = ''.join(f"{i+offset+1}. {line}" for i, line in enumerate(selected_lines))
        else:
            content = ''.join(selected_lines)
        
        was_truncated = False
        truncation_reason = None
        
        # Check line limit truncation
        if limit and len(lines) > offset + limit:
            was_truncated = True
            truncation_reason = f"line_limit_{limit}"
        
        # Check token limit truncation
        if max_tokens:
            content, token_truncated = self.truncate_text_by_tokens(content, max_tokens)
            if token_truncated:
                was_truncated = True
                truncation_reason = f"token_limit_{max_tokens}"
        
        token_count = self.count_tokens(content)
        
        return {
            'content': content,
            'total_lines': total_lines,
            'lines_shown': len(selected_lines),
            'was_truncated': was_truncated,
            'truncation_reason': truncation_reason,
            'token_count': token_count
        }
    
    def smart_read_large_file(
        self,
        path: Path,
        max_tokens: int = 4000,
        show_start: bool = True,
        show_end: bool = True
    ) -> Dict:
        """
        Smart reading strategy for large files during investigations
        
        Shows beginning and end of file, which is often sufficient for
        understanding structure and recent changes.
        
        Args:
            path: File to read
            max_tokens: Maximum tokens to use
            show_start: Include start of file
            show_end: Include end of file
            
        Returns:
            Same format as read_file_with_limits
        """
        result = self.read_file_with_limits(path)
        
        if result.get('error'):
            return result
        
        content = result['content']
        token_count = self.count_tokens(content)
        
        if token_count <= max_tokens:
            return result
        
        # File is too large, use smart strategy
        lines = content.split('\n')
        total_lines = len(lines)
        
        if show_start and show_end:
            # Show first and last portions
            tokens_per_section = max_tokens // 2
            
            # Binary search for how many lines fit in token budget
            start_lines = self._find_lines_for_tokens(lines[:total_lines//2], tokens_per_section)
            end_lines = self._find_lines_for_tokens(lines[total_lines//2:], tokens_per_section)
            
            start_content = '\n'.join(lines[:start_lines])
            end_content = '\n'.join(lines[-end_lines:])
            
            smart_content = f"{start_content}\n\n... [{total_lines - start_lines - end_lines} lines omitted] ...\n\n{end_content}"
        elif show_start:
            start_lines = self._find_lines_for_tokens(lines, max_tokens)
            smart_content = '\n'.join(lines[:start_lines]) + f"\n\n... [{total_lines - start_lines} lines omitted] ..."
        else:
            end_lines = self._find_lines_for_tokens(lines, max_tokens)
            smart_content = f"... [{total_lines - end_lines} lines omitted] ...\n\n" + '\n'.join(lines[-end_lines:])
        
        return {
            'content': smart_content,
            'total_lines': total_lines,
            'lines_shown': start_lines + end_lines if show_start and show_end else (start_lines if show_start else end_lines),
            'was_truncated': True,
            'truncation_reason': f'smart_truncation_max_tokens_{max_tokens}',
            'token_count': self.count_tokens(smart_content)
        }
    
    def _find_lines_for_tokens(self, lines: list, target_tokens: int) -> int:
        """Binary search to find how many lines fit in token budget"""
        if not lines:
            return 0
        
        low, high = 0, len(lines)
        best = 0
        
        while low <= high:
            mid = (low + high) // 2
            content = '\n'.join(lines[:mid])
            tokens = self.count_tokens(content)
            
            if tokens <= target_tokens:
                best = mid
                low = mid + 1
            else:
                high = mid - 1
        
        return max(1, best)  # Always show at least 1 line


# Example usage for investigations
if __name__ == "__main__":
    tools = EnhancedFileTools()
    
    # Test with a file
    result = tools.read_file_with_limits(
        path=Path(__file__),
        max_tokens=1000
    )
    
    print(f"Lines: {result['lines_shown']}/{result['total_lines']}")
    print(f"Tokens: {result['token_count']}")
    print(f"Truncated: {result['was_truncated']}")
    if result['was_truncated']:
        print(f"Reason: {result['truncation_reason']}")
