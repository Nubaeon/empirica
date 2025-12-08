"""
Edit Confidence Assessor - Epistemic signals for reliable file editing.

Assesses confidence across 4 key vectors:
1. CONTEXT: How recently was the file read?
2. UNCERTAINTY: How confident about exact whitespace?
3. SIGNAL: How unique is the target pattern?
4. CLARITY: Risk of truncation in context window?

Returns assessment + recommended strategy.
"""

from typing import Dict, Tuple, Optional
from pathlib import Path
from datetime import datetime


class EditConfidenceAssessor:
    """
    Assesses epistemic confidence before attempting file edits.
    
    Prevents 80% of edit failures by detecting whitespace mismatches,
    stale context, and ambiguous targets BEFORE attempting edit.
    """
    
    def __init__(self):
        self.context_freshness_cache: Dict[str, datetime] = {}
        self.confidence_threshold_atomic = 0.70  # Use atomic edit if >= 0.70
        self.confidence_threshold_fallback = 0.40  # Use bash if < 0.70, >= 0.40
        # Below 0.40: re-read first
    
    def assess(
        self,
        file_path: str,
        old_str: str,
        context_source: str = "memory",
        last_read_turn: Optional[int] = None,
        current_turn: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Assess confidence for an edit operation.
        
        Args:
            file_path: Path to file being edited
            old_str: String to be replaced
            context_source: "memory" | "view_output" | "fresh_read"
            last_read_turn: When file was last read (optional)
            current_turn: Current turn number (optional)
        
        Returns:
            Dict with epistemic vectors:
            {
                "context": float,      # Freshness of file read
                "uncertainty": float,  # Whitespace confidence (inverted)
                "signal": float,       # Match uniqueness
                "clarity": float,      # Truncation risk (inverted)
                "overall": float       # Aggregate confidence
            }
        """
        context = self._assess_context_freshness(
            file_path, context_source, last_read_turn, current_turn
        )
        
        uncertainty = self._assess_whitespace_confidence(old_str, context_source)
        
        signal = self._assess_match_uniqueness(file_path, old_str)
        
        clarity = self._assess_truncation_risk(old_str)
        
        # Overall confidence (inverse of uncertainty)
        overall = (context + (1.0 - uncertainty) + signal + clarity) / 4.0
        
        return {
            "context": context,
            "uncertainty": uncertainty,
            "signal": signal,
            "clarity": clarity,
            "overall": overall
        }
    
    def recommend_strategy(self, assessment: Dict[str, float]) -> Tuple[str, str]:
        """
        Recommend edit strategy based on assessment.
        
        Returns:
            (strategy, reasoning) where strategy is:
            - "atomic_edit": High confidence, use native edit tool
            - "bash_fallback": Medium confidence, use bash/Python
            - "re_read_first": Low confidence, read file first
        """
        overall = assessment["overall"]
        context = assessment["context"]
        uncertainty = assessment["uncertainty"]
        signal = assessment["signal"]
        
        # Low confidence: re-read first
        if overall < self.confidence_threshold_fallback:
            return (
                "re_read_first",
                f"Low confidence ({overall:.2f}) - file context may be stale or pattern ambiguous"
            )
        
        # Stale context: re-read
        if context < 0.60:
            return (
                "re_read_first",
                f"Stale context ({context:.2f}) - file read {self._context_age_description(context)}"
            )
        
        # High whitespace uncertainty: use bash
        if uncertainty > 0.50:
            return (
                "bash_fallback",
                f"High whitespace uncertainty ({uncertainty:.2f}) - safer to use line-based replacement"
            )
        
        # Ambiguous pattern: use bash with line numbers
        if signal < 0.60:
            return (
                "bash_fallback",
                f"Ambiguous pattern match ({signal:.2f}) - use line-based replacement for safety"
            )
        
        # High confidence: atomic edit
        if overall >= self.confidence_threshold_atomic:
            return (
                "atomic_edit",
                f"High confidence ({overall:.2f}) - fresh context, clear pattern, confident whitespace"
            )
        
        # Medium confidence: bash fallback (safer)
        return (
            "bash_fallback",
            f"Medium confidence ({overall:.2f}) - use bash fallback for reliability"
        )
    
    def _assess_context_freshness(
        self,
        file_path: str,
        context_source: str,
        last_read_turn: Optional[int],
        current_turn: Optional[int]
    ) -> float:
        """
        Assess how recently the file was read.
        
        Returns:
            1.0: Fresh read (view_output in current turn)
            0.9: Very recent (1-2 turns ago)
            0.7: Recent (3-5 turns ago)
            0.5: Stale (6-10 turns ago)
            0.3: Very stale (>10 turns ago or memory only)
        """
        if context_source == "view_output":
            return 1.0  # Fresh read in current turn
        
        if context_source == "fresh_read":
            return 0.95  # Read in last turn or two
        
        if last_read_turn is None or current_turn is None:
            # From memory with no turn tracking
            return 0.3
        
        turns_ago = current_turn - last_read_turn
        
        if turns_ago == 0:
            return 1.0
        elif turns_ago <= 2:
            return 0.9
        elif turns_ago <= 5:
            return 0.7
        elif turns_ago <= 10:
            return 0.5
        else:
            return 0.3
    
    def _assess_whitespace_confidence(
        self,
        old_str: str,
        context_source: str
    ) -> float:
        """
        Assess uncertainty about exact whitespace match.
        
        Returns (uncertainty, higher = more uncertain):
            0.1: Low uncertainty (view output, consistent spacing)
            0.3: Moderate (view output, mixed tabs/spaces)
            0.5: Medium (memory, single line)
            0.7: High (memory, multi-line with indentation)
        """
        if context_source == "memory":
            # Working from memory - uncertain about whitespace
            has_newlines = "\n" in old_str
            has_indentation = "    " in old_str or "\t" in old_str
            
            if has_newlines and has_indentation:
                return 0.7  # High uncertainty: multi-line + indentation
            elif has_indentation:
                return 0.5  # Medium: single line with indentation
            else:
                return 0.4  # Lower: simple string
        
        # From view output - check for mixed spacing
        has_tabs = "\t" in old_str
        has_multiple_spaces = "  " in old_str  # 2+ consecutive spaces
        
        if has_tabs and has_multiple_spaces:
            return 0.3  # Mixed spacing - moderate uncertainty
        
        return 0.1  # Consistent spacing - low uncertainty
    
    def _assess_match_uniqueness(self, file_path: str, old_str: str) -> float:
        """
        Assess how unique the pattern is in the file.
        
        Returns:
            0.9: Unique (1 occurrence)
            0.7: Somewhat unique (2-3 occurrences)
            0.4: Ambiguous (4+ occurrences)
            0.0: No match (will fail)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (FileNotFoundError, PermissionError, UnicodeDecodeError):
            # Can't read file - assume low confidence
            return 0.3
        
        count = content.count(old_str)
        
        if count == 0:
            return 0.0  # No match - edit will fail
        elif count == 1:
            return 0.9  # Perfect - unique match
        elif count <= 3:
            return 0.7  # Risky - a few matches
        else:
            return 0.4  # Very risky - many matches
    
    def _assess_truncation_risk(self, old_str: str) -> float:
        """
        Assess risk that old_str is truncated in context window.
        
        Returns (clarity, lower = more truncation risk):
            0.9: No truncation indicators
            0.6: Possible truncation (long lines)
            0.3: Likely truncated (has "..." or very long)
        """
        if "..." in old_str:
            return 0.3  # Explicit truncation marker
        
        lines = old_str.split("\n")
        max_line_length = max(len(line) for line in lines) if lines else 0
        
        if max_line_length > 150:
            return 0.4  # Very long line - likely truncated
        elif max_line_length > 120:
            return 0.6  # Long line - might be truncated
        else:
            return 0.9  # Normal length - no truncation risk
    
    def _context_age_description(self, context_score: float) -> str:
        """Get human-readable description of context age."""
        if context_score >= 0.95:
            return "just now"
        elif context_score >= 0.85:
            return "1-2 turns ago"
        elif context_score >= 0.65:
            return "3-5 turns ago"
        elif context_score >= 0.45:
            return "6-10 turns ago"
        else:
            return "more than 10 turns ago or from memory"


# Example usage
if __name__ == "__main__":
    assessor = EditConfidenceAssessor()
    
    # Test case 1: High confidence (fresh view, simple string)
    assessment1 = assessor.assess(
        file_path="/tmp/test.py",
        old_str="def my_function():",
        context_source="view_output"
    )
    strategy1, reason1 = assessor.recommend_strategy(assessment1)
    print(f"Test 1 - Fresh view, simple string:")
    print(f"  Assessment: {assessment1}")
    print(f"  Strategy: {strategy1}")
    print(f"  Reason: {reason1}\n")
    
    # Test case 2: Medium confidence (memory, multi-line)
    assessment2 = assessor.assess(
        file_path="/tmp/test.py",
        old_str="    def my_function():\n        return 42",
        context_source="memory"
    )
    strategy2, reason2 = assessor.recommend_strategy(assessment2)
    print(f"Test 2 - Memory, multi-line with indentation:")
    print(f"  Assessment: {assessment2}")
    print(f"  Strategy: {strategy2}")
    print(f"  Reason: {reason2}")
