"""
Edit Strategy Executor - Reliable file modification strategies.

Implements 3 execution strategies based on confidence:
1. atomic_edit: High confidence - use native edit tool
2. bash_fallback: Medium confidence - use Python line replacement  
3. re_read_first: Low confidence - read file, then re-assess

Each strategy has different reliability characteristics and use cases.
"""

import subprocess
import re
from typing import Dict, Optional, Tuple
from pathlib import Path


class EditStrategyExecutor:
    """
    Executes file edits using confidence-appropriate strategies.
    
    Prevents whitespace failures by choosing the right tool for the job.
    """
    
    def __init__(self):
        self.edit_attempts = []  # Track for calibration
    
    async def execute_strategy(
        self,
        strategy: str,
        file_path: str,
        old_str: str,
        new_str: str,
        assessment: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        Execute edit using the specified strategy.
        
        Args:
            strategy: "atomic_edit" | "bash_fallback" | "re_read_first"
            file_path: Path to file
            old_str: String to replace
            new_str: Replacement string
            assessment: Optional confidence assessment for logging
        
        Returns:
            {
                "success": bool,
                "strategy_used": str,
                "message": str,
                "changes_made": bool
            }
        """
        if strategy == "atomic_edit":
            return await self.atomic_edit(file_path, old_str, new_str)
        elif strategy == "bash_fallback":
            return await self.bash_line_replacement(file_path, old_str, new_str)
        elif strategy == "re_read_first":
            return await self.re_read_then_edit(file_path, old_str, new_str)
        else:
            return {
                "success": False,
                "strategy_used": "unknown",
                "message": f"Unknown strategy: {strategy}",
                "changes_made": False
            }
    
    async def atomic_edit(
        self,
        file_path: str,
        old_str: str,
        new_str: str
    ) -> Dict:
        """
        Strategy 1: Atomic edit using exact string match.
        
        Requires PERFECT string match. Use only when confidence is high.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if pattern exists
            if old_str not in content:
                return {
                    "success": False,
                    "strategy_used": "atomic_edit",
                    "message": f"Pattern not found in {file_path}",
                    "changes_made": False
                }
            
            # Count occurrences
            count = content.count(old_str)
            if count > 1:
                return {
                    "success": False,
                    "strategy_used": "atomic_edit",
                    "message": f"Ambiguous: found {count} matches (expected 1)",
                    "changes_made": False
                }
            
            # Perform replacement
            new_content = content.replace(old_str, new_str, 1)
            
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return {
                "success": True,
                "strategy_used": "atomic_edit",
                "message": f"Successfully replaced 1 occurrence in {file_path}",
                "changes_made": True
            }
        
        except Exception as e:
            return {
                "success": False,
                "strategy_used": "atomic_edit",
                "message": f"Error: {str(e)}",
                "changes_made": False
            }
    
    async def bash_line_replacement(
        self,
        file_path: str,
        old_str: str,
        new_str: str
    ) -> Dict:
        """
        Strategy 2: Bash/Python line-based replacement.
        
        More forgiving of whitespace variations. Uses Python for safety.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Try exact match first
            if old_str in ''.join(lines):
                # Exact match exists - use it
                content = ''.join(lines)
                content = content.replace(old_str, new_str, 1)
                lines = content.splitlines(keepends=True)
                # Make sure last line has newline
                if lines and not lines[-1].endswith('\n'):
                    lines[-1] += '\n'
            else:
                # No exact match - try regex with flexible whitespace
                pattern = self._make_flexible_pattern(old_str)
                found = False
                
                for i, line in enumerate(lines):
                    if re.search(pattern, line):
                        # Replace this line
                        lines[i] = re.sub(pattern, new_str, line)
                        found = True
                        break
                
                if not found:
                    return {
                        "success": False,
                        "strategy_used": "bash_fallback",
                        "message": f"Pattern not found (even with flexible whitespace)",
                        "changes_made": False
                    }
            
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return {
                "success": True,
                "strategy_used": "bash_fallback",
                "message": f"Successfully replaced using line-based approach",
                "changes_made": True
            }
        
        except Exception as e:
            return {
                "success": False,
                "strategy_used": "bash_fallback",
                "message": f"Error: {str(e)}",
                "changes_made": False
            }
    
    async def re_read_then_edit(
        self,
        file_path: str,
        old_str: str,
        new_str: str
    ) -> Dict:
        """
        Strategy 3: Re-read file first, then assess again.
        
        Use when confidence is low or context is stale.
        This would typically integrate with view tool in MCP context.
        """
        try:
            # Read current file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # For now, just verify the pattern exists
            if old_str not in content:
                return {
                    "success": False,
                    "strategy_used": "re_read_first",
                    "message": f"After re-reading: pattern still not found",
                    "changes_made": False
                }
            
            # Pattern exists - try atomic edit now
            result = await self.atomic_edit(file_path, old_str, new_str)
            result["strategy_used"] = "re_read_first->atomic_edit"
            return result
        
        except Exception as e:
            return {
                "success": False,
                "strategy_used": "re_read_first",
                "message": f"Error: {str(e)}",
                "changes_made": False
            }
    
    def _make_flexible_pattern(self, old_str: str) -> str:
        """
        Convert exact string to regex with flexible whitespace.
        
        Example: "def  my_func():" -> r"def\s+my_func\(\):"
        """
        # Escape special regex characters
        pattern = re.escape(old_str)
        
        # Replace literal spaces with \s+ (flexible whitespace)
        pattern = pattern.replace(r'\ ', r'\s+')
        
        return pattern


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    import tempfile
    import os
    
    async def test_strategies():
        executor = EditStrategyExecutor()
        
        # Create test file
        test_content = """def my_function():
    return 42

def another_function():
    return 100
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            test_file = f.name
        
        try:
            # Test 1: Atomic edit (exact match)
            print("Test 1: Atomic edit with exact match")
            result1 = await executor.atomic_edit(
                test_file,
                "def my_function():\n    return 42",
                "def my_function():\n    return 84"
            )
            print(f"  Result: {result1}\n")
            
            # Test 2: Bash fallback (whitespace variations)
            print("Test 2: Bash fallback with whitespace flexibility")
            result2 = await executor.bash_line_replacement(
                test_file,
                "def  another_function",  # Note: extra space
                "def  renamed_function"
            )
            print(f"  Result: {result2}\n")
            
            # Test 3: Re-read first
            print("Test 3: Re-read then edit")
            result3 = await executor.re_read_then_edit(
                test_file,
                "return 84",
                "return 168"
            )
            print(f"  Result: {result3}\n")
            
            # Show final content
            with open(test_file, 'r') as f:
                print("Final file content:")
                print(f.read())
        
        finally:
            os.unlink(test_file)
    
    asyncio.run(test_strategies())
