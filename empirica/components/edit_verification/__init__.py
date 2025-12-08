"""
Empirica Edit Guard - Metacognitive Edit Verification

Provides confidence assessment and strategy selection for reliable file edits.
Prevents whitespace mismatch failures by assessing epistemic uncertainty before editing.
"""

from .confidence_assessor import EditConfidenceAssessor
from .strategy_executor import EditStrategyExecutor

__all__ = ['EditConfidenceAssessor', 'EditStrategyExecutor']
