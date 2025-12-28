"""
Canonical Epistemic Cascade - DEPRECATED STUB

This file now contains only minimal stubs for backward compatibility.

DEPRECATED: Orchestration logic has been replaced by:
- AI self-prompting (preflight-submit, check-submit, postflight-submit CLI)
- GitEnhancedReflexLogger for storage
- MCP server as stateless CLI wrapper

For self-assessment workflow, use CLI commands:
  empirica preflight-submit - (JSON via stdin)
  empirica check-submit - (JSON via stdin)
  empirica postflight-submit - (JSON via stdin)
"""

import time
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, UTC
import asyncio
import requests
import json
import logging

# Sys path setup for reasoning service imports (if needed)
import sys
from pathlib import Path

# NOTE: All imports kept for compatibility, even if unused in stub

# Canonical imports (minimal for compatibility)
# NOTE: Imports removed since orchestration logic is gone
# from empirica.core.canonical import GitEnhancedReflexLogger

from empirica.core.schemas.epistemic_assessment import (
    EpistemicAssessmentSchema,
    VectorAssessment,
    CascadePhase as NewCascadePhase
)

# Investigation imports removed (orchestration deprecated)
# from .investigation_strategy import recommend_investigation_tools, Domain, ToolRecommendation
# from .investigation_plugin import InvestigationPlugin, PluginRegistry

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and DataClasses (kept for compatibility)
# ============================================================================

class CascadePhase(Enum):
    """
    OLD CascadePhase enum (for backward compatibility)
    
    NOTE: New schema uses NewCascadePhase from epistemic_assessment.py
    which doesn't have PLAN phase. Use mapping when needed.
    """
    PREFLIGHT = "preflight"
    THINK = "think"
    PLAN = "plan"  # Deprecated in new schema
    INVESTIGATE = "investigate"
    CHECK = "check"
    ACT = "act"
    POSTFLIGHT = "postflight"

    def __str__(self):
        return self.value

    def to_new_phase(self) -> NewCascadePhase:
        """Convert OLD enum to NEW enum"""
        mapping = {
            CascadePhase.PREFLIGHT: NewCascadePhase.PREFLIGHT,
            CascadePhase.THINK: NewCascadePhase.THINK,
            CascadePhase.PLAN: NewCascadePhase.THINK,  # No PLAN in new schema
            CascadePhase.INVESTIGATE: NewCascadePhase.INVESTIGATE,
            CascadePhase.CHECK: NewCascadePhase.CHECK,
            CascadePhase.ACT: NewCascadePhase.ACT,
            CascadePhase.POSTFLIGHT: NewCascadePhase.POSTFLIGHT,
        }
        return mapping.get(self, NewCascadePhase.PREFLIGHT)


@dataclass
class CanonicalCascadeState:
    """State tracking for canonical cascade (kept for compatibility)"""
    task_id: str
    phase: CascadePhase
    round_num: int = 0
    investigation_count: int = 0
    
    # Current assessment
    current_assessment: Optional[EpistemicAssessmentSchema] = None
    
    # Phase-specific data
    preflight_assessment: Optional[EpistemicAssessmentSchema] = None
    think_assessment: Optional[EpistemicAssessmentSchema] = None
    plan_assessment: Optional[EpistemicAssessmentSchema] = None
    check_assessment: Optional[EpistemicAssessmentSchema] = None
    postflight_assessment: Optional[EpistemicAssessmentSchema] = None
    
    # Investigation tracking
    investigation_recommendations: List[Dict[str, Any]] = None  # Changed from ToolRecommendation
    gaps_identified: List[Dict[str, Any]] = None
    
    # Execution tracking
    action_taken: bool = False
    execution_result: Optional[Dict[str, Any]] = None
    
    # Uncertainty tracking
    uncertainty_history: List[float] = None
    confidence_history: List[float] = None
    
    # Calibration tracking
    calibration_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.investigation_recommendations is None:
            self.investigation_recommendations = []
        if self.gaps_identified is None:
            self.gaps_identified = []
        if self.uncertainty_history is None:
            self.uncertainty_history = []
        if self.confidence_history is None:
            self.confidence_history = []
        if self.calibration_data is None:
            self.calibration_data = {}
    
    def to_json(self) -> Dict[str, Any]:
        """Convert state to JSON for serialization"""
        return {
            'task_id': self.task_id,
            'phase': self.phase.value,
            'round_num': self.round_num,
            'investigation_count': self.investigation_count,
            'action_taken': self.action_taken,
            'uncertainty_history': self.uncertainty_history,
            'confidence_history': self.confidence_history
        }
    
    def _extract_vector_summary(self) -> Dict[str, float]:
        """Extract vector summary from current assessment"""
        if not self.current_assessment:
            return {}
        
        from empirica.core.schemas.assessment_converters import extract_vector_summary
        return extract_vector_summary(self.current_assessment)


# ============================================================================
# DEPRECATED: Orchestration logic removed (replaced by CLI self-assessment)
# ============================================================================

class CanonicalEpistemicCascade:
    """
    DEPRECATED: Legacy stub for backward compatibility.
    
    All orchestration logic removed. Use CLI commands for self-assessment:
    - preflight-submit
    - check-submit  
    - postflight-submit
    """
    
    def __init__(
        self,
        action_confidence_threshold: float = 0.7,
        max_investigation_rounds: int = 5,
        agent_id: Optional[str] = None,
        session_db = None,
        reasoning_service = None,
        epistemic_bus = None
    ):
        """
        Initialize cascade stub (for backward compatibility only).
        
        DEPRECATED: This class no longer performs orchestration.
        Use CLI commands for self-assessment workflow.
        """
        self.action_confidence_threshold = action_confidence_threshold
        self.max_investigation_rounds = max_investigation_rounds
        self.agent_id = agent_id
        self.session_db = session_db
        self.reasoning_service = reasoning_service
        self.epistemic_bus = epistemic_bus
        
        logger.warning(
            "CanonicalEpistemicCascade is deprecated. "
            "Use CLI commands: preflight-submit, check-submit, postflight-submit"
        )

    async def run_epistemic_cascade(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        DEPRECATED: Orchestration removed.
        
        This method is no longer functional. Use CLI commands for self-assessment:
        - preflight-submit
        - check-submit
        - postflight-submit
        """
        raise NotImplementedError(
            "run_epistemic_cascade() is deprecated. "
            "Use CLI commands: empirica preflight-submit -, empirica check-submit -, empirica postflight-submit -"
        )


async def run_canonical_cascade(
    task: str,
    context: Dict[str, Any],
    confidence_threshold: float = 0.7,
    max_investigation_rounds: int = 5,
    agent_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    DEPRECATED: Use CLI commands instead.
    
    For self-assessment workflow:
      empirica preflight-submit -
      empirica check-submit -
      empirica postflight-submit -
    """
    raise NotImplementedError(
        "run_canonical_cascade() is deprecated. "
        "Use CLI commands for self-assessment workflow."
    )
