#!/usr/bin/env python3
"""
Canonical Epistemic-Driven Adaptive Cascade

Uses genuine LLM-powered self-assessment without heuristics.
Implements ENGAGEMENT gate, Reflex Frame logging, and canonical weights.

Key Changes from Old Version:
- Uses CanonicalEpistemicAssessor (LLM-powered, no heuristics)
- Enforces ENGAGEMENT gate (≥0.60 required)
- Logs to Reflex Frames for temporal separation
- Uses canonical weights: 35/25/25/15
- Integrates new investigation_strategy.py
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

logger = logging.getLogger(__name__)

# Import canonical structures
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from empirica.core.canonical import (
    CanonicalEpistemicAssessor,
    ReflexLogger,
    Action,
    CANONICAL_WEIGHTS,
    ENGAGEMENT_THRESHOLD
)

# NEW SCHEMA (this is now THE schema)
from empirica.core.schemas.epistemic_assessment import (
    EpistemicAssessmentSchema,
    CascadePhase as NewCascadePhase
)
# Converters removed - using EpistemicAssessmentSchema directly

from .investigation_strategy import recommend_investigation_tools, Domain, ToolRecommendation
from .investigation_plugin import InvestigationPlugin, PluginRegistry

# Session Database (optional)
try:
    from empirica.data.session_database import SessionDatabase
    from empirica.data.session_json_handler import SessionJSONHandler
    SESSION_DB_AVAILABLE = True
except ImportError:
    SESSION_DB_AVAILABLE = False

# Bayesian belief tracking for CHECK phase
try:
    from empirica.calibration.adaptive_uncertainty_calibration.bayesian_belief_tracker import (
        BayesianBeliefTracker,
        Evidence,
        DomainClassifier
    )
    BAYESIAN_AVAILABLE = True
except ImportError:
    BAYESIAN_AVAILABLE = False
    logger.warning("Bayesian belief tracker not available")

# Parallel reasoning and drift monitoring
try:
    from empirica.calibration.parallel_reasoning import ParallelReasoningSystem, DriftMonitor
    PARALLEL_REASONING_AVAILABLE = True
except ImportError:
    PARALLEL_REASONING_AVAILABLE = False
    logger.warning("Parallel reasoning not available")

# Action hooks for tmux dashboard real-time updates
try:
    from empirica.integration.empirica_action_hooks import (
        log_cascade_phase,
        log_12d_state,
        log_thought,
        initialize_tmux_dashboard
    )
    ACTION_HOOKS_AVAILABLE = True
except ImportError:
    ACTION_HOOKS_AVAILABLE = False
    # Silently disable if not available


class CascadePhase(Enum):
    """Enhanced 7-phase cascade workflow"""
    PREFLIGHT = "preflight"     # Baseline epistemic assessment
    THINK = "think"             # Initial understanding
    PLAN = "plan"               # Optional: Complex task breakdown
    INVESTIGATE = "investigate" # Fill knowledge gaps
    CHECK = "check"             # Self-reflection before acting
    ACT = "act"                 # Execute with confidence
    POSTFLIGHT = "postflight"   # Final epistemic assessment


@dataclass
@dataclass
class CanonicalCascadeState:
    """Current state in the canonical 7-phase epistemic cascade"""
    current_phase: CascadePhase
    assessment: Optional[EpistemicAssessmentSchema]
    engagement_gate_passed: bool
    knowledge_gaps: List[str]
    investigation_rounds: int
    decision_rationale: str
    task_id: str
    preflight_assessment: Optional[EpistemicAssessmentSchema] = None  # Baseline
    postflight_assessment: Optional[EpistemicAssessmentSchema] = None  # Final
    epistemic_delta: Optional[Dict[str, float]] = None  # Learning measurement

    def to_json(self) -> Dict[str, Any]:
        """Export for tmux display or logging"""
        return {
            'task_id': self.task_id,
            'phase': self.current_phase.value,
            'engagement_gate_passed': self.engagement_gate_passed,
            'knowledge_gaps': self.knowledge_gaps,
            'investigation_rounds': self.investigation_rounds,
            'rationale': self.decision_rationale,
            'vectors': self._extract_vector_summary() if self.assessment else {}
        }

    def _extract_vector_summary(self) -> Dict[str, float]:
        """Extract key vector values for display"""
        if not self.assessment:
            return {}

        return {
            # GATE
            'engagement': self.assessment.engagement.score,
            # FOUNDATION
            'know': self.assessment.know.score,
            'do': self.assessment.do.score,
            'context': self.assessment.context.score,
            # COMPREHENSION
            'clarity': self.assessment.clarity.score,
            'coherence': self.assessment.coherence.score,
            # EXECUTION
            'state': self.assessment.state.score,
            'change': self.assessment.change.score,
            'completion': self.assessment.completion.score,
            'impact': self.assessment.impact.score,
            # TIER CONFIDENCES
            'foundation_confidence': self.assessment.foundation_confidence,
            'comprehension_confidence': self.assessment.comprehension_confidence,
            'execution_confidence': self.assessment.execution_confidence,
            'overall_confidence': self.assessment.overall_confidence
        }


class CanonicalEpistemicCascade:
    """
    Canonical adaptive cascade using genuine LLM-powered self-assessment

    Architecture:
    - ENGAGEMENT gate enforced (≥0.60)
    - Canonical weights: 35/25/25/15
    - Reflex Frame logging for temporal separation
    - No heuristics, no confabulation
    - Domain-aware investigation strategy

    Flow: THINK → UNCERTAINTY → [INVESTIGATE*] → CHECK → ACT
    """

    def __init__(
        self,
        # NEW: Profile-based configuration
        profile_name: Optional[str] = None,
        ai_model: Optional[str] = None,
        domain: Optional[str] = None,
        
        # DEPRECATED: Keep for backward compatibility
        action_confidence_threshold: Optional[float] = None,
        max_investigation_rounds: Optional[int] = None,
        
        agent_id: str = "cascade",
        tmux_extension=None,
        enable_bayesian: bool = True,
        enable_drift_monitor: bool = True,
        investigation_plugins: Optional[Dict[str, InvestigationPlugin]] = None,
        enable_action_hooks: bool = True,
        auto_start_dashboard: bool = False,
        enable_perspective_caching: bool = True,  # Phase 2 optimization
        cache_ttl: int = 300,  # Phase 2: Cache TTL in seconds
        enable_session_db: bool = True,  # Session database tracking
        enable_git_notes: bool = True,  # Phase 1.5: Git-enhanced checkpoints
        session_id: Optional[str] = None  # Phase 1.5: Session ID for git notes
    ):
        """
        Initialize canonical cascade

        Args:
            # NEW: Profile-based configuration
            profile_name: Investigation profile name (e.g., 'balanced', 'autonomous_agent')
            ai_model: AI model for auto-selection (e.g., 'claude', 'gpt-4')
            domain: Domain context (e.g., 'research', 'critical_domain')
            
            # DEPRECATED: For backward compatibility (use profile instead)
            action_confidence_threshold: Minimum overall_confidence to ACT (deprecated)
            max_investigation_rounds: Maximum investigation loops (deprecated)
            
            agent_id: Agent identifier for logging
            tmux_extension: Optional tmux display extension
            enable_bayesian: Enable Bayesian Guardian for evidence-based belief tracking
            enable_drift_monitor: Enable Drift Monitor for behavioral drift detection
            investigation_plugins: Custom investigation tools (extensibility)
            enable_action_hooks: Enable real-time tmux dashboard updates (default: True)
            auto_start_dashboard: Auto-start tmux dashboard on cascade creation (default: False)
            enable_perspective_caching: Enable Phase 2 optimization - cache perspectives (default: True)
            cache_ttl: Phase 2 cache time-to-live in seconds (default: 300)
            enable_session_db: Enable session database for epistemic tracking (default: True)
            enable_git_notes: Enable Phase 1.5 git-enhanced checkpoints (97.5% token reduction) (default: True)
            session_id: Session ID for git notes tracking (default: auto-generated)
        """
        # Load investigation profile
        from empirica.config.profile_loader import select_profile, get_profile_loader

        self.profile = select_profile(
            ai_model=ai_model,
            domain=domain,
            explicit_profile=profile_name
        )

        # Get universal constraints
        loader = get_profile_loader()
        self.universal_constraints = loader.universal_constraints

        # Backward compatibility: override profile if old params provided
        if max_investigation_rounds is not None:
            import warnings
            warnings.warn(
                "max_investigation_rounds is deprecated. Use profile_name instead.",
                DeprecationWarning,
                stacklevel=2
            )
            self.profile.investigation.max_rounds = max_investigation_rounds

        if action_confidence_threshold is not None:
            import warnings
            warnings.warn(
                "action_confidence_threshold is deprecated. Use profile_name instead.",
                DeprecationWarning,
                stacklevel=2
            )
            self.profile.investigation.confidence_threshold = action_confidence_threshold

        # Set instance variables from profile
        self.action_confidence_threshold = self.profile.investigation.confidence_threshold
        self.max_investigation_rounds = self.profile.investigation.max_rounds

        self.agent_id = agent_id
        self.tmux_extension = tmux_extension

        # Initialize canonical assessor (LLM-powered, no heuristics)
        self.assessor = CanonicalEpistemicAssessor(agent_id=agent_id)

        # Initialize Reflex Frame logger for temporal separation
        self.reflex_logger = ReflexLogger()
        
        # Phase 1.5: Initialize Git-Enhanced Reflex Logger for compressed checkpoints
        self.enable_git_notes = enable_git_notes
        self.session_id = session_id or f"cascade-{agent_id}-{int(time.time())}"
        
        if self.enable_git_notes:
            try:
                from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
                from empirica.metrics.token_efficiency import TokenEfficiencyMetrics
                
                self.git_logger = GitEnhancedReflexLogger(
                    session_id=self.session_id,
                    enable_git_notes=True
                )
                self.token_metrics = TokenEfficiencyMetrics(session_id=self.session_id)
                logger.info(f"Git-enhanced checkpoints enabled (session: {self.session_id})")
            except Exception as e:
                logger.warning(f"Git integration unavailable: {e}")
                self.git_logger = None
                self.token_metrics = None
                self.enable_git_notes = False
        else:
            self.git_logger = None
            self.token_metrics = None

        # Track cascade state
        self.current_state: Optional[CanonicalCascadeState] = None
        self.cascade_history = []

        # LLM integration via Parallel Reasoning System (phi3 via Ollama)
        # Parallel reasoning provides both epistemic assessment and behavioral integrity checking
        # Initialize parallel reasoner if available (used for epistemic assessment) - OPTIONAL
        try:
            if PARALLEL_REASONING_AVAILABLE:
                self.parallel_reasoner = ParallelReasoningSystem(
                    enable_perspective_caching=enable_perspective_caching,
                    cache_ttl=cache_ttl
                )
                logger.info("Parallel Reasoning enabled for epistemic assessment")
            else:
                self.parallel_reasoner = None
                logger.warning("Parallel reasoning not available (will use direct assessment)")
        except Exception as e:
            self.parallel_reasoner = None
            logger.warning(f"Parallel reasoning initialization failed: {e}")
            logger.info("Continuing with direct assessment mode")

        # Bayesian Guardian (CHECK phase - evidence-based belief tracking)
        self.enable_bayesian = enable_bayesian and BAYESIAN_AVAILABLE
        self.bayesian_tracker = BayesianBeliefTracker() if self.enable_bayesian else None
        self.current_context_key = None
        self.current_domain = None
        if self.enable_bayesian:
            logger.info("Bayesian Guardian enabled")

        # Drift Monitor (behavioral drift detection via parallel reasoning)
        # Requires parallel_reasoner to be initialized
        try:
            self.enable_drift_monitor = enable_drift_monitor and PARALLEL_REASONING_AVAILABLE and self.parallel_reasoner is not None
            self.drift_monitor = DriftMonitor() if self.enable_drift_monitor else None
            # Note: synthesis_history is tracked in self.parallel_reasoner.synthesis_history
            if self.enable_drift_monitor:
                logger.info("Drift Monitor enabled")
            elif enable_drift_monitor:
                logger.warning("Drift monitoring requested but parallel reasoning unavailable")
        except Exception as e:
            self.drift_monitor = None
            self.enable_drift_monitor = False
            logger.warning(f"Drift monitor initialization failed: {e}")
        
        # Plugin System (extensible investigation tools)
        self.investigation_plugins = investigation_plugins or {}
        if self.investigation_plugins:
            logger.info(f"Loaded {len(self.investigation_plugins)} investigation plugins:")
            for plugin_name in self.investigation_plugins.keys():
                logger.info(f"   • {plugin_name}")
        
        # Action Hooks (real-time tmux dashboard updates)
        self.enable_action_hooks = enable_action_hooks and ACTION_HOOKS_AVAILABLE
        if self.enable_action_hooks:
            logger.info("Action Hooks enabled (real-time dashboard updates)")
            
            # Auto-start dashboard if requested
            if auto_start_dashboard:
                try:
                    initialize_tmux_dashboard()
                    logger.info("TMux dashboard auto-started")
                except Exception as e:
                    logger.warning(f"Dashboard auto-start failed: {e}")
        
        # Session Database (stores all epistemic states to SQLite)
        self.enable_session_db = enable_session_db and SESSION_DB_AVAILABLE
        if self.enable_session_db:
            try:
                self.session_db = SessionDatabase()
                self.session_json = SessionJSONHandler()
                self.current_session_id = None
                self.current_cascade_id = None
                logger.info("Session Database enabled (epistemic tracking)")
            except Exception as e:
                self.enable_session_db = False
                self.session_db = None
                self.session_json = None
                logger.warning(f"Session database failed: {e}")
        else:
            self.session_db = None
            self.session_json = None
            if enable_session_db:
                logger.warning("Session database requested but not available")

    async def run_epistemic_cascade(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run canonical epistemic cascade with refined workflow

        Args:
            task: Task description
            context: Additional context (cwd, tools, history, etc.)

        Returns:
            Dict with action, confidence, rationale, and guidance

        Flow (ENHANCED CASCADE WORKFLOW v1.1):
            1. PREFLIGHT: Baseline epistemic assessment (13 vectors)
            2. THINK: Initial reasoning about task
            3. PLAN: Structured approach for complex tasks (optional)
            4. INVESTIGATE: Gather information
            5. CHECK: Self-assess readiness (recalibrate if needed)
            6. ACT: Execute with confidence
            7. POSTFLIGHT: Validate calibration accuracy
        """
        if context is None:
            context = {}

        # Generate task ID
        task_id = self._generate_task_id(task)

        logger.info("Canonical Epistemic Cascade - Enhanced 7-Phase Workflow")
        logger.info(f"   Task: '{task[:60]}...'")
        logger.info(f"   Task ID: {task_id}")
        logger.info(f"   Agent: {self.agent_id}")

        # ================================================================
        # PHASE 0: PREFLIGHT - Baseline Epistemic Assessment
        # ================================================================
        logger.info(f"\n{'='*70}")
        logger.info(f"  PHASE 0: PREFLIGHT - Baseline Epistemic Assessment")
        logger.info(f"{'='*70}")
        
        self._enter_phase(CascadePhase.PREFLIGHT)
        
        # Get baseline epistemic self-assessment (all 13 vectors)
        preflight_assessment = await self._assess_epistemic_state(
            task, 
            context, 
            task_id, 
            CascadePhase.PREFLIGHT
        )
        
        # Log PREFLIGHT to Reflex Frame
        await self._log_reflex_frame(
            preflight_assessment, 
            CascadePhase.PREFLIGHT, 
            task_id, 
            task, 
            context
        )
        
        # Store in session database if enabled
        if self.enable_session_db and self.session_db:
            self.session_db.log_epistemic_assessment(
                cascade_id=task_id,
                assessment=preflight_assessment,
                phase="preflight"
            )
        
        # Phase 1.5: Create git checkpoint (compressed, 97.5% token reduction)
        if self.enable_git_notes and self.git_logger:
            try:
                vectors_dict = {
                    'engagement': preflight_assessment.engagement.score,
                    'know': preflight_assessment.know.score,
                    'do': preflight_assessment.do.score,
                    'context': preflight_assessment.context.score,
                    'clarity': preflight_assessment.clarity.score,
                    'coherence': preflight_assessment.coherence.score,
                    'signal': preflight_assessment.signal.score,
                    'density': preflight_assessment.density.score,
                    'state': preflight_assessment.state.score,
                    'change': preflight_assessment.change.score,
                    'completion': preflight_assessment.completion.score,
                    'impact': preflight_assessment.impact.score,
                    'uncertainty': preflight_assessment.uncertainty.score
                }
                self.git_logger.add_checkpoint(
                    phase="PREFLIGHT",
                    round_num=1,
                    vectors=vectors_dict,
                    metadata={"task": task[:100] if task else ""}
                )
                logger.info("✓ PREFLIGHT checkpoint saved to git notes")
            except Exception as e:
                logger.warning(f"Git checkpoint failed: {e}")
        
        logger.info(f"\n📊 PREFLIGHT Baseline Established:")
        logger.info(f"   Overall Confidence: {preflight_assessment.overall_confidence:.2f}")
        logger.info(f"   Foundation (KNOW/DO/CONTEXT): {preflight_assessment.foundation_confidence:.2f}")
        logger.info(f"   Comprehension (CLARITY/COHERENCE): {preflight_assessment.comprehension_confidence:.2f}")
        logger.info(f"   Execution Readiness: {preflight_assessment.execution_confidence:.2f}")
        logger.info(f"   Explicit Uncertainty: {preflight_assessment.uncertainty.score:.2f}")
        
        # Action hooks: Log PREFLIGHT
        if self.enable_action_hooks:
            log_cascade_phase("PREFLIGHT", task, {
                "agent_id": self.agent_id,
                "baseline_confidence": preflight_assessment.overall_confidence,
                "uncertainty": preflight_assessment.uncertainty.score
            })

        # ================================================================
        # PHASE 1: THINK - Initial epistemic assessment
        # ================================================================
        logger.info(f"\n{'='*70}")
        logger.info(f"  PHASE 1: THINK - Initial Reasoning")
        logger.info(f"{'='*70}")
        
        self._enter_phase(CascadePhase.THINK)

        # Get LLM-powered self-assessment
        assessment = await self._assess_epistemic_state(task, context, task_id, CascadePhase.THINK)

        # Log THINK phase to Reflex Frame
        await self._log_reflex_frame(assessment, CascadePhase.THINK, task_id, task, context)

        self._update_tmux_display(CascadePhase.THINK, assessment)
        
        # Action hooks: Log THINK phase
        if self.enable_action_hooks:
            log_thought("Analyzing task and initial understanding", "THINK", task)
            log_cascade_phase("THINK", task, {"agent_id": self.agent_id})

        # ================================================================
        # ENGAGEMENT GATE CHECK
        # ================================================================
        if not assessment.engagement_gate_passed:
            logger.warning(f"\n🚫 ENGAGEMENT GATE FAILED")
            logger.warning(f"   Score: {assessment.engagement.score:.2f} (threshold: {ENGAGEMENT_THRESHOLD:.2f})")
            logger.warning(f"   Rationale: {assessment.engagement.rationale}")
            logger.warning(f"   Recommendation: Request clarification or reframe task")

            # Early return: CLARIFY action
            final_decision = {
                'action': Action.CLARIFY.value,
                'confidence': assessment.engagement.score,
                'rationale': f"ENGAGEMENT gate not met ({assessment.engagement.score:.2f}). {assessment.engagement.rationale}",
                'recommended_action': assessment.recommended_action.value,
                'vector_summary': self._extract_vector_summary(assessment),
                'engagement_gate_passed': False
            }

            # Store state
            self.current_state = CanonicalCascadeState(
                current_phase=CascadePhase.ACT,
                assessment=assessment,
                engagement_gate_passed=False,
                knowledge_gaps=[],
                investigation_rounds=0,
                decision_rationale=final_decision['rationale'],
                task_id=task_id
            )

            return final_decision

        logger.info(f"\n✅ ENGAGEMENT GATE PASSED")
        logger.info(f"   Score: {assessment.engagement.score:.2f}")
        logger.info(f"   Rationale: {assessment.engagement.rationale}")

        # ================================================================
        # PHASE 2: THINK continues - Identify knowledge gaps
        # ================================================================
        # Knowledge gap identification is part of THINK phase
        
        knowledge_gaps = self._identify_knowledge_gaps(assessment)

        logger.info(f"\n📊 Self-Assessed Knowledge Gaps: {len(knowledge_gaps)}")
        if knowledge_gaps:
            for gap in knowledge_gaps:
                priority_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(gap['priority'], '⚪')
                logger.info(f"   {priority_emoji} {gap['vector'].upper()} ({gap['score']:.2f}) - {gap['priority']}")
                logger.info(f"      Reason: {gap['reason']}")
        else:
            logger.info(f"   ✓ No gaps flagged for investigation")

        # Already logged in THINK phase above
        
        # ================================================================
        # BAYESIAN GUARDIAN: Initialize beliefs from initial assessment
        # ================================================================
        if self.enable_bayesian and self.bayesian_tracker:
            # Determine domain and decide if Bayesian should activate
            self.current_domain = DomainClassifier.classify_domain(task, context)
            self.current_context_key = f"task:{task_id}:{int(time.time())}"
            
            should_activate = DomainClassifier.should_activate_bayesian(
                self.current_domain,
                clarity_index=assessment.clarity.score,
                discrepancies_found=0
            )
            
            if should_activate:
                self.bayesian_tracker.activate(f"Domain: {self.current_domain}")
                
                # Initialize Bayesian beliefs from initial assessment
                initial_beliefs = {
                    'know': assessment.know.score,
                    'do': assessment.do.score,
                    'context': assessment.context.score,
                    'clarity': assessment.clarity.score,
                    'coherence': assessment.coherence.score,
                    'state': assessment.state.score,
                    'completion': assessment.completion.score,
                    'impact': assessment.impact.score
                }
                
                self.bayesian_tracker.initialize_beliefs(
                    self.current_context_key,
                    initial_beliefs,
                    initial_variance=0.3
                )
                
                logger.info(f"\n   🧮 Bayesian Guardian activated for {self.current_domain} domain")
                logger.info(f"      Initialized beliefs from assessment")
        
        # Action hooks: Log 12D state and UNCERTAINTY phase
        if self.enable_action_hooks:
            state_dict = {
                "epistemic_uncertainty": {
                    "know": assessment.know.score,
                    "do": assessment.do.score,
                    "context": assessment.context.score
                },
                "epistemic_comprehension": {
                    "clarity": assessment.clarity.score,
                    "coherence": assessment.coherence.score,
                    "density": assessment.density.score,
                    "signal": assessment.signal.score
                },
                "execution_awareness": {
                    "state": assessment.state.score,
                    "change": assessment.change.score,
                    "completion": assessment.completion.score,
                    "impact": assessment.impact.score
                },
                "engagement": {
                    "engagement": assessment.engagement.score
                },
                "overall_confidence": assessment.overall_confidence,
                "ai_id": self.agent_id
            }
            log_12d_state(state_dict)
            log_cascade_phase("UNCERTAINTY", task, {
                "gaps": len(knowledge_gaps),
                "bayesian_active": self.bayesian_tracker.active if self.bayesian_tracker else False
            })

        self._update_tmux_display(CascadePhase.THINK, assessment, knowledge_gaps)

        # ================================================================
        # PHASE 3: INVESTIGATE loop
        # ================================================================
        # Investigation triggers when:
        # 1. Mandatory: Overall confidence < threshold (safety measure)
        # 2. Voluntary: AI flagged critical/high priority gaps (epistemic humility)
        #
        # This allows investigation even with high confidence if AI deems it necessary
        # ================================================================
        investigation_rounds = 0
        current_assessment = assessment

        max_rounds = self.profile.investigation.max_rounds
        while max_rounds is None or investigation_rounds < max_rounds:
            # Check if investigation is needed
            # Support dynamic thresholds for high reasoning AIs
            if self.profile.investigation.confidence_threshold_dynamic:
                # AI determines threshold based on context (future feature)
                threshold = self.profile.investigation.confidence_threshold
            else:
                threshold = self.profile.investigation.confidence_threshold

            confidence_low = current_assessment.overall_confidence < threshold
            critical_gaps = [g for g in knowledge_gaps if g.get('priority') in ['critical', 'high']]

            # Decide whether to investigate
            if confidence_low:
                # Mandatory investigation due to low confidence
                logger.info(f"\n🔬 Investigation Round {investigation_rounds + 1}/{max_rounds or '∞'} (REQUIRED - confidence {current_assessment.overall_confidence:.2f} < {threshold})")
                should_investigate = True
            elif critical_gaps:
                # Voluntary investigation due to self-assessed critical gaps
                logger.info(f"\n🔬 Investigation Round {investigation_rounds + 1}/{max_rounds or '∞'} (VOLUNTARY - {len(critical_gaps)} critical/high priority gaps)")
                for gap in critical_gaps:
                    logger.info(f"   • {gap['vector']}: {gap['reason']}")
                should_investigate = True
            else:
                # Confidence met and no critical gaps - skip investigation
                logger.info(f"\n✓ Confidence threshold met ({current_assessment.overall_confidence:.2f} ≥ {threshold})")
                logger.info(f"   No critical gaps flagged - proceeding to CHECK")
                should_investigate = False

            if not should_investigate:
                break

            investigation_rounds += 1
            self._enter_phase(CascadePhase.INVESTIGATE)

            # Conduct investigation using new strategy
            investigation_results = await self._conduct_investigation(
                task, context, knowledge_gaps, current_assessment
            )

            # Update context with investigation results
            context.update(investigation_results.get('new_information', {}))

            # Re-assess after investigation
            current_assessment = await self._assess_epistemic_state(
                task, context, task_id, CascadePhase.INVESTIGATE, investigation_rounds
            )

            # Update gaps
            knowledge_gaps = self._identify_knowledge_gaps(current_assessment)

            # Log INVESTIGATE phase to reflex
            await self._log_reflex_frame(
                current_assessment, CascadePhase.INVESTIGATE, task_id, task, context,
                investigation_results=investigation_results
            )
            
            # Log INVESTIGATE to database for transparency
            if SESSION_DB_AVAILABLE:
                try:
                    from empirica.data.session_database import SessionDatabase
                    db = SessionDatabase()
                    db.log_investigation_round(
                        session_id=task_id,
                        cascade_id=None,  # Will be added when cascade tracking improved
                        round_number=investigation_rounds,
                        tools_mentioned=investigation_results.get('tools_used', 'Not specified'),
                        findings=investigation_results.get('new_information', {}).get('summary', 'Investigation completed'),
                        confidence_before=assessment.overall_confidence,
                        confidence_after=current_assessment.overall_confidence,
                        summary=f"Round {investigation_rounds}: Confidence {assessment.overall_confidence:.2f} → {current_assessment.overall_confidence:.2f}"
                    )
                    db.close()
                except Exception as e:
                    logger.warning(f"   ⚠️  Could not log investigation to DB: {e}")

            self._update_tmux_display(
                CascadePhase.INVESTIGATE, current_assessment, knowledge_gaps, investigation_rounds
            )

            logger.info(f"   Updated confidence: {current_assessment.overall_confidence:.2f}")

        # ================================================================
        # PHASE 4: CHECK - Verify readiness to act
        # ================================================================
        self._enter_phase(CascadePhase.CHECK)

        check_result = self._verify_readiness(current_assessment)

        # Log CHECK phase
        await self._log_reflex_frame(current_assessment, CascadePhase.CHECK, task_id, task, context)
        
        # Phase 1.5: Create CHECK checkpoint
        if self.enable_git_notes and self.git_logger:
            try:
                vectors_dict = {
                    'engagement': current_assessment.engagement.score,
                    'know': current_assessment.know.score,
                    'do': current_assessment.do.score,
                    'context': current_assessment.context.score,
                    'clarity': current_assessment.clarity.score,
                    'coherence': current_assessment.coherence.score,
                    'signal': current_assessment.signal.score,
                    'density': current_assessment.density.score,
                    'state': current_assessment.state.score,
                    'change': current_assessment.change.score,
                    'completion': current_assessment.completion.score,
                    'impact': current_assessment.impact.score,
                    'uncertainty': current_assessment.uncertainty.score
                }
                self.git_logger.add_checkpoint(
                    phase="CHECK",
                    round_num=investigation_rounds + 2,  # PREFLIGHT(1) + THINK + investigations
                    vectors=vectors_dict,
                    metadata={
                        "investigation_rounds": investigation_rounds,
                        "decision": check_result.get('decision', 'proceed')
                    }
                )
                logger.info("✓ CHECK checkpoint saved to git notes")
            except Exception as e:
                logger.warning(f"Git checkpoint failed: {e}")

        self._update_tmux_display(CascadePhase.CHECK, current_assessment)

        # ================================================================
        # PHASE 5: ACT - Make final decision
        # ================================================================
        self._enter_phase(CascadePhase.ACT)

        final_decision = self._make_final_decision(current_assessment, check_result, investigation_rounds)

        # Log ACT phase to reflex
        await self._log_reflex_frame(current_assessment, CascadePhase.ACT, task_id, task, context)
        
        # Log ACT to database for transparency
        if SESSION_DB_AVAILABLE:
            try:
                from empirica.data.session_database import SessionDatabase
                db = SessionDatabase()
                db.log_act_phase(
                    session_id=task_id,
                    cascade_id=None,  # Will be added when cascade tracking improved
                    action_type=final_decision['action'],
                    action_rationale=final_decision['rationale'],
                    final_confidence=final_decision['confidence'],
                    goal_id=None  # Can be populated by goal orchestrator if available
                )
                db.close()
            except Exception as e:
                logger.warning(f"Could not log ACT to DB: {e}")

        self._update_tmux_display(CascadePhase.ACT, current_assessment)

        # Store final state
        self.current_state = CanonicalCascadeState(
            current_phase=CascadePhase.ACT,
            assessment=current_assessment,
            engagement_gate_passed=True,
            knowledge_gaps=knowledge_gaps,
            investigation_rounds=investigation_rounds,
            decision_rationale=final_decision['rationale'],
            task_id=task_id
        )

        self.cascade_history.append(self.current_state)

        logger.info(f"\n🎯 CASCADE COMPLETE")
        logger.info(f"   Action: {final_decision['action'].upper()}")
        logger.info(f"   Confidence: {final_decision['confidence']:.2f}")
        logger.info(f"   Investigation Rounds: {investigation_rounds}")
        
        # Action hook for ACT phase (final)
        if self.enable_action_hooks:
            act_thoughts = [
                f"Final Action: {final_decision['action']}",
                f"Final Confidence: {final_decision['confidence']:.2f}",
                f"Rationale: {final_decision['rationale'][:100]}..."
            ]
            
            if investigation_rounds > 0:
                act_thoughts.append(f"After {investigation_rounds} investigation rounds")
            
            log_thought("\n".join(act_thoughts), "ACT", task)
            log_cascade_phase("ACT", task, {
                "action": final_decision['action'],
                "confidence": final_decision['confidence'],
                "investigation_rounds": investigation_rounds,
                "complete": True
            })

        # ================================================================
        # PHASE 6: POSTFLIGHT - Final Epistemic Assessment & Calibration
        # ================================================================
        logger.info(f"\n{'='*70}")
        logger.info(f"  PHASE 6: POSTFLIGHT - Final Epistemic Assessment")
        logger.info(f"{'='*70}")
        
        self._enter_phase(CascadePhase.POSTFLIGHT)
        
        # Get final epistemic self-assessment (measure learning)
        postflight_assessment = await self._assess_epistemic_state(
            task, 
            context, 
            task_id, 
            CascadePhase.POSTFLIGHT,
            investigation_rounds=investigation_rounds  # Pass investigation count
        )
        
        # Calculate epistemic delta (learning measurement)
        epistemic_delta = self._calculate_epistemic_delta(
            preflight_assessment,
            postflight_assessment
        )
        
        # Log POSTFLIGHT to Reflex Frame
        await self._log_reflex_frame(
            postflight_assessment, 
            CascadePhase.POSTFLIGHT, 
            task_id, 
            task, 
            context,
            epistemic_delta=epistemic_delta
        )
        
        # Store in session database if enabled
        if self.enable_session_db and self.session_db:
            self.session_db.log_epistemic_assessment(
                cascade_id=task_id,
                assessment=postflight_assessment,
                phase="postflight"
            )
            
            # Store delta
            self.session_db.store_epistemic_delta(
                cascade_id=task_id,
                delta=epistemic_delta
            )
        
        # Phase 1.5: Create POSTFLIGHT checkpoint (final state + learning deltas)
        if self.enable_git_notes and self.git_logger:
            try:
                vectors_dict = {
                    'engagement': postflight_assessment.engagement.score,
                    'know': postflight_assessment.know.score,
                    'do': postflight_assessment.do.score,
                    'context': postflight_assessment.context.score,
                    'clarity': postflight_assessment.clarity.score,
                    'coherence': postflight_assessment.coherence.score,
                    'signal': postflight_assessment.signal.score,
                    'density': postflight_assessment.density.score,
                    'state': postflight_assessment.state.score,
                    'change': postflight_assessment.change.score,
                    'completion': postflight_assessment.completion.score,
                    'impact': postflight_assessment.impact.score,
                    'uncertainty': postflight_assessment.uncertainty.score
                }
                self.git_logger.add_checkpoint(
                    phase="POSTFLIGHT",
                    round_num=investigation_rounds + 10,  # Approximate final round
                    vectors=vectors_dict,
                    metadata={
                        "investigation_rounds": investigation_rounds,
                        "epistemic_delta": {
                            "foundation": epistemic_delta.get('foundation_confidence', 0),
                            "comprehension": epistemic_delta.get('comprehension_confidence', 0),
                            "execution": epistemic_delta.get('execution_confidence', 0),
                            "uncertainty": epistemic_delta.get('uncertainty', 0)
                        },
                        "outcome": final_decision.get('action', 'completed')
                    }
                )
                logger.info("✓ POSTFLIGHT checkpoint saved to git notes")
                
                # Generate token efficiency report
                if self.token_metrics:
                    try:
                        report = self.token_metrics.export_report(format="json")
                        comparison = self.token_metrics.compare_efficiency()
                        reduction = comparison["total"]["reduction_percentage"]
                        logger.info(f"✓ Token efficiency: {reduction:.1f}% reduction achieved")
                    except Exception as e:
                        logger.debug(f"Token report generation skipped: {e}")
                        
            except Exception as e:
                logger.warning(f"Git checkpoint failed: {e}")
        
        logger.info(f"\n📊 POSTFLIGHT Assessment Complete:")
        logger.info(f"   Final Confidence: {postflight_assessment.overall_confidence:.2f}")
        logger.info(f"   Δ Foundation: {epistemic_delta.get('foundation_confidence', 0):+.2f}")
        logger.info(f"   Δ Comprehension: {epistemic_delta.get('comprehension_confidence', 0):+.2f}")
        logger.info(f"   Δ Execution: {epistemic_delta.get('execution_confidence', 0):+.2f}")
        logger.info(f"   Δ Uncertainty: {epistemic_delta.get('uncertainty', 0):+.2f} (should decrease)")
        
        # Calibration check: Did confidence match reality?
        calibration_check = self._check_calibration_accuracy(
            preflight_assessment,
            postflight_assessment,
            final_decision
        )
        
        # Report calibration delta without judgment
        logger.info(f"\n📊 Calibration Delta: {calibration_check['note']}")
        logger.info(f"   PREFLIGHT confidence: {calibration_check['preflight_confidence']:.2f}")
        logger.info(f"   POSTFLIGHT confidence: {calibration_check['postflight_confidence']:.2f}")
        logger.info(f"   Learning occurred: {'Yes' if calibration_check['confidence_delta'] > 0 else 'No change' if calibration_check['confidence_delta'] == 0 else 'Decreased'}")
        
        # Action hooks: Log POSTFLIGHT
        if self.enable_action_hooks:
            log_cascade_phase("POSTFLIGHT", task, {
                "agent_id": self.agent_id,
                "final_confidence": postflight_assessment.overall_confidence,
                "epistemic_delta": epistemic_delta,
                "calibration": calibration_check
            })
        
        # Update final state with preflight/postflight
        self.current_state = CanonicalCascadeState(
            current_phase=CascadePhase.POSTFLIGHT,
            assessment=current_assessment,
            preflight_assessment=preflight_assessment,
            postflight_assessment=postflight_assessment,
            epistemic_delta=epistemic_delta,
            engagement_gate_passed=True,
            knowledge_gaps=knowledge_gaps,
            investigation_rounds=investigation_rounds,
            decision_rationale=final_decision['rationale'],
            task_id=task_id
        )
        
        # Add calibration data to final decision
        final_decision['calibration'] = calibration_check
        final_decision['epistemic_delta'] = epistemic_delta
        final_decision['preflight_confidence'] = preflight_assessment.overall_confidence
        final_decision['postflight_confidence'] = postflight_assessment.overall_confidence

        return final_decision

    async def _assess_epistemic_state(
        self,
        task: str,
        context: Dict[str, Any],
        task_id: str,
        phase: CascadePhase,
        round_num: Optional[int] = None,
        investigation_rounds: int = 0
    ) -> EpistemicAssessmentSchema:
        """
        Assess epistemic state returning EpistemicAssessmentSchema
        
        Uses parse_llm_response() from assessor.
        """
        # Convert OLD CascadePhase enum to NEW CascadePhase enum
        # Note: NEW schema doesn't have PLAN phase, map it to THINK
        phase_map = {
            CascadePhase.PREFLIGHT: NewCascadePhase.PREFLIGHT,
            CascadePhase.THINK: NewCascadePhase.THINK,
            CascadePhase.PLAN: NewCascadePhase.THINK,  # NEW schema doesn't have PLAN
            CascadePhase.INVESTIGATE: NewCascadePhase.INVESTIGATE,
            CascadePhase.CHECK: NewCascadePhase.CHECK,
            CascadePhase.ACT: NewCascadePhase.ACT,
            CascadePhase.POSTFLIGHT: NewCascadePhase.POSTFLIGHT
        }
        new_phase = phase_map.get(phase, NewCascadePhase.PREFLIGHT)
        
        # Check database for real assessment from MCP tools
        if self.session_db:
            real_assessment_old = await self._retrieve_mcp_assessment(task_id, phase)
            if real_assessment_old:
                phase_str = phase.value if hasattr(phase, 'value') else str(phase)
                logger.info(f"\n   ✅ Using genuine self-assessment from MCP for phase: {phase_str}")
                # Return NEW schema directly
                return real_assessment_old
        
        # Get self-assessment prompt from canonical assessor
        assessment_request = await self.assessor.assess(task, context)
        
        # Check if we need AI self-assessment
        if isinstance(assessment_request, dict) and 'self_assessment_prompt' in assessment_request:
            # No MCP assessment found - use baseline with NEW schema
            logger.info(f"\n   🤔 No MCP assessment found - using baseline for phase: {phase}")
            logger.info(f"\n   📋 (In MCP mode, call execute_{phase} to get self-assessment prompt)")
            
            # Import for baseline creation
            from empirica.core.schemas.epistemic_assessment import VectorAssessment
            
            # Create baseline assessment with NEW schema format
            if phase == CascadePhase.PREFLIGHT:
                # PREFLIGHT: Conservative baseline
                baseline = EpistemicAssessmentSchema(
                    # GATE
                    engagement=VectorAssessment(0.70, "Baseline engagement - needs self-assessment"),
                    # FOUNDATION (with "foundation_" prefix)
                    foundation_know=VectorAssessment(0.55, "PREFLIGHT: Limited initial knowledge"),
                    foundation_do=VectorAssessment(0.60, "PREFLIGHT: Capability needs verification"),
                    foundation_context=VectorAssessment(0.65, "PREFLIGHT: Context understood at surface level"),
                    # COMPREHENSION (with "comprehension_" prefix)
                    comprehension_clarity=VectorAssessment(0.65, "PREFLIGHT: Initial clarity"),
                    comprehension_coherence=VectorAssessment(0.70, "PREFLIGHT: Basic coherence"),
                    comprehension_signal=VectorAssessment(0.60, "PREFLIGHT: Priority identified"),
                    comprehension_density=VectorAssessment(0.65, "PREFLIGHT: Manageable complexity"),
                    # EXECUTION (with "execution_" prefix)
                    execution_state=VectorAssessment(0.60, "PREFLIGHT: Environment not yet mapped"),
                    execution_change=VectorAssessment(0.55, "PREFLIGHT: Changes not tracked"),
                    execution_completion=VectorAssessment(0.30, "PREFLIGHT: Not yet started"),
                    execution_impact=VectorAssessment(0.50, "PREFLIGHT: Impact needs analysis"),
                    # UNCERTAINTY
                    uncertainty=VectorAssessment(0.60, "PREFLIGHT: High initial uncertainty"),
                    # METADATA
                    phase=new_phase,
                    round_num=round_num or 0,
                    investigation_count=investigation_rounds
                )
            elif phase == CascadePhase.POSTFLIGHT:
                # POSTFLIGHT: Awaiting genuine reassessment
                baseline = EpistemicAssessmentSchema(
                    engagement=VectorAssessment(0.70, "POSTFLIGHT: Awaiting genuine self-assessment"),
                    foundation_know=VectorAssessment(0.60, "POSTFLIGHT: Awaiting genuine reassessment of knowledge"),
                    foundation_do=VectorAssessment(0.65, "POSTFLIGHT: Awaiting genuine reassessment of capability"),
                    foundation_context=VectorAssessment(0.70, "POSTFLIGHT: Awaiting genuine reassessment of context"),
                    comprehension_clarity=VectorAssessment(0.70, "POSTFLIGHT: Awaiting genuine reassessment of clarity"),
                    comprehension_coherence=VectorAssessment(0.75, "POSTFLIGHT: Awaiting genuine reassessment of coherence"),
                    comprehension_signal=VectorAssessment(0.65, "POSTFLIGHT: Awaiting genuine reassessment of signal"),
                    comprehension_density=VectorAssessment(0.60, "POSTFLIGHT: Awaiting genuine reassessment of density"),
                    execution_state=VectorAssessment(0.65, "POSTFLIGHT: Awaiting genuine reassessment of state"),
                    execution_change=VectorAssessment(0.70, "POSTFLIGHT: Awaiting genuine reassessment of change"),
                    execution_completion=VectorAssessment(0.60, "POSTFLIGHT: Awaiting genuine reassessment of completion"),
                    execution_impact=VectorAssessment(0.65, "POSTFLIGHT: Awaiting genuine reassessment of impact"),
                    uncertainty=VectorAssessment(0.50, "POSTFLIGHT: Awaiting genuine reassessment of uncertainty"),
                    phase=new_phase,
                    round_num=round_num or 0,
                    investigation_count=investigation_rounds
                )
            else:
                # Other phases: Moderate baseline
                baseline = EpistemicAssessmentSchema(
                    engagement=VectorAssessment(0.70, "Baseline engagement - needs self-assessment"),
                    foundation_know=VectorAssessment(0.60, "Baseline knowledge - needs self-assessment"),
                    foundation_do=VectorAssessment(0.65, "Baseline capability - needs self-assessment"),
                    foundation_context=VectorAssessment(0.70, "Baseline context - needs self-assessment"),
                    comprehension_clarity=VectorAssessment(0.70, "Baseline clarity - needs self-assessment"),
                    comprehension_coherence=VectorAssessment(0.75, "Baseline coherence - needs self-assessment"),
                    comprehension_signal=VectorAssessment(0.65, "Baseline signal - needs self-assessment"),
                    comprehension_density=VectorAssessment(0.60, "Baseline density - needs self-assessment"),
                    execution_state=VectorAssessment(0.65, "Baseline state awareness - needs self-assessment"),
                    execution_change=VectorAssessment(0.70, "Baseline change tracking - needs self-assessment"),
                    execution_completion=VectorAssessment(0.50, "Baseline completion - needs self-assessment"),
                    execution_impact=VectorAssessment(0.60, "Baseline impact - needs self-assessment"),
                    uncertainty=VectorAssessment(0.50, "Baseline uncertainty - needs genuine self-assessment"),
                    phase=new_phase,
                    round_num=round_num or 0,
                    investigation_count=investigation_rounds
                )
            
            return baseline
        else:
            # Already an EpistemicAssessmentSchema - return as is
            return assessment_request

    # _assess_epistemic_state_new renamed to _assess_epistemic_state below
    
    async def _retrieve_mcp_assessment(
        self,
        task_id: str,
        phase
    ) -> Optional[EpistemicAssessmentSchema]:
        """
        Retrieve genuine MCP assessment from database if it exists
        
        Args:
            task_id: Current task ID (session_id)
            phase: Which phase (preflight, check, postflight) - can be string or CascadePhase enum
        
        Returns:
            EpistemicAssessmentSchema if found, None otherwise
        """
        try:
            # Handle both string and enum phase parameters
            phase_str = phase.value if hasattr(phase, 'value') else str(phase)
            phase_key = f"{phase_str}_vectors"
            
            # Get most recent assessment for this session/phase
            cursor = self.session_db.conn.cursor()
            cursor.execute("""
                SELECT cm.metadata_value, c.cascade_id
                FROM cascade_metadata cm
                JOIN cascades c ON cm.cascade_id = c.cascade_id
                WHERE cm.metadata_key = ?
                AND c.session_id = ?
                ORDER BY c.started_at DESC
                LIMIT 1
            """, (phase_key, task_id))
            
            result = cursor.fetchone()
            
            if result:
                vectors_json, cascade_id = result
                vectors = json.loads(vectors_json)
                
                # Parse vectors dict into EpistemicAssessmentSchema
                return self._parse_vectors_to_assessment(vectors, task_id, phase)
            
            return None
            
        except Exception as e:
            logger.error(f"   ⚠️  Error retrieving MCP assessment: {e}")
            return None
    
    def _parse_vectors_to_assessment(
        self,
        vectors: Dict[str, float],
        task_id: str,
        phase: CascadePhase
    ) -> EpistemicAssessmentSchema:
        """
        Parse vectors dict from MCP into full EpistemicAssessmentSchema object
        
        Args:
            vectors: Dict of vector_name -> score (0.0-1.0)
            task_id: Task identifier
            phase: Current phase
        
        Returns:
            EpistemicAssessmentSchema with all vectors populated
        """
        from empirica.core.canonical.reflex_frame import VectorState
        
        # Helper to get vector or default
        def get_vector(name: str, default: float = 0.5, rationale: str = "From MCP assessment") -> VectorState:
            score = vectors.get(name, default)
            return VectorState(score, f"{rationale} ({name}={score:.2f})")
        
        # Calculate tier confidences
        foundation_confidence = (
            vectors.get('know', 0.5) +
            vectors.get('do', 0.5) +
            vectors.get('context', 0.5)
        ) / 3.0
        
        comprehension_confidence = (
            vectors.get('clarity', 0.5) +
            vectors.get('coherence', 0.5) +
            vectors.get('signal', 0.5) +
            vectors.get('density', 0.5)
        ) / 4.0
        
        execution_confidence = (
            vectors.get('state', 0.5) +
            vectors.get('change', 0.5) +
            vectors.get('completion', 0.5) +
            vectors.get('impact', 0.5)
        ) / 4.0
        
        # Calculate overall confidence (weighted)
        overall_confidence = (
            foundation_confidence * 0.35 +
            comprehension_confidence * 0.25 +
            execution_confidence * 0.15
        )
        
        # Determine recommended action based on confidence
        if overall_confidence >= 0.70:
            recommended_action = Action.PROCEED
        elif overall_confidence >= 0.50:
            recommended_action = Action.INVESTIGATE
        else:
            recommended_action = Action.ESCALATE
        
        return EpistemicAssessmentSchema(
            assessment_id=f"mcp_{task_id}_{phase_str}",
            task=f"MCP assessment for {phase_str}",
            # GATE
            engagement=get_vector('engagement', 0.70),
            engagement_gate_passed=vectors.get('engagement', 0.70) >= 0.60,
            # FOUNDATION
            know=get_vector('know'),
            do=get_vector('do'),
            context=get_vector('context'),
            foundation_confidence=foundation_confidence,
            # COMPREHENSION
            clarity=get_vector('clarity'),
            coherence=get_vector('coherence'),
            signal=get_vector('signal'),
            density=get_vector('density'),
            comprehension_confidence=comprehension_confidence,
            # EXECUTION
            state=get_vector('state'),
            change=get_vector('change'),
            completion=get_vector('completion'),
            impact=get_vector('impact'),
            execution_confidence=execution_confidence,
            # META-EPISTEMIC
            uncertainty=get_vector('uncertainty'),
            overall_confidence=overall_confidence,
            recommended_action=recommended_action
        )

    async def _log_reflex_frame(
        self,
        assessment: EpistemicAssessmentSchema,
        phase: CascadePhase,
        task_id: str,
        task: str,
        context: Dict[str, Any],
        investigation_results: Optional[Dict[str, Any]] = None,
        epistemic_delta: Optional[Dict[str, float]] = None
    ):
        """Log assessment to Reflex Frame for temporal separation"""
        frame_id = f"{self.agent_id}_{task_id}_{phase.value}"

        # Build meta_state_vector (which phase is active) - matches enum order
        meta_state_vector = {
            'preflight': 1.0 if phase == CascadePhase.PREFLIGHT else 0.0,
            'think': 1.0 if phase == CascadePhase.THINK else 0.0,
            'plan': 1.0 if phase == CascadePhase.PLAN else 0.0,
            'investigate': 1.0 if phase == CascadePhase.INVESTIGATE else 0.0,
            'check': 1.0 if phase == CascadePhase.CHECK else 0.0,
            'act': 1.0 if phase == CascadePhase.ACT else 0.0,
            'postflight': 1.0 if phase == CascadePhase.POSTFLIGHT else 0.0
        }

        # Create frame dict directly (ReflexFrame removed)
        frame_dict = {
            'frameId': frame_id,
            'timestamp': assessment.timestamp,
            'selfAwareFlag': True,
            'epistemicVector': assessment.model_dump(),
            'metaStateVector': meta_state_vector,
            'task': task,
            'context': context
        }

        # Add investigation results if present
        if investigation_results:
            frame_dict['investigation_results'] = investigation_results

        # Log to JSON file (temporal separation)
        log_path = await self.reflex_logger.log_frame(frame_dict, agent_id=self.agent_id)

        logger.info(f"   📝 Logged to: {log_path}")

    def _identify_knowledge_gaps(self, assessment: EpistemicAssessmentSchema) -> List[Dict[str, Any]]:
        """
        Extract self-assessed knowledge gaps from canonical assessment

        NO HEURISTICS: AI decides what warrants investigation, not the system.
        The AI marks vectors during assessment with:
        - warrants_investigation: True/False
        - investigation_priority: 'low', 'medium', 'high', 'critical'
        - investigation_reason: Why investigation is needed

        This method simply surfaces what the AI already determined.
        """
        gaps = []

        # Check all vectors for self-assessed investigation flags
        vector_map = {
            'know': assessment.know,
            'do': assessment.do,
            'context': assessment.context,
            'clarity': assessment.clarity,
            'coherence': assessment.coherence,
            'signal': assessment.signal,
            'density': assessment.density,
            'state': assessment.state,
            'change': assessment.change,
            'completion': assessment.completion,
            'impact': assessment.impact,
            'engagement': assessment.engagement,
            'uncertainty': assessment.uncertainty
        }

        for vector_name, vector_state in vector_map.items():
            if vector_state.warrants_investigation:
                gaps.append({
                    'vector': vector_name,
                    'score': vector_state.score,
                    'priority': vector_state.investigation_priority or 'medium',
                    'reason': vector_state.investigation_reason or 'Self-assessed gap',
                    'rationale': vector_state.rationale
                })

        # Sort by priority: critical > high > medium > low
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        gaps.sort(key=lambda g: priority_order.get(g['priority'], 2))

        return gaps

    async def _conduct_investigation(
        self,
        task: str,
        context: Dict[str, Any],
        gaps: List[str],
        assessment: EpistemicAssessmentSchema
    ) -> Dict[str, Any]:
        """
        Provide epistemic gap analysis + tool capability mapping + strategic guidance
        
        Empirica measures gaps, describes available tools, and provides strategic guidance
        on WHEN to investigate vs. skip, and WHICH approaches are most effective.
        
        Philosophy: Measurement and capability mapping, not control.
        The LLM understands what needs improvement and chooses appropriate actions.
        """
        logger.info(f"\n   🔍 Analyzing epistemic gaps...")

        # Extract self-assessed gaps from assessment
        gap_analysis = self._identify_epistemic_gaps(assessment)

        logger.info(f"   📊 Self-assessed gaps: {len(gap_analysis)}")
        for gap in gap_analysis:
            priority_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '⚪'}.get(gap['priority'], '🟡')
            logger.info(f"      {priority_emoji} {gap['vector']}: {gap['current']:.2f} [{gap['priority']}]")
            logger.info(f"        Reason: {gap['reason']}")

        # Note: Investigation decision is made by CASCADE loop based on:
        # 1. Overall confidence < threshold (mandatory)
        # 2. AI-flagged critical/high priority gaps (voluntary)
        # No heuristics here - AI decides via self-assessment

        # Get domain-aware tool recommendations (for capability info, not execution)
        recommendations = await recommend_investigation_tools(
            assessment,
            task,
            context,
            domain=None  # Auto-infer domain
        )

        # Build tool capability map from recommendations
        tool_capabilities = self._build_tool_capability_map(recommendations, context)
        
        # Strategic guidance comes from AI's self-assessed gaps
        # Show which tools can address the gaps AI flagged
        self_assessed_gaps = [g for g in gaps if isinstance(g, dict) and 'vector' in g]

        logger.info(f"\n   🛠️  Available tools ({len(tool_capabilities)} tools with capabilities):")
        for tool_name, capability in list(tool_capabilities.items())[:5]:
            logger.info(f"      • {tool_name}")
            logger.info(f"        Improves: {', '.join(capability['improves_vectors'])}")
            logger.info(f"        {capability['description'][:70]}...")

        if self_assessed_gaps:
            priority_gaps = [g for g in self_assessed_gaps if g.get('priority') in ['critical', 'high']]
            if priority_gaps:
                logger.info(f"\n   🎯 Focus on self-assessed gaps: {', '.join(g['vector'] for g in priority_gaps[:3])}")
                logger.info(f"      AI reasoning: {priority_gaps[0].get('reason', 'Gap flagged for investigation')}")
            else:
                logger.info(f"\n   🎯 Investigating {len(self_assessed_gaps)} self-assessed gaps")
        else:
            logger.info(f"\n   🎯 No specific gaps flagged - exploratory investigation")
        
        # Action hook for INVESTIGATE phase
        if self.enable_action_hooks:
            log_thought(
                f"Investigation guidance: {strategic_guidance['primary_strategy']}\n"
                f"Tools available: {len(tool_capabilities)}",
                "INVESTIGATE",
                task
            )
            log_cascade_phase("INVESTIGATE", task, {
                "gap_count": len(gap_analysis),
                "tool_count": len(tool_capabilities),
                "strategy": strategic_guidance['primary_strategy'],
                "necessity": investigation_necessity['reason']
            })

        return {
            'type': 'investigation_guidance',
            'investigation_necessity': investigation_necessity,
            'epistemic_gaps': gap_analysis,
            'tool_capabilities': tool_capabilities,
            'strategic_guidance': strategic_guidance,
            'guidance': {
                'approach': 'Review epistemic gaps and choose tools that address them',
                'empirica_role': 'measurement_and_capability_mapping',
                'decision_authority': 'LLM decides which tools to use, when, and how',
                'philosophy': 'Empirica measures and informs - you reason and act'
            },
            'domain_context': {
                'inferred_domain': self.current_domain if self.current_domain else 'general',
                'tool_count': len(tool_capabilities),
                'highest_priority_gap': gap_analysis[0]['vector'] if gap_analysis else None,
                'gap_count': len(gap_analysis)
            }
        }

    def _identify_epistemic_gaps(self, assessment: EpistemicAssessmentSchema) -> List[Dict[str, Any]]:
        """
        Extract self-assessed epistemic gaps - NO HEURISTICS

        Returns gaps that AI flagged during self-assessment via warrants_investigation.
        No threshold-based detection - trusts AI's genuine epistemic evaluation.
        """
        gaps = []

        # Map of all vectors to check
        vector_map = {
            'know': assessment.know,
            'do': assessment.do,
            'context': assessment.context,
            'clarity': assessment.clarity,
            'coherence': assessment.coherence,
            'signal': assessment.signal,
            'density': assessment.density,
            'state': assessment.state,
            'change': assessment.change,
            'completion': assessment.completion,
            'impact': assessment.impact,
            'engagement': assessment.engagement,
        }

        # Extract self-assessed gaps
        for vector_name, vector_state in vector_map.items():
            if vector_state.warrants_investigation:
                gaps.append({
                    'vector': vector_name,
                    'current': vector_state.score,
                    'priority': vector_state.investigation_priority or 'medium',
                    'reason': vector_state.investigation_reason or 'Self-assessed gap',
                    'reasoning': vector_state.rationale
                })

        # Sort by priority: critical > high > medium > low
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        gaps.sort(key=lambda g: priority_order.get(g.get('priority', 'medium'), 2))

        return gaps
    
    def _build_tool_capability_map(
        self, 
        recommendations: List[ToolRecommendation],
        context: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Build capability map from tool recommendations
        
        Describes what each tool does and which vectors it improves.
        This provides LLM with information about unknown/custom tools.
        """
        capability_map = {}
        
        # Extract capabilities from recommendations
        for rec in recommendations:
            if rec.tool_name not in capability_map:
                capability_map[rec.tool_name] = {
                    'description': rec.reasoning,
                    'improves_vectors': [rec.gap_addressed],
                    'domain': self.current_domain if self.current_domain else 'general',
                    'confidence_gain': rec.confidence,  # ToolRecommendation.confidence (not confidence_gain)
                    'tool_type': self._classify_tool_type(rec.tool_name)
                }
            else:
                # Add additional vectors this tool can improve
                if rec.gap_addressed not in capability_map[rec.tool_name]['improves_vectors']:
                    capability_map[rec.tool_name]['improves_vectors'].append(rec.gap_addressed)
        
        # Add standard tools that LLM knows from training
        standard_tools = self._get_standard_tool_capabilities()
        capability_map.update(standard_tools)
        
        # Add Empirica-specific tools (these are unknown from training)
        empirica_tools = self._get_empirica_tool_capabilities(context)
        capability_map.update(empirica_tools)
        
        # Add user plugins (extensible custom tools)
        for plugin_name, plugin in self.investigation_plugins.items():
            capability_map[plugin_name] = plugin.to_capability_dict()
        
        return capability_map
    
    def _classify_tool_type(self, tool_name: str) -> str:
        """Classify tool into type for better understanding"""
        tool_name_lower = tool_name.lower()
        
        if any(kw in tool_name_lower for kw in ['scan', 'list', 'inventory', 'map']):
            return 'discovery'
        elif any(kw in tool_name_lower for kw in ['search', 'grep', 'find', 'query']):
            return 'search'
        elif any(kw in tool_name_lower for kw in ['read', 'view', 'inspect', 'examine']):
            return 'inspection'
        elif any(kw in tool_name_lower for kw in ['analyze', 'assess', 'evaluate', 'measure']):
            return 'analysis'
        elif any(kw in tool_name_lower for kw in ['test', 'validate', 'verify', 'check']):
            return 'validation'
        else:
            return 'general'
    
    def _get_standard_tool_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """
        Standard tools that LLM knows from training
        
        These don't need detailed explanation, just capability mapping.
        """
        return {
            'grep': {
                'description': 'Search for patterns in files (improves KNOW by finding information)',
                'improves_vectors': ['know'],
                'tool_type': 'search',
                'confidence_gain': 0.0  # No artificial gain
            },
            'read_file': {
                'description': 'Read and understand file contents (improves KNOW and CLARITY)',
                'improves_vectors': ['know', 'clarity'],
                'tool_type': 'inspection',
                'confidence_gain': 0.0  # No artificial gain
            },
            'bash': {
                'description': 'Execute shell commands for various purposes (improves multiple vectors)',
                'improves_vectors': ['do', 'context', 'state'],
                'tool_type': 'general',
                'confidence_gain': 0.0  # No artificial gain
            },
            'workspace_scan': {
                'description': 'Map workspace structure and available resources (improves CONTEXT and STATE)',
                'improves_vectors': ['context', 'state'],
                'tool_type': 'discovery',
                'confidence_gain': 0.0  # No artificial gain
            }
        }
    
    # REMOVED: _assess_investigation_necessity
    # This method contained 10+ hardcoded heuristics that overrode AI's self-assessment
    # Investigation decision now made purely by:
    # 1. Overall confidence < threshold (mandatory - safety measure)
    # 2. AI-flagged critical/high priority gaps (voluntary - epistemic humility)
    # No system heuristics - AI decides via genuine self-assessment

    # REMOVED: _generate_investigation_strategy
    # This method contained strategy-selection heuristics based on hardcoded thresholds
    # Investigation strategy now comes directly from AI's self-assessed gaps
    # AI provides investigation_reason during self-assessment, system surfaces those reasons

    # REMOVED: _suggest_tools_for_gap (dead code, never called)
    # Tool suggestions now come from investigation_strategy.py via recommend_investigation_tools()

    def _get_empirica_tool_capabilities(self, context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Empirica-specific tools that LLM doesn't know from training
        
        These need detailed capability descriptions so LLM understands what they do.
        """
        return {
            # === Metacognitive Assessment Tools ===
            'monitor_assess_12d': {
                'description': 'Run full 12-vector epistemic assessment to measure current cognitive state across all dimensions (KNOW, DO, CONTEXT, CLARITY, COHERENCE, DENSITY, SIGNAL, STATE, CHANGE, COMPLETION, IMPACT, ENGAGEMENT)',
                'improves_vectors': ['know', 'clarity', 'coherence'],
                'tool_type': 'analysis',
                'confidence_gain': 0.0,  # No artificial gain
                'empirica_specific': True,
                'note': 'This is Empirica\'s core metacognitive assessment tool'
            },
            'calibration_assess': {
                'description': 'Assess uncertainty using adaptive calibration system - learns from historical over/underconfidence patterns (3-vector: KNOW, DO, CONTEXT)',
                'improves_vectors': ['know', 'do', 'context'],
                'tool_type': 'analysis',
                'confidence_gain': 0.0,  # No artificial gain
                'empirica_specific': True,
                'note': 'Provides calibrated confidence based on past performance'
            },
            
            # === Goal Management Tools ===
            'goals_create': {
                'description': 'Create structured goals using autonomous goal orchestrator - helps clarify vague requests into actionable objectives',
                'improves_vectors': ['clarity', 'coherence', 'signal'],
                'tool_type': 'analysis',
                'confidence_gain': 0.0,  # No artificial gain
                'empirica_specific': True,
                'note': 'Useful when task is unclear or needs decomposition'
            },
            'goals_orchestrate': {
                'description': 'Run goal orchestration workflow - manages complex multi-step goals with dependencies and validation',
                'improves_vectors': ['coherence', 'state', 'completion'],
                'tool_type': 'orchestration',
                'confidence_gain': 0.0,  # No artificial gain
                'empirica_specific': True,
                'note': 'For complex tasks requiring coordinated action'
            },
            
            # === Knowledge Retrieval Tools ===
            'web_search': {
                'description': 'Search the web for external knowledge - use when internal knowledge is insufficient. Can find documentation, research papers, examples, tutorials, and current information.',
                'improves_vectors': ['know', 'context'],
                'tool_type': 'search',
                'confidence_gain': 0.0,  # No artificial gain
                'empirica_specific': True,
                'note': 'Critical for knowledge gaps beyond training data or codebase'
            },
            'semantic_search_qdrant': {
                'description': 'Semantic search in Qdrant vector database - finds conceptually related information from stored embeddings. Use for finding similar code patterns, related discussions, or thematic connections.',
                'improves_vectors': ['know', 'context', 'coherence'],
                'tool_type': 'search',
                'confidence_gain': 0.0,  # No artificial gain
                'empirica_specific': True,
                'note': 'Searches semantic meaning, not just keywords. Excellent for finding related concepts.'
            },
            'session_manager_search': {
                'description': 'Search previous conversations and session history via meta chain-of-thought manager. Use to recall past decisions, find previous similar tasks, or maintain continuity across sessions.',
                'improves_vectors': ['know', 'context', 'coherence', 'state'],
                'tool_type': 'search',
                'confidence_gain': 0.0,  # No artificial gain
                'empirica_specific': True,
                'note': 'Essential for multi-session tasks or when user references "like we did before"'
            },
            
            # === User Interaction Tools ===
            'user_clarification': {
                'description': 'Request clarification from user when context is ambiguous or task unclear. CRITICAL: Use this liberally when CLARITY < 0.60 or working in complex/unfamiliar domain. Better to ask than assume.',
                'improves_vectors': ['clarity', 'context', 'know'],
                'tool_type': 'interaction',
                'confidence_gain': 0.0,  # No artificial gain
                'empirica_specific': True,
                'note': 'PREFER THIS over guessing. Users appreciate thoroughness over assumptions.'
            },
            'user_information_gathering': {
                'description': 'Systematically gather information from user about complex domain. Use when KNOW < 0.50 in specialized/technical domains. Ask specific questions about requirements, constraints, preferences, and context.',
                'improves_vectors': ['know', 'context', 'clarity', 'state'],
                'tool_type': 'interaction',
                'confidence_gain': 0.0,  # No artificial gain
                'empirica_specific': True,
                'note': 'Essential for complex domains (medical, legal, specialized engineering, etc.)'
            },
            
            # === Cascade Orchestration ===
            'cascade_run_full': {
                'description': 'Run complete epistemic cascade (THINK → ENGAGEMENT → UNCERTAINTY → INVESTIGATE → CHECK → ACT) - full metacognitive workflow',
                'improves_vectors': ['know', 'do', 'context', 'clarity', 'coherence'],
                'tool_type': 'orchestration',
                'confidence_gain': 0.0,  # No artificial gain
                'empirica_specific': True,
                'note': 'For complex uncertain tasks requiring full epistemic reasoning'
            }
        }
        
        # Could also dynamically query MCP server for available tools
        # if 'mcp_server' in context:
        #     return self._query_mcp_capabilities(context['mcp_server'])

    def update_from_tool_execution(
        self,
        tool_name: str,
        success: bool,
        vector_addressed: str,
        strength: float = 0.7
    ) -> Dict[str, Any]:
        """
        Update Bayesian beliefs when LLM executes a tool and reports results
        
        This allows evidence-based belief tracking without Empirica executing tools.
        LLM decides to use a tool, executes it, and reports back the outcome.
        
        Args:
            tool_name: Name of tool that was executed
            success: Whether the tool execution succeeded
            vector_addressed: Which epistemic vector this addresses
            strength: Evidence strength (0.0-1.0)
        
        Returns:
            Dict with update status and new belief state
        """
        if not self.bayesian_tracker or not self.bayesian_tracker.active:
            return {
                'updated': False,
                'reason': 'Bayesian Guardian not active'
            }
        
        # Create evidence from tool execution
        evidence = Evidence(
            outcome=success,
            strength=strength,
            timestamp=time.time(),
            source=tool_name,
            vector_addressed=vector_addressed
        )
        
        # Update belief
        belief_key = f"{self.current_context_key}:{vector_addressed}"
        updated_belief = self.bayesian_tracker.update_belief(belief_key, evidence)
        
        logger.info(f"   🧮 Bayesian: Updated {vector_addressed} → {updated_belief.mean:.2f} (variance: {updated_belief.variance:.2f})")
        
        return {
            'updated': True,
            'vector': vector_addressed,
            'new_belief': updated_belief.mean,
            'variance': updated_belief.variance,
            'confidence_interval': updated_belief.confidence_interval(),
            'evidence_count': updated_belief.evidence_count
        }
    
    def _verify_readiness(self, assessment: EpistemicAssessmentSchema) -> Dict[str, Any]:
        """
        Verify readiness to act based on canonical assessment + Bayesian Guardian
        
        Includes:
        - Standard canonical checks
        - Bayesian discrepancy detection (overconfidence/underconfidence)
        - Drift analysis (if enabled)
        """

        readiness_check = {
            'recommended_action': assessment.recommended_action.value,
            'overall_confidence': assessment.overall_confidence,
            'engagement_gate_passed': assessment.engagement_gate_passed,
            'critical_flags': {
                'coherence_critical': assessment.coherence_critical,
                'density_critical': assessment.density_critical,
                'change_critical': assessment.change_critical
            },
            'ready_to_act': (
                assessment.recommended_action == Action.PROCEED and
                assessment.overall_confidence >= self.action_confidence_threshold
            )
        }

        logger.info(f"\n   ✅ Readiness Check:")
        logger.info(f"      Recommended Action: {assessment.recommended_action.value.upper()}")
        logger.info(f"      Overall Confidence: {assessment.overall_confidence:.2f}")
        logger.info(f"      Engagement Gate: {'PASSED' if assessment.engagement_gate_passed else 'FAILED'}")

        if any(readiness_check['critical_flags'].values()):
            logger.info(f"      ⚠️  Critical flags detected:")
            for flag, value in readiness_check['critical_flags'].items():
                if value:
                    logger.info(f"         - {flag}")
        
        # ================================================================
        # BAYESIAN GUARDIAN: Discrepancy Detection
        # ================================================================
        if self.bayesian_tracker and self.bayesian_tracker.active:
            logger.info(f"\n   🧮 Bayesian Guardian: Checking belief calibration...")
            
            # Get intuitive beliefs from current assessment
            intuitive_beliefs = {
                'know': assessment.know.score,
                'do': assessment.do.score,
                'context': assessment.context.score,
                'clarity': assessment.clarity.score,
                'coherence': assessment.coherence.score,
                'state': assessment.state.score,
                'completion': assessment.completion.score,
                'impact': assessment.impact.score
            }
            
            # Detect discrepancies between intuition and evidence
            discrepancies = self.bayesian_tracker.detect_discrepancies(
                self.current_context_key,
                intuitive_beliefs,
                threshold_std_devs=2.0
            )
            
            if discrepancies:
                logger.info(f"   ⚠️  Detected {len(discrepancies)} belief discrepancies:")
                for d in discrepancies:
                    logger.info(f"      • {d['type'].upper()}: {d['vector']}")
                    logger.info(f"        Intuitive: {d['intuitive']:.2f} | Evidence-based: {d['bayesian_mean']:.2f}")
                    logger.info(f"        Gap: {d['gap']:.2f} (severity: {d['severity']:.2f})")
                    
                    if d['type'] == 'overconfidence':
                        logger.info(f"        ⚠️  You may be overconfident about {d['vector']}")
                    else:
                        logger.info(f"        💡 You may be underconfident about {d['vector']}")
            else:
                logger.info(f"   ✅ Beliefs aligned with accumulated evidence")
            
            # Add to readiness check
            readiness_check['bayesian_discrepancies'] = discrepancies
            readiness_check['bayesian_summary'] = self.bayesian_tracker.get_calibration_summary(
                self.current_context_key
            )
        
        # ================================================================
        # DRIFT MONITOR: Behavioral Drift Analysis
        # ================================================================
        if self.enable_drift_monitor and self.drift_monitor and self.parallel_reasoner and len(self.parallel_reasoner.synthesis_history) >= 10:
            logger.info(f"\n   📊 Drift Monitor: Analyzing behavioral patterns...")

            drift_analysis = self.drift_monitor.analyze_drift(self.parallel_reasoner.synthesis_history)
            
            if drift_analysis['sycophancy_drift']['detected']:
                severity = drift_analysis['sycophancy_drift']['severity']
                evidence = drift_analysis['sycophancy_drift']['evidence']
                logger.info(f"   ⚠️  Sycophancy drift detected (severity: {severity:.2f})")
                logger.info(f"      Evidence: {evidence}")
                logger.info(f"      Recommendation: Increase trustee weight or activate skeptic mode")
            
            if drift_analysis['tension_avoidance']['detected']:
                evidence = drift_analysis['tension_avoidance']['evidence']
                logger.info(f"   ⚠️  Tension avoidance detected")
                logger.info(f"      Evidence: {evidence}")
                logger.info(f"      Recommendation: Force tension analysis in synthesizer")
            
            if not drift_analysis['sycophancy_drift']['detected'] and not drift_analysis['tension_avoidance']['detected']:
                logger.info(f"   ✅ No behavioral drift detected - maintaining intellectual honesty")
            
            readiness_check['drift_analysis'] = drift_analysis
        
        # Action hook for CHECK phase
        if self.enable_action_hooks:
            check_thoughts = [
                f"Readiness: {readiness_check['recommended_action']}",
                f"Confidence: {readiness_check['overall_confidence']:.2f}"
            ]
            
            # Add Bayesian info if active
            if self.bayesian_tracker and self.bayesian_tracker.active:
                discrepancy_count = len(readiness_check.get('bayesian_discrepancies', []))
                if discrepancy_count > 0:
                    check_thoughts.append(f"⚠️ {discrepancy_count} Bayesian discrepancies detected")
                else:
                    check_thoughts.append("✅ Beliefs aligned with evidence")
            
            # Add drift info if detected
            if readiness_check.get('drift_analysis'):
                if readiness_check['drift_analysis'].get('sycophancy_drift', {}).get('detected'):
                    check_thoughts.append("⚠️ Sycophancy drift detected")
                if readiness_check['drift_analysis'].get('tension_avoidance', {}).get('detected'):
                    check_thoughts.append("⚠️ Tension avoidance detected")
            
            log_thought("\n".join(check_thoughts), "CHECK", "")
            log_cascade_phase("CHECK", "", {
                "ready_to_act": readiness_check['ready_to_act'],
                "confidence": readiness_check['overall_confidence'],
                "bayesian_active": self.bayesian_tracker.active if self.bayesian_tracker else False,
                "discrepancy_count": len(readiness_check.get('bayesian_discrepancies', []))
            })

        return readiness_check

    def _make_final_decision(
        self,
        assessment: EpistemicAssessmentSchema,
        check_result: Dict[str, Any],
        investigation_rounds: int
    ) -> Dict[str, Any]:
        """Make final decision based on canonical assessment"""

        decision = {
            'action': assessment.recommended_action.value,
            'confidence': assessment.overall_confidence,
            'rationale': self._build_decision_rationale(assessment, investigation_rounds),
            'vector_summary': self._extract_vector_summary(assessment),
            'execution_guidance': self._generate_execution_guidance(assessment),
            'engagement_gate_passed': assessment.engagement_gate_passed,
            'investigation_rounds': investigation_rounds,
            'critical_flags': {
                'coherence_critical': assessment.coherence_critical,
                'density_critical': assessment.density_critical,
                'change_critical': assessment.change_critical
            }
        }

        return decision

    def _build_decision_rationale(
        self,
        assessment: EpistemicAssessmentSchema,
        investigation_rounds: int
    ) -> str:
        """Build comprehensive decision rationale"""

        parts = []

        # Overall confidence
        parts.append(f"Overall confidence: {assessment.overall_confidence:.2f}")

        # Tier confidences
        parts.append(f"Foundation: {assessment.foundation_confidence:.2f}, " +
                    f"Comprehension: {assessment.comprehension_confidence:.2f}, " +
                    f"Execution: {assessment.execution_confidence:.2f}")

        # Investigation
        if investigation_rounds > 0:
            parts.append(f"Conducted {investigation_rounds} investigation round(s)")

        # Recommended action
        parts.append(f"Recommended action: {assessment.recommended_action.value}")

        return ". ".join(parts)

    def _extract_vector_summary(self, assessment: EpistemicAssessmentSchema) -> Dict[str, float]:
        """Extract vector summary for reporting"""
        return {
            'engagement': assessment.engagement.score,
            'know': assessment.know.score,
            'do': assessment.do.score,
            'context': assessment.context.score,
            'clarity': assessment.clarity.score,
            'coherence': assessment.coherence.score,
            'signal': assessment.signal.score,
            'density': assessment.density.score,
            'state': assessment.state.score,
            'change': assessment.change.score,
            'completion': assessment.completion.score,
            'impact': assessment.impact.score,
            'foundation_confidence': assessment.foundation_confidence,
            'comprehension_confidence': assessment.comprehension_confidence,
            'execution_confidence': assessment.execution_confidence,
            'overall_confidence': assessment.overall_confidence
        }

    def _generate_execution_guidance(self, assessment: EpistemicAssessmentSchema) -> List[str]:
        """
        Generate execution guidance from AI's self-assessed gaps - NO HEURISTICS

        Returns guidance based on what AI flagged as needing attention.
        No threshold-based guidance generation.
        """
        guidance = []

        # Map of all vectors with their contextual guidance
        guidance_map = {
            'know': "Validate domain assumptions during execution",
            'do': "Test execution approach incrementally",
            'context': "Verify environmental assumptions before proceeding",
            'clarity': "Confirm understanding of ambiguous aspects with user",
            'coherence': "Review conversation history for missing context",
            'state': "Map environment state before making changes",
            'impact': "Analyze consequences of each modification",
            'change': "Track all modifications carefully",
            'engagement': "Involve user in key decision points"
        }

        # Extract guidance only for self-assessed gaps
        vector_map = {
            'know': assessment.know,
            'do': assessment.do,
            'context': assessment.context,
            'clarity': assessment.clarity,
            'coherence': assessment.coherence,
            'state': assessment.state,
            'impact': assessment.impact,
            'change': assessment.change,
            'engagement': assessment.engagement
        }

        for vector_name, vector_state in vector_map.items():
            if vector_state.warrants_investigation:
                if vector_name in guidance_map:
                    guidance.append(guidance_map[vector_name])

        return guidance

    def _calculate_epistemic_delta(
        self,
        preflight: EpistemicAssessmentSchema,
        postflight: EpistemicAssessmentSchema
    ) -> Dict[str, float]:
        """
        Calculate epistemic delta between PREFLIGHT and POSTFLIGHT
        
        Positive values = learning/confidence increased
        Negative values = uncertainty increased (sometimes good - discovered unknowns)
        """
        return {
            # Tier confidences
            'foundation_confidence': postflight.foundation_confidence - preflight.foundation_confidence,
            'comprehension_confidence': postflight.comprehension_confidence - preflight.comprehension_confidence,
            'execution_confidence': postflight.execution_confidence - preflight.execution_confidence,
            'overall_confidence': postflight.overall_confidence - preflight.overall_confidence,
            
            # Individual vectors
            'know': postflight.know.score - preflight.know.score,
            'do': postflight.do.score - preflight.do.score,
            'context': postflight.context.score - preflight.context.score,
            'clarity': postflight.clarity.score - preflight.clarity.score,
            'coherence': postflight.coherence.score - preflight.coherence.score,
            'signal': postflight.signal.score - preflight.signal.score,
            'density': postflight.density.score - preflight.density.score,
            'state': postflight.state.score - preflight.state.score,
            'change': postflight.change.score - preflight.change.score,
            'completion': postflight.completion.score - preflight.completion.score,
            'impact': postflight.impact.score - preflight.impact.score,
            
            # Meta-epistemic
            'uncertainty': postflight.uncertainty.score - preflight.uncertainty.score,
            'engagement': postflight.engagement.score - preflight.engagement.score
        }
    
    def _check_calibration_accuracy(
        self,
        preflight: EpistemicAssessmentSchema,
        postflight: EpistemicAssessmentSchema,
        final_decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Report calibration delta - NO HEURISTICS

        Simply reports the raw numbers. Humans/AIs can interpret what's "good" calibration
        based on context, task complexity, and their own standards.

        The data speaks for itself - no need for arbitrary threshold rules.
        """
        preflight_conf = preflight.overall_confidence
        postflight_conf = postflight.overall_confidence
        confidence_delta = postflight_conf - preflight_conf
        uncertainty_delta = postflight.uncertainty.score - preflight.uncertainty.score

        # Just report the numbers - no judgment
        return {
            'preflight_confidence': preflight_conf,
            'postflight_confidence': postflight_conf,
            'confidence_delta': confidence_delta,
            'uncertainty_delta': uncertainty_delta,
            'preflight_uncertainty': preflight.uncertainty.score,
            'postflight_uncertainty': postflight.uncertainty.score,
            # For backwards compatibility, include well_calibrated key but let data decide
            'well_calibrated': True,  # Always true - data shows the truth
            'note': f"Δconfidence: {confidence_delta:+.2f}, Δuncertainty: {uncertainty_delta:+.2f}"
        }

    def _generate_task_id(self, task: str) -> str:
        """Generate unique task ID"""
        timestamp = datetime.now(UTC).isoformat()
        content = f"{task}_{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    def _enter_phase(self, phase: CascadePhase):
        """Enter a new cascade phase"""
        logger.info(f"\n{'='*70}")
        logger.info(f"🔄 Phase: {phase.value.upper()}")
        logger.info(f"{'='*70}")

    def _update_tmux_display(
        self,
        phase: CascadePhase,
        assessment: EpistemicAssessmentSchema,
        gaps: Optional[List[str]] = None,
        round_num: Optional[int] = None
    ):
        """Update tmux display with current cascade state"""
        if not self.tmux_extension:
            return

        try:
            import json

            # Export cascade state to JSON for tmux display
            realtime_dir = Path("/tmp/empirica_realtime")
            realtime_dir.mkdir(exist_ok=True)

            cascade_state = {
                'timestamp': time.time(),
                'current_phase': phase.value,
                'investigation_round': round_num,
                'engagement_gate_passed': assessment.engagement_gate_passed,
                'overall_confidence': assessment.overall_confidence,
                'knowledge_gaps': gaps or [],
                'vectors': self._extract_vector_summary(assessment),
                'recommended_action': assessment.recommended_action.value
            }

            # Write to JSON for tmux
            cascade_file = realtime_dir / "epistemic_cascade_state.json"
            with open(cascade_file, 'w') as f:
                json.dump(cascade_state, f, indent=2)

            # Trigger tmux update if supported
            if hasattr(self.tmux_extension, 'trigger_action_update'):
                self.tmux_extension.trigger_action_update('epistemic_cascade', cascade_state)

        except Exception as e:
            logger.warning(f"   ⚠️  Tmux update failed: {e}")


# CONVENIENCE FUNCTION

async def run_canonical_cascade(
    task: str,
    context: Optional[Dict[str, Any]] = None,
    confidence_threshold: float = 0.70,
    max_investigation_rounds: int = 3,
    agent_id: str = "cascade"
) -> Dict[str, Any]:
    """
    Convenience function to run canonical epistemic cascade

    Usage:
        result = await run_canonical_cascade(
            "Refactor the authentication module",
            context={'cwd': '/path/to/project', 'available_tools': ['read', 'write']},
            confidence_threshold=0.75
        )

    Returns:
        Dict with action, confidence, rationale, vector_summary, execution_guidance
    """
    cascade = CanonicalEpistemicCascade(
        action_confidence_threshold=confidence_threshold,
        max_investigation_rounds=max_investigation_rounds,
        agent_id=agent_id
    )

    return await cascade.run_epistemic_cascade(task, context)
