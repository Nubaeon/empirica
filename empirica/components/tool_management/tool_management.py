#!/usr/bin/env python3
"""
🛠️🧠 Standalone AI-Enhanced Tool Management
Clean, sanitized tool management system with no external dependencies

This is a completely self-contained tool management system for open source distribution.
No filesystem references, no project-specific paths, no proprietary connections.

Features:
- AI-enhanced tool discovery and recommendation
- Usage pattern learning (with safety limits)
- Context-aware tool selection
- Predictive performance assessment
- Completely standalone operation
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

class ToolIntelligenceLevel(Enum):
    """Intelligence levels for AI-enhanced tool management"""
    BASIC = "basic"
    ADAPTIVE = "adaptive"
    PREDICTIVE = "predictive"
    COLLABORATIVE = "collaborative"
    AUTONOMOUS = "autonomous"

@dataclass
class ToolUsagePattern:
    """Pattern analysis for tool usage by AI systems"""
    tool_id: str
    ai_id: str
    usage_frequency: float
    success_rate: float
    average_duration: float
    context_patterns: List[str] = field(default_factory=list)
    performance_trend: str = "stable"  # improving, stable, declining
    last_used: Optional[float] = None

@dataclass
class ToolRecommendation:
    """AI-generated tool recommendation"""
    tool_id: str
    confidence_score: float
    reasoning: List[str]
    estimated_benefit: float
    context_match: float
    usage_prediction: float

@dataclass
class ToolRegistryEntry:
    """Registry entry for a tool"""
    tool_id: str
    name: str
    description: str
    category: str
    capabilities: List[str]
    usage_count: int = 0
    success_rate: float = 1.0
    last_used: Optional[float] = None

class StandaloneToolRegistry:
    """Standalone tool registry with no external dependencies"""
    
    def __init__(self):
        self.tools = {}
        self.categories = set()
        
        # Initialize with safe, generic tools
        self._initialize_default_tools()
    
    def _initialize_default_tools(self):
        """Initialize with the actual, mappable tools the system uses."""
        default_tools = [
            {
                "tool_id": "workspace_scanner",
                "name": "Workspace Scanner", 
                "description": "Scans the workspace to assess the environment state.",
                "category": "workspace",
                "capabilities": ["workspace_scan", "state_mapping", "inventory", "environment_check"]
            },
            {
                "tool_id": "knowledge_retriever",
                "name": "Knowledge Retriever",
                "description": "Retrieves knowledge to address 'know' gaps.", 
                "category": "knowledge",
                "capabilities": ["knowledge_retrieval", "research", "documentation"]
            },
            {
                "tool_id": "goal_analyzer",
                "name": "Goal Analyzer",
                "description": "Analyzes and creates goals.",
                "category": "planning",
                "capabilities": ["goal_creation", "priority_analysis"]
            },
            {
                "tool_id": "state_mapper",
                "name": "State Mapper",
                "description": "Performs a deep scan to map system state.",
                "category": "workspace",
                "capabilities": ["state_mapping", "inventory"]
            },
            {
                "tool_id": "calibrator",
                "name": "Uncertainty Calibrator",
                "description": "Assesses and calibrates uncertainty.",
                "category": "metacognition",
                "capabilities": ["capability_assessment", "state_validation", "context_validation"]
            },
            {
                "tool_id": "engagement_analyzer",
                "name": "Engagement Analyzer",
                "description": "Analyzes engagement and orchestrates goals.",
                "category": "metacognition",
                "capabilities": ["collaboration_analysis", "goal_creation"]
            }
        ]
        
        for tool_data in default_tools:
            entry = ToolRegistryEntry(**tool_data)
            self.tools[tool_data["tool_id"]] = entry
            self.categories.add(tool_data["category"])
    
    def register_tool(self, tool_data: Dict[str, Any]) -> bool:
        """Register a new tool (safe operation)"""
        required_fields = ["tool_id", "name", "description", "category", "capabilities"]
        
        if not all(field in tool_data for field in required_fields):
            return False
        
        # Sanitize tool_id to prevent path traversal
        tool_id = str(tool_data["tool_id"]).replace("/", "_").replace("\\", "_").replace("..", "_")
        
        entry = ToolRegistryEntry(
            tool_id=tool_id,
            name=str(tool_data["name"])[:100],  # Limit length
            description=str(tool_data["description"])[:500],  # Limit length
            category=str(tool_data["category"])[:50],  # Limit length
            capabilities=[str(cap)[:50] for cap in tool_data["capabilities"][:10]]  # Limit count and length
        )
        
        self.tools[tool_id] = entry
        self.categories.add(entry.category)
        return True
    
    def get_tools_by_category(self, category: str) -> List[ToolRegistryEntry]:
        """Get tools by category"""
        return [tool for tool in self.tools.values() if tool.category == category]
    
    def search_tools(self, query: str) -> List[ToolRegistryEntry]:
        """Search tools by name or description"""
        query_lower = query.lower()
        matches = []
        
        for tool in self.tools.values():
            if (query_lower in tool.name.lower() or 
                query_lower in tool.description.lower() or
                any(query_lower in cap.lower() for cap in tool.capabilities)):
                matches.append(tool)
        
        return matches
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        return {
            "total_tools": len(self.tools),
            "categories": list(self.categories),
            "most_used_tools": sorted(
                self.tools.values(), 
                key=lambda t: t.usage_count, 
                reverse=True
            )[:5]
        }

class AIEnhancedToolManager:
    """
    Standalone AI-Enhanced Tool Manager with intelligent capabilities
    
    Features:
    - Learning from tool usage patterns (with safety limits)
    - Predictive tool recommendations
    - Context-aware tool selection
    - Performance optimization
    - Completely standalone operation
    """
    
    def __init__(self, intelligence_level: ToolIntelligenceLevel = ToolIntelligenceLevel.ADAPTIVE):
        self.intelligence_level = intelligence_level
        self.tool_usage_patterns = {}
        self.tool_performance_history = {}
        self.ai_contexts = {}
        self.recommendation_engine = None
        self.tool_registry = StandaloneToolRegistry()
        
        # Safety limits for learning
        self.max_patterns_per_ai = 100  # Prevent memory bloat
        self.max_context_patterns = 20  # Limit context storage
        self.learning_rate_limit = 0.1  # Conservative learning rate
        
        # Enable learning based on intelligence level
        self.learning_enabled = intelligence_level.value in ['adaptive', 'predictive', 'collaborative', 'autonomous']
        self.logger = logging.getLogger("ai_enhanced_tool_manager")
        
        if self.learning_enabled:
            self.recommendation_engine = ToolRecommendationEngine()
            print(f"🧠 AI-Enhanced Tool Manager initialized with {intelligence_level.value} intelligence")
            print(f"🔒 Safety limits: Max {self.max_patterns_per_ai} patterns per AI")
        else:
            print(f"🛠️ Tool Manager initialized with {intelligence_level.value} intelligence (no learning)")
        
    async def analyze_tool_usage_patterns(self, ai_id: str, time_window_hours: int = 24) -> Dict[str, Any]:
        """Analyze tool usage patterns for an AI system (with safety limits)"""
        if not self.learning_enabled:
            return {"analysis": "disabled", "intelligence_level": self.intelligence_level.value}
        
        # Sanitize ai_id
        ai_id = str(ai_id).replace("/", "_").replace("\\", "_")[:50]
        
        ai_usage = [p for p in self.tool_usage_patterns.values() if p.ai_id == ai_id]
        
        if not ai_usage:
            return {"patterns": "insufficient_data", "recommendations": []}
        
        # Analyze usage frequency (limited scope)
        tool_frequencies = {}
        for pattern in ai_usage[:self.max_patterns_per_ai]:  # Safety limit
            tool_frequencies[pattern.tool_id] = pattern.usage_frequency
        
        # Identify most/least used tools
        sorted_tools = sorted(tool_frequencies.items(), key=lambda x: x[1], reverse=True)
        
        analysis = {
            "ai_id": ai_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "total_tools_used": len(sorted_tools),
            "most_used_tools": sorted_tools[:5],  # Top 5 only
            "least_used_tools": sorted_tools[-5:],  # Bottom 5 only
            "usage_efficiency": await self._calculate_usage_efficiency(ai_usage),
            "performance_trends": await self._analyze_performance_trends(ai_usage),
            "context_insights": await self._extract_context_insights(ai_usage),
            "safety_limits_applied": True
        }
        
        return analysis
    
    async def get_intelligent_tool_recommendations(self, ai_id: str, current_context: Dict[str, Any]) -> List[ToolRecommendation]:
        """Get AI-powered tool recommendations based on context and patterns"""
        if not self.recommendation_engine:
            # Fallback to registry-based recommendations
            return await self._get_registry_recommendations(current_context)
        
        # Sanitize inputs
        ai_id = str(ai_id).replace("/", "_").replace("\\", "_")[:50]
        
        return await self.recommendation_engine.generate_recommendations(
            ai_id, current_context, self.tool_usage_patterns, self.tool_registry
        )
    
    async def _get_registry_recommendations(self, context: Dict[str, Any]) -> List[ToolRecommendation]:
        """
        Get recommendations from tool registry based on required capabilities.
        This is the default logic when no learned patterns are available.
        """
        recommendations = []
        required_capabilities = context.get('required_capabilities', [])
        
        if not required_capabilities:
            return []

        # Find tools that match the required capabilities
        for tool in self.tool_registry.tools.values():
            matched_capabilities = [cap for cap in required_capabilities if cap in tool.capabilities]
            
            if matched_capabilities:
                # Simple confidence score based on the number of matched capabilities
                confidence = 0.6 + (len(matched_capabilities) * 0.1)
                
                recommendation = ToolRecommendation(
                    tool_id=tool.tool_id,
                    confidence_score=min(confidence, 0.9),  # Cap confidence
                    reasoning=[
                        "Registry-based recommendation",
                        f"Matches capabilities: {', '.join(matched_capabilities)}"
                    ],
                    estimated_benefit=0.5, # Static benefit for now
                    context_match=confidence,
                    usage_prediction=0.5 # Static prediction for now
                )
                recommendations.append(recommendation)
        
        # Sort by confidence and return top 5
        recommendations.sort(key=lambda r: r.confidence_score, reverse=True)
        return recommendations[:5]
    
    async def predict_tool_performance(self, tool_id: str, ai_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Predict tool performance based on historical data and context (with safety limits)"""
        if not self.learning_enabled:
            return {"prediction": "unavailable", "reason": "learning_disabled"}
        
        # Sanitize inputs
        tool_id = str(tool_id).replace("/", "_").replace("\\", "_")[:50]
        ai_id = str(ai_id).replace("/", "_").replace("\\", "_")[:50]
        
        # Get historical performance
        pattern_key = f"{ai_id}_{tool_id}"
        if pattern_key not in self.tool_usage_patterns:
            return {
                "prediction": "insufficient_data",
                "confidence": 0.0,
                "recommendation": "try_with_monitoring"
            }
        
        pattern = self.tool_usage_patterns[pattern_key]
        
        # Simple prediction based on historical success rate and context match
        context_match = await self._calculate_context_match(pattern.context_patterns, context)
        
        # Conservative prediction with safety limits
        predicted_success_rate = min(pattern.success_rate * (0.7 + 0.3 * context_match), 0.95)  # Cap at 95%
        predicted_duration = max(pattern.average_duration * (1.0 + (1.0 - context_match) * 0.5), 0.1)  # Min 0.1s
        
        return {
            "tool_id": tool_id,
            "ai_id": ai_id,
            "predicted_success_rate": predicted_success_rate,
            "predicted_duration": predicted_duration,
            "confidence": min(pattern.success_rate * context_match, 0.9),  # Cap confidence
            "context_match_score": context_match,
            "recommendation": "proceed" if predicted_success_rate > 0.7 else "caution_advised",
            "safety_limited": True
        }
    
    async def learn_from_tool_usage(self, ai_id: str, tool_id: str, usage_result: Dict[str, Any]):
        """Learn from tool usage to improve future recommendations (with safety limits)"""
        if not self.learning_enabled:
            return
        
        # Sanitize inputs
        ai_id = str(ai_id).replace("/", "_").replace("\\", "_")[:50]
        tool_id = str(tool_id).replace("/", "_").replace("\\", "_")[:50]
        
        # Check safety limits
        ai_pattern_count = len([p for p in self.tool_usage_patterns.values() if p.ai_id == ai_id])
        if ai_pattern_count >= self.max_patterns_per_ai:
            self.logger.warning(f"Pattern limit reached for AI {ai_id}, skipping learning")
            return
        
        pattern_key = f"{ai_id}_{tool_id}"
        
        # Update or create usage pattern
        if pattern_key not in self.tool_usage_patterns:
            self.tool_usage_patterns[pattern_key] = ToolUsagePattern(
                tool_id=tool_id,
                ai_id=ai_id,
                usage_frequency=1.0,
                success_rate=1.0 if usage_result.get('success', False) else 0.0,
                average_duration=max(0.0, min(float(usage_result.get('duration', 1.0)), 3600.0)),  # Cap at 1 hour
                context_patterns=[],
                last_used=time.time()
            )
        else:
            pattern = self.tool_usage_patterns[pattern_key]
            
            # Update metrics with conservative learning rate
            pattern.usage_frequency += 1
            
            if 'success' in usage_result:
                new_success = 1.0 if usage_result['success'] else 0.0
                pattern.success_rate = (1 - self.learning_rate_limit) * pattern.success_rate + self.learning_rate_limit * new_success
            
            if 'duration' in usage_result:
                # Sanitize duration
                duration = max(0.0, min(float(usage_result['duration']), 3600.0))
                pattern.average_duration = (1 - self.learning_rate_limit) * pattern.average_duration + self.learning_rate_limit * duration
            
            # Update context patterns (with limits)
            if 'context' in usage_result and len(pattern.context_patterns) < self.max_context_patterns:
                context_str = str(usage_result['context'])[:200]  # Limit context string length
                if context_str not in pattern.context_patterns:
                    pattern.context_patterns.append(context_str)
            
            pattern.last_used = time.time()
        
        # Log learning event (sanitized)
        self.logger.info(f"Learned from {ai_id} using {tool_id}: success={usage_result.get('success', 'unknown')}")
    
    async def optimize_tool_access_for_ai(self, ai_id: str) -> Dict[str, Any]:
        """Optimize tool access patterns for specific AI based on learning (with safety limits)"""
        if not self.learning_enabled:
            return {"optimization": "disabled"}
        
        # Sanitize ai_id
        ai_id = str(ai_id).replace("/", "_").replace("\\", "_")[:50]
        
        ai_patterns = [p for p in self.tool_usage_patterns.values() if p.ai_id == ai_id]
        
        if not ai_patterns:
            return {"optimization": "insufficient_data"}
        
        optimizations = {
            "ai_id": ai_id,
            "optimizations_applied": [],
            "performance_improvements": {},
            "recommendations": [],
            "safety_limited": True
        }
        
        # Identify underperforming tools (limited analysis)
        poor_performers = [p for p in ai_patterns[:20] if p.success_rate < 0.6]  # Limit to 20 patterns
        for pattern in poor_performers[:5]:  # Limit recommendations
            optimizations["recommendations"].append(
                f"Consider alternative to {pattern.tool_id} (success rate: {pattern.success_rate:.2f})"
            )
        
        # Identify highly efficient tools (limited analysis)
        top_performers = [p for p in ai_patterns[:20] if p.success_rate > 0.9 and p.usage_frequency > 5]
        for pattern in top_performers[:5]:  # Limit recommendations
            optimizations["recommendations"].append(
                f"Leverage {pattern.tool_id} more frequently (excellent performance: {pattern.success_rate:.2f})"
            )
        
        return optimizations
    
    async def _calculate_usage_efficiency(self, usage_patterns: List[ToolUsagePattern]) -> float:
        """Calculate overall usage efficiency for an AI (with safety limits)"""
        if not usage_patterns:
            return 0.0
        
        # Limit analysis to prevent computational overload
        limited_patterns = usage_patterns[:50]
        
        total_weighted_success = sum(p.success_rate * min(p.usage_frequency, 100) for p in limited_patterns)
        total_frequency = sum(min(p.usage_frequency, 100) for p in limited_patterns)
        
        return total_weighted_success / max(total_frequency, 1.0)
    
    async def _analyze_performance_trends(self, usage_patterns: List[ToolUsagePattern]) -> Dict[str, Any]:
        """Analyze performance trends across tools (with safety limits)"""
        trends = {
            "improving": [],
            "stable": [],
            "declining": []
        }
        
        # Limit analysis scope
        for pattern in usage_patterns[:20]:
            trends[pattern.performance_trend].append(pattern.tool_id)
        
        return trends
    
    async def _extract_context_insights(self, usage_patterns: List[ToolUsagePattern]) -> Dict[str, Any]:
        """Extract insights about context-tool relationships (with safety limits)"""
        context_tool_map = {}
        
        # Limit analysis scope
        for pattern in usage_patterns[:20]:
            for context in pattern.context_patterns[:5]:  # Limit contexts per pattern
                if len(context_tool_map) >= 50:  # Global limit
                    break
                if context not in context_tool_map:
                    context_tool_map[context] = []
                if len(context_tool_map[context]) < 10:  # Limit tools per context
                    context_tool_map[context].append(pattern.tool_id)
        
        return {
            "context_specific_tools": len(context_tool_map) > 0,
            "context_diversity": len(context_tool_map),
            "most_common_contexts": list(context_tool_map.keys())[:5],
            "safety_limited": True
        }
    
    async def _calculate_context_match(self, historical_contexts: List[str], current_context: Dict[str, Any]) -> float:
        """Calculate how well current context matches historical usage patterns (with safety limits)"""
        if not historical_contexts:
            return 0.5  # Neutral when no historical data
        
        current_context_str = str(current_context)[:200]  # Limit context string length
        
        # Simple string similarity (safe implementation)
        max_similarity = 0.0
        for hist_context in historical_contexts[:10]:  # Limit context checking
            # Calculate simple similarity based on common words
            hist_words = set(hist_context.lower().split()[:20])  # Limit words
            curr_words = set(current_context_str.lower().split()[:20])  # Limit words
            
            if hist_words and curr_words:
                similarity = len(hist_words.intersection(curr_words)) / len(hist_words.union(curr_words))
                max_similarity = max(max_similarity, similarity)
        
        return min(max_similarity, 0.9)  # Cap similarity score

class ToolRecommendationEngine:
    """AI-powered tool recommendation engine (with safety limits)"""
    
    def __init__(self):
        self.recommendation_history = []
        self.success_feedback = {}
        self.max_history_size = 100  # Limit history storage
    
    async def generate_recommendations(self, ai_id: str, context: Dict[str, Any], 
                                     usage_patterns: Dict[str, ToolUsagePattern],
                                     tool_registry: 'StandaloneToolRegistry') -> List[ToolRecommendation]:
        """Generate intelligent tool recommendations (with safety limits)"""
        recommendations = []
        
        # Get patterns for this AI (limited scope)
        ai_patterns = [p for p in usage_patterns.values() if p.ai_id == ai_id][:20]  # Limit to 20 patterns
        
        if not ai_patterns:
            # Cold start - recommend based on registry and capabilities
            return await self._generate_cold_start_recommendations(context, tool_registry)
        
        # Analyze context and generate recommendations (limited scope)
        for pattern in ai_patterns:
            if pattern.success_rate > 0.7:  # Only recommend successful tools
                context_match = await self._calculate_context_relevance(pattern, context)
                
                if context_match > 0.5:  # Threshold for relevance
                    recommendation = ToolRecommendation(
                        tool_id=pattern.tool_id,
                        confidence_score=min(pattern.success_rate * context_match, 0.9),  # Cap confidence
                        reasoning=[
                            f"High success rate: {pattern.success_rate:.2f}",
                            f"Good context match: {context_match:.2f}",
                            f"Used {min(pattern.usage_frequency, 999)} times"
                        ],
                        estimated_benefit=min(pattern.success_rate * context_match * 0.8, 0.9),  # Cap benefit
                        context_match=context_match,
                        usage_prediction=min(pattern.usage_frequency / 10.0, 1.0)  # Normalize and cap
                    )
                    recommendations.append(recommendation)
        
        # Sort by confidence score and limit results
        recommendations.sort(key=lambda r: r.confidence_score, reverse=True)
        
        # Update history (with size limit)
        if len(self.recommendation_history) >= self.max_history_size:
            self.recommendation_history.pop(0)  # Remove oldest
        
        self.recommendation_history.append({
            'ai_id': ai_id,
            'timestamp': time.time(),
            'recommendations_count': len(recommendations)
        })
        
        return recommendations[:5]  # Top 5 recommendations
    
    async def _generate_cold_start_recommendations(self, context: Dict[str, Any], tool_registry: 'StandaloneToolRegistry') -> List[ToolRecommendation]:
        """Generate recommendations for new AIs by searching the registry for capabilities."""
        recommendations = []
        required_capabilities = context.get('required_capabilities', [])
        
        if not required_capabilities:
            return []

        # Find tools that match the required capabilities
        for tool in tool_registry.tools.values():
            matched_capabilities = [cap for cap in required_capabilities if cap in tool.capabilities]
            
            if matched_capabilities:
                confidence = 0.6 + (len(matched_capabilities) * 0.1)
                recommendation = ToolRecommendation(
                    tool_id=tool.tool_id,
                    confidence_score=min(confidence, 0.9),
                    reasoning=[
                        "Registry-based cold start recommendation",
                        f"Matches capabilities: {', '.join(matched_capabilities)}"
                    ],
                    estimated_benefit=0.5,
                    context_match=confidence,
                    usage_prediction=0.5
                )
                recommendations.append(recommendation)
        
        recommendations.sort(key=lambda r: r.confidence_score, reverse=True)
        return recommendations[:5]
    
    async def _calculate_context_relevance(self, pattern: ToolUsagePattern, context: Dict[str, Any]) -> float:
        """Calculate how relevant a tool is for the current context (safe implementation)"""
        # Simple implementation with safety limits
        context_str = str(context)[:200].lower()  # Limit context string length
        
        relevance_score = 0.5  # Base relevance
        
        # Check if any historical contexts match (limited scope)
        for hist_context in pattern.context_patterns[:5]:  # Limit context checking
            if any(word in context_str for word in hist_context.lower().split()[:10]):  # Limit word checking
                relevance_score += 0.1
        
        return min(relevance_score, 1.0)  # Cap relevance score
