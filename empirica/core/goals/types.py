#!/usr/bin/env python3
"""
Goal Type Definitions

Core dataclasses for structured goal representation.
Designed for explicit AI-driven goal creation (MVP - no automatic parsing).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import time
import uuid


@dataclass
class ScopeVector:
    """
    Goal scope as epistemic vectors (AI self-assesses, Sentinel validates coherence)
    
    Replaces categorical enum with numeric dimensions for genuine AI assessment.
    """
    breadth: float      # 0.0-1.0: How wide the goal spans (0=single function, 1=entire codebase)
    duration: float     # 0.0-1.0: Expected lifetime (0=minutes/hours, 1=weeks/months)
    coordination: float # 0.0-1.0: Multi-agent/session coordination needed
    
    def __post_init__(self):
        """Validate ranges"""
        for field_name in ['breadth', 'duration', 'coordination']:
            value = getattr(self, field_name)
            if not isinstance(value, (int, float)):
                raise ValueError(f"{field_name} must be numeric, got {type(value)}")
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"{field_name} must be 0.0-1.0, got {value}")
    
    def to_dict(self) -> Dict[str, float]:
        """Serialize to dictionary"""
        return {
            'breadth': self.breadth,
            'duration': self.duration,
            'coordination': self.coordination
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ScopeVector':
        """Deserialize from dictionary"""
        return ScopeVector(
            breadth=float(data['breadth']),
            duration=float(data['duration']),
            coordination=float(data['coordination'])
        )


class DependencyType(Enum):
    """Dependency relationship types"""
    PREREQUISITE = "prerequisite"        # Must complete before starting
    CONCURRENT = "concurrent"            # Can work on simultaneously
    INFORMATIONAL = "informational"      # Nice to have context


@dataclass
class SuccessCriterion:
    """Measurable success criterion for goal completion"""
    id: str
    description: str
    validation_method: str               # "completion", "quality_gate", "metric_threshold"
    threshold: Optional[float] = None    # For metric-based criteria
    is_required: bool = True             # vs. optional/nice-to-have
    is_met: bool = False                 # Completion status


@dataclass
class Dependency:
    """Goal dependency specification"""
    id: str
    goal_id: str                         # Which goal this depends on
    dependency_type: DependencyType
    description: str


@dataclass
class Goal:
    """
    Structured goal representation
    
    MVP Design: AI creates goals explicitly via MCP tools.
    No automatic parsing - keeps it simple and heuristic-free.
    """
    id: str
    objective: str                       # Clear, actionable goal statement
    success_criteria: List[SuccessCriterion]
    scope: ScopeVector
    dependencies: List[Dependency] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    estimated_complexity: Optional[float] = None
    created_timestamp: float = field(default_factory=time.time)
    completed_timestamp: Optional[float] = None
    is_completed: bool = False
    
    @staticmethod
    def create(
        objective: str,
        success_criteria: List[SuccessCriterion],
        scope: ScopeVector = None,
        **kwargs
    ) -> 'Goal':
        """Convenience factory method"""
        if scope is None:
            scope = ScopeVector(breadth=0.3, duration=0.2, coordination=0.1)  # Default: narrow, short, solo
        return Goal(
            id=str(uuid.uuid4()),
            objective=objective,
            success_criteria=success_criteria,
            scope=scope,
            **kwargs
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'id': self.id,
            'objective': self.objective,
            'success_criteria': [
                {
                    'id': sc.id,
                    'description': sc.description,
                    'validation_method': sc.validation_method,
                    'threshold': sc.threshold,
                    'is_required': sc.is_required,
                    'is_met': sc.is_met
                }
                for sc in self.success_criteria
            ],
            'scope': self.scope.to_dict(),
            'dependencies': [
                {
                    'id': dep.id,
                    'goal_id': dep.goal_id,
                    'dependency_type': dep.dependency_type.value,
                    'description': dep.description
                }
                for dep in self.dependencies
            ],
            'constraints': self.constraints,
            'metadata': self.metadata,
            'estimated_complexity': self.estimated_complexity,
            'created_timestamp': self.created_timestamp,
            'completed_timestamp': self.completed_timestamp,
            'is_completed': self.is_completed
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Goal':
        """Deserialize from dictionary"""
        return Goal(
            id=data['id'],
            objective=data['objective'],
            success_criteria=[
                SuccessCriterion(
                    id=sc['id'],
                    description=sc['description'],
                    validation_method=sc['validation_method'],
                    threshold=sc.get('threshold'),
                    is_required=sc.get('is_required', True),
                    is_met=sc.get('is_met', False)
                )
                for sc in data['success_criteria']
            ],
            scope=ScopeVector.from_dict(data['scope']),
            dependencies=[
                Dependency(
                    id=dep['id'],
                    goal_id=dep['goal_id'],
                    dependency_type=DependencyType(dep['dependency_type']),
                    description=dep['description']
                )
                for dep in data.get('dependencies', [])
            ],
            constraints=data.get('constraints', {}),
            metadata=data.get('metadata', {}),
            estimated_complexity=data.get('estimated_complexity'),
            created_timestamp=data.get('created_timestamp', time.time()),
            completed_timestamp=data.get('completed_timestamp'),
            is_completed=data.get('is_completed', False)
        )
