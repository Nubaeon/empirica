#!/usr/bin/env python3
"""
Bayesian Belief Tracker - Evidence-based belief updating for epistemic states

This system tracks beliefs about epistemic vectors using Bayesian updates from
investigation tool results. It complements AdaptiveUncertaintyCalibration by:

1. Real-time evidence accumulation (during current task)
2. Variance tracking (quantifying uncertainty about uncertainty)
3. Discrepancy detection (intuition vs evidence)
4. Selective activation (precision-critical domains only)

Key Principle: Guidance, not rules - Bayesian beliefs inform but don't override
"""

import time
import json
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import os


@dataclass
class Evidence:
    """Single piece of evidence from an investigation tool"""
    outcome: bool  # Did the tool succeed/find what it expected?
    strength: float  # 0.0-1.0 how strong is this evidence
    timestamp: float
    source: str  # Which tool provided this evidence
    vector_addressed: str  # Which epistemic vector this addresses (e.g., "know", "context")
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BeliefState:
    """Bayesian belief about a specific epistemic vector"""
    mean: float  # Current belief (0.0-1.0, where 1.0 = high confidence)
    variance: float  # Uncertainty about the belief (0.0-1.0)
    evidence_count: int  # How many pieces of evidence contributed
    last_updated: float
    prior_mean: float  # Starting belief before evidence
    prior_variance: float  # Starting uncertainty
    
    def confidence_interval(self, std_devs: float = 2.0) -> Tuple[float, float]:
        """Calculate confidence interval around belief"""
        std = math.sqrt(self.variance)
        lower = max(0.0, self.mean - (std * std_devs))
        upper = min(1.0, self.mean + (std * std_devs))
        return (lower, upper)
    
    def is_confident(self, threshold: float = 0.15) -> bool:
        """Is variance low enough to be considered confident?"""
        return self.variance < threshold


class DomainClassifier:
    """Classifies tasks into precision-critical vs creative domains"""
    
    PRECISION_CRITICAL = {
        'code_analysis',
        'bug_diagnosis', 
        'security_review',
        'architecture',
        'system_design',
        'performance_optimization',
        'data_migration',
        'refactoring'
    }
    
    CREATIVE_FLOW = {
        'design',
        'writing',
        'brainstorm',
        'ideation',
        'exploration',
        'creative_coding'
    }
    
    @classmethod
    def classify_domain(cls, task: str, context: Dict[str, Any]) -> str:
        """Classify task domain from task description and context"""
        task_lower = task.lower()
        
        # Check for precision-critical keywords
        precision_keywords = [
            'analyze', 'debug', 'fix', 'refactor', 'security', 'performance',
            'optimize', 'diagnose', 'investigate', 'audit', 'migrate', 'test'
        ]
        
        creative_keywords = [
            'design', 'create', 'write', 'brainstorm', 'explore', 'ideate',
            'prototype', 'sketch', 'draft'
        ]
        
        precision_score = sum(1 for kw in precision_keywords if kw in task_lower)
        creative_score = sum(1 for kw in creative_keywords if kw in task_lower)
        
        if precision_score > creative_score:
            # Find specific domain
            for domain in cls.PRECISION_CRITICAL:
                if domain.replace('_', ' ') in task_lower:
                    return domain
            return 'code_analysis'  # Default precision domain
        elif creative_score > 0:
            return 'creative_flow'
        else:
            return 'general'  # Neutral domain
    
    @classmethod
    def should_activate_bayesian(cls, domain: str, 
                                 clarity_index: float = 0.7,
                                 discrepancies_found: int = 0) -> bool:
        """Determine if Bayesian calibration should be active"""
        
        # Always activate for precision-critical domains
        if domain in cls.PRECISION_CRITICAL:
            return True
        
        # Activate if clarity is low (confusion = need evidence tracking)
        if clarity_index < 0.5:
            return True
        
        # Activate if discrepancies detected (overconfidence signals)
        if discrepancies_found > 2:
            return True
        
        # Keep dormant for creative work
        if domain in cls.CREATIVE_FLOW:
            return False
        
        return False  # Default: dormant


class BayesianBeliefTracker:
    """
    Tracks epistemic beliefs using Bayesian updates from investigation evidence
    
    Core functionality:
    1. Initialize beliefs from initial assessment (prior)
    2. Update beliefs as investigation tools provide evidence
    3. Compare beliefs to intuitive assessments (detect discrepancies)
    4. Provide guidance when beliefs diverge from intuition
    """
    
    def __init__(self, persistence_dir: Optional[str] = None):
        self.beliefs: Dict[str, BeliefState] = {}
        self.evidence_history: List[Evidence] = []
        self.active = False
        self.activation_reason: Optional[str] = None
        
        # Persistence
        if persistence_dir:
            self.persistence_dir = Path(persistence_dir)
            self.persistence_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Default to .empirica_beliefs in the empirica directory
            default_dir = Path(__file__).parent.parent / '.empirica_beliefs'
            self.persistence_dir = default_dir
            self.persistence_dir.mkdir(parents=True, exist_ok=True)
        
        # Bayesian update parameters
        self.UPDATE_STRENGTH = 0.3  # How much evidence affects belief (0.0-1.0)
        self.VARIANCE_REDUCTION_RATE = 0.2  # How much variance reduces per evidence
        self.MIN_VARIANCE = 0.05  # Minimum uncertainty
    
    def initialize_beliefs(self, 
                          context_key: str,
                          initial_assessment: Dict[str, float],
                          initial_variance: float = 0.3) -> None:
        """
        Initialize Bayesian beliefs from initial assessment
        
        Args:
            context_key: Unique identifier for this task/context
            initial_assessment: Dict of vector_name -> confidence (0.0-1.0)
            initial_variance: Initial uncertainty about each belief
        """
        for vector_name, confidence in initial_assessment.items():
            belief_key = f"{context_key}:{vector_name}"
            
            self.beliefs[belief_key] = BeliefState(
                mean=confidence,
                variance=initial_variance,
                evidence_count=0,
                last_updated=time.time(),
                prior_mean=confidence,
                prior_variance=initial_variance
            )
    
    def get_belief(self, belief_key: str) -> BeliefState:
        """Get current belief state, creating default if not exists"""
        if belief_key not in self.beliefs:
            # Create default belief with high uncertainty
            self.beliefs[belief_key] = BeliefState(
                mean=0.5,  # Maximum uncertainty
                variance=0.5,  # High variance
                evidence_count=0,
                last_updated=time.time(),
                prior_mean=0.5,
                prior_variance=0.5
            )
        
        return self.beliefs[belief_key]
    
    def update_belief(self, belief_key: str, evidence: Evidence) -> BeliefState:
        """
        Update belief using Bayesian update from evidence
        
        Simplified Bayesian update:
        - Positive evidence (outcome=True) increases confidence (reduces uncertainty)
        - Negative evidence (outcome=False) decreases confidence (increases uncertainty)
        - Strength modulates the size of the update
        """
        belief = self.get_belief(belief_key)
        
        # Calculate update direction based on evidence
        if evidence.outcome:
            # Positive evidence: increase confidence
            update = evidence.strength * self.UPDATE_STRENGTH
            new_mean = belief.mean + (1.0 - belief.mean) * update
        else:
            # Negative evidence: decrease confidence
            update = evidence.strength * self.UPDATE_STRENGTH
            new_mean = belief.mean - belief.mean * update
        
        # Reduce variance as we gather evidence (more certain)
        new_variance = belief.variance * (1.0 - self.VARIANCE_REDUCTION_RATE * evidence.strength)
        new_variance = max(self.MIN_VARIANCE, new_variance)
        
        # Update belief
        belief.mean = max(0.0, min(1.0, new_mean))
        belief.variance = new_variance
        belief.evidence_count += 1
        belief.last_updated = time.time()
        
        # Record evidence
        self.evidence_history.append(evidence)
        
        return belief
    
    def detect_discrepancies(self,
                           context_key: str,
                           intuitive_assessment: Dict[str, float],
                           threshold_std_devs: float = 2.0) -> List[Dict[str, Any]]:
        """
        Detect discrepancies between intuitive assessment and Bayesian beliefs
        
        Returns list of discrepancies with type (overconfidence/underconfidence)
        """
        discrepancies = []
        
        for vector_name, intuitive_value in intuitive_assessment.items():
            belief_key = f"{context_key}:{vector_name}"
            belief = self.get_belief(belief_key)
            
            # Calculate threshold based on variance
            std = math.sqrt(belief.variance)
            threshold = std * threshold_std_devs
            
            # Check for overconfidence
            if intuitive_value > belief.mean + threshold:
                discrepancies.append({
                    'type': 'overconfidence',
                    'vector': vector_name,
                    'intuitive': intuitive_value,
                    'bayesian_mean': belief.mean,
                    'bayesian_variance': belief.variance,
                    'confidence_interval': belief.confidence_interval(),
                    'gap': intuitive_value - belief.mean,
                    'severity': min(1.0, (intuitive_value - belief.mean) / threshold)
                })
            
            # Check for underconfidence
            elif intuitive_value < belief.mean - threshold:
                discrepancies.append({
                    'type': 'underconfidence',
                    'vector': vector_name,
                    'intuitive': intuitive_value,
                    'bayesian_mean': belief.mean,
                    'bayesian_variance': belief.variance,
                    'confidence_interval': belief.confidence_interval(),
                    'gap': belief.mean - intuitive_value,
                    'severity': min(1.0, (belief.mean - intuitive_value) / threshold)
                })
        
        return discrepancies
    
    def activate(self, reason: str) -> None:
        """Activate Bayesian tracking with reason"""
        self.active = True
        self.activation_reason = reason
        print(f"🧮 Bayesian Belief Tracker activated: {reason}")
    
    def deactivate(self) -> None:
        """Deactivate Bayesian tracking"""
        self.active = False
        self.activation_reason = None
    
    def get_calibration_summary(self, context_key: str) -> Dict[str, Any]:
        """Get summary of Bayesian calibration state for a context"""
        relevant_beliefs = {
            k: v for k, v in self.beliefs.items() 
            if k.startswith(context_key)
        }
        
        return {
            'active': self.active,
            'activation_reason': self.activation_reason,
            'beliefs': {
                k: {
                    'mean': v.mean,
                    'variance': v.variance,
                    'evidence_count': v.evidence_count,
                    'confidence_interval': v.confidence_interval(),
                    'is_confident': v.is_confident()
                }
                for k, v in relevant_beliefs.items()
            },
            'total_evidence': len(self.evidence_history)
        }
    
    def get_all_beliefs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all tracked beliefs in serializable format

        Returns:
            Dictionary mapping belief_keys to belief state information
        """
        result = {}

        for belief_key, belief_state in self.beliefs.items():
            result[belief_key] = {
                'mean': belief_state.mean,
                'variance': belief_state.variance,
                'evidence_count': belief_state.evidence_count,
                'last_updated': belief_state.last_updated,
                'prior_mean': belief_state.prior_mean,
                'prior_variance': belief_state.prior_variance,
                'is_confident': belief_state.is_confident(),
                'confidence_interval': belief_state.confidence_interval()
            }

        return result
    
    def save_state(self, filename: str = "bayesian_state.json") -> None:
        """Persist Bayesian state to disk"""
        state = {
            'beliefs': {
                k: {
                    'mean': v.mean,
                    'variance': v.variance,
                    'evidence_count': v.evidence_count,
                    'last_updated': v.last_updated,
                    'prior_mean': v.prior_mean,
                    'prior_variance': v.prior_variance
                }
                for k, v in self.beliefs.items()
            },
            'active': self.active,
            'activation_reason': self.activation_reason
        }
        
        filepath = self.persistence_dir / filename
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self, filename: str = "bayesian_state.json") -> None:
        """Load Bayesian state from disk"""
        filepath = self.persistence_dir / filename
        
        if not filepath.exists():
            return
        
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            # Restore beliefs
            self.beliefs = {}
            for k, v in state.get('beliefs', {}).items():
                self.beliefs[k] = BeliefState(
                    mean=v['mean'],
                    variance=v['variance'],
                    evidence_count=v['evidence_count'],
                    last_updated=v['last_updated'],
                    prior_mean=v['prior_mean'],
                    prior_variance=v['prior_variance']
                )
            
            self.active = state.get('active', False)
            self.activation_reason = state.get('activation_reason')
            
        except Exception as e:
            print(f"⚠️ Failed to load Bayesian state: {e}")


# Convenience function for quick integration
def create_bayesian_tracker(persistence_dir: Optional[str] = None) -> BayesianBeliefTracker:
    """Create and return a BayesianBeliefTracker instance"""
    tracker = BayesianBeliefTracker(persistence_dir)
    tracker.load_state()
    return tracker


if __name__ == "__main__":
    # Test the Bayesian belief tracker
    print("🧮 Testing Bayesian Belief Tracker\n")
    
    tracker = BayesianBeliefTracker()
    
    # Initialize beliefs for a code analysis task
    context_key = "task:code_analysis_1"
    initial_assessment = {
        'know': 0.7,
        'do': 0.6,
        'context': 0.5
    }
    
    tracker.initialize_beliefs(context_key, initial_assessment)
    print("✓ Initialized beliefs from assessment")
    
    # Simulate investigation: workspace scan finds lots of info
    evidence1 = Evidence(
        outcome=True,
        strength=0.8,
        timestamp=time.time(),
        source="workspace_scanner",
        vector_addressed="context"
    )
    
    belief_after_scan = tracker.update_belief(f"{context_key}:context", evidence1)
    print(f"\n✓ After workspace scan:")
    print(f"  Context belief: {belief_after_scan.mean:.2f} (variance: {belief_after_scan.variance:.2f})")
    
    # Simulate another tool: codebase search
    evidence2 = Evidence(
        outcome=True,
        strength=0.7,
        timestamp=time.time(),
        source="codebase_search",
        vector_addressed="know"
    )
    
    belief_after_search = tracker.update_belief(f"{context_key}:know", evidence2)
    print(f"\n✓ After codebase search:")
    print(f"  Know belief: {belief_after_search.mean:.2f} (variance: {belief_after_search.variance:.2f})")
    
    # Check for discrepancies (intuition didn't update but evidence did)
    intuitive_assessment = {
        'know': 0.7,  # Still thinks 0.7
        'do': 0.6,
        'context': 0.5  # Still thinks 0.5
    }
    
    discrepancies = tracker.detect_discrepancies(context_key, intuitive_assessment)
    
    print(f"\n✓ Discrepancy detection:")
    if discrepancies:
        for d in discrepancies:
            print(f"  {d['type'].upper()}: {d['vector']}")
            print(f"    Intuitive: {d['intuitive']:.2f}")
            print(f"    Bayesian: {d['bayesian_mean']:.2f} ± {math.sqrt(d['bayesian_variance']):.2f}")
            print(f"    Gap: {d['gap']:.2f} (severity: {d['severity']:.2f})")
    else:
        print("  No discrepancies detected")
    
    # Test domain classification
    print(f"\n✓ Domain classification:")
    print(f"  'Fix the authentication bug': {DomainClassifier.classify_domain('Fix the authentication bug', {})}")
    print(f"  'Design a new logo': {DomainClassifier.classify_domain('Design a new logo', {})}")
    print(f"  'Refactor the codebase': {DomainClassifier.classify_domain('Refactor the codebase', {})}")
    
    print("\n🎉 Bayesian Belief Tracker tests complete!")
