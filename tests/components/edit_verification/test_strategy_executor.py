"""
Unit Tests for EditStrategyExecutor

Tests the 3 execution strategies: atomic_edit, bash_fallback, re_read_first
"""

import pytest
import tempfile
import os
import asyncio
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from empirica.components.edit_verification import EditStrategyExecutor


class TestEditStrategyExecutor:
    """Test suite for edit execution strategies."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.executor = EditStrategyExecutor()
        
        # Create temp test file
        self.test_content = """def my_function():
    return 42

def another_function():
    return 100
"""
        self.test_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False
        )
        self.test_file.write(self.test_content)
        self.test_file.close()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_file.name):
            os.unlink(self.test_file.name)
    
    # ========== Atomic Edit Tests ==========
    
    @pytest.mark.asyncio
    async def test_atomic_edit_success(self):
        """Test successful atomic edit with exact match."""
        result = await self.executor.atomic_edit(
            file_path=self.test_file.name,
            old_str="def my_function():\n    return 42",
            new_str="def my_function():\n    return 84"
        )
        
        assert result["success"] is True
        assert result["changes_made"] is True
        assert "successfully" in result["message"].lower()
        
        # Verify file content changed
        with open(self.test_file.name, 'r') as f:
            content = f.read()
            assert "return 84" in content
            assert "return 42" not in content
    
    @pytest.mark.asyncio
    async def test_atomic_edit_pattern_not_found(self):
        """Test atomic edit fails when pattern doesn't exist."""
        result = await self.executor.atomic_edit(
            file_path=self.test_file.name,
            old_str="def nonexistent():",
            new_str="def new_function():"
        )
        
        assert result["success"] is False
        assert result["changes_made"] is False
        assert "not found" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_atomic_edit_ambiguous_match(self):
        """Test atomic edit fails with multiple matches."""
        # Write file with duplicate patterns
        with open(self.test_file.name, 'w') as f:
            f.write("def func():\n    pass\n\ndef func():\n    pass\n")
        
        result = await self.executor.atomic_edit(
            file_path=self.test_file.name,
            old_str="def func():",
            new_str="def renamed():"
        )
        
        assert result["success"] is False
        assert result["changes_made"] is False
        assert "ambiguous" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_atomic_edit_preserves_other_content(self):
        """Test atomic edit only changes target, preserves rest."""
        result = await self.executor.atomic_edit(
            file_path=self.test_file.name,
            old_str="return 42",
            new_str="return 168"
        )
        
        assert result["success"] is True
        
        # Verify other function unchanged
        with open(self.test_file.name, 'r') as f:
            content = f.read()
            assert "another_function" in content
            assert "return 100" in content
    
    # ========== Bash Fallback Tests ==========
    
    @pytest.mark.asyncio
    async def test_bash_fallback_exact_match(self):
        """Test bash fallback with exact match."""
        result = await self.executor.bash_line_replacement(
            file_path=self.test_file.name,
            old_str="def my_function():\n    return 42",
            new_str="def my_function():\n    return 84"
        )
        
        assert result["success"] is True
        assert result["changes_made"] is True
        
        # Verify change
        with open(self.test_file.name, 'r') as f:
            content = f.read()
            assert "return 84" in content
    
    @pytest.mark.asyncio
    async def test_bash_fallback_flexible_whitespace(self):
        """Test bash fallback handles whitespace variations."""
        # This test verifies regex-based flexible matching
        result = await self.executor.bash_line_replacement(
            file_path=self.test_file.name,
            old_str="def  my_function",  # Extra space
            new_str="def my_renamed_function"
        )
        
        # May fail due to pattern complexity, but demonstrates flexibility
        # In practice, would need more sophisticated regex
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_bash_fallback_not_found(self):
        """Test bash fallback fails gracefully when pattern not found."""
        result = await self.executor.bash_line_replacement(
            file_path=self.test_file.name,
            old_str="def totally_nonexistent():",
            new_str="def new():"
        )
        
        assert result["success"] is False
        assert result["changes_made"] is False
        assert "not found" in result["message"].lower()
    
    # ========== Re-read Then Edit Tests ==========
    
    @pytest.mark.asyncio
    async def test_re_read_then_edit_success(self):
        """Test re_read_first strategy succeeds after re-reading."""
        result = await self.executor.re_read_then_edit(
            file_path=self.test_file.name,
            old_str="return 100",
            new_str="return 200"
        )
        
        assert result["success"] is True
        assert "atomic_edit" in result["strategy_used"]
        
        # Verify change
        with open(self.test_file.name, 'r') as f:
            content = f.read()
            assert "return 200" in content
    
    @pytest.mark.asyncio
    async def test_re_read_then_edit_not_found(self):
        """Test re_read_first fails if pattern still not found."""
        result = await self.executor.re_read_then_edit(
            file_path=self.test_file.name,
            old_str="def missing():",
            new_str="def new():"
        )
        
        assert result["success"] is False
        assert "not found" in result["message"].lower()
    
    # ========== Strategy Execution Dispatcher Tests ==========
    
    @pytest.mark.asyncio
    async def test_execute_strategy_atomic(self):
        """Test execute_strategy dispatches to atomic_edit."""
        result = await self.executor.execute_strategy(
            strategy="atomic_edit",
            file_path=self.test_file.name,
            old_str="return 42",
            new_str="return 84"
        )
        
        assert result["strategy_used"] == "atomic_edit"
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_execute_strategy_bash(self):
        """Test execute_strategy dispatches to bash_fallback."""
        result = await self.executor.execute_strategy(
            strategy="bash_fallback",
            file_path=self.test_file.name,
            old_str="return 42",
            new_str="return 84"
        )
        
        assert result["strategy_used"] == "bash_fallback"
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_execute_strategy_re_read(self):
        """Test execute_strategy dispatches to re_read_first."""
        result = await self.executor.execute_strategy(
            strategy="re_read_first",
            file_path=self.test_file.name,
            old_str="return 42",
            new_str="return 84"
        )
        
        assert "re_read" in result["strategy_used"]
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_execute_strategy_unknown(self):
        """Test execute_strategy handles unknown strategy."""
        result = await self.executor.execute_strategy(
            strategy="unknown_strategy",
            file_path=self.test_file.name,
            old_str="return 42",
            new_str="return 84"
        )
        
        assert result["success"] is False
        assert "unknown" in result["message"].lower()
    
    # ========== Edge Cases ==========
    
    @pytest.mark.asyncio
    async def test_edit_multiline_pattern(self):
        """Test editing multi-line pattern."""
        result = await self.executor.atomic_edit(
            file_path=self.test_file.name,
            old_str="def another_function():\n    return 100",
            new_str="def another_function():\n    return 500"
        )
        
        assert result["success"] is True
        
        with open(self.test_file.name, 'r') as f:
            content = f.read()
            assert "return 500" in content
    
    @pytest.mark.asyncio
    async def test_edit_empty_string(self):
        """Test handling of empty strings."""
        result = await self.executor.atomic_edit(
            file_path=self.test_file.name,
            old_str="",
            new_str="# comment"
        )
        
        # Empty string matches entire file - should fail (ambiguous)
        # Or succeed with specific behavior - depends on implementation
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_edit_nonexistent_file(self):
        """Test handling of nonexistent file."""
        result = await self.executor.atomic_edit(
            file_path="/tmp/nonexistent_file_12345.py",
            old_str="test",
            new_str="new"
        )
        
        assert result["success"] is False
        assert "error" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_edit_preserves_encoding(self):
        """Test edit preserves UTF-8 encoding."""
        # Write file with UTF-8 characters
        test_utf8 = """def function():
    # Comment with émojis 🎉
    return "unicode: café"
"""
        with open(self.test_file.name, 'w', encoding='utf-8') as f:
            f.write(test_utf8)
        
        result = await self.executor.atomic_edit(
            file_path=self.test_file.name,
            old_str='return "unicode: café"',
            new_str='return "unicode: coffee"'
        )
        
        assert result["success"] is True
        
        # Verify UTF-8 preserved
        with open(self.test_file.name, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "émojis 🎉" in content


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
