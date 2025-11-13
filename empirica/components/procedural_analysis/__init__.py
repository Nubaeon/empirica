#!/usr/bin/env python3
"""
🧠 Procedural Analysis Module
Intelligent procedural analysis and cached context awareness for AI systems
"""

from .procedural_analysis import (
    ProceduralContext,
    ProceduralAnalysisEngine
)

def create_procedural_analyzer(cache_dir: str = ".procedural_cache") -> ProceduralAnalysisEngine:
    """
    Create a Procedural Analysis Engine instance
    
    Args:
        cache_dir (str): Directory for persistent caching
        
    Returns:
        ProceduralAnalysisEngine: Instance of the procedural analyzer
    """
    return ProceduralAnalysisEngine(cache_dir)

def activate_procedural_analysis(cache_dir: str = ".procedural_cache") -> ProceduralAnalysisEngine:
    """
    Activate procedural analysis with intelligent caching
    
    Args:
        cache_dir (str): Directory for persistent caching
        
    Returns:
        ProceduralAnalysisEngine: Active procedural analysis engine
    """
    print("🧠 ACTIVATING PROCEDURAL ANALYSIS")
    print("=" * 35)
    print("✅ Lightweight procedural analysis")
    print("✅ Token-efficient caching")
    print("✅ Context-aware monitoring")
    print("✅ Performance optimization")
    
    return ProceduralAnalysisEngine(cache_dir)

__all__ = [
    'ProceduralContext',
    'ProceduralAnalysisEngine',
    'create_procedural_analyzer',
    'activate_procedural_analysis'
]

__version__ = "1.0.0"
__component__ = "procedural_analysis"
__purpose__ = "Intelligent procedural analysis and cached context awareness for AI systems"

print(f"🧠 Procedural analysis ready for AI collaboration!")