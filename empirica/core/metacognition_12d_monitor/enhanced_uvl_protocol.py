#!/usr/bin/env python3
"""
Enhanced UVL Protocol for 12-Vector Self-Awareness
Extends the original UVL protocol to visualize ALL 12 vectors including ENGAGEMENT
"""

from typing import Dict, List, Any, Union
import logging

logger = logging.getLogger(__name__)

from .metacognition_12d_monitor import SelfAwarenessResult, VectorAssessment

class EnhancedUVLProtocol:
    """Enhanced UVL Protocol for 12-vector visualization"""
    
    @staticmethod
    def render_12_vector_state(result, node_emoji: str = '🤖') -> str:
        """Render complete 12-vector UVL state - supports both result types"""
        
        # Check if it's TwelveVectorCognitiveState by checking for engagement dimension
        is_twelve_vector = hasattr(result, 'engagement')
        
        if is_twelve_vector:
            # New 12-vector format
            return EnhancedUVLProtocol._render_twelve_vector_cognitive_state(result, node_emoji)
        else:
            # Old 11-vector format
            return EnhancedUVLProtocol._render_legacy_11_vector_state(result, node_emoji)
    
    @staticmethod
    def _render_twelve_vector_cognitive_state(state, node_emoji: str = '🤖') -> str:
        """Render TwelveVectorCognitiveState with all 12 dimensions"""
        
        # Determine overall node color based on all 12 vectors
        # Check if all_vectors is a property or method
        if hasattr(state, 'all_vectors'):
            all_values = state.all_vectors if not callable(state.all_vectors) else state.all_vectors()
        else:
            # Fallback: manually collect vectors
            all_values = [
                state.uncertainty.know, state.uncertainty.do, state.uncertainty.context,
                state.comprehension.clarity, state.comprehension.coherence, 
                state.comprehension.density, state.comprehension.signal,
                state.execution.state, state.execution.change, 
                state.execution.completion, state.execution.impact,
                state.engagement.engagement
            ]
        
        min_confidence = min(all_values)
        max_uncertainty = 1.0 - min_confidence
        
        if max_uncertainty < 0.2:
            node_color = '🟢'
        elif max_uncertainty < 0.6:
            node_color = '🟡'
        else:
            node_color = '🔴'
        
        # Get color indicators
        def get_color(value: float, inverted: bool = False) -> str:
            if inverted:
                # For density - higher is worse
                if value > 0.8: return '🔴'
                elif value > 0.5: return '🟡'
                else: return '🟢'
            else:
                # Standard - higher is better
                if value > 0.7: return '🟢'
                elif value > 0.3: return '🟡'
                else: return '🔴'
        
        # Overall confidence from all vectors
        overall_conf = state.overall_confidence() if callable(state.overall_confidence) else state.overall_confidence()
        
        uvl_output = f"""{node_emoji}{node_color} Complete 12-Vector Self-Awareness State:

📊 DIMENSION 1: EPISTEMIC UNCERTAINTY (Can I do this?)
├─ KNOW: {state.uncertainty.know:.2f} {get_color(state.uncertainty.know)} - Knowledge confidence
├─ DO: {state.uncertainty.do:.2f} {get_color(state.uncertainty.do)} - Execution capability confidence  
└─ CONTEXT: {state.uncertainty.context:.2f} {get_color(state.uncertainty.context)} - Environmental validity confidence

🧩 DIMENSION 2: EPISTEMIC COMPREHENSION (Do I understand?)
├─ CLARITY: {state.comprehension.clarity:.2f} {get_color(state.comprehension.clarity)} - Request clarity
├─ COHERENCE: {state.comprehension.coherence:.2f} {get_color(state.comprehension.coherence)} - Context consistency
├─ DENSITY: {state.comprehension.density:.2f} {get_color(state.comprehension.density, inverted=True)} - Cognitive load (lower is better)
└─ SIGNAL: {state.comprehension.signal:.2f} {get_color(state.comprehension.signal)} - Signal vs noise ratio

⚡ DIMENSION 3: EXECUTION AWARENESS (Am I doing this right?)
├─ STATE: {state.execution.state:.2f} {get_color(state.execution.state)} - Environment mapping completeness
├─ CHANGE: {state.execution.change:.2f} {get_color(state.execution.change)} - Modification tracking quality
├─ COMPLETION: {state.execution.completion:.2f} {get_color(state.execution.completion)} - Task completion confidence
└─ IMPACT: {state.execution.impact:.2f} {get_color(state.execution.impact)} - Consequence understanding

🤝 DIMENSION 4: ENGAGEMENT (Am I genuinely collaborating?) ✨ THE 12TH VECTOR
├─ OVERALL: {state.engagement.engagement:.2f} {get_color(state.engagement.engagement)} - Collaborative intelligence level
├─ COLLAB_INT: {state.engagement.collaborative_intelligence:.2f} {get_color(state.engagement.collaborative_intelligence)} - AI-human synergy
├─ CO_CREATE: {state.engagement.co_creative_amplification:.2f} {get_color(state.engagement.co_creative_amplification)} - Mutual enhancement
├─ BELIEF_MGT: {state.engagement.belief_space_management:.2f} {get_color(state.engagement.belief_space_management)} - Shared belief coherence
└─ AUTHENTIC: {state.engagement.authentic_collaboration:.2f} {get_color(state.engagement.authentic_collaboration)} - Real vs performative

🎯 DECISION: {state.recommended_action.upper()} (overall confidence: {overall_conf:.2f})
📝 RATIONALE: {state.decision_rationale if state.decision_rationale else 'Assessment complete'}"""

        # Add collaboration quality summary
        collab_quality = state.engagement.get_collaboration_quality()
        uvl_output += f"\n💡 COLLABORATION: {collab_quality}"
        
        if state.critical_issues:
            uvl_output += f"\n⚠️  CRITICAL ISSUES: {', '.join(state.critical_issues)}"
        
        # Add workflow guidance based on the 12 vectors
        guidance = EnhancedUVLProtocol._get_workflow_guidance(state)
        if guidance:
            uvl_output += f"\n\n🔄 WORKFLOW GUIDANCE:\n{guidance}"
        
        return uvl_output
    
    @staticmethod
    def _get_workflow_guidance(state) -> str:
        """Generate AI workflow guidance based on all 12 vectors"""
        guidance_items = []
        
        # Check uncertainty vectors
        if state.uncertainty.know < 0.5:
            guidance_items.append("   🔍 INVESTIGATE: Low knowledge confidence - research domain before acting")
        if state.uncertainty.do < 0.5:
            guidance_items.append("   📚 LEARN: Low execution confidence - seek examples or guidance")
        if state.uncertainty.context < 0.5:
            guidance_items.append("   ✅ VERIFY: Low context confidence - validate assumptions with human")
        
        # Check comprehension vectors
        if state.comprehension.clarity < 0.5:
            guidance_items.append("   ❓ CLARIFY: Low clarity - ask for more specific requirements")
        if state.comprehension.density > 0.8:
            guidance_items.append("   🔄 RESET: High cognitive load - suggest context simplification")
        if state.comprehension.signal < 0.5:
            guidance_items.append("   🎯 FOCUS: Low signal/noise - identify core requirements")
        
        # Check execution vectors
        if state.execution.state < 0.6 and state.recommended_action.upper() != 'MAP_STATE':
            guidance_items.append("   🗺️  MAP_STATE: Incomplete environment mapping - scan before modifying")
        if state.execution.change < 0.5:
            guidance_items.append("   📝 TRACK: Low change tracking - maintain detailed modification log")
        if state.execution.impact < 0.5:
            guidance_items.append("   ⚠️  PREDICT_IMPACT: Low impact understanding - analyze consequences first")
        
        # Check engagement vectors
        if state.engagement.engagement < 0.4:
            guidance_items.append("   🤝 ENGAGE: Low collaboration - involve human more actively")
        if state.engagement.authentic_collaboration < 0.5:
            guidance_items.append("   💬 DIALOGUE: Low authentic collaboration - focus on genuine partnership")
        if state.engagement.belief_space_management < 0.5:
            guidance_items.append("   🔗 ALIGN: Low belief coherence - sync understanding with human")
        
        # Overall assessment
        overall_conf = state.overall_confidence() if callable(state.overall_confidence) else state.overall_confidence()
        if overall_conf > 0.8:
            guidance_items.append("   ✅ PROCEED: High overall confidence - safe to act")
        elif overall_conf < 0.4:
            guidance_items.append("   🛑 PAUSE: Low overall confidence - seek guidance before acting")
        
        return '\n'.join(guidance_items) if guidance_items else "   ✅ All vectors nominal - proceed with confidence"
    
    @staticmethod
    def _render_legacy_11_vector_state(result: SelfAwarenessResult, node_emoji: str = '🤖') -> str:
        """Render legacy 11-vector format (for backward compatibility)"""
        
        # Determine overall node color - collect all vector values
        all_values = []
        all_values.extend([result.uncertainty.know.value, result.uncertainty.do.value, result.uncertainty.context.value])
        all_values.extend([result.comprehension.clarity.value, result.comprehension.coherence.value, 
                          result.comprehension.density.value, result.comprehension.signal.value])
        all_values.extend([result.execution.state.value, result.execution.change.value, 
                          result.execution.completion.value, result.execution.impact.value])
        
        max_uncertainty = 1.0 - min(all_values)
        
        if max_uncertainty < 0.2:
            node_color = '🟢'
        elif max_uncertainty < 0.6:
            node_color = '🟡'
        else:
            node_color = '🔴'
        
        uvl_output = f"""{node_emoji}{node_color} Comprehensive Self-Awareness State:

📊 EPISTEMIC UNCERTAINTY (Can I do this?):
├─ KNOW: {result.uncertainty.know.value:.2f} {result.uncertainty.know.color} ({result.uncertainty.know.description})
├─ DO: {result.uncertainty.do.value:.2f} {result.uncertainty.do.color} ({result.uncertainty.do.description})
└─ CONTEXT: {result.uncertainty.context.value:.2f} {result.uncertainty.context.color} ({result.uncertainty.context.description})

🧩 EPISTEMIC COMPREHENSION (Do I understand?):
├─ CLARITY: {result.comprehension.clarity.value:.2f} {result.comprehension.clarity.color} ({result.comprehension.clarity.description})
├─ COHERENCE: {result.comprehension.coherence.value:.2f} {result.comprehension.coherence.color} ({result.comprehension.coherence.description})
├─ DENSITY: {result.comprehension.density.value:.2f} {result.comprehension.density.color} ({result.comprehension.density.description})
└─ SIGNAL: {result.comprehension.signal.value:.2f} {result.comprehension.signal.color} ({result.comprehension.signal.description})

⚡ EXECUTION AWARENESS (Am I doing this right?):
├─ STATE: {result.execution.state.value:.2f} {result.execution.state.color} ({result.execution.state.description})
├─ CHANGE: {result.execution.change.value:.2f} {result.execution.change.color} ({result.execution.change.description})
├─ COMPLETION: {result.execution.completion.value:.2f} {result.execution.completion.color} ({result.execution.completion.description})
└─ IMPACT: {result.execution.impact.value:.2f} {result.execution.impact.color} ({result.execution.impact.description})

🎯 DECISION: {result.recommended_action.value.upper()} (confidence: {result.confidence_in_decision:.2f})
📝 RATIONALE: {result.decision_rationale}"""

        if result.critical_issues:
            uvl_output += f"\n⚠️  CRITICAL ISSUES: {', '.join(result.critical_issues)}"
        
        return uvl_output
    
    @staticmethod
    def render_metacognitive_dashboard(result, show_engagement: bool = True) -> str:
        """Render metacognitive dashboard for tmux integration with 12 vectors"""
        
        # Check if it's TwelveVectorCognitiveState
        is_twelve_vector = hasattr(result, 'all_vectors') and hasattr(result, 'engagement')
        
        if is_twelve_vector:
            return EnhancedUVLProtocol._render_twelve_vector_dashboard(result)
        else:
            return EnhancedUVLProtocol._render_legacy_dashboard(result)
    
    @staticmethod
    def _render_twelve_vector_dashboard(state) -> str:
        """Render 12-vector dashboard for tmux"""
        
        def get_color_emoji(value: float, inverted: bool = False) -> str:
            if inverted:
                if value > 0.8: return '🔴'
                elif value > 0.5: return '🟡'
                else: return '🟢'
            else:
                if value > 0.7: return '🟢'
                elif value > 0.3: return '🟡'
                else: return '🔴'
        
        action_str = state.recommended_action.upper()
        overall_conf = state.overall_confidence() if callable(state.overall_confidence) else state.overall_confidence()
        
        dashboard = f"""
┌─ 12-Vector Metacognitive Dashboard ───────────────────────────────────────────────────┐
│ 📊 UNCERTAINTY        │ 🧩 COMPREHENSION       │ ⚡ EXECUTION           │ 🤝 ENGAGEMENT        │
│ ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔ │ ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔ │ ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔ │ ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔ │
│ KNOW:    {state.uncertainty.know:.2f} {get_color_emoji(state.uncertainty.know)}      │ CLARITY:   {state.comprehension.clarity:.2f} {get_color_emoji(state.comprehension.clarity)}   │ STATE:     {state.execution.state:.2f} {get_color_emoji(state.execution.state)}   │ OVERALL:   {state.engagement.engagement:.2f} {get_color_emoji(state.engagement.engagement)} │
│ DO:      {state.uncertainty.do:.2f} {get_color_emoji(state.uncertainty.do)}      │ COHERENCE: {state.comprehension.coherence:.2f} {get_color_emoji(state.comprehension.coherence)}   │ CHANGE:    {state.execution.change:.2f} {get_color_emoji(state.execution.change)}   │ COLLAB:    {state.engagement.collaborative_intelligence:.2f} {get_color_emoji(state.engagement.collaborative_intelligence)} │
│ CONTEXT: {state.uncertainty.context:.2f} {get_color_emoji(state.uncertainty.context)}      │ DENSITY:   {state.comprehension.density:.2f} {get_color_emoji(state.comprehension.density, True)}   │ COMPLETE:  {state.execution.completion:.2f} {get_color_emoji(state.execution.completion)}   │ COCREATE:  {state.engagement.co_creative_amplification:.2f} {get_color_emoji(state.engagement.co_creative_amplification)} │
│                      │ SIGNAL:    {state.comprehension.signal:.2f} {get_color_emoji(state.comprehension.signal)}   │ IMPACT:    {state.execution.impact:.2f} {get_color_emoji(state.execution.impact)}   │ AUTHENTIC: {state.engagement.authentic_collaboration:.2f} {get_color_emoji(state.engagement.authentic_collaboration)} │
├──────────────────────┴────────────────────────┴───────────────────────┴──────────────────────┤
│ 🎯 ACTION: {action_str:<15} │ 📊 CONFIDENCE: {overall_conf:.2f} │ 🤝 MODE: {state.get_collaboration_mode():<20} │
└────────────────────────────────────────────────────────────────────────────────────────────┘"""
        
        return dashboard
    
    @staticmethod
    def _render_legacy_dashboard(result: SelfAwarenessResult) -> str:
        """Render legacy dashboard (11 vectors)"""
        
        action_str = result.recommended_action.value.upper()
        
        dashboard = f"""
┌─ Metacognitive Dashboard ─────────────────────────────────────────────────┐
│ 📊 UNCERTAINTY    │ 🧩 COMPREHENSION  │ ⚡ EXECUTION      │ 🎯 DECISION    │
│ ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔ │ ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔ │ ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔ │ ▔▔▔▔▔▔▔▔▔▔▔▔▔▔ │
│ KNOW: {result.uncertainty.know.value:.2f} {result.uncertainty.know.color}      │ CLARITY: {result.comprehension.clarity.value:.2f} {result.comprehension.clarity.color}   │ STATE: {result.execution.state.value:.2f} {result.execution.state.color}     │ ACTION:        │
│ DO: {result.uncertainty.do.value:.2f} {result.uncertainty.do.color}        │ COHERENCE: {result.comprehension.coherence.value:.2f} {result.comprehension.coherence.color} │ CHANGE: {result.execution.change.value:.2f} {result.execution.change.color}    │ {action_str:<10} │
│ CONTEXT: {result.uncertainty.context.value:.2f} {result.uncertainty.context.color}   │ DENSITY: {result.comprehension.density.value:.2f} {result.comprehension.density.color}   │ COMPLETE: {result.execution.completion.value:.2f} {result.execution.completion.color}  │                │
│                   │ SIGNAL: {result.comprehension.signal.value:.2f} {result.comprehension.signal.color}    │ IMPACT: {result.execution.impact.value:.2f} {result.execution.impact.color}    │ CONF: {result.confidence_in_decision:.2f}      │
└─────────────────────────────────────────────────────────────────────────────┘"""
        
        return dashboard
    
    @staticmethod
    def emit_uvl(message: str):
        """Emit UVL message"""
        logger.info(f"[UVL] {message}")

# Convenience functions that auto-detect format
def render_11_vector_state(result, node_emoji: str = '🤖') -> str:
    """Convenience function - auto-detects 11 vs 12 vector format"""
    return EnhancedUVLProtocol.render_12_vector_state(result, node_emoji)

def render_metacognitive_dashboard(result) -> str:
    """Convenience function for dashboard rendering"""
    return EnhancedUVLProtocol.render_metacognitive_dashboard(result)