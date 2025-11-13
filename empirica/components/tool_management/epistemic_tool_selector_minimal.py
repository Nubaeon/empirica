#!/usr/bin/env python3
"""
Minimal Epistemic Tool Selector
Bridges 12D assessment → Your existing tool_management.py → MCP tools

Add this to your cascade's INVESTIGATE phase
"""

from typing import Dict, List, Any, Tuple, Optional
from .tool_management import AIEnhancedToolManager, ToolIntelligenceLevel

try:
    from metacognition_12d_monitor.metacognition_12d_monitor import SelfAwarenessResult
    MONITOR_AVAILABLE = True
except ImportError:
    MONITOR_AVAILABLE = False


class EpistemicToolSelector:
    """
    Minimal selector: 12D vectors → tool_management recommendations → MCP invocation
    """
    
    def __init__(self, ai_id: str = "claude"):
        self.ai_id = ai_id
        self.tool_manager = AIEnhancedToolManager(
            intelligence_level=ToolIntelligenceLevel.PREDICTIVE
        )
        
        # Map 12D vectors to tool capabilities your MCP server has
        self.vector_to_capability_map = {
            'know': ['knowledge_retrieval', 'research', 'documentation'],
            'do': ['capability_assessment', 'tool_check', 'execution_planning'],
            'context': ['workspace_scan', 'environment_check', 'state_validation'],
            'clarity': ['clarification', 'human_interaction'],
            'coherence': ['conversation_analysis', 'context_validation'],
            'signal': ['priority_analysis', 'intent_detection'],
            'state': ['state_mapping', 'inventory', 'workspace_scan'],
            'change': ['change_tracking', 'modification_log'],
            'completion': ['validation', 'verification', 'quality_check'],
            'impact': ['impact_analysis', 'risk_assessment'],
            'engagement': ['collaboration_analysis', 'goal_creation']
        }
    
    async def select_tools_for_investigation(self, 
                                            assessment: SelfAwarenessResult,
                                            task_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Main entry point: Convert 12D assessment → tool recommendations
        """
        
        # Extract gaps from assessment
        gaps = self._extract_vector_gaps(assessment)
        
        # Build context for tool_management
        tool_context = {
            **task_context,
            'gaps': gaps,
            'required_capabilities': self._gaps_to_capabilities(gaps)
        }
        
        # Get AI-enhanced recommendations from your existing tool_management
        recommendations = await self.tool_manager.get_intelligent_tool_recommendations(
            ai_id=self.ai_id,
            current_context=tool_context
        )
        
        # Map recommendations to MCP tools
        investigation_plan = []
        for rec in recommendations[:5]:  # Top 5
            mcp_tool = self._map_to_mcp_tool(rec.tool_id, gaps)
            if mcp_tool:
                investigation_plan.append({
                    'mcp_tool': mcp_tool,
                    'gap_addressed': self._find_matching_gap(rec, gaps),
                    'confidence': rec.confidence_score,
                    'reasoning': rec.reasoning
                })
        
        return investigation_plan
    
    def _extract_vector_gaps(self, assessment: SelfAwarenessResult, 
                            threshold: float = 0.6) -> List[Tuple[str, float]]:
        """Extract vectors below threshold"""
        gaps = []
        
        # Uncertainty
        if assessment.uncertainty.know.value < threshold:
            gaps.append(('know', assessment.uncertainty.know.value))
        if assessment.uncertainty.do.value < threshold:
            gaps.append(('do', assessment.uncertainty.do.value))
        if assessment.uncertainty.context.value < threshold:
            gaps.append(('context', assessment.uncertainty.context.value))
        
        # Comprehension
        if assessment.comprehension.clarity.value < threshold:
            gaps.append(('clarity', assessment.comprehension.clarity.value))
        if assessment.comprehension.coherence.value < threshold:
            gaps.append(('coherence', assessment.comprehension.coherence.value))
        if assessment.comprehension.signal.value < threshold:
            gaps.append(('signal', assessment.comprehension.signal.value))
        
        # Execution
        if assessment.execution.state.value < threshold:
            gaps.append(('state', assessment.execution.state.value))
        if assessment.execution.impact.value < 0.5:
            gaps.append(('impact', assessment.execution.impact.value))
        if assessment.execution.completion.value < threshold:
            gaps.append(('completion', assessment.execution.completion.value))
        
        # Engagement (12th vector)
        if hasattr(assessment, 'engagement') and assessment.engagement.engagement < threshold:
            gaps.append(('engagement', assessment.engagement.engagement))
        
        gaps.sort(key=lambda x: x[1])  # Worst first
        return gaps
    
    def _gaps_to_capabilities(self, gaps: List[Tuple[str, float]]) -> List[str]:
        """Convert vector gaps to required capabilities"""
        capabilities = []
        for vector_name, _ in gaps:
            capabilities.extend(self.vector_to_capability_map.get(vector_name, []))
        return list(set(capabilities))  # Unique
    
    def _map_to_mcp_tool(self, tool_id: str, gaps: List[Tuple[str, float]]) -> Optional[str]:
        """Map tool_management tool_id to actual MCP tool name"""
        
        # Your MCP tools from empirica_mcp_server.py
        mcp_mapping = {
            'workspace_scanner': 'monitor_assess_12d',  # Re-assess after scan
            'knowledge_retriever': 'calibration_assess',
            'goal_analyzer': 'goals_create',
            'state_mapper': 'monitor_assess_12d',
            'calibrator': 'calibration_assess',
            'engagement_analyzer': 'goals_orchestrate'
        }
        
        return mcp_mapping.get(tool_id)
    
    def _find_matching_gap(self, recommendation, gaps: List[Tuple[str, float]]) -> str:
        """Find which gap this recommendation addresses"""
        # Simple heuristic - first gap
        return gaps[0][0] if gaps else 'unknown'


# Drop-in function for your cascade
async def epistemic_investigate(assessment: SelfAwarenessResult,
                               task: str,
                               context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use this in your cascade's INVESTIGATE phase
    
    Returns MCP tool invocations to execute
    """
    selector = EpistemicToolSelector(ai_id="claude")
    
    task_context = {**context, 'task': task}
    
    plan = await selector.select_tools_for_investigation(assessment, task_context)
    
    return {
        'investigation_plan': plan,
        'tools_to_invoke': [p['mcp_tool'] for p in plan],
        'gaps_addressed': [p['gap_addressed'] for p in plan]
    }