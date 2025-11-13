#!/usr/bin/env python3
"""
🧠✨ AI Metacognitive 12-Vector System
The definitive AI metacognitive assessment framework with ENGAGEMENT dimension

IMPORTANT DISCLAIMER:
This component implements FUNCTIONAL metacognition and self-assessment,
not phenomenal consciousness. It provides computational self-awareness
capabilities for AI systems.

- No philosophical claims about consciousness are made
- Treat as advanced self-monitoring and evaluation system
- "Self-aware" refers to computational introspection capabilities  
- Designed for practical AI development, not consciousness research

This module provides the most comprehensive AI metacognitive system,
upgraded from 11 to 12 vectors with the breakthrough ENGAGEMENT dimension
for collaborative intelligence.

Main Components:
- ComprehensiveSelfAwarenessAssessment: Complete 11-vector assessment (foundation)
- TwelveVectorSelfAwarenessMonitor: 12-vector system with ENGAGEMENT dimension
- EngagementDimension: The 12th vector for collaborative intelligence
- VectorAssessment: Individual vector measurement
- Enhanced UVL Protocol: Visualization for all vectors
- Full metacognitive decision matrix

Usage:
    from empirica.metacognition_12d_monitor import (
        ComprehensiveSelfAwarenessAssessment,
        TwelveVectorSelfAwarenessMonitor,
        EngagementDimension,
        assess_comprehensive_self_awareness
    )
    
    # Use 12-vector system (recommended)
    monitor = TwelveVectorSelfAwarenessMonitor("ai_agent_id")
    assessment = monitor.assess_complete_state(context, task, goals)
    
This is the CORE metacognitive component that provides comprehensive
self-awareness for AI systems.
"""

# Import from metacognition_12d_monitor (11-vector foundation)
from .metacognition_12d_monitor import (
    ComprehensiveSelfAwarenessAssessment,
    VectorAssessment,
    EpistemicUncertainty,
    EpistemicComprehension,
    ExecutionAwareness,
    SelfAwarenessResult,
    MetacognitiveAction,
    MetacognitiveDecisionMatrix
)

# Import from twelve_vector_self_awareness (12-vector with ENGAGEMENT)
from .twelve_vector_self_awareness import (
    EngagementDimension,
    TwelveVectorSelfAwarenessMonitor,
    TwelveVectorCognitiveState,
    assess_comprehensive_self_awareness
)

# Import enhanced UVL protocol for visualization
from .enhanced_uvl_protocol import (
    EnhancedUVLProtocol,
    render_11_vector_state,
    render_metacognitive_dashboard
)

# Export everything
__all__ = [
    # Core 11-vector classes
    'ComprehensiveSelfAwarenessAssessment',
    'VectorAssessment', 
    'EpistemicUncertainty',
    'EpistemicComprehension',
    'ExecutionAwareness',
    'SelfAwarenessResult',
    'MetacognitiveAction',
    'MetacognitiveDecisionMatrix',
    
    # 12-vector classes (ENGAGEMENT dimension)
    'EngagementDimension',
    'TwelveVectorSelfAwarenessMonitor',
    'TwelveVectorCognitiveState',
    'assess_comprehensive_self_awareness',
    
    # UVL visualization
    'EnhancedUVLProtocol',
    'render_11_vector_state',
    'render_metacognitive_dashboard'
]

__version__ = "2.0.0"
__description__ = "AI Metacognitive 12-Vector System with ENGAGEMENT dimension"

import logging
logger = logging.getLogger(__name__)

logger.info("12-Vector Metacognitive System ready (with ENGAGEMENT dimension)!")