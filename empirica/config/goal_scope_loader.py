#!/usr/bin/env python3
"""
Goal Scope Loader - Epistemic Vector to Scope Vector Mapping

Part of the Empirica Meta-Agent Configuration Object (MCO) architecture.
Maps epistemic vector patterns to recommended scope vectors for goal setting.

Philosophy:
- NO goal heuristics/templates - AI determines goals, system maps scope vectors
- Based on AI's epistemic state, recommend appropriate scope parameters
- Advisory only - AI/Sentinel can override based on requirements

Usage:
    from empirica.config.goal_scope_loader import get_scope_recommendations
    
    # Get recommendations based on epistemic state
    recommendations = get_scope_recommendations(
        epistemic_vectors={
            'know': 0.85,
            'uncertainty': 0.3,
            'clarity': 0.80,
            ...
        }
    )
    
    # AI can then set scope based on recommendations
    scope_vector = ScopeVector(
        breadth=recommendations['breadth'],
        duration=recommendations['duration'], 
        coordination=recommendations['coordination']
    )

Architecture:
    - Part of MCO: goal_scopes.yaml provides scope recommendations
    - Used by AI during self-assessment for scope determination
    - Sentinel can override for strategic resource allocation
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
import copy

logger = logging.getLogger(__name__)


class GoalScopeLoader:
    """
    Goal scope recommendation engine based on epistemic vectors.
    
    Design:
    - Loads scope recommendations from goal_scopes.yaml
    - Maps epistemic patterns to scope vectors
    - Provides advisory recommendations (AI can override)
    - Includes validation coherence checks
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize goal scope loader.
        
        Args:
            config_path: Optional path to goal_scopes.yaml
        
        Note: Use get_instance() for singleton pattern
        """
        if config_path is None:
            config_path = Path(__file__).parent / 'mco' / 'goal_scopes.yaml'
        
        self.config_path = config_path
        self.scope_recommendations: Dict[str, Dict[str, Any]] = {}
        self.adjustment_rules: Dict[str, Any] = {}
        self.validation_rules: Dict[str, Any] = {}
        
        # Load configurations
        self._load_configurations()
    
    def _load_configurations(self):
        """Load all configurations from YAML"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Goal scope config not found: {self.config_path}")
                self._load_hardcoded_defaults()
                return
            
            with open(self.config_path) as f:
                data = yaml.safe_load(f)
                
                if not data or 'scope_recommendations' not in data:
                    logger.error("Invalid goal scope config: missing 'scope_recommendations'")
                    self._load_hardcoded_defaults()
                    return
                
                self.scope_recommendations = data.get('scope_recommendations', {})
                self.adjustment_rules = data.get('adjustment_rules', {})
                self.validation_rules = data.get('validation_coherence', {})
                
                logger.info(f"✅ Loaded {len(self.scope_recommendations)} scope recommendations")
                
        except Exception as e:
            logger.error(f"Failed to load goal scope config: {e}")
            self._load_hardcoded_defaults()
    
    def _load_hardcoded_defaults(self):
        """Fallback hardcoded recommendations if YAML loading fails"""
        logger.warning("⚠️  Using hardcoded goal scope defaults")
        
        self.scope_recommendations = {
            'knowledge_leader': {
                'epistemic_pattern': {'know': {'min': 0.80}, 'clarity': {'min': 0.75}},
                'recommended_scope': {'breadth': 0.7, 'duration': 0.6, 'coordination': 0.4},
                'rationale': 'High knowledge enables broader scope'
            },
            'learning_mode': {
                'epistemic_pattern': {'know': {'max': 0.50}, 'uncertainty': {'min': 0.60}},
                'recommended_scope': {'breadth': 0.2, 'duration': 0.2, 'coordination': 0.1},
                'rationale': 'Uncertainty requires narrow scope'
            }
        }
    
    def get_scope_recommendations(
        self,
        epistemic_vectors: Dict[str, float],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get scope recommendations based on epistemic vector pattern.
        
        Args:
            epistemic_vectors: Current epistemic assessment (13 vectors)
            context: Additional context (task type, user priority, etc.)
            
        Returns:
            Dictionary with scope recommendation or None if no match
        
        Example:
            >>> vectors = {'know': 0.85, 'uncertainty': 0.3, 'clarity': 0.80}
            >>> recommendations = loader.get_scope_recommendations(vectors)
            >>> print(recommendations)
            {'breadth': 0.7, 'duration': 0.6, 'coordination': 0.4, 'pattern': 'knowledge_leader'}
        """
        if not epistemic_vectors:
            return None
        
        # Find best matching pattern
        best_match = None
        best_score = 0.0
        
        for pattern_name, pattern_data in self.scope_recommendations.items():
            score = self._calculate_pattern_match(
                epistemic_vectors, 
                pattern_data.get('epistemic_pattern', {})
            )
            
            if score > best_score and score >= 0.5:  # Minimum match threshold
                best_score = score
                best_match = pattern_data
                best_match['pattern'] = pattern_name
                best_match['match_score'] = score
        
        # If no good match, try conservative defaults
        if not best_match:
            logger.debug("No strong pattern match, using conservative defaults")
            return self._get_conservative_defaults(epistemic_vectors)
        
        # Apply context adjustments if provided
        if context:
            best_match = self._apply_context_adjustments(best_match, context)
        
        # Extract scope recommendation
        recommended_scope = best_match.get('recommended_scope', {})
        
        logger.info(f"✅ Scope recommendation: {best_match['pattern']} (score: {best_score:.2f})")
        logger.info(f"   Recommended: breadth={recommended_scope['breadth']:.2f}, "
                   f"duration={recommended_scope['duration']:.2f}, "
                   f"coordination={recommended_scope['coordination']:.2f}")
        
        return {
            'breadth': recommended_scope['breadth'],
            'duration': recommended_scope['duration'],
            'coordination': recommended_scope['coordination'],
            'pattern': best_match['pattern'],
            'match_score': best_score,
            'rationale': best_match.get('rationale', 'No rationale provided'),
            'context_applied': context is not None
        }
    
    def _calculate_pattern_match(
        self,
        epistemic_vectors: Dict[str, float],
        pattern: Dict[str, Any]
    ) -> float:
        """
        Calculate how well current epistemic state matches a pattern.
        
        Args:
            epistemic_vectors: Current epistemic values
            pattern: Pattern definition with min/max constraints
            
        Returns:
            Match score (0.0-1.0)
        """
        if not pattern or not epistemic_vectors:
            return 0.0
        
        total_conditions = 0
        matched_conditions = 0
        
        for vector_name, constraints in pattern.items():
            if vector_name not in epistemic_vectors:
                continue
            
            total_conditions += 1
            value = epistemic_vectors[vector_name]
            
            # Check constraints
            constraint_met = True
            
            if 'min' in constraints and value < constraints['min']:
                constraint_met = False
            if 'max' in constraints and value > constraints['max']:
                constraint_met = False
            
            if constraint_met:
                matched_conditions += 1
        
        # Return fraction of conditions met
        return matched_conditions / max(total_conditions, 1)
    
    def _apply_context_adjustments(
        self,
        recommendation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply context-based adjustments to scope recommendation"""
        
        # Deep copy to avoid modifying original
        adjusted = copy.deepcopy(recommendation)
        
        # Context-based adjustments
        if context.get('priority') == 'high':
            # High priority work might warrant broader scope
            scope = adjusted['recommended_scope']
            scope['breadth'] = min(scope['breadth'] + 0.1, 1.0)
            adjusted['adjusted_for'] = 'high_priority'
            
        elif context.get('deadline_tight'):
            # Tight deadlines might require scope reduction
            scope = adjusted['recommended_scope']
            scope['duration'] = max(scope['duration'] - 0.2, 0.1)
            scope['breadth'] = max(scope['breadth'] - 0.1, 0.1)
            adjusted['adjusted_for'] = 'tight_deadline'
        
        return adjusted
    
    def _get_conservative_defaults(
        self,
        epistemic_vectors: Dict[str, float]
    ) -> Dict[str, Any]:
        """Get conservative scope defaults when no pattern matches well"""
        
        # Conservative baseline
        breadth = 0.3
        duration = 0.2
        coordination = 0.2
        
        # Adjust based on key indicators
        if epistemic_vectors.get('know', 0) > 0.7:
            breadth += 0.2
            duration += 0.2
            
        if epistemic_vectors.get('engagement', 0) < 0.6:
            # Low engagement - be very conservative
            breadth *= 0.7
            duration *= 0.7
            
        # Cap values
        breadth = max(0.1, min(breadth, 0.6))
        duration = max(0.1, min(duration, 0.5))
        coordination = max(0.1, min(coordination, 0.4))
        
        return {
            'breadth': breadth,
            'duration': duration,
            'coordination': coordination,
            'pattern': 'conservative_defaults',
            'match_score': 0.0,
            'rationale': 'Conservative defaults when no pattern matches well'
        }
    
    def validate_scope_coherence(self, scope_vector: Dict[str, float]) -> Dict[str, Any]:
        """
        Validate scope vector coherence and provide warnings.
        
        Args:
            scope_vector: {'breadth': float, 'duration': float, 'coordination': float}
            
        Returns:
            Validation results with warnings and suggestions
        """
        warnings = []
        suggestions = []
        
        # Check against validation rules (detect BAD combinations)
        for rule_name, rule_config in self.validation_rules.items():
            rule_scope = rule_config.get('scope', {})
            
            # Check if this specific bad combination is present
            bad_combination = True
            for scope_param, constraint in rule_scope.items():
                if scope_param not in scope_vector:
                    bad_combination = False
                    break
                    
                value = scope_vector[scope_param]
                
                # Check if this parameter violates the "good" combination
                if 'min' in constraint and value < constraint['min']:
                    # This parameter is below the minimum, so the bad combination is NOT present
                    bad_combination = False
                    break
                if 'max' in constraint and value > constraint['max']:
                    # This parameter is above the maximum, so the bad combination is NOT present  
                    bad_combination = False
                    break
            
            # If we checked all parameters and none violated their good ranges, it's a bad combination
            if bad_combination:
                warnings.append(rule_config.get('warning', f'Rule {rule_name} violated'))
        
        # Provide suggestions for improvement
        if scope_vector.get('coordination', 0) > 0.7 and scope_vector.get('breadth', 0) < 0.4:
            suggestions.append("Consider increasing scope breadth for heavy coordination tasks")
            
        if scope_vector.get('duration', 0) < 0.3 and scope_vector.get('coordination', 0) > 0.6:
            suggestions.append("Consider increasing duration for heavy coordination tasks")
        
        return {
            'coherent': len(warnings) == 0,
            'warnings': warnings,
            'suggestions': suggestions,
            'severity': 'high' if len(warnings) > 1 else 'medium' if warnings else 'none'
        }
    
    def list_available_patterns(self) -> Dict[str, str]:
        """List all available scope recommendation patterns"""
        return {
            name: data.get('description', 'No description')
            for name, data in self.scope_recommendations.items()
        }


# Global instance accessor
def get_scope_recommendations(
    epistemic_vectors: Dict[str, float],
    context: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get scope recommendations based on epistemic state.
    
    Convenience function that creates and uses a GoalScopeLoader.
    
    Args:
        epistemic_vectors: Current epistemic assessment (13 vectors)
        context: Optional context for adjustments
        
    Returns:
        Scope recommendation dictionary or None
    """
    loader = GoalScopeLoader()
    return loader.get_scope_recommendations(epistemic_vectors, context)


def validate_scope_coherence(scope_vector: Dict[str, float]) -> Dict[str, Any]:
    """
    Validate scope vector coherence.
    
    Convenience function.
    
    Args:
        scope_vector: {'breadth': float, 'duration': float, 'coordination': float}
        
    Returns:
        Validation results
    """
    loader = GoalScopeLoader()
    return loader.validate_scope_coherence(scope_vector)