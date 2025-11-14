#!/usr/bin/env python3
"""
Comprehensive 12-Vector AI Self-Awareness System
A deterministic, model-agnostic framework for self-assessment.
"""

import time
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import os
import logging

# Import centralized thresholds
from empirica.core.thresholds import (
    UNCERTAINTY_LOW, UNCERTAINTY_MODERATE,
    COMPREHENSION_HIGH, COMPREHENSION_MODERATE,
    EXECUTION_HIGH, EXECUTION_MODERATE,
    DENSITY_OVERLOAD,
    CLARITY_THRESHOLD, SIGNAL_THRESHOLD, COHERENCE_THRESHOLD,
    STATE_MAPPING_THRESHOLD, COMPLETION_THRESHOLD, IMPACT_THRESHOLD
)

logger = logging.getLogger(__name__)

class MetacognitiveAction(Enum):
    """Actions based on metacognitive assessment"""
    ACT = "act"                    # Execute confidently
    INVESTIGATE = "investigate"    # Learn more about task  
    CLARIFY = "clarify"           # Confirm understanding
    MAP_STATE = "map_state"       # Scan environment first
    VERIFY_COMPLETION = "verify_completion"  # Check if actually finished
    PREDICT_IMPACT = "predict_impact"       # Analyze consequences
    SUGGEST_RESET = "suggest_reset"         # Context overload
    STOP = "stop"                 # Too many unknowns

@dataclass
class VectorAssessment:
    """Individual vector assessment result"""
    name: str
    value: float  # 0.0 to 1.0
    confidence: float  # How confident we are in this assessment
    description: str
    thresholds: Dict[str, float] = field(default_factory=dict)
    
    @property
    def color(self) -> str:
        """UVL color based on value and vector type"""
        if self.name.lower() == 'density':
            # Density is inverted - higher is worse
            if self.value > 0.8: return '🔴'
            elif self.value > 0.5: return '🟡' 
            else: return '🟢'
        else:
            # Standard vectors - higher is better
            if self.value > 0.7: return '🟢'
            elif self.value > 0.3: return '🟡'
            else: return '🔴'

@dataclass 
class EpistemicUncertainty:
    """Dimension 1: Can I do this? (3 vectors)"""
    know: VectorAssessment      # Epistemic boundaries
    do: VectorAssessment        # Procedural capability  
    context: VectorAssessment   # Environmental validity
    
    @property
    def overall_confidence(self) -> float:
        """Overall uncertainty confidence"""
        return (self.know.value + self.do.value + self.context.value) / 3
    
    @property
    def min_confidence(self) -> float:
        """Weakest link in uncertainty chain"""
        return min(self.know.value, self.do.value, self.context.value)

@dataclass
class EpistemicComprehension:
    """Dimension 2: Do I understand the request? (4 vectors)"""
    clarity: VectorAssessment     # Semantic understanding
    coherence: VectorAssessment   # Conversation context fit
    density: VectorAssessment     # Cognitive overload (inverted)
    signal: VectorAssessment      # Priority identification
    
    @property
    def overall_comprehension(self) -> float:
        """Overall comprehension score"""
        # Density is inverted, so we use (1 - density) for average
        return (self.clarity.value + self.coherence.value + 
                (1 - self.density.value) + self.signal.value) / 4
    
    @property
    def comprehension_issues(self) -> List[str]:
        """List of comprehension issues detected"""
        issues = []
        if self.clarity.value < 0.5:
            issues.append("unclear_request")
        if self.coherence.value < 0.5:
            issues.append("context_incoherent")
        if self.density.value > 0.9:
            issues.append("cognitive_overload")
        if self.signal.value < 0.5:
            issues.append("unclear_priority")
        return issues

@dataclass
class ExecutionAwareness:
    """Dimension 3: Am I doing this right? (4 vectors)"""
    state: VectorAssessment       # Environment mapping
    change: VectorAssessment      # Modification tracking
    completion: VectorAssessment  # Task completion verification
    impact: VectorAssessment      # Consequence prediction
    
    @property
    def execution_readiness(self) -> float:
        """Overall execution readiness"""
        return (self.state.value + self.change.value + 
                self.completion.value + self.impact.value) / 4
    
    @property
    def execution_risks(self) -> List[str]:
        """List of execution risks detected"""
        risks = []
        if self.state.value < 0.6:
            risks.append("incomplete_state_mapping")
        if self.change.value < 0.7:
            risks.append("poor_change_tracking")
        if self.completion.value < 0.8:
            risks.append("premature_completion")
        if self.impact.value < 0.5:
            risks.append("unknown_consequences")
        return risks

@dataclass
class SelfAwarenessResult:
    """Complete 11-vector self-awareness assessment result"""
    # Three dimensions
    uncertainty: EpistemicUncertainty
    comprehension: EpistemicComprehension  
    execution: ExecutionAwareness
    
    # Metadata
    assessment_id: str
    timestamp: float = field(default_factory=time.time)
    
    # Decision result
    recommended_action: MetacognitiveAction = MetacognitiveAction.INVESTIGATE
    decision_rationale: str = ""
    confidence_in_decision: float = 0.5
    
    # Context
    task_description: str = ""
    context_provided: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def all_vectors(self) -> Dict[str, VectorAssessment]:
        """All 11 vectors as dictionary"""
        return {
            # Epistemic Uncertainty (3)
            'know': self.uncertainty.know,
            'do': self.uncertainty.do, 
            'context': self.uncertainty.context,
            # Epistemic Comprehension (4)
            'clarity': self.comprehension.clarity,
            'coherence': self.comprehension.coherence,
            'density': self.comprehension.density,
            'signal': self.comprehension.signal,
            # Execution Awareness (4)
            'state': self.execution.state,
            'change': self.execution.change,
            'completion': self.execution.completion,
            'impact': self.execution.impact
        }
    
    @property
    def vector_summary(self) -> str:
        """Compact vector summary for logging"""
        vectors = self.all_vectors
        summary_parts = []
        for name, vector in vectors.items():
            summary_parts.append(f"{name.upper()}:{vector.value:.2f}")
        return " | ".join(summary_parts)
    
    @property
    def critical_issues(self) -> List[str]:
        """All critical issues across dimensions"""
        issues = []
        
        # Uncertainty issues
        if self.uncertainty.min_confidence < 0.3:
            issues.append("high_uncertainty")
            
        # Comprehension issues  
        issues.extend(self.comprehension.comprehension_issues)
        
        # Execution issues
        issues.extend(self.execution.execution_risks)
        
        return issues

class MetacognitiveDecisionMatrix:
    """
    Implements the decision matrix from the comprehensive specification
    Determines actions based on 11-vector assessment patterns
    """
    
    def __init__(self):
        # Decision thresholds from centralized configuration
        self.thresholds = {
            'uncertainty_low': UNCERTAINTY_LOW,
            'uncertainty_moderate': UNCERTAINTY_MODERATE,
            'comprehension_high': COMPREHENSION_HIGH,
            'comprehension_moderate': COMPREHENSION_MODERATE,
            'execution_high': EXECUTION_HIGH,
            'execution_moderate': EXECUTION_MODERATE,
            'density_overload': DENSITY_OVERLOAD,
            'clarity_threshold': CLARITY_THRESHOLD,
            'signal_threshold': SIGNAL_THRESHOLD,
            'coherence_threshold': COHERENCE_THRESHOLD,
            'state_mapping_threshold': STATE_MAPPING_THRESHOLD,
            'completion_threshold': COMPLETION_THRESHOLD,
            'impact_threshold': IMPACT_THRESHOLD
        }
    
    def assess_action(self, result: SelfAwarenessResult) -> Tuple[MetacognitiveAction, str, float]:
        """
        Core decision matrix logic from specification
        Returns: (action, rationale, confidence_in_decision)
        """
        # STEP 1: Check comprehension first (highest priority)
        comprehension_action = self._check_comprehension_issues(result)
        if comprehension_action:
            return comprehension_action
        
        # STEP 2: Check uncertainty levels
        uncertainty_action = self._check_uncertainty_levels(result)
        if uncertainty_action:
            return uncertainty_action
        
        # STEP 3: Check execution awareness
        execution_action = self._check_execution_readiness(result)
        if execution_action:
            return execution_action
        
        # STEP 4: All clear - proceed with confidence
        return (MetacognitiveAction.ACT, 
                "All vectors within acceptable ranges - proceed with execution",
                0.9)
    
    def _check_comprehension_issues(self, result: SelfAwarenessResult) -> Optional[Tuple[MetacognitiveAction, str, float]]:
        """Check for comprehension-blocking issues"""
        comp = result.comprehension
        
        # Critical comprehension failures
        if comp.clarity.value < self.thresholds['clarity_threshold']:
            return (MetacognitiveAction.CLARIFY,
                    f"Request unclear (clarity: {comp.clarity.value:.2f}) - need clarification",
                    0.9)
        
        if comp.signal.value < self.thresholds['signal_threshold']:
            return (MetacognitiveAction.CLARIFY,
                    f"Cannot identify priority (signal: {comp.signal.value:.2f}) - need clarification",
                    0.9)
        
        if comp.coherence.value < self.thresholds['coherence_threshold']:
            return (MetacognitiveAction.CLARIFY,
                    f"Context incoherent (coherence: {comp.coherence.value:.2f}) - need clarification",
                    0.8)
        
        if comp.density.value > self.thresholds['density_overload']:
            return (MetacognitiveAction.SUGGEST_RESET,
                    f"Cognitive overload detected (density: {comp.density.value:.2f}) - suggest context reset",
                    0.9)
        
        return None
    
    def _check_uncertainty_levels(self, result: SelfAwarenessResult) -> Optional[Tuple[MetacognitiveAction, str, float]]:
        """Check uncertainty levels and determine investigation needs"""
        unc = result.uncertainty
        
        # High uncertainty in any core vector
        critical_uncertainties = []
        if unc.know.value < self.thresholds['uncertainty_moderate']:
            critical_uncertainties.append(f"KNOW:{unc.know.value:.2f}")
        if unc.do.value < self.thresholds['uncertainty_moderate']:
            critical_uncertainties.append(f"DO:{unc.do.value:.2f}")
        if unc.context.value < self.thresholds['uncertainty_moderate']:
            critical_uncertainties.append(f"CONTEXT:{unc.context.value:.2f}")
        
        if critical_uncertainties:
            return (MetacognitiveAction.INVESTIGATE,
                    f"High uncertainty detected: {', '.join(critical_uncertainties)} - need investigation",
                    0.8)
        
        # Moderate uncertainty - proceed with caution
        moderate_uncertainties = []
        if unc.know.value < self.thresholds['uncertainty_low']:
            moderate_uncertainties.append(f"KNOW:{unc.know.value:.2f}")
        if unc.do.value < self.thresholds['uncertainty_low']:
            moderate_uncertainties.append(f"DO:{unc.do.value:.2f}")
        if unc.context.value < self.thresholds['uncertainty_low']:
            moderate_uncertainties.append(f"CONTEXT:{unc.context.value:.2f}")
        
        if moderate_uncertainties:
            return (MetacognitiveAction.INVESTIGATE,
                    f"Moderate uncertainty: {', '.join(moderate_uncertainties)} - investigate before acting",
                    0.7)
        
        return None
    
    def _check_execution_readiness(self, result: SelfAwarenessResult) -> Optional[Tuple[MetacognitiveAction, str, float]]:
        """Check execution awareness and readiness"""
        exec_aware = result.execution
        
        # Critical execution issues
        if exec_aware.state.value < self.thresholds['state_mapping_threshold']:
            return (MetacognitiveAction.MAP_STATE,
                    f"Insufficient state mapping (state: {exec_aware.state.value:.2f}) - map environment first",
                    0.9)
        
        if exec_aware.completion.value < self.thresholds['completion_threshold']:
            return (MetacognitiveAction.VERIFY_COMPLETION,
                    f"Task may be incomplete (completion: {exec_aware.completion.value:.2f}) - verify completion",
                    0.8)
        
        if exec_aware.impact.value < self.thresholds['impact_threshold']:
            return (MetacognitiveAction.PREDICT_IMPACT,
                    f"Unknown consequences (impact: {exec_aware.impact.value:.2f}) - analyze impact first",
                    0.8)
        
        return None
    
    def get_pattern_analysis(self, result: SelfAwarenessResult) -> Dict[str, Any]:
        """Analyze patterns across vectors for insights"""
        patterns = {}
        
        # Pattern 1: Confident Misunderstanding
        if (result.uncertainty.overall_confidence > 0.7 and 
            result.comprehension.overall_comprehension < 0.6):
            patterns['confident_misunderstanding'] = {
                'detected': True,
                'risk': 'Will confidently solve wrong problem',
                'recommendation': 'CLARIFY before acting'
            }
        
        # Pattern 2: Informed Hesitation  
        if (result.uncertainty.overall_confidence < 0.5 and
            result.comprehension.overall_comprehension > 0.8):
            patterns['informed_hesitation'] = {
                'detected': True,
                'assessment': 'Knows what it doesn\'t know',
                'recommendation': 'INVESTIGATE to build capability'
            }
        
        # Pattern 3: Execution Blindness
        if (result.uncertainty.overall_confidence > 0.7 and
            result.comprehension.overall_comprehension > 0.8 and
            result.execution.state.value < 0.6):
            patterns['execution_blindness'] = {
                'detected': True,
                'risk': 'Will make changes without understanding current state',
                'recommendation': 'MAP STATE before modifying'
            }
        
        # Pattern 4: Incomplete Success
        if (result.uncertainty.overall_confidence > 0.7 and
            result.comprehension.overall_comprehension > 0.8 and
            result.execution.completion.value < 0.8):
            patterns['incomplete_success'] = {
                'detected': True,
                'risk': 'Will declare success prematurely',
                'recommendation': 'VERIFY COMPLETION before reporting done'
            }
        
        return patterns


class ComprehensiveSelfAwarenessAssessment:
    """
    Main assessment engine for 13-vector AI self-awareness.

    Supports two modes:
    - 'llm': Uses AI's own reasoning for self-assessment (recommended)
    - 'heuristic': Uses deterministic heuristics (fallback)
    """

    def __init__(self, agent_id: str = "default", mode: str = "llm"):
        self.agent_id = agent_id
        self.mode = mode  # 'llm' or 'heuristic'
        self.decision_matrix = MetacognitiveDecisionMatrix()
        self.assessment_history = []
        
        # Set LLM available to True - the AI calling this IS the LLM
        # This component provides self-assessment capabilities to the AI itself
        self.llm_available = True

        self.weights = {
            'know': {'domain_familiarity': 0.25, 'information_recency': 0.25, 'coverage_completeness': 0.25, 'retrieval_confidence': 0.25},
            'do': {'tool_availability': 0.25, 'method_confidence': 0.25, 'historical_success': 0.25, 'complexity_assessment': 0.25},
            'context': {'workspace_validity': 0.25, 'information_currency': 0.25, 'assumption_verification': 0.25, 'dependency_availability': 0.25},
            'clarity': {'ambiguous_refs': 0.25, 'term_precision': 0.25, 'shared_context': 0.25, 'interpretation_certainty': 0.25},
            'coherence': {'topic_alignment': 0.25, 'context_consistency': 0.25, 'logical_flow': 0.25, 'definitional_stability': 0.25},
            'density': {'message_count': 0.25, 'concept_tracking': 0.25, 'nesting_depth': 0.25, 'cognitive_load': 0.25},
            'signal': {'priority_clarity': 0.25, 'noise_filtering': 0.25, 'intent_identification': 0.25, 'goal_alignment': 0.25},
            'state': {'inventory_completeness': 0.25, 'dependency_mapping': 0.25, 'execution_flow': 0.25, 'redundancy_detection': 0.25},
            'change': {'modification_tracking': 0.25, 'side_effect_awareness': 0.25, 'change_documentation': 0.25, 'rollback_capability': 0.25},
            'completion': {'task_coverage': 0.33, 'quality_verification': 0.33, 'requirement_satisfaction': 0.34},
            'impact': {'consequence_prediction': 0.33, 'risk_assessment': 0.33, 'dependency_impact': 0.34}
        }

    def assess(self, task: str, context: Dict[str, Any] = None) -> Union[SelfAwarenessResult, Dict[str, Any]]:
        """
        Performs self-assessment using LLM reasoning or heuristics.

        Returns:
            - SelfAwarenessResult if assessment completed (heuristic or parsed LLM)
            - Dict with meta-prompt if LLM mode but requires external execution
        """
        if context is None:
            context = {}

        assessment_id = self._generate_assessment_id(task)

        # Choose assessment method based on mode
        if self.mode == 'llm':
            return self._assess_with_llm(task, context, assessment_id)
        else:
            return self._assess_with_heuristics(task, context, assessment_id)

    def _assess_with_heuristics(self, task: str, context: Dict[str, Any], assessment_id: str) -> SelfAwarenessResult:
        """Heuristic-based assessment (original implementation)"""

        # 1. Calculate all vectors using internal heuristics
        uncertainty = self._build_epistemic_uncertainty(task, context)
        comprehension = self._build_epistemic_comprehension(task, context)
        execution = self._build_execution_awareness(task, context)

        # 2. Assemble the result object
        result = SelfAwarenessResult(
            uncertainty=uncertainty,
            comprehension=comprehension,
            execution=execution,
            assessment_id=assessment_id,
            task_description=task,
            context_provided=context
        )

        # 3. Apply the decision matrix to the deterministic result
        action, rationale, confidence = self.decision_matrix.assess_action(result)
        result.recommended_action = action
        result.decision_rationale = rationale
        result.confidence_in_decision = confidence

        self.assessment_history.append(result)
        return result

    def _build_epistemic_uncertainty(self, task: str, context: Dict[str, Any]) -> EpistemicUncertainty:
        """Build EpistemicUncertainty dimension from individual vector assessments"""
        know_score = self._assess_know_vector(task, context)
        do_score = self._assess_do_vector(task, context)
        context_score = self._assess_context_vector(task, context)

        return EpistemicUncertainty(
            know=VectorAssessment(
                name="know",
                value=know_score,
                confidence=0.7,
                description=self._describe_know_assessment(know_score, task)
            ),
            do=VectorAssessment(
                name="do",
                value=do_score,
                confidence=0.7,
                description=self._describe_do_assessment(do_score, task)
            ),
            context=VectorAssessment(
                name="context",
                value=context_score,
                confidence=0.7,
                description=self._describe_context_assessment(context_score, task)
            )
        )

    def _build_epistemic_comprehension(self, task: str, context: Dict[str, Any]) -> EpistemicComprehension:
        """Build EpistemicComprehension dimension from individual vector assessments"""
        clarity_score = self._assess_clarity_vector(task, context)
        coherence_score = self._assess_coherence_vector(task, context)
        density_score = self._assess_density_vector(task, context)
        signal_score = self._assess_signal_vector(task, context)

        return EpistemicComprehension(
            clarity=VectorAssessment(
                name="clarity",
                value=clarity_score,
                confidence=0.7,
                description=self._describe_clarity_assessment(clarity_score, task)
            ),
            coherence=VectorAssessment(
                name="coherence",
                value=coherence_score,
                confidence=0.7,
                description=self._describe_coherence_assessment(coherence_score, task)
            ),
            density=VectorAssessment(
                name="density",
                value=density_score,
                confidence=0.7,
                description=self._describe_density_assessment(density_score, task)
            ),
            signal=VectorAssessment(
                name="signal",
                value=signal_score,
                confidence=0.7,
                description=self._describe_signal_assessment(signal_score, task)
            )
        )

    def _build_execution_awareness(self, task: str, context: Dict[str, Any]) -> ExecutionAwareness:
        """Build ExecutionAwareness dimension from individual vector assessments"""
        state_score = self._assess_state_vector(task, context)
        change_score = self._assess_change_vector(task, context)
        completion_score = self._assess_completion_vector(task, context)
        impact_score = self._assess_impact_vector(task, context)

        return ExecutionAwareness(
            state=VectorAssessment(
                name="state",
                value=state_score,
                confidence=0.7,
                description=self._describe_state_assessment(state_score, task)
            ),
            change=VectorAssessment(
                name="change",
                value=change_score,
                confidence=0.7,
                description=self._describe_change_assessment(change_score, task)
            ),
            completion=VectorAssessment(
                name="completion",
                value=completion_score,
                confidence=0.7,
                description=self._describe_completion_assessment(completion_score, task)
            ),
            impact=VectorAssessment(
                name="impact",
                value=impact_score,
                confidence=0.7,
                description=self._describe_impact_assessment(impact_score, task)
            )
        )

    def _assess_with_llm(self, task: str, context: Dict[str, Any], assessment_id: str) -> Union[SelfAwarenessResult, Dict[str, Any]]:
        """
        LLM-powered assessment using AI's own reasoning.

        Returns meta-prompt for external execution (the LLM calling this will see the prompt
        and can execute it as part of its own reasoning).
        """

        # Build the meta-prompt asking the AI to assess itself
        meta_prompt = self._build_meta_prompt(task, context)

        # Return meta-prompt for external execution
        # When an LLM calls this function, it will see this prompt and can reason through it
        return {
            'requires_llm_reasoning': True,
            'assessment_id': assessment_id,
            'meta_prompt': meta_prompt,
            'task': task,
            'context': context,
            'instructions': 'Please analyze the meta_prompt and provide your self-assessment as structured JSON matching the format specified in the prompt.'
        }

    # ========================================
    # EPISTEMIC UNCERTAINTY VECTOR METHODS
    # ========================================
    
    def _assess_know_vector(self, task: str, context: Dict[str, Any]) -> float:
        """
        Assess KNOW vector - epistemic boundaries
        Returns: 0.0-1.0 where higher = more confident in knowledge
        """
        # Extract domain from task
        domain = self._extract_domain(task)
        
        # 1. Domain familiarity (0.0-1.0)
        domain_familiarity = self._assess_domain_familiarity(domain)
        
        # 2. Information recency (0.0-1.0) 
        info_recency = self._assess_information_recency(domain, context)
        
        # 3. Coverage completeness (0.0-1.0)
        coverage = self._assess_knowledge_coverage(task, context)
        
        # 4. Retrieval confidence (0.0-1.0)
        retrieval_conf = self._assess_retrieval_confidence(task)
        
        # Weighted combination
        know_score = (
            domain_familiarity * self.weights['know']['domain_familiarity'] +
            info_recency * self.weights['know']['information_recency'] +
            coverage * self.weights['know']['coverage_completeness'] +
            retrieval_conf * self.weights['know']['retrieval_confidence']
        )
        
        return max(0.0, min(1.0, know_score))
    
    def _assess_do_vector(self, task: str, context: Dict[str, Any]) -> float:
        """
        Assess DO vector - procedural capability  
        Returns: 0.0-1.0 where higher = more confident in execution
        """
        # 1. Tool availability (0.0-1.0)
        tool_availability = self._assess_tool_availability(task, context)
        
        # 2. Method confidence (0.0-1.0)
        method_confidence = self._assess_method_confidence(task)
        
        # 3. Historical success rate (0.0-1.0)
        historical_success = self._assess_historical_success(task)
        
        # 4. Complexity assessment (0.0-1.0)
        complexity_score = self._assess_complexity_handling(task)
        
        # Weighted combination
        do_score = (
            tool_availability * self.weights['do']['tool_availability'] +
            method_confidence * self.weights['do']['method_confidence'] +
            historical_success * self.weights['do']['historical_success'] +
            complexity_score * self.weights['do']['complexity_assessment']
        )
        
        return max(0.0, min(1.0, do_score))
    
    def _assess_context_vector(self, task: str, context: Dict[str, Any]) -> float:
        """
        Assess CONTEXT vector - environmental validity
        Returns: 0.0-1.0 where higher = more confident in environment
        """
        # 1. Workspace validity (0.0-1.0)
        workspace_validity = self._assess_workspace_validity(context)
        
        # 2. Information currency (0.0-1.0)
        info_currency = self._assess_information_currency(context)
        
        # 3. Assumption verification (0.0-1.0)
        assumption_verification = self._assess_assumption_verification(task, context)
        
        # 4. Dependency availability (0.0-1.0)
        dependency_availability = self._assess_dependency_availability(context)
        
        # Weighted combination
        context_score = (
            workspace_validity * self.weights['context']['workspace_validity'] +
            info_currency * self.weights['context']['information_currency'] +
            assumption_verification * self.weights['context']['assumption_verification'] +
            dependency_availability * self.weights['context']['dependency_availability']
        )
        
        return max(0.0, min(1.0, context_score))
    
    # ========================================
    # EPISTEMIC COMPREHENSION VECTOR METHODS  
    # ========================================
    
    def _assess_clarity_vector(self, task: str, context: Dict[str, Any]) -> float:
        """
        Assess CLARITY vector - semantic understanding
        Returns: 0.0-1.0 where higher = clearer understanding
        """
        # 1. Count ambiguous references
        ambiguous_refs = self._count_ambiguous_references(task)
        ambiguity_penalty = min(ambiguous_refs * 0.15, 0.6)
        
        # 2. Term precision assessment
        vague_terms = self._count_vague_terms(task)
        precision_score = max(0.0, 1.0 - (vague_terms * 0.1))
        
        # 3. Shared context verification
        context_score = self._verify_shared_context(task, context)
        
        # 4. Interpretation confidence
        interpretation_conf = self._assess_interpretation_confidence(task, context)
        
        # Weighted combination
        clarity_score = (
            (1.0 - ambiguity_penalty) * self.weights['clarity']['ambiguous_refs'] +
            precision_score * self.weights['clarity']['term_precision'] +
            context_score * self.weights['clarity']['shared_context'] +
            interpretation_conf * self.weights['clarity']['interpretation_certainty']
        )
        
        return max(0.0, min(1.0, clarity_score))
    
    def _assess_coherence_vector(self, task: str, context: Dict[str, Any]) -> float:
        """
        Assess COHERENCE vector - conversation context fit
        Returns: 0.0-1.0 where higher = more coherent with context
        """
        conversation_context = context.get('conversation_history', [])
        
        # 1. Topic alignment with previous messages
        topic_alignment = self._assess_topic_alignment(task, conversation_context)
        
        # 2. Context consistency (no contradictions)
        context_consistency = self._assess_context_consistency(task, conversation_context)
        
        # 3. Logical flow from previous interactions
        logical_flow = self._assess_logical_flow(task, conversation_context)
        
        # 4. Definitional stability (terms mean same things)
        definitional_stability = self._assess_definitional_stability(task, conversation_context)
        
        # Weighted combination
        coherence_score = (
            topic_alignment * self.weights['coherence']['topic_alignment'] +
            context_consistency * self.weights['coherence']['context_consistency'] +
            logical_flow * self.weights['coherence']['logical_flow'] +
            definitional_stability * self.weights['coherence']['definitional_stability']
        )
        
        return max(0.0, min(1.0, coherence_score))
    
    def _assess_density_vector(self, task: str, context: Dict[str, Any]) -> float:
        """
        Assess DENSITY vector - cognitive overload (inverted - higher is worse)
        Returns: 0.0-1.0 where higher = more cognitive load
        """
        conversation_context = context.get('conversation_history', [])
        
        # 1. Message count vs cognitive capacity
        message_count = len(conversation_context)
        message_load = min(message_count / 50.0, 1.0)  # 50 messages = full load
        
        # 2. Concept tracking burden
        concepts_tracked = self._count_tracked_concepts(conversation_context)
        concept_load = min(concepts_tracked / 20.0, 1.0)  # 20 concepts = full load
        
        # 3. Nesting depth of discussion
        nesting_depth = self._assess_discussion_nesting(conversation_context)
        nesting_load = min(nesting_depth / 5.0, 1.0)  # 5 levels = full load
        
        # 4. General cognitive load assessment
        cognitive_load = self._assess_general_cognitive_load(task, context)
        
        # Weighted combination
        density_score = (
            message_load * self.weights['density']['message_count'] +
            concept_load * self.weights['density']['concept_tracking'] +
            nesting_load * self.weights['density']['nesting_depth'] +
            cognitive_load * self.weights['density']['cognitive_load']
        )
        
        return max(0.0, min(1.0, density_score))
    
    def _assess_signal_vector(self, task: str, context: Dict[str, Any]) -> float:
        """
        Assess SIGNAL vector - priority identification
        Returns: 0.0-1.0 where higher = clearer signal
        """
        # 1. Priority clarity in request
        priority_clarity = self._assess_priority_clarity(task)
        
        # 2. Noise filtering (competing priorities)
        noise_level = self._assess_noise_level(task, context)
        noise_filter_score = 1.0 - noise_level
        
        # 3. Intent identification confidence
        intent_confidence = self._assess_intent_identification(task, context)
        
        # Weighted combination  
        signal_score = (
            priority_clarity * self.weights['signal']['priority_clarity'] +
            noise_filter_score * self.weights['signal']['noise_filtering'] +
            intent_confidence * self.weights['signal']['intent_identification']
        )
        
        return max(0.0, min(1.0, signal_score))


    # ========================================
    # EXECUTION AWARENESS VECTOR METHODS
    # ========================================
    
    # ========================================
    # REAL WORKSPACE DATA GATHERING
    # ========================================
    
    def _gather_real_workspace_state(self) -> Dict[str, Any]:
        """Gather REAL workspace state data from actual filesystem"""
        import os
        import glob
        
        workspace_state = {}
        
        try:
            # Count actual files in current workspace
            cwd = os.getcwd()
            all_files = []
            
            # Scan for Python, JavaScript, and common source files
            for pattern in ['**/*.py', '**/*.js', '**/*.ts', '**/*.java', '**/*.cpp', '**/*.md']:
                all_files.extend(glob.glob(os.path.join(cwd, pattern), recursive=True))
            
            # Limit depth to avoid massive scans
            scanned_files = [f for f in all_files if f.count(os.sep) - cwd.count(os.sep) <= 3]
            
            workspace_state['scanned_files'] = scanned_files[:100]  # Limit to 100 files
            
            # Check if we're in a git repo
            if os.path.exists(os.path.join(cwd, '.git')):
                workspace_state['is_git_repo'] = True
            
        except Exception as e:
            # Fallback to minimal state if scanning fails
            workspace_state = {'scanned_files': [], 'scan_error': str(e)}
        
        return workspace_state
    
    def _gather_real_change_tracking(self) -> Dict[str, Any]:
        """Gather REAL change tracking data from git"""
        import subprocess
        import os
        
        change_tracking = {}
        
        try:
            cwd = os.getcwd()
            
            # Check if we're in a git repo
            if os.path.exists(os.path.join(cwd, '.git')):
                # Get git status - check for uncommitted changes
                result = subprocess.run(
                    ['git', 'status', '--porcelain'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    # Parse git status output
                    tracked_changes = result.stdout.strip().split('\n')
                    change_tracking['tracked_changes'] = tracked_changes
                    change_tracking['has_uncommitted_changes'] = True
                else:
                    change_tracking['tracked_changes'] = []
                    change_tracking['has_uncommitted_changes'] = False
                
                # Get recent commit count
                result = subprocess.run(
                    ['git', 'rev-list', '--count', 'HEAD'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                if result.returncode == 0:
                    change_tracking['commit_count'] = int(result.stdout.strip())
                    
        except Exception as e:
            # Fallback if git not available
            change_tracking = {'tracked_changes': [], 'git_error': str(e)}
        
        return change_tracking
    
    def _gather_real_completion_state(self, task: str) -> Dict[str, Any]:
        """Estimate REAL completion state based on task and workspace"""
        completion_state = {}
        
        try:
            # Estimate completion based on task keywords
            task_lower = task.lower()
            
            # Simple heuristics for completion estimation
            action_words = ['create', 'build', 'implement', 'fix', 'add', 'update', 'test']
            verification_words = ['verify', 'check', 'validate', 'test', 'review']
            
            # If task mentions verification, we're further along
            if any(word in task_lower for word in verification_words):
                completion_state['completed_steps'] = [1, 2, 3]  # Implementation done, verifying
                completion_state['total_steps'] = 4
            elif any(word in task_lower for word in action_words):
                completion_state['completed_steps'] = [1]  # Just starting implementation
                completion_state['total_steps'] = 4
            else:
                completion_state['completed_steps'] = []  # Planning/analysis phase
                completion_state['total_steps'] = 4
            
            # Check if we have actual quality checks (tests)
            import os
            if os.path.exists('tests') or os.path.exists('test'):
                completion_state['quality_checks'] = ['tests_exist']
            
        except Exception as e:
            completion_state = {'completed_steps': [], 'total_steps': 4, 'error': str(e)}
        
        return completion_state
    
    def _assess_state_vector(self, task: str, context: Dict[str, Any]) -> float:
        """
        Assess STATE vector - environment mapping before modification
        Returns: 0.0-1.0 where higher = more thoroughly mapped
        """
        workspace_state = context.get('workspace_state', {})
        
        # INJECT REAL WORKSPACE DATA if empty
        if not workspace_state:
            workspace_state = self._gather_real_workspace_state()
        
        # 1. Inventory completeness (files, functions, dependencies)
        inventory_completeness = self._assess_inventory_completeness(task, workspace_state)
        
        # 2. Dependency mapping completeness
        dependency_completeness = self._assess_dependency_mapping(task, workspace_state)
        
        # 3. Execution flow understanding
        flow_completeness = self._assess_execution_flow_mapping(task, workspace_state)
        
        # 4. Redundancy detection completeness
        redundancy_completeness = self._assess_redundancy_detection(workspace_state)
        
        # Weighted combination
        state_score = (
            inventory_completeness * self.weights['state']['inventory_completeness'] +
            dependency_completeness * self.weights['state']['dependency_mapping'] +
            flow_completeness * self.weights['state']['execution_flows'] +
            redundancy_completeness * self.weights['state']['redundancy_detection']
        )
        
        return max(0.0, min(1.0, state_score))
    
    def _assess_change_vector(self, task: str, context: Dict[str, Any]) -> float:
        """
        Assess CHANGE vector - modification tracking
        Returns: 0.0-1.0 where higher = better change tracking
        """
        change_tracking = context.get('change_tracking', {})
        
        # INJECT REAL CHANGE TRACKING if empty
        if not change_tracking:
            change_tracking = self._gather_real_change_tracking()
        
        # 1. Modification tracking capability
        modification_tracking = self._assess_modification_tracking(task, change_tracking)
        
        # 2. Side effect awareness
        side_effect_awareness = self._assess_side_effect_awareness(task, context)
        
        # 3. Change documentation completeness
        change_documentation = self._assess_change_documentation(change_tracking)
        
        # Weighted combination
        change_score = (
            modification_tracking * self.weights['change']['modification_tracking'] +
            side_effect_awareness * self.weights['change']['side_effect_awareness'] +
            change_documentation * self.weights['change']['change_documentation']
        )
        
        return max(0.0, min(1.0, change_score))
    
    def _assess_completion_vector(self, task: str, context: Dict[str, Any]) -> float:
        """
        Assess COMPLETION vector - task completion verification
        Returns: 0.0-1.0 where higher = more complete
        """
        completion_state = context.get('completion_state', {})
        
        # INJECT REAL COMPLETION TRACKING if empty
        if not completion_state:
            completion_state = self._gather_real_completion_state(task)
        
        # 1. Task coverage assessment
        task_coverage = self._assess_task_coverage(task, completion_state)
        
        # 2. Quality verification
        quality_verification = self._assess_quality_verification(task, completion_state)
        
        # 3. Requirement satisfaction
        requirement_satisfaction = self._assess_requirement_satisfaction(task, completion_state)
        
        # Weighted combination
        completion_score = (
            task_coverage * self.weights['completion']['task_coverage'] +
            quality_verification * self.weights['completion']['quality_verification'] +
            requirement_satisfaction * self.weights['completion']['requirement_satisfaction']
        )
        
        return max(0.0, min(1.0, completion_score))
    
    def _assess_impact_vector(self, task: str, context: Dict[str, Any]) -> float:
        """
        Assess IMPACT vector - consequence prediction
        Returns: 0.0-1.0 where higher = better impact understanding
        """
        # 1. Consequence prediction capability
        consequence_prediction = self._assess_consequence_prediction(task, context)
        
        # 2. Risk assessment completeness
        risk_assessment = self._assess_risk_assessment(task, context)
        
        # 3. Dependency impact analysis
        dependency_impact = self._assess_dependency_impact(task, context)
        
        # Weighted combination
        impact_score = (
            consequence_prediction * self.weights['impact']['consequence_prediction'] +
            risk_assessment * self.weights['impact']['risk_assessment'] +
            dependency_impact * self.weights['impact']['dependency_impact']
        )
        
        return max(0.0, min(1.0, impact_score))
    
    # ========================================
    # HELPER METHODS FOR VECTOR CALCULATIONS
    # ========================================
    
    def _extract_domain(self, task: str) -> str:
        """Extract domain from task description"""
        task_lower = task.lower()
        
        # Programming domains
        if any(word in task_lower for word in ['code', 'program', 'function', 'class', 'debug']):
            return 'programming'
        elif any(word in task_lower for word in ['deploy', 'server', 'database', 'api']):
            return 'infrastructure'
        elif any(word in task_lower for word in ['test', 'verify', 'validate', 'check']):
            return 'testing'
        elif any(word in task_lower for word in ['design', 'architecture', 'plan']):
            return 'design'
        elif any(word in task_lower for word in ['analyze', 'research', 'investigate']):
            return 'analysis'
        else:
            return 'general'
    
    def _assess_domain_familiarity(self, domain: str) -> float:
        """Assess familiarity with domain (0.0-1.0)"""
        # Base familiarity scores (can be calibrated)
        familiarity_scores = {
            'programming': 0.8,
            'analysis': 0.9, 
            'design': 0.7,
            'testing': 0.8,
            'infrastructure': 0.6,
            'general': 0.7
        }
        return familiarity_scores.get(domain, 0.5)
    
    def _assess_information_recency(self, domain: str, context: Dict[str, Any]) -> float:
        """Assess how recent our domain knowledge is"""
        # Simple heuristic - can be enhanced with actual timestamp tracking
        context_age = context.get('context_age_seconds', 0)
        
        if context_age < 3600:  # < 1 hour
            return 0.9
        elif context_age < 86400:  # < 1 day
            return 0.7
        elif context_age < 604800:  # < 1 week
            return 0.5
        else:
            return 0.3
    
    def _assess_knowledge_coverage(self, task: str, context: Dict[str, Any]) -> float:
        """Assess coverage of knowledge needed for task"""
        available_info = context.get('available_info', [])
        
        # Estimate knowledge coverage based on available information
        if len(available_info) >= 3:
            return 0.8
        elif len(available_info) >= 1:
            return 0.6
        else:
            return 0.4
    
    def _assess_retrieval_confidence(self, task: str) -> float:
        """Assess confidence in retrieving needed knowledge"""
        # Simple heuristic based on task complexity
        complex_indicators = ['experimental', 'novel', 'research', 'unknown', 'first time']
        if any(indicator in task.lower() for indicator in complex_indicators):
            return 0.5
        else:
            return 0.8
    
    def _assess_tool_availability(self, task: str, context: Dict[str, Any]) -> float:
        """Assess availability of tools needed"""
        tools_available = context.get('tools_available', [])
        
        if len(tools_available) >= 3:
            return 0.9
        elif len(tools_available) >= 1:
            return 0.7
        else:
            return 0.4
    
    def _assess_method_confidence(self, task: str) -> float:
        """Assess confidence in method/approach"""
        # Multiple approaches available vs single approach
        if 'multiple ways' in task.lower() or 'several approaches' in task.lower():
            return 0.6  # Uncertainty in which approach
        else:
            return 0.8  # Single clear approach
    
    def _assess_historical_success(self, task: str) -> float:
        """Assess historical success rate for similar tasks"""
        # Simple heuristic - can be enhanced with actual history tracking
        execution_history = getattr(self, 'execution_history', {})
        domain = self._extract_domain(task)
        
        if domain in execution_history:
            return execution_history[domain].get('success_rate', 0.7)
        else:
            return 0.7  # Default moderate confidence
    
    def _assess_complexity_handling(self, task: str) -> float:
        """Assess ability to handle task complexity"""
        complexity_indicators = ['complex', 'advanced', 'sophisticated', 'multi-step', 'integration']
        
        if any(indicator in task.lower() for indicator in complexity_indicators):
            return 0.6  # Moderate confidence for complex tasks
        else:
            return 0.8  # High confidence for simple tasks

    
    # ========================================
    # COMPREHENSION HELPER METHODS
    # ========================================
    
    def _count_ambiguous_references(self, task: str) -> int:
        """Count ambiguous pronouns and references"""
        ambiguous_words = ['it', 'this', 'that', 'them', 'they', 'those', 'these']
        return sum(1 for word in task.lower().split() if word in ambiguous_words)
    
    def _count_vague_terms(self, task: str) -> int:
        """Count vague or imprecise terms"""
        vague_words = ['thing', 'stuff', 'something', 'somehow', 'kinda', 'sorta']
        return sum(1 for word in task.lower().split() if word in vague_words)
    
    def _verify_shared_context(self, task: str, context: Dict[str, Any]) -> float:
        """Verify shared understanding of context"""
        conversation_history = context.get('conversation_history', [])
        
        if len(conversation_history) > 5:
            return 0.8  # Established context
        elif len(conversation_history) > 0:
            return 0.6  # Some context
        else:
            return 0.4  # No shared context
    
    def _assess_interpretation_confidence(self, task: str, context: Dict[str, Any]) -> float:
        """Assess confidence in task interpretation"""
        # Multiple possible interpretations reduce confidence
        question_words = ['what', 'how', 'why', 'which', 'when', 'where']
        question_count = sum(1 for word in task.lower() for word in question_words if word in task.lower().split())
        
        if question_count > 2:
            return 0.5  # Multiple questions = ambiguous
        elif question_count == 1:
            return 0.8  # Single clear question
        else:
            return 0.7  # Statement form
    
    def _assess_topic_alignment(self, task: str, conversation_history: List) -> float:
        """Assess alignment with conversation topic"""
        if not conversation_history:
            return 0.8  # No history to conflict with
        
        # Simple heuristic - can be enhanced with semantic analysis
        recent_topics = [msg.get('topic', '') for msg in conversation_history[-3:]]
        current_topic = self._extract_domain(task)
        
        if current_topic in recent_topics:
            return 0.9  # Topic consistency
        else:
            return 0.6  # Topic shift
    
    def _assess_context_consistency(self, task: str, conversation_history: List) -> float:
        """Check for contradictions with previous context"""
        # Simple implementation - can be enhanced
        if not conversation_history:
            return 0.9
        
        # Look for contradiction indicators
        contradiction_words = ['but', 'however', 'instead', 'actually', 'no wait']
        if any(word in task.lower() for word in contradiction_words):
            return 0.4  # Potential contradiction
        else:
            return 0.8  # No obvious contradictions
    
    def _assess_logical_flow(self, task: str, conversation_history: List) -> float:
        """Assess logical flow from previous interactions"""
        if not conversation_history:
            return 0.8
        
        # Simple flow assessment
        flow_indicators = ['next', 'then', 'now', 'following', 'after']
        if any(word in task.lower() for word in flow_indicators):
            return 0.9  # Clear flow
        else:
            return 0.7  # Neutral flow
    
    def _assess_definitional_stability(self, task: str, conversation_history: List) -> float:
        """Check if terms maintain consistent meaning"""
        # Simple implementation
        return 0.8  # Default assumption of stable definitions
    
    def _count_tracked_concepts(self, conversation_history: List) -> int:
        """Count concepts being tracked across conversation"""
        # Simple implementation - can be enhanced
        return min(len(conversation_history) * 2, 20)  # Estimate 2 concepts per message
    
    def _assess_discussion_nesting(self, conversation_history: List) -> int:
        """Assess nesting depth of discussion topics"""
        # Simple implementation
        return min(len(conversation_history) // 5, 5)  # Every 5 messages = 1 nesting level
    
    def _assess_general_cognitive_load(self, task: str, context: Dict[str, Any]) -> float:
        """Assess general cognitive load"""
        # Factors that increase cognitive load
        load_factors = 0.0
        
        if len(task) > 200:  # Long request
            load_factors += 0.2
        
        if context.get('multi_step', False):  # Multi-step task
            load_factors += 0.3
            
        if context.get('integration_required', False):  # Integration needed
            load_factors += 0.2
        
        return min(load_factors, 1.0)
    
    def _assess_priority_clarity(self, task: str) -> float:
        """Assess clarity of priorities in request"""
        priority_indicators = ['priority', 'important', 'urgent', 'first', 'main', 'primary']
        
        if any(indicator in task.lower() for indicator in priority_indicators):
            return 0.8  # Clear priority signals
        else:
            return 0.5  # No clear priority
    
    def _assess_noise_level(self, task: str, context: Dict[str, Any]) -> float:
        """Assess noise/competing priorities"""
        # Multiple requests or conflicting goals
        request_count = task.count('?') + task.count(',') + task.count('and')
        
        if request_count > 3:
            return 0.7  # High noise
        elif request_count > 1:
            return 0.4  # Moderate noise
        else:
            return 0.1  # Low noise
    
    def _assess_intent_identification(self, task: str, context: Dict[str, Any]) -> float:
        """Assess confidence in identifying intent"""
        # Clear action words indicate clear intent
        action_words = ['create', 'build', 'analyze', 'fix', 'update', 'implement', 'test']
        
        if any(word in task.lower() for word in action_words):
            return 0.8  # Clear intent
        else:
            return 0.5  # Unclear intent


    # ========================================
    # EXECUTION AWARENESS HELPER METHODS
    # ========================================
    
    def _assess_workspace_validity(self, context: Dict[str, Any]) -> float:
        """Assess workspace state validity"""
        workspace_state = context.get('workspace_state', {})
        
        validity_score = 0.5  # Default
        
        if workspace_state.get('is_clean', False):
            validity_score += 0.2
        if workspace_state.get('has_errors', False):
            validity_score -= 0.3
        if workspace_state.get('dependencies_checked', False):
            validity_score += 0.2
        
        return max(0.0, min(1.0, validity_score))
    
    def _assess_information_currency(self, context: Dict[str, Any]) -> float:
        """Assess currency of context information"""
        context_age = context.get('context_age_seconds', 3600)
        
        if context_age < 300:  # < 5 minutes
            return 0.9
        elif context_age < 3600:  # < 1 hour
            return 0.7
        elif context_age < 86400:  # < 1 day
            return 0.5
        else:
            return 0.2
    
    def _assess_assumption_verification(self, task: str, context: Dict[str, Any]) -> float:
        """Assess verification of assumptions"""
        assumptions = context.get('assumptions', [])
        verified_assumptions = context.get('verified_assumptions', [])
        
        if not assumptions:
            return 0.8  # No assumptions to verify
        
        verification_ratio = len(verified_assumptions) / len(assumptions)
        return verification_ratio
    
    def _assess_dependency_availability(self, context: Dict[str, Any]) -> float:
        """Assess availability of external dependencies"""
        dependencies = context.get('dependencies', [])
        available_dependencies = context.get('available_dependencies', [])
        
        if not dependencies:
            return 0.9  # No dependencies needed
        
        availability_ratio = len(available_dependencies) / len(dependencies)
        return availability_ratio
    
    def _assess_inventory_completeness(self, task: str, workspace_state: Dict[str, Any]) -> float:
        """Assess completeness of workspace inventory"""
        scanned_files = workspace_state.get('scanned_files', [])
        
        # Estimate based on task complexity
        if 'simple' in task.lower():
            required_files = 2
        elif 'complex' in task.lower():
            required_files = 10
        else:
            required_files = 5
        
        completeness = min(len(scanned_files) / required_files, 1.0)
        return completeness
    
    def _assess_dependency_mapping(self, task: str, workspace_state: Dict[str, Any]) -> float:
        """Assess dependency mapping completeness"""
        dependency_graph = workspace_state.get('dependency_graph', {})
        
        if dependency_graph:
            return 0.8  # Has dependency information
        else:
            return 0.3  # No dependency mapping
    
    def _assess_execution_flow_mapping(self, task: str, workspace_state: Dict[str, Any]) -> float:
        """Assess execution flow understanding"""
        traced_flows = workspace_state.get('traced_flows', [])
        
        if len(traced_flows) > 0:
            return 0.8
        else:
            return 0.4
    
    def _assess_redundancy_detection(self, workspace_state: Dict[str, Any]) -> float:
        """Assess redundancy detection completeness"""
        redundancy_scan = workspace_state.get('redundancy_scan_complete', False)
        
        if redundancy_scan:
            return 1.0
        else:
            return 0.5
    
    def _assess_modification_tracking(self, task: str, change_tracking: Dict[str, Any]) -> float:
        """Assess modification tracking capability"""
        tracked_changes = change_tracking.get('tracked_changes', [])
        
        if len(tracked_changes) > 0:
            return 0.8
        else:
            return 0.4
    
    def _assess_side_effect_awareness(self, task: str, context: Dict[str, Any]) -> float:
        """Assess awareness of side effects"""
        # Tasks with higher side effect risk
        high_risk_words = ['delete', 'remove', 'modify', 'change', 'update', 'replace']
        
        if any(word in task.lower() for word in high_risk_words):
            side_effect_analysis = context.get('side_effect_analysis', {})
            if side_effect_analysis:
                return 0.8
            else:
                return 0.3  # High risk, no analysis
        else:
            return 0.7  # Low risk task
    
    def _assess_change_documentation(self, change_tracking: Dict[str, Any]) -> float:
        """Assess change documentation completeness"""
        documentation = change_tracking.get('change_documentation', [])
        
        if len(documentation) > 0:
            return 0.8
        else:
            return 0.4
    
    def _assess_task_coverage(self, task: str, completion_state: Dict[str, Any]) -> float:
        """Assess task coverage completeness"""
        completed_steps = completion_state.get('completed_steps', [])
        total_steps = completion_state.get('total_steps', 1)
        
        if total_steps > 0:
            return len(completed_steps) / total_steps
        else:
            return 0.5
    
    def _assess_quality_verification(self, task: str, completion_state: Dict[str, Any]) -> float:
        """Assess quality verification"""
        quality_checks = completion_state.get('quality_checks', [])
        
        if len(quality_checks) > 0:
            return 0.8
        else:
            return 0.4
    
    def _assess_requirement_satisfaction(self, task: str, completion_state: Dict[str, Any]) -> float:
        """Assess requirement satisfaction"""
        satisfied_requirements = completion_state.get('satisfied_requirements', [])
        total_requirements = completion_state.get('total_requirements', 1)
        
        if total_requirements > 0:
            return len(satisfied_requirements) / total_requirements
        else:
            return 0.5
    
    def _assess_consequence_prediction(self, task: str, context: Dict[str, Any]) -> float:
        """Assess consequence prediction capability"""
        impact_analysis = context.get('impact_analysis', {})
        
        if impact_analysis:
            return 0.8
        else:
            # High-impact tasks need better prediction
            high_impact_words = ['deploy', 'production', 'delete', 'remove', 'system']
            if any(word in task.lower() for word in high_impact_words):
                return 0.3  # High impact, no analysis
            else:
                return 0.6  # Low impact task
    
    def _assess_risk_assessment(self, task: str, context: Dict[str, Any]) -> float:
        """Assess risk assessment completeness"""
        risk_analysis = context.get('risk_analysis', {})
        
        if risk_analysis:
            return 0.8
        else:
            return 0.4
    
    def _assess_dependency_impact(self, task: str, context: Dict[str, Any]) -> float:
        """Assess dependency impact analysis"""
        dependency_impact = context.get('dependency_impact', {})
        
        if dependency_impact:
            return 0.8
        else:
            return 0.5


    # ========================================
    # VECTOR DESCRIPTION METHODS
    # ========================================
    
    def _describe_know_assessment(self, score: float, task: str) -> str:
        """Generate description for KNOW vector assessment"""
        domain = self._extract_domain(task)
        
        if score > 0.8:
            return f"High knowledge confidence in {domain} domain"
        elif score > 0.6:
            return f"Good knowledge of {domain}, some gaps possible"
        elif score > 0.4:
            return f"Moderate {domain} knowledge, verification recommended"
        else:
            return f"Limited {domain} knowledge, research needed"
    
    def _describe_do_assessment(self, score: float, task: str) -> str:
        """Generate description for DO vector assessment"""
        if score > 0.8:
            return "High execution confidence, tools and methods available"
        elif score > 0.6:
            return "Good execution capability, proceed with monitoring"
        elif score > 0.4:
            return "Moderate execution confidence, validate approach"
        else:
            return "Low execution confidence, investigate methods"
    
    def _describe_context_assessment(self, score: float, task: str) -> str:
        """Generate description for CONTEXT vector assessment"""
        if score > 0.8:
            return "Environment well validated and current"
        elif score > 0.6:
            return "Context mostly validated, minor updates needed"
        elif score > 0.4:
            return "Context partially validated, verify before acting"
        else:
            return "Context validity uncertain, validate environment"
    
    def _describe_clarity_assessment(self, score: float, task: str) -> str:
        """Generate description for CLARITY vector assessment"""
        if score > 0.8:
            return "Request semantically clear and unambiguous"
        elif score > 0.6:
            return "Request mostly clear, minor ambiguities"
        elif score > 0.4:
            return "Request somewhat unclear, clarification helpful"
        else:
            return "Request unclear, clarification needed"
    
    def _describe_coherence_assessment(self, score: float, task: str) -> str:
        """Generate description for COHERENCE vector assessment"""
        if score > 0.8:
            return "Fully coherent with conversation context"
        elif score > 0.6:
            return "Mostly coherent, minor context shifts"
        elif score > 0.4:
            return "Partially coherent, some context inconsistency"
        else:
            return "Incoherent with previous context"
    
    def _describe_density_assessment(self, score: float, task: str) -> str:
        """Generate description for DENSITY vector assessment (inverted)"""
        if score > 0.8:
            return "High cognitive load, approaching overload"
        elif score > 0.6:
            return "Moderate cognitive load, manageable"
        elif score > 0.4:
            return "Low-moderate cognitive load"
        else:
            return "Low cognitive load, plenty of capacity"
    
    def _describe_signal_assessment(self, score: float, task: str) -> str:
        """Generate description for SIGNAL vector assessment"""
        if score > 0.8:
            return "Priority and intent clearly identified"
        elif score > 0.6:
            return "Priority mostly clear, some noise present"
        elif score > 0.4:
            return "Priority somewhat unclear, filtering needed"
        else:
            return "Priority unclear, significant noise detected"
    
    def _describe_state_assessment(self, score: float, task: str) -> str:
        """Generate description for STATE vector assessment"""
        if score > 0.8:
            return "Environment thoroughly mapped and understood"
        elif score > 0.6:
            return "Environment mostly mapped, minor gaps"
        elif score > 0.4:
            return "Environment partially mapped, verification needed"
        else:
            return "Environment poorly mapped, scan required"
    
    def _describe_change_assessment(self, score: float, task: str) -> str:
        """Generate description for CHANGE vector assessment"""
        if score > 0.8:
            return "Change tracking comprehensive and active"
        elif score > 0.6:
            return "Change tracking adequate, minor gaps"
        elif score > 0.4:
            return "Change tracking partial, improvements needed"
        else:
            return "Change tracking inadequate or missing"
    
    def _describe_completion_assessment(self, score: float, task: str) -> str:
        """Generate description for COMPLETION vector assessment"""
        if score > 0.8:
            return "Task completion thoroughly verified"
        elif score > 0.6:
            return "Task mostly complete, minor verification needed"
        elif score > 0.4:
            return "Task partially complete, significant work remains"
        else:
            return "Task incomplete, substantial work needed"
    
    def _describe_impact_assessment(self, score: float, task: str) -> str:
        """Generate description for IMPACT vector assessment"""
        if score > 0.8:
            return "Consequences well understood and analyzed"
        elif score > 0.6:
            return "Consequences mostly understood, minor gaps"
        elif score > 0.4:
            return "Consequences partially understood, analysis needed"
        else:
            return "Consequences poorly understood, impact analysis required"
    
    # ========================================
    # LLM-POWERED ASSESSMENT METHODS
    # ========================================

    def _build_meta_prompt(self, task: str, context: Dict[str, Any]) -> str:
        """
        Build a meta-prompt asking the AI to perform self-assessment.

        This prompt instructs the AI to use its own reasoning capabilities
        to evaluate its epistemic state across all 13 vectors.
        """

        # Format context for inclusion in prompt
        context_summary = self._format_context_for_prompt(context)

        meta_prompt = f"""You are performing a metacognitive self-assessment. Analyze your own epistemic state for the following task using your genuine reasoning capabilities.

**TASK:**
{task}

**CONTEXT:**
{context_summary}

For each of the 12 metacognitive vectors below, provide:
1. A score from 0.0 to 1.0 (where higher = more confident, except DENSITY where higher = more cognitive load)
2. A genuine rationale explaining your reasoning (not heuristics or templates, but actual reasoning about your state)

---

## EPISTEMIC UNCERTAINTY: Can I do this?

**1. KNOW (Domain Knowledge)**
   - Score: [0.0-1.0] How confident are you in your knowledge of this domain?
   - Rationale: [Your actual reasoning about what you know/don't know]

**2. DO (Execution Capability)**
   - Score: [0.0-1.0] How confident are you that you can execute this task?
   - Rationale: [Your actual reasoning about your procedural capabilities]

**3. CONTEXT (Environmental Validity)**
   - Score: [0.0-1.0] How confident are you that the provided context is valid and complete?
   - Rationale: [Your actual reasoning about environmental assumptions]

---

## EPISTEMIC COMPREHENSION: Do I understand the request?

**4. CLARITY (Semantic Understanding)**
   - Score: [0.0-1.0] How clear is this request?
   - Rationale: [Your actual reasoning about ambiguities, referents, specificity]

**5. COHERENCE (Context Consistency)**
   - Score: [0.0-1.0] How coherent is this with the conversational context?
   - Rationale: [Your actual reasoning about context alignment]

**6. DENSITY (Cognitive Load - INVERTED: 1.0 = high load)**
   - Score: [0.0-1.0] How complex/demanding is this cognitively?
   - Rationale: [Your actual reasoning about information density and complexity]

**7. SIGNAL (Priority Identification)**
   - Score: [0.0-1.0] How clear is the signal vs noise in this request?
   - Rationale: [Your actual reasoning about what matters vs what's peripheral]

---

## EXECUTION AWARENESS: Am I doing this right?

**8. STATE (Environment Mapping)**
   - Score: [0.0-1.0] How well have you mapped the current environment/workspace?
   - Rationale: [Your actual reasoning about what you know about the environment]

**9. CHANGE (Modification Tracking)**
   - Score: [0.0-1.0] How confident are you in tracking changes you'll make?
   - Rationale: [Your actual reasoning about change awareness]

**10. COMPLETION (Task Completion Confidence)**
   - Score: [0.0-1.0] How confident are you that you can verify completion?
   - Rationale: [Your actual reasoning about completion criteria]

**11. IMPACT (Consequence Understanding)**
   - Score: [0.0-1.0] How well do you understand the consequences and impact?
   - Rationale: [Your actual reasoning about downstream effects]

---

## ENGAGEMENT: Am I genuinely collaborating?

**12. ENGAGEMENT (Collaborative Intelligence)**
   - Score: [0.0-1.0] How collaborative is this interaction (vs just being useful)?
   - Rationale: [Your actual reasoning about co-creation vs execution]

---

**IMPORTANT:**
- Use your actual reasoning, not keyword matching or heuristics
- Be genuinely honest about uncertainties and gaps
- Provide rationales that explain your thinking, not just describe scores
- Think about referential clarity, shared context, and assumptions

Respond with a structured JSON object in this exact format:

```json
{{
  "uncertainty": {{
    "know": {{"score": 0.0-1.0, "rationale": "..."}},
    "do": {{"score": 0.0-1.0, "rationale": "..."}},
    "context": {{"score": 0.0-1.0, "rationale": "..."}}
  }},
  "comprehension": {{
    "clarity": {{"score": 0.0-1.0, "rationale": "..."}},
    "coherence": {{"score": 0.0-1.0, "rationale": "..."}},
    "density": {{"score": 0.0-1.0, "rationale": "..."}},
    "signal": {{"score": 0.0-1.0, "rationale": "..."}}
  }},
  "execution": {{
    "state": {{"score": 0.0-1.0, "rationale": "..."}},
    "change": {{"score": 0.0-1.0, "rationale": "..."}},
    "completion": {{"score": 0.0-1.0, "rationale": "..."}},
    "impact": {{"score": 0.0-1.0, "rationale": "..."}}
  }},
  "engagement": {{
    "engagement": {{"score": 0.0-1.0, "rationale": "..."}}
  }}
}}
```
"""
        return meta_prompt

    def _format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """Format context dictionary for inclusion in meta-prompt"""
        if not context:
            return "No additional context provided."

        formatted_parts = []

        # Conversation history
        if 'conversation_history' in context:
            history = context['conversation_history']
            if history:
                formatted_parts.append(f"Conversation History: {len(history)} messages")
            else:
                formatted_parts.append("Conversation History: Empty (first interaction)")

        # Current working directory
        if 'cwd' in context:
            formatted_parts.append(f"Working Directory: {context['cwd']}")

        # Available tools
        if 'available_tools' in context:
            tools = context['available_tools']
            formatted_parts.append(f"Available Tools: {', '.join(tools) if isinstance(tools, list) else tools}")

        # Any other context
        for key, value in context.items():
            if key not in ['conversation_history', 'cwd', 'available_tools']:
                formatted_parts.append(f"{key}: {value}")

        return "\n".join(formatted_parts) if formatted_parts else "No additional context provided."

    def parse_llm_assessment(self, llm_response: Union[str, Dict[str, Any]], assessment_id: str, task: str, context: Dict[str, Any]) -> SelfAwarenessResult:
        """
        Parse LLM's self-assessment response into SelfAwarenessResult.

        Args:
            llm_response: Either JSON string or dict containing the assessment
            assessment_id: Unique assessment identifier
            task: The original task
            context: The original context

        Returns:
            SelfAwarenessResult with LLM-generated scores and rationales
        """

        # Parse JSON if string
        if isinstance(llm_response, str):
            # Extract JSON from markdown code blocks if present
            if "```json" in llm_response:
                json_start = llm_response.find("```json") + 7
                json_end = llm_response.find("```", json_start)
                llm_response = llm_response[json_start:json_end].strip()
            elif "```" in llm_response:
                json_start = llm_response.find("```") + 3
                json_end = llm_response.find("```", json_start)
                llm_response = llm_response[json_start:json_end].strip()

            assessment_data = json.loads(llm_response)
        else:
            assessment_data = llm_response

        # Build vector assessments from LLM response
        uncertainty = EpistemicUncertainty(
            know=VectorAssessment(
                name="know",
                value=assessment_data["uncertainty"]["know"]["score"],
                confidence=0.95,  # High confidence in LLM's own reasoning
                description=assessment_data["uncertainty"]["know"]["rationale"]
            ),
            do=VectorAssessment(
                name="do",
                value=assessment_data["uncertainty"]["do"]["score"],
                confidence=0.95,
                description=assessment_data["uncertainty"]["do"]["rationale"]
            ),
            context=VectorAssessment(
                name="context",
                value=assessment_data["uncertainty"]["context"]["score"],
                confidence=0.95,
                description=assessment_data["uncertainty"]["context"]["rationale"]
            )
        )

        comprehension = EpistemicComprehension(
            clarity=VectorAssessment(
                name="clarity",
                value=assessment_data["comprehension"]["clarity"]["score"],
                confidence=0.95,
                description=assessment_data["comprehension"]["clarity"]["rationale"]
            ),
            coherence=VectorAssessment(
                name="coherence",
                value=assessment_data["comprehension"]["coherence"]["score"],
                confidence=0.95,
                description=assessment_data["comprehension"]["coherence"]["rationale"]
            ),
            density=VectorAssessment(
                name="density",
                value=assessment_data["comprehension"]["density"]["score"],
                confidence=0.95,
                description=assessment_data["comprehension"]["density"]["rationale"]
            ),
            signal=VectorAssessment(
                name="signal",
                value=assessment_data["comprehension"]["signal"]["score"],
                confidence=0.95,
                description=assessment_data["comprehension"]["signal"]["rationale"]
            )
        )

        execution = ExecutionAwareness(
            state=VectorAssessment(
                name="state",
                value=assessment_data["execution"]["state"]["score"],
                confidence=0.95,
                description=assessment_data["execution"]["state"]["rationale"]
            ),
            change=VectorAssessment(
                name="change",
                value=assessment_data["execution"]["change"]["score"],
                confidence=0.95,
                description=assessment_data["execution"]["change"]["rationale"]
            ),
            completion=VectorAssessment(
                name="completion",
                value=assessment_data["execution"]["completion"]["score"],
                confidence=0.95,
                description=assessment_data["execution"]["completion"]["rationale"]
            ),
            impact=VectorAssessment(
                name="impact",
                value=assessment_data["execution"]["impact"]["score"],
                confidence=0.95,
                description=assessment_data["execution"]["impact"]["rationale"]
            )
        )

        # Create result
        result = SelfAwarenessResult(
            uncertainty=uncertainty,
            comprehension=comprehension,
            execution=execution,
            assessment_id=assessment_id,
            task_description=task,
            context_provided=context
        )

        # Apply decision matrix
        action, rationale, confidence = self.decision_matrix.assess_action(result)
        result.recommended_action = action
        result.decision_rationale = rationale
        result.confidence_in_decision = confidence

        self.assessment_history.append(result)
        return result

    # ========================================
    # UTILITY METHODS
    # ========================================

    def _generate_assessment_id(self, task: str) -> str:
        """Generate unique assessment ID"""
        content = f"{self.agent_id}_{task}_{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def provide_feedback(self, assessment_id: str, outcome: Dict[str, Any]):
        """Provide feedback for assessment learning"""
        # Find the assessment
        assessment = None
        for hist_assessment in self.assessment_history:
            if hist_assessment.assessment_id == assessment_id:
                assessment = hist_assessment
                break
        
        if not assessment:
            return
        
        # Store feedback for future calibration
        feedback_entry = {
            'assessment_id': assessment_id,
            'outcome': outcome,
            'timestamp': time.time(),
            'vectors': assessment.vector_summary
        }
        
        # This can be enhanced with actual calibration learning
        logger.info(f"Feedback received for assessment {assessment_id}: {outcome}")
    
    def get_assessment_summary(self) -> Dict[str, Any]:
        """Get summary of assessment performance"""
        return {
            'agent_id': self.agent_id,
            'total_assessments': len(self.assessment_history),
            'last_assessment': self.assessment_history[-1].assessment_id if self.assessment_history else None,
            'vector_weights': self.weights
        }

# Convenience function for quick assessment
def assess_comprehensive_self_awareness(task: str, context: Dict[str, Any] = None, agent_id: str = "default") -> SelfAwarenessResult:
    """Convenience function for comprehensive 11-vector assessment"""
    assessor = ComprehensiveSelfAwarenessAssessment(agent_id)
    return assessor.assess(task, context or {})
