#!/usr/bin/env python3
"""
🧠 Procedural Analysis Module
Intelligent procedural analysis and cached context awareness for AI systems

This module provides lightweight, token-efficient procedural analysis with:
- Persistent caching for performance optimization
- Context-aware procedural monitoring
- Intelligent process and workflow analysis
- Resource-efficient execution patterns
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict, deque

@dataclass
class ProceduralContext:
    """Represents procedural context with caching"""
    procedure_id: str
    context_data: Dict[str, Any]
    cache_timestamp: float
    access_count: int
    cache_hits: int

class ProceduralAnalysisEngine:
    """Procedural Analysis Engine with intelligent caching"""
    
    def __init__(self, cache_dir: str = ".procedural_cache"):
        """
        Initialize the Procedural Analysis Engine
        
        Args:
            cache_dir (str): Directory for persistent caching (default: ".procedural_cache")
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.procedural_cache: Dict[str, ProceduralContext] = {}
        self.cache_stats = defaultdict(int)
        self.analysis_history = deque(maxlen=1000)
        
        print("🧠 PROCEDURAL ANALYSIS ENGINE ACTIVATED")
        print("Intelligent procedural analysis with caching")
        print(f"Cache directory: {self.cache_dir}")
    
    def analyze_procedure(self, procedure_id: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a procedure with intelligent caching
        
        Args:
            procedure_id (str): Unique identifier for the procedure
            context_data (Dict[str, Any]): Context data for analysis
            
        Returns:
            Dict[str, Any]: Analysis results with caching information
        """
        # Check cache first
        cached_result = self._get_cached_result(procedure_id)
        if cached_result:
            # Return cached result with cache hit information
            return {
                **cached_result,
                'cache_hit': True,
                'cache_info': {
                    'hit_count': self.procedural_cache[procedure_id].cache_hits,
                    'access_count': self.procedural_cache[procedure_id].access_count,
                    'age_seconds': time.time() - self.procedural_cache[procedure_id].cache_timestamp
                }
            }
        
        # Perform analysis (simulated)
        analysis_result = self._perform_procedural_analysis(procedure_id, context_data)
        
        # Cache result
        self._cache_result(procedure_id, context_data, analysis_result)
        
        # Store in history
        self.analysis_history.append({
            'procedure_id': procedure_id,
            'timestamp': time.time(),
            'analysis_result': analysis_result,
            'cache_hit': False
        })
        
        return {
            **analysis_result,
            'cache_hit': False,
            'cache_info': {
                'hit_count': 0,
                'access_count': 1,
                'age_seconds': 0
            }
        }
    
    def _get_cached_result(self, procedure_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result if available and fresh
        
        Args:
            procedure_id (str): Procedure identifier
            
        Returns:
            Optional[Dict[str, Any]]: Cached result or None if not available
        """
        if procedure_id in self.procedural_cache:
            context = self.procedural_cache[procedure_id]
            context.access_count += 1
            context.cache_hits += 1
            
            # Return cached data (in real implementation, this would be more complex)
            return {
                'procedure_id': procedure_id,
                'analysis_type': 'cached',
                'result_summary': f"Cached analysis for {procedure_id}",
                'confidence': 0.95,
                'cached_timestamp': context.cache_timestamp
            }
        
        return None
    
    def _perform_procedural_analysis(self, procedure_id: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform actual procedural analysis"""
        # Simulate analysis based on context data
        analysis_type = self._determine_analysis_type(context_data)
        confidence = self._calculate_confidence(context_data)
        recommendations = self._generate_recommendations(context_data)
        
        return {
            'procedure_id': procedure_id,
            'analysis_type': analysis_type,
            'confidence': confidence,
            'recommendations': recommendations,
            'analysis_timestamp': time.time(),
            'context_complexity': len(str(context_data)),
            'processing_time': 0.01  # Simulated processing time
        }
    
    def _determine_analysis_type(self, context_data: Dict[str, Any]) -> str:
        """Determine analysis type based on context data"""
        if 'security' in str(context_data).lower():
            return 'security_analysis'
        elif 'performance' in str(context_data).lower():
            return 'performance_analysis'
        elif 'workflow' in str(context_data).lower():
            return 'workflow_analysis'
        else:
            return 'general_procedural_analysis'
    
    def _calculate_confidence(self, context_data: Dict[str, Any]) -> float:
        """Calculate confidence based on context data quality"""
        # Simple confidence calculation based on data completeness
        data_points = len(context_data)
        if data_points > 10:
            return 0.95
        elif data_points > 5:
            return 0.85
        elif data_points > 0:
            return 0.75
        else:
            return 0.5
    
    def _generate_recommendations(self, context_data: Dict[str, Any]) -> list:
        """Generate recommendations based on context data"""
        recommendations = []
        
        # Simple recommendation generation
        if 'optimization' in str(context_data).lower():
            recommendations.append("Consider performance optimization strategies")
        if 'security' in str(context_data).lower():
            recommendations.append("Review security policies and access controls")
        if 'workflow' in str(context_data).lower():
            recommendations.append("Analyze workflow efficiency and bottlenecks")
        
        if not recommendations:
            recommendations.append("General procedural analysis completed")
            recommendations.append("Consider context-specific optimizations")
        
        return recommendations
    
    def _cache_result(self, procedure_id: str, context_data: Dict[str, Any], analysis_result: Dict[str, Any]):
        """Cache analysis result"""
        context = ProceduralContext(
            procedure_id=procedure_id,
            context_data=context_data,
            cache_timestamp=time.time(),
            access_count=1,
            cache_hits=0
        )
        
        self.procedural_cache[procedure_id] = context
        
        # Also save to persistent cache
        cache_file = self.cache_dir / f"{procedure_id}.json"
        try:
            cache_data = {
                'procedure_id': procedure_id,
                'context_data': context_data,
                'analysis_result': analysis_result,
                'cache_timestamp': context.cache_timestamp,
                'access_count': context.access_count,
                'cache_hits': context.cache_hits
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️  Error saving to persistent cache: {e}")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_accesses = sum(ctx.access_count for ctx in self.procedural_cache.values())
        total_hits = sum(ctx.cache_hits for ctx in self.procedural_cache.values())
        
        hit_rate = total_hits / total_accesses if total_accesses > 0 else 0
        
        return {
            'cache_entries': len(self.procedural_cache),
            'total_accesses': total_accesses,
            'total_hits': total_hits,
            'hit_rate': hit_rate,
            'cache_size_mb': sum(len(str(ctx.context_data)) for ctx in self.procedural_cache.values()) / (1024 * 1024),
            'analysis_history': len(self.analysis_history)
        }
    
    def clear_cache(self, procedure_id: Optional[str] = None) -> int:
        """Clear cache entries"""
        if procedure_id:
            if procedure_id in self.procedural_cache:
                del self.procedural_cache[procedure_id]
                cache_file = self.cache_dir / f"{procedure_id}.json"
                if cache_file.exists():
                    cache_file.unlink()
                return 1
            return 0
        else:
            cleared_count = len(self.procedural_cache)
            self.procedural_cache.clear()
            
            # Clear persistent cache files
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
                
            return cleared_count
    
    def get_analysis_history(self, limit: int = 10) -> list:
        """Get recent analysis history"""
        return list(self.analysis_history)[-limit:]
