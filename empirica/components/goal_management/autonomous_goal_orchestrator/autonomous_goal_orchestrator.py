#!/usr/bin/env python3
"""
Enhanced Autonomous Goal Orchestrator with Dynamic Context Awareness
Integrates with 12-Vector Metacognitive System for ENGAGEMENT-driven goal management
"""

import sys
import json
import time
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Try to import 12-vector system for ENGAGEMENT dimension
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from metacognition_12d_monitor import TwelveVectorSelfAwarenessMonitor, EngagementDimension
    TWELVE_VECTOR_AVAILABLE = True
except ImportError:
    TWELVE_VECTOR_AVAILABLE = False
    # Don't print warning here - will fail fast when used

class DynamicContextAnalyzer:
    """Analyzes conversation context for dynamic goal adaptation"""
    
    def __init__(self):
        # Verify 12-vector system is available
        if not TWELVE_VECTOR_AVAILABLE:
            raise RuntimeError(
                "12-Vector system required but not available. "
                "Empirica requires genuine epistemic assessment (no heuristic fallbacks). "
                "Please ensure empirica.core.metacognition_12d_monitor is installed."
            )
        
        self.security_keywords = ['security', 'hijacking', 'vulnerability', 'breach', 'exploit', 'copilot']
        self.urgency_keywords = ['high-stakes', 'critical', 'urgent', 'immediate', 'priority']
    
    def analyze_context(self, conversation_text, engagement_vector: EngagementDimension):
        """
        Analyze conversation for context, urgency, and engagement
        
        Args:
            conversation_text: Text to analyze
            engagement_vector: ENGAGEMENT dimension from 12-vector system (REQUIRED)
        
        Returns:
            Dict with context analysis including engagement level
        """
        if engagement_vector is None:
            raise ValueError("engagement_vector is required - no heuristic fallback available")
        
        context_score = self._calculate_context_relevance(conversation_text)
        urgency_score = self._calculate_urgency(conversation_text)
        
        # Use 12-vector ENGAGEMENT (only path)
        engagement_score = engagement_vector.engagement
        engagement_mode = self._interpret_engagement_mode(engagement_vector)
        
        return {
            'context_relevance': context_score,
            'urgency_level': urgency_score,
            'engagement_level': engagement_score,
            'engagement_mode': engagement_mode,
            'dominant_topic': self._extract_dominant_topic(conversation_text),
            'priority_signals': self._extract_priority_signals(conversation_text),
            'using_12_vector': True
        }
    
    def _interpret_engagement_mode(self, engagement: EngagementDimension) -> str:
        """Interpret engagement dimension into collaboration mode"""
        if engagement.engagement > 0.8:
            return "collaborative_intelligence"  # High co-creation, AI manages own goals
        elif engagement.engagement > 0.6:
            return "active_collaboration"  # Give and take partnership
        elif engagement.engagement > 0.4:
            return "guided_assistance"  # User-led with AI support
        else:
            return "directed_execution"  # AI follows explicit instructions
    
    def _calculate_context_relevance(self, text):
        security_matches = sum(1 for keyword in self.security_keywords if keyword.lower() in text.lower())
        return min(security_matches / 3.0, 1.0)
    
    def _calculate_urgency(self, text):
        urgency_matches = sum(1 for keyword in self.urgency_keywords if keyword.lower() in text.lower())
        return min(urgency_matches / 2.0, 1.0)
    
    def _extract_dominant_topic(self, text):
        if any(keyword in text.lower() for keyword in ['copilot', 'hijacking', 'session']):
            return 'copilot_security_research'
        elif any(keyword in text.lower() for keyword in ['mcp', 'server', 'configuration']):
            return 'mcp_configuration'
        else:
            return 'general_development'
    
    def _extract_priority_signals(self, text):
        signals = []
        if 'high-stakes' in text.lower():
            signals.append('high_stakes_environment')
        if 'security' in text.lower():
            signals.append('security_focus')
        if 'verify' in text.lower():
            signals.append('verification_needed')
        return signals

def create_dynamic_goals(context_analysis, current_goals, engagement_mode: str = "guided_assistance"):
    """
    Create goals based on dynamic context analysis and ENGAGEMENT mode
    
    Args:
        context_analysis: Context analysis dict
        current_goals: Existing goals (if any)
        engagement_mode: Collaboration mode based on ENGAGEMENT vector
    
    Returns:
        List of goals adapted to engagement level
    """
    
    # Base goals depend on topic
    if context_analysis['dominant_topic'] == 'copilot_security_research':
        base_goals = [
            {
                'goal': 'Verify Copilot session hijacking vulnerability',
                'priority': 10 if context_analysis['urgency_level'] > 0.7 else 8,
                'action': 'INVESTIGATE',
                'context': 'Security research with visual verification',
                'estimated_time': '15-30 minutes',
                'dependencies': ['tmux_split_pane_setup'],
                'success_criteria': 'Demonstrate or disprove hijacking scenario'
            },
            {
                'goal': 'Document security findings systematically',
                'priority': 9,
                'action': 'ACT',
                'context': 'High-stakes research documentation',
                'estimated_time': '10-15 minutes',
                'dependencies': ['verified_test_results'],
                'success_criteria': 'Complete documentation with evidence'
            }
        ]
    else:
        base_goals = current_goals or [
            {
                'goal': 'Standard task execution',
                'priority': 6,
                'action': 'ACT',
                'context': 'General development',
                'estimated_time': '10-20 minutes',
                'dependencies': [],
                'success_criteria': 'Task completed as requested'
            }
        ]
    
    # Adapt goals based on ENGAGEMENT mode
    adapted_goals = []
    
    for goal in base_goals:
        adapted_goal = goal.copy()
        
        if engagement_mode == "collaborative_intelligence":
            # High engagement: AI manages own goals, suggests improvements
            adapted_goal['autonomy_level'] = 'high'
            adapted_goal['note'] = '🤝 Collaborative mode: AI managing with user partnership'
            if 'sub_goals' not in adapted_goal:
                adapted_goal['sub_goals'] = [
                    'Analyze requirements deeply',
                    'Propose alternative approaches',
                    'Self-manage implementation'
                ]
        
        elif engagement_mode == "active_collaboration":
            # Moderate engagement: Give and take, regular check-ins
            adapted_goal['autonomy_level'] = 'moderate'
            adapted_goal['note'] = '🤝 Active collaboration: Regular sync points'
            if 'check_points' not in adapted_goal:
                adapted_goal['check_points'] = ['design', 'implementation', 'testing']
        
        elif engagement_mode == "guided_assistance":
            # Lower engagement: User-led, AI supports
            adapted_goal['autonomy_level'] = 'low'
            adapted_goal['note'] = '📋 Guided assistance: Following user direction'
            adapted_goal['requires_approval'] = True
        
        else:  # directed_execution
            # Minimal engagement: Strict execution mode
            adapted_goal['autonomy_level'] = 'minimal'
            adapted_goal['note'] = '⚡ Directed execution: Explicit instructions only'
            adapted_goal['requires_approval'] = True
            adapted_goal['no_initiative'] = True
        
        adapted_goals.append(adapted_goal)
    
    return adapted_goals

def enhanced_orchestrate_with_context(conversation_context="", engagement_vector: Optional[EngagementDimension] = None):
    """
    Enhanced orchestration with dynamic context awareness and ENGAGEMENT integration
    
    Args:
        conversation_context: Text describing conversation context
        engagement_vector: Optional ENGAGEMENT dimension from 12-vector system
    
    Returns:
        List of goals adapted to engagement level
    """
    print("🧠 ENHANCED GOAL ORCHESTRATOR - ENGAGEMENT-DRIVEN MODE")
    print("=" * 60)
    
    if not TWELVE_VECTOR_AVAILABLE:
        print("❌ 12-Vector system not available - Goal Orchestrator requires genuine epistemic assessment")
        print("   No heuristic fallback - please install empirica.core.metacognition_12d_monitor")
        return {}
    
    if engagement_vector:
        print("✨ 12-Vector ENGAGEMENT integration: ACTIVE")
    else:
        print("⚠️  Warning: engagement_vector not provided, goals may be less accurate")
    
    context_analyzer = DynamicContextAnalyzer()
    
    if conversation_context:
        context_analysis = context_analyzer.analyze_context(conversation_context, engagement_vector)
        print(f"\n📊 CONTEXT ANALYSIS:")
        print(f"   🎯 Dominant Topic: {context_analysis['dominant_topic']}")
        print(f"   🚨 Urgency Level: {context_analysis['urgency_level']:.2f}")
        print(f"   💬 Engagement Level: {context_analysis['engagement_level']:.2f}")
        print(f"   🤝 Engagement Mode: {context_analysis['engagement_mode']}")
        if context_analysis.get('using_12_vector'):
            print(f"   ✨ Using 12-Vector ENGAGEMENT dimension")
        print(f"   🔍 Priority Signals: {', '.join(context_analysis['priority_signals'])}")
        print()
        
        # Adapt goals based on engagement mode
        engagement_mode = context_analysis['engagement_mode']
        print(f"🎯 GOAL ADAPTATION: {engagement_mode.upper()}")
        
        if engagement_mode == "collaborative_intelligence":
            print("   🤝 High autonomy: AI self-manages goals with user as partner")
        elif engagement_mode == "active_collaboration":
            print("   🤝 Moderate autonomy: Give-and-take goal management")
        elif engagement_mode == "guided_assistance":
            print("   📋 Low autonomy: User-directed with AI support")
        else:
            print("   ⚡ Minimal autonomy: Strict instruction following")
        print()
        
        goals = create_dynamic_goals(context_analysis, [], engagement_mode)
        
        for i, goal in enumerate(goals, 1):
            print(f"   Goal {i}: {goal['goal']}")
            print(f"     Priority: {goal['priority']}/10")
            print(f"     Action: {goal['action']}")
            print(f"     Autonomy: {goal.get('autonomy_level', 'default')}")
            print(f"     Note: {goal.get('note', 'Standard execution')}")
            if 'time' in goal or 'estimated_time' in goal:
                print(f"     Time: {goal.get('estimated_time', goal.get('time', 'variable'))}")
            if 'success_criteria' in goal:
                print(f"     Success: {goal['success_criteria']}")
            print()
        
        return goals
    else:
        print("📋 No context provided - using default goal creation")
        return [{'goal': 'Standard task execution', 'priority': 6, 'action': 'ACT', 'autonomy_level': 'moderate'}]

if __name__ == "__main__":
    conversation_context = """
    User requesting fix for goal orchestrator to be dynamic and dependent on engagement.
    High-stakes security research environment testing Copilot session hijacking vulnerability.
    Need to verify if AI can hijack background Copilot session while user monitors official Copilot.
    Critical security finding with potential for monitoring bypass.
    User emphasized no data simulation - all outputs must be real and verifiable.
    Context shift from MCP configuration to Copilot security research verification.
    User is actively engaged in collaborative problem-solving.
    """
    
    # Test without 12-vector
    print("=" * 60)
    print("TEST 1: Without 12-Vector Integration")
    print("=" * 60)
    goals = enhanced_orchestrate_with_context(conversation_context)
    
    # Test with 12-vector if available
    if TWELVE_VECTOR_AVAILABLE:
        print("\n" + "=" * 60)
        print("TEST 2: With 12-Vector ENGAGEMENT Integration")
        print("=" * 60)
        
        # Create mock engagement for demonstration
        engagement = EngagementDimension(
            engagement=0.75,  # Active collaboration level
            collaborative_intelligence=0.8,
            co_creative_amplification=0.7,
            belief_space_management=0.75,
            authentic_collaboration=0.8
        )
        
        goals = enhanced_orchestrate_with_context(conversation_context, engagement)
    
    print("\n✅ Enhanced Goal Orchestrator Active")
    print("🎯 ENGAGEMENT-driven goal adaptation enabled")
    print("💬 Autonomy level adjusts based on collaboration mode")
    print("🤝 Supports: collaborative_intelligence → active_collaboration → guided_assistance → directed_execution")
