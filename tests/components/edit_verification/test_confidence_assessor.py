"""
Unit Tests for EditConfidenceAssessor

Tests the 4 epistemic signals and strategy recommendation logic.
"""

import pytest
import tempfile
import os
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from empirica.components.edit_verification import EditConfidenceAssessor


class TestEditConfidenceAssessor:
    """Test suite for confidence assessment logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.assessor = EditConfidenceAssessor()
        
        # Create temp test file
        self.test_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False
        )
        self.test_file.write("""def my_function():
    return 42

def another_function():
    return 100
""")
        self.test_file.close()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_file.name):
            os.unlink(self.test_file.name)
    
    # ========== Context Freshness Tests ==========
    
    def test_context_freshness_view_output(self):
        """Test context assessment for fresh view output."""
        assessment = self.assessor.assess(
            file_path=self.test_file.name,
            old_str="def my_function():",
            context_source="view_output"
        )
        
        assert assessment["context"] == 1.0, "view_output should have context=1.0"
    
    def test_context_freshness_memory(self):
        """Test context assessment for memory-based edits."""
        assessment = self.assessor.assess(
            file_path=self.test_file.name,
            old_str="def my_function():",
            context_source="memory"
        )
        
        assert assessment["context"] == 0.3, "memory should have context=0.3 (stale)"
    
    def test_context_freshness_with_turns(self):
        """Test context decay with turn tracking."""
        # Recent read (2 turns ago)
        assessment = self.assessor.assess(
            file_path=self.test_file.name,
            old_str="def my_function():",
            context_source="memory",
            last_read_turn=8,
            current_turn=10
        )
        
        assert assessment["context"] == 0.9, "2 turns ago should be 0.9"
        
        # Stale read (10 turns ago)
        assessment2 = self.assessor.assess(
            file_path=self.test_file.name,
            old_str="def my_function():",
            context_source="memory",
            last_read_turn=0,
            current_turn=10
        )
        
        assert assessment2["context"] == 0.5, "10 turns ago should be 0.5"
    
    # ========== Whitespace Confidence Tests ==========
    
    def test_whitespace_simple_from_view(self):
        """Test whitespace assessment for simple string from view."""
        assessment = self.assessor.assess(
            file_path=self.test_file.name,
            old_str="def my_function():",
            context_source="view_output"
        )
        
        assert assessment["uncertainty"] == 0.1, "Simple string from view should have low uncertainty"
    
    def test_whitespace_multiline_from_memory(self):
        """Test whitespace assessment for multi-line from memory."""
        assessment = self.assessor.assess(
            file_path=self.test_file.name,
            old_str="def my_function():\n    return 42",
            context_source="memory"
        )
        
        assert assessment["uncertainty"] == 0.7, "Multi-line from memory should have high uncertainty"
    
    def test_whitespace_mixed_spacing(self):
        """Test whitespace assessment for mixed tabs/spaces."""
        assessment = self.assessor.assess(
            file_path=self.test_file.name,
            old_str="def\tmy_function():  # tabs and spaces",
            context_source="view_output"
        )
        
        assert assessment["uncertainty"] == 0.3, "Mixed spacing should have moderate uncertainty"
    
    # ========== Match Uniqueness Tests ==========
    
    def test_signal_unique_match(self):
        """Test signal assessment for unique pattern."""
        assessment = self.assessor.assess(
            file_path=self.test_file.name,
            old_str="def my_function():",
            context_source="view_output"
        )
        
        assert assessment["signal"] == 0.9, "Unique match should have signal=0.9"
    
    def test_signal_no_match(self):
        """Test signal assessment for non-existent pattern."""
        assessment = self.assessor.assess(
            file_path=self.test_file.name,
            old_str="def nonexistent_function():",
            context_source="view_output"
        )
        
        assert assessment["signal"] == 0.0, "No match should have signal=0.0"
    
    def test_signal_ambiguous_match(self):
        """Test signal assessment for ambiguous pattern."""
        # Write file with duplicate patterns
        with open(self.test_file.name, 'w') as f:
            f.write("def func():\n    pass\n\ndef func():\n    pass\n\ndef func():\n    pass\n\ndef func():\n    pass\n")
        
        assessment = self.assessor.assess(
            file_path=self.test_file.name,
            old_str="def func():",
            context_source="view_output"
        )
        
        assert assessment["signal"] == 0.4, "4+ matches should have signal=0.4"
    
    # ========== Truncation Risk Tests ==========
    
    def test_clarity_no_truncation(self):
        """Test clarity assessment for normal-length string."""
        assessment = self.assessor.assess(
            file_path=self.test_file.name,
            old_str="def my_function():",
            context_source="view_output"
        )
        
        assert assessment["clarity"] == 0.9, "Normal length should have clarity=0.9"
    
    def test_clarity_with_ellipsis(self):
        """Test clarity assessment for truncated string."""
        assessment = self.assessor.assess(
            file_path=self.test_file.name,
            old_str="def my_function(...):",
            context_source="view_output"
        )
        
        assert assessment["clarity"] == 0.3, "Ellipsis indicates truncation, clarity=0.3"
    
    def test_clarity_long_line(self):
        """Test clarity assessment for very long line."""
        long_str = "def my_function(" + ", ".join([f"param{i}" for i in range(50)]) + "):"
        
        assessment = self.assessor.assess(
            file_path=self.test_file.name,
            old_str=long_str,
            context_source="view_output"
        )
        
        assert assessment["clarity"] <= 0.6, "Very long line should have clarity<=0.6"
    
    # ========== Overall Assessment Tests ==========
    
    def test_overall_confidence_calculation(self):
        """Test overall confidence is average of components."""
        assessment = self.assessor.assess(
            file_path=self.test_file.name,
            old_str="def my_function():",
            context_source="view_output"
        )
        
        # Overall = (context + (1-uncertainty) + signal + clarity) / 4
        expected = (assessment["context"] + (1.0 - assessment["uncertainty"]) + 
                   assessment["signal"] + assessment["clarity"]) / 4.0
        
        assert abs(assessment["overall"] - expected) < 0.01, "Overall should be average"
    
    # ========== Strategy Recommendation Tests ==========
    
    def test_recommend_atomic_edit_high_confidence(self):
        """Test atomic_edit recommendation for high confidence."""
        assessment = {
            "overall": 0.85,
            "context": 1.0,
            "uncertainty": 0.1,
            "signal": 0.9,
            "clarity": 0.9
        }
        
        strategy, reasoning = self.assessor.recommend_strategy(assessment)
        
        assert strategy == "atomic_edit", "High confidence should recommend atomic_edit"
        assert "high confidence" in reasoning.lower()
    
    def test_recommend_bash_fallback_medium_confidence(self):
        """Test bash_fallback recommendation for medium confidence."""
        assessment = {
            "overall": 0.60,
            "context": 0.7,
            "uncertainty": 0.5,
            "signal": 0.7,
            "clarity": 0.9
        }
        
        strategy, reasoning = self.assessor.recommend_strategy(assessment)
        
        assert strategy == "bash_fallback", "Medium confidence should recommend bash_fallback"
    
    def test_recommend_re_read_low_confidence(self):
        """Test re_read_first recommendation for low confidence."""
        assessment = {
            "overall": 0.30,
            "context": 0.3,
            "uncertainty": 0.7,
            "signal": 0.3,
            "clarity": 0.5
        }
        
        strategy, reasoning = self.assessor.recommend_strategy(assessment)
        
        assert strategy == "re_read_first", "Low confidence should recommend re_read_first"
    
    def test_recommend_re_read_stale_context(self):
        """Test re_read_first recommendation for stale context."""
        assessment = {
            "overall": 0.70,
            "context": 0.5,  # Stale
            "uncertainty": 0.2,
            "signal": 0.9,
            "clarity": 0.9
        }
        
        strategy, reasoning = self.assessor.recommend_strategy(assessment)
        
        assert strategy == "re_read_first", "Stale context should trigger re_read_first"
        assert "stale" in reasoning.lower()
    
    def test_recommend_bash_high_uncertainty(self):
        """Test bash_fallback recommendation for high whitespace uncertainty."""
        assessment = {
            "overall": 0.70,
            "context": 1.0,
            "uncertainty": 0.6,  # High
            "signal": 0.9,
            "clarity": 0.9
        }
        
        strategy, reasoning = self.assessor.recommend_strategy(assessment)
        
        assert strategy == "bash_fallback", "High uncertainty should trigger bash_fallback"
        assert "whitespace" in reasoning.lower()
    
    def test_recommend_bash_ambiguous_signal(self):
        """Test bash_fallback recommendation for ambiguous pattern."""
        assessment = {
            "overall": 0.70,
            "context": 1.0,
            "uncertainty": 0.2,
            "signal": 0.5,  # Ambiguous
            "clarity": 0.9
        }
        
        strategy, reasoning = self.assessor.recommend_strategy(assessment)
        
        assert strategy == "bash_fallback", "Ambiguous signal should trigger bash_fallback"
        assert "ambiguous" in reasoning.lower()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
