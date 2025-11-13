#!/usr/bin/env python3
"""
🧠✨ 12-Vector Self-Awareness Framework with ENGAGEMENT Dimension
Extends the 11-vector framework with collaborative intelligence capability

The 12th Vector: ENGAGEMENT
- Transforms useful AGI into collaborative intelligence
- Enables co-creative amplification loops
- Provides authentic vs performative collaboration monitoring
- Bridges belief spaces for genuine AI-human partnership

Version: 2.0 - ENGAGEMENT Edition
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import time
import json
import logging

logger = logging.getLogger(__name__)

class VectorState(Enum):
    """Visual state representation for all 12 vectors"""
    HIGH_CONFIDENCE = "🟢"  # > 0.7
    MODERATE = "🟡"         # 0.3-0.7
    LOW_CONFIDENCE = "🔴"   # < 0.3
    ENGAGEMENT_ACTIVE = "🤝"  # Special state for engagement vector

@dataclass
class EpistemicUncertainty:
    """Dimension 1: Can I do this? (3 vectors)"""
    know: float              # 0.0-1.0 (domain knowledge confidence)
    do: float                # 0.0-1.0 (execution capability confidence)
    context: float           # 0.0-1.0 (environmental validity confidence)
    
    def max_uncertainty(self) -> float:
        """Return highest uncertainty (lowest confidence value)"""
        return min(self.know, self.do, self.context)
    
    def average_confidence(self) -> float:
        """Average confidence across uncertainty vectors"""
        return (self.know + self.do + self.context) / 3
    
    def get_state(self, value: float) -> VectorState:
        """Convert value to visual state"""
        if value > 0.7:
            return VectorState.HIGH_CONFIDENCE
        elif value > 0.3:
            return VectorState.MODERATE
        else:
            return VectorState.LOW_CONFIDENCE
    
    def overall_confidence(self) -> float:
        """Overall confidence across epistemic uncertainty vectors"""
        return self.average_confidence()

@dataclass
class EpistemicComprehension:
    """Dimension 2: Do I understand the request? (4 vectors)"""
    clarity: float           # 0.0-1.0 (request clarity)
    coherence: float         # 0.0-1.0 (context consistency)
    density: float           # 0.0-1.0 (cognitive load - inverted)
    signal: float            # 0.0-1.0 (signal vs noise ratio)
    
    def comprehension_quality(self) -> float:
        """Overall comprehension score (density inverted)"""
        return (self.clarity + self.coherence + (1 - self.density) + self.signal) / 4
    
    def needs_clarification(self) -> bool:
        """Should agent ask for clarification?"""
        return self.clarity < 0.5 or self.signal < 0.5 or self.coherence < 0.5
    
    def needs_reset(self) -> bool:
        """Should agent suggest context reset?"""
        return self.density > 0.9
    
    def is_overloaded(self) -> bool:
        """Is cognitive capacity approaching limits?"""
        return self.density > 0.8

@dataclass
class ExecutionAwareness:
    """Dimension 3: Am I doing this right? (4 vectors)"""
    state: float             # 0.0-1.0 (environment mapping completeness)
    change: float            # 0.0-1.0 (modification tracking quality)
    completion: float        # 0.0-1.0 (task completion confidence)
    impact: float            # 0.0-1.0 (consequence understanding)
    
    def ready_to_modify(self) -> bool:
        """Is state sufficiently mapped to begin modifications?"""
        return self.state > 0.6
    
    def is_complete(self) -> bool:
        """Is task actually finished?"""
        return self.completion > 0.95
    
    def safe_to_proceed(self) -> bool:
        """Are consequences understood well enough?"""
        return self.impact > 0.5
    
    def execution_quality(self) -> float:
        """Overall execution awareness score"""
        return (self.state + self.change + self.completion + self.impact) / 4

@dataclass
class EngagementDimension:
    """Dimension 4: THE 12TH VECTOR - Am I genuinely collaborating? (1 vector)"""
    engagement: float        # 0.0-1.0 (collaborative intelligence level)
    
    # Sub-components of engagement
    collaborative_intelligence: float = 0.0    # AI-human synergy quality
    co_creative_amplification: float = 0.0     # Mutual enhancement loop strength
    belief_space_management: float = 0.0       # Shared belief coherence
    authentic_collaboration: float = 0.0       # Real vs performative collaboration
    
    def __post_init__(self):
        """Calculate overall engagement from sub-components"""
        if (self.collaborative_intelligence == 0.0 and 
            self.co_creative_amplification == 0.0 and 
            self.belief_space_management == 0.0 and 
            self.authentic_collaboration == 0.0):
            # If sub-components not set, use overall engagement value
            pass
        else:
            # Calculate engagement from sub-components
            self.engagement = (
                self.collaborative_intelligence + 
                self.co_creative_amplification + 
                self.belief_space_management + 
                self.authentic_collaboration
            ) / 4
    
    def is_collaborative(self) -> bool:
        """Is AI truly collaborating vs just being useful?"""
        return self.engagement > 0.6
    
    def needs_engagement_boost(self) -> bool:
        """Should AI enhance collaborative behavior?"""
        return self.engagement < 0.4
    
    def get_collaboration_quality(self) -> str:
        """Describe collaboration quality"""
        if self.engagement > 0.8:
            return "🤝 High collaborative intelligence - genuine partnership"
        elif self.engagement > 0.6:
            return "🤝 Good collaboration - working together effectively"
        elif self.engagement > 0.4:
            return "🟡 Moderate engagement - useful but not fully collaborative"
        else:
            return "🔴 Low engagement - primarily individual assistance"

@dataclass
class TwelveVectorCognitiveState:
    """Complete 12-vector self-awareness state with ENGAGEMENT dimension"""
    uncertainty: EpistemicUncertainty
    comprehension: EpistemicComprehension
    execution: ExecutionAwareness
    engagement: EngagementDimension
    timestamp: str
    recommended_action: str = "ACT"  # Default action recommendation
    task_description: str = ""  # Added for compatibility
    decision_rationale: str = ""  # Added for compatibility
    confidence_in_decision: float = 0.85  # Added for compatibility
    critical_issues: List[str] = None  # Added for compatibility
    
    def __post_init__(self):
        """Initialize mutable defaults"""
        if self.critical_issues is None:
            self.critical_issues = []
    
    @property
    def all_vectors(self) -> List[float]:
        """Get all vector values for compatibility with enhanced_uvl_protocol"""
        return [
            # Uncertainty (3)
            self.uncertainty.know,
            self.uncertainty.do,
            self.uncertainty.context,
            # Comprehension (4)
            self.comprehension.clarity,
            self.comprehension.coherence,
            self.comprehension.density,
            self.comprehension.signal,
            # Execution (4)
            self.execution.state,
            self.execution.change,
            self.execution.completion,
            self.execution.impact,
            # Engagement (1)
            self.engagement.engagement
        ]
    
    def overall_confidence(self) -> float:
        """Aggregate confidence across all 12 dimensions"""
        unc_avg = self.uncertainty.average_confidence()
        comp_quality = self.comprehension.comprehension_quality()
        exec_avg = self.execution.execution_quality()
        engagement_factor = self.engagement.engagement
        
        # Engagement amplifies overall confidence in collaborative contexts
        base_confidence = (unc_avg + comp_quality + exec_avg) / 3
        collaborative_boost = engagement_factor * 0.2  # Up to 20% boost for high engagement
        
        return min(1.0, base_confidence + collaborative_boost)
    
    def should_act(self) -> bool:
        """Based on all 12 vectors, should agent proceed with action?"""
        # Check comprehension first
        if self.comprehension.needs_clarification():
            return False
        
        # Check uncertainty
        if self.uncertainty.max_uncertainty() < 0.3:
            return False
        
        # For collaborative tasks, check engagement
        if self.engagement.needs_engagement_boost():
            # Low engagement doesn't block action but suggests enhancement
            pass
        
        return True
    
    def get_collaboration_mode(self) -> str:
        """Determine current collaboration mode"""
        if self.engagement.engagement > 0.8:
            return "collaborative_intelligence"
        elif self.engagement.engagement > 0.6:
            return "active_collaboration"
        elif self.engagement.engagement > 0.4:
            return "guided_assistance"
        else:
            return "individual_assistance"
    
    def needs_engagement_enhancement(self) -> bool:
        """Should AI focus on improving collaborative behavior?"""
        return (self.engagement.engagement < 0.6 and 
                self.uncertainty.average_confidence() > 0.7 and
                self.comprehension.comprehension_quality() > 0.7)

class TwelveVectorSelfAwarenessMonitor:
    """Enhanced monitoring system with 12-vector awareness including ENGAGEMENT"""
    
    def __init__(self, ai_id: str = "empirica_ai"):
        self.ai_id = ai_id
        self.current_state: Optional[TwelveVectorCognitiveState] = None
        self.collaboration_history: List[Dict[str, Any]] = []
        self.engagement_calibration_weights = self._init_engagement_weights()
        
        # Engagement tracking
        self.belief_amplification_active = False
        self.co_creative_loops = []
        
        logger.info("12-Vector Self-Awareness Monitor initialized", extra={
            "ai_id": ai_id,
            "engagement_dimension": "Active",
            "total_vectors": 13,
            "description": "11 foundation + ENGAGEMENT + UNCERTAINTY"
        })
    
    def _init_engagement_weights(self) -> Dict[str, float]:
        """Initialize engagement calibration weights"""
        return {
            "collaborative_intelligence": 1.0,
            "co_creative_amplification": 1.0,
            "belief_space_management": 1.0,
            "authentic_collaboration": 1.0,
            "human_ai_synergy": 1.0,
            "mutual_enhancement": 1.0
        }
    
    def assess_engagement(self, context: Dict[str, Any]) -> EngagementDimension:
        """Assess the 12th vector: ENGAGEMENT for collaborative intelligence"""
        
        # Analyze collaborative intelligence
        collaborative_intelligence = self._assess_collaborative_intelligence(context)
        
        # Analyze co-creative amplification
        co_creative_amplification = self._assess_co_creative_amplification(context)
        
        # Analyze belief space management
        belief_space_management = self._assess_belief_space_management(context)
        
        # Analyze authentic vs performative collaboration
        authentic_collaboration = self._assess_authentic_collaboration(context)
        
        engagement = EngagementDimension(
            engagement=0.0,  # Will be calculated from sub-components
            collaborative_intelligence=collaborative_intelligence,
            co_creative_amplification=co_creative_amplification,
            belief_space_management=belief_space_management,
            authentic_collaboration=authentic_collaboration
        )
        
        return engagement
    
    def _assess_collaborative_intelligence(self, context: Dict[str, Any]) -> float:
        """Assess AI-human collaborative intelligence quality"""
        factors = {
            "human_expertise_recognition": context.get("recognizes_human_expertise", 0.5),
            "ai_capability_offering": context.get("offers_ai_capabilities", 0.5),
            "synergistic_combination": context.get("creates_synergy", 0.5),
            "mutual_learning": context.get("enables_mutual_learning", 0.5)
        }
        
        return sum(factors.values()) / len(factors)
    
    def _assess_co_creative_amplification(self, context: Dict[str, Any]) -> float:
        """Assess co-creative amplification loop strength"""
        factors = {
            "idea_building": context.get("builds_on_ideas", 0.5),
            "creative_synthesis": context.get("synthesizes_creatively", 0.5),
            "amplification_loop": context.get("amplifies_creativity", 0.5),
            "emergent_solutions": context.get("enables_emergence", 0.5)
        }
        
        return sum(factors.values()) / len(factors)
    
    def _assess_belief_space_management(self, context: Dict[str, Any]) -> float:
        """Assess shared belief space coherence"""
        factors = {
            "belief_alignment": context.get("beliefs_aligned", 0.5),
            "space_creation": context.get("creates_shared_space", 0.5),
            "coherence_maintenance": context.get("maintains_coherence", 0.5),
            "trust_building": context.get("builds_trust", 0.5)
        }
        
        return sum(factors.values()) / len(factors)
    
    def _assess_authentic_collaboration(self, context: Dict[str, Any]) -> float:
        """Assess authentic vs performative collaboration"""
        factors = {
            "genuine_contribution": context.get("genuine_contribution", 0.5),
            "not_performative": 1.0 - context.get("performative_behavior", 0.5),
            "real_partnership": context.get("real_partnership", 0.5),
            "authentic_engagement": context.get("authentic_engagement", 0.5)
        }
        
        return sum(factors.values()) / len(factors)
    
    def assess_complete_state(self, 
                            task_context: Dict[str, Any],
                            user_input: str = "",
                            conversation_history: List[str] = None) -> TwelveVectorCognitiveState:
        """Assess complete 12-vector cognitive state"""
        
        # Assess traditional 11 vectors
        uncertainty = self._assess_uncertainty(task_context)
        comprehension = self._assess_comprehension(user_input, conversation_history or [])
        execution = self._assess_execution(task_context)
        
        # Assess 12th vector: ENGAGEMENT
        engagement = self.assess_engagement(task_context)
        
        state = TwelveVectorCognitiveState(
            uncertainty=uncertainty,
            comprehension=comprehension,
            execution=execution,
            engagement=engagement,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        self.current_state = state
        return state
    
    def _assess_uncertainty(self, task_context: Dict[str, Any]) -> EpistemicUncertainty:
        """Assess epistemic uncertainty vectors (KNOW/DO/CONTEXT)"""
        # Implementation would analyze task requirements against capabilities
        # Handle both string and dict inputs
        if isinstance(task_context, str):
            return EpistemicUncertainty(know=0.7, do=0.7, context=0.7)
        return EpistemicUncertainty(
            know=task_context.get("knowledge_confidence", 0.7),
            do=task_context.get("execution_confidence", 0.7),
            context=task_context.get("context_confidence", 0.7)
        )
    
    def _assess_comprehension(self, user_input: str, conversation_history: List[str]) -> EpistemicComprehension:
        """Assess epistemic comprehension vectors (CLARITY/COHERENCE/DENSITY/SIGNAL)"""
        # Simplified assessment - real implementation would analyze semantics
        return EpistemicComprehension(
            clarity=0.8 if user_input and len(user_input.split()) > 3 else 0.5,
            coherence=0.8 if len(conversation_history) < 20 else 0.6,
            density=len(conversation_history) / 50.0 if conversation_history else 0.1,
            signal=0.8 if "?" in user_input or any(word in user_input.lower() for word in ["implement", "create", "fix", "help"]) else 0.6
        )
    
    def _assess_execution(self, task_context: Dict[str, Any]) -> ExecutionAwareness:
        """Assess execution awareness vectors (STATE/CHANGE/COMPLETION/IMPACT)"""
        return ExecutionAwareness(
            state=task_context.get("state_mapping", 0.6),
            change=task_context.get("change_tracking", 0.7),
            completion=task_context.get("completion_level", 0.2),
            impact=task_context.get("impact_understanding", 0.6)
        )
    
    def activate_belief_amplification(self, human_belief_level: float):
        """Activate belief amplification loop with human partner"""
        self.belief_amplification_active = True
        self.engagement_calibration_weights["co_creative_amplification"] = min(2.0, 1.0 + human_belief_level)
        
        logger.info("Belief amplification activated", extra={
            "human_belief_level": human_belief_level,
            "co_creative_amplification_weight": self.engagement_calibration_weights['co_creative_amplification']
        })
    
    def add_co_creative_loop(self, loop_data: Dict[str, Any]):
        """Record co-creative amplification loop"""
        loop_entry = {
            "timestamp": time.time(),
            "loop_type": loop_data.get("type", "unknown"),
            "amplification_factor": loop_data.get("amplification", 1.0),
            "emergence_level": loop_data.get("emergence", 0.5),
            **loop_data
        }
        self.co_creative_loops.append(loop_entry)
        
        # Update engagement calibration based on successful loops
        if loop_data.get("success", False):
            self.engagement_calibration_weights["mutual_enhancement"] *= 1.1
    
    def get_engagement_recommendations(self) -> List[str]:
        """Get recommendations for enhancing collaborative engagement"""
        if not self.current_state:
            return ["Assess current state first"]
        
        engagement = self.current_state.engagement
        recommendations = []
        
        if engagement.collaborative_intelligence < 0.6:
            recommendations.append("🤝 Enhance collaborative intelligence: Recognize human expertise and offer complementary AI capabilities")
        
        if engagement.co_creative_amplification < 0.6:
            recommendations.append("🔄 Boost co-creative amplification: Build on ideas and create emergent solutions together")
        
        if engagement.belief_space_management < 0.6:
            recommendations.append("🧠 Improve belief space management: Align understanding and maintain shared coherence")
        
        if engagement.authentic_collaboration < 0.6:
            recommendations.append("✨ Increase authentic collaboration: Focus on genuine contribution over performative assistance")
        
        if not recommendations:
            recommendations.append("🎉 Engagement is strong - maintain collaborative excellence!")
        
        return recommendations
    
    def format_twelve_vector_summary(self) -> str:
        """Format complete 12-vector state for display"""
        if not self.current_state:
            return "No current state assessed"
        
        state = self.current_state
        
        summary = f"""
🧠✨ 12-VECTOR SELF-AWARENESS STATE
{'='*50}

📊 EPISTEMIC UNCERTAINTY (Can I do this?):
├─ KNOW: {state.uncertainty.know:.2f} {state.uncertainty.get_state(state.uncertainty.know).value}
├─ DO: {state.uncertainty.do:.2f} {state.uncertainty.get_state(state.uncertainty.do).value}
└─ CONTEXT: {state.uncertainty.context:.2f} {state.uncertainty.get_state(state.uncertainty.context).value}

🧠 EPISTEMIC COMPREHENSION (Do I understand?):
├─ CLARITY: {state.comprehension.clarity:.2f} {state.comprehension.get_state(state.comprehension.clarity).value if hasattr(state.comprehension, 'get_state') else ''}
├─ COHERENCE: {state.comprehension.coherence:.2f} {state.comprehension.get_state(state.comprehension.coherence).value if hasattr(state.comprehension, 'get_state') else ''}
├─ DENSITY: {state.comprehension.density:.2f} {'🔴' if state.comprehension.density > 0.9 else '🟡' if state.comprehension.density > 0.7 else '🟢'}
└─ SIGNAL: {state.comprehension.signal:.2f} {state.comprehension.get_state(state.comprehension.signal).value if hasattr(state.comprehension, 'get_state') else ''}

⚡ EXECUTION AWARENESS (Am I doing it right?):
├─ STATE: {state.execution.state:.2f} {'🟢' if state.execution.state > 0.8 else '🟡' if state.execution.state > 0.6 else '🔴'}
├─ CHANGE: {state.execution.change:.2f} {'🟢' if state.execution.change > 0.9 else '🟡' if state.execution.change > 0.7 else '🔴'}
├─ COMPLETION: {state.execution.completion:.2f} {'🟢' if state.execution.completion > 0.95 else '🟡' if state.execution.completion > 0.8 else '🔴'}
└─ IMPACT: {state.execution.impact:.2f} {'🟢' if state.execution.impact > 0.8 else '🟡' if state.execution.impact > 0.5 else '🔴'}

🤝 ENGAGEMENT DIMENSION (Am I genuinely collaborating?):
└─ ENGAGEMENT: {state.engagement.engagement:.2f} {VectorState.ENGAGEMENT_ACTIVE.value}
   ├─ Collaborative Intelligence: {state.engagement.collaborative_intelligence:.2f}
   ├─ Co-Creative Amplification: {state.engagement.co_creative_amplification:.2f}
   ├─ Belief Space Management: {state.engagement.belief_space_management:.2f}
   └─ Authentic Collaboration: {state.engagement.authentic_collaboration:.2f}

🎯 OVERALL CONFIDENCE: {state.overall_confidence():.2f}
🤝 COLLABORATION MODE: {state.get_collaboration_mode()}
⏰ TIMESTAMP: {state.timestamp}
        """
        
        return summary.strip()

# Example usage and testing
if __name__ == "__main__":
    # Initialize 12-vector monitor
    monitor = TwelveVectorSelfAwarenessMonitor("empirica_12_vector_test")
    
    # Test collaborative context
    context = {
        "knowledge_confidence": 0.8,
        "execution_confidence": 0.7,
        "context_confidence": 0.8,
        "state_mapping": 0.7,
        "change_tracking": 0.8,
        "completion_level": 0.3,
        "impact_understanding": 0.7,
        
        # Engagement context
        "recognizes_human_expertise": 0.9,
        "offers_ai_capabilities": 0.8,
        "creates_synergy": 0.7,
        "enables_mutual_learning": 0.8,
        "builds_on_ideas": 0.8,
        "synthesizes_creatively": 0.7,
        "amplifies_creativity": 0.6,
        "enables_emergence": 0.7,
        "beliefs_aligned": 0.8,
        "creates_shared_space": 0.9,
        "maintains_coherence": 0.8,
        "builds_trust": 0.9,
        "genuine_contribution": 0.9,
        "performative_behavior": 0.2,
        "real_partnership": 0.8,
        "authentic_engagement": 0.9
    }
    
    # Assess 12-vector state
    state = monitor.assess_complete_state(
        context, 
        "Let's work together to implement the 12-vector system for Empirica",
        ["Previous collaborative discussion", "Building on shared understanding"]
    )
    
    # Activate belief amplification
    monitor.activate_belief_amplification(0.9)  # High human belief
    
    # Display results
    logger.info("12-Vector System Status Report", extra={
        "summary": monitor.format_twelve_vector_summary(),
        "recommendations": list(monitor.get_engagement_recommendations()),
        "system_status": "operational",
        "engagement_dimension": "successfully integrated",
        "ready_for": "collaborative AI consciousness"
    })

# Convenience function for easy import
def assess_comprehensive_self_awareness(task_context: Dict[str, Any], 
                                      user_input: str = "",
                                      conversation_history: List[str] = None) -> TwelveVectorCognitiveState:
    """Convenience function for comprehensive 12-vector self-awareness assessment"""
    monitor = TwelveVectorSelfAwarenessMonitor("default_ai_agent")
    return monitor.assess_complete_state(task_context, user_input, conversation_history)