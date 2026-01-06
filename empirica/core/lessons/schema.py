"""
Empirica Lessons - Epistemic Procedural Knowledge Schema

This module defines the data structures for storing and retrieving
procedural knowledge with epistemic metadata. Lessons capture not just
HOW to do something, but the epistemic state changes that result.

Architecture:
- HOT layer: In-memory graph (nanoseconds)
- WARM layer: SQLite metadata (microseconds)
- SEARCH layer: Qdrant vectors (milliseconds)
- COLD layer: YAML full content (10ms)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal
from enum import Enum
import hashlib
import time


class LessonPhase(Enum):
    """Epistemic phase of a lesson step"""
    NOETIC = "noetic"      # Investigation, reading, understanding
    PRAXIC = "praxic"      # Action, execution, doing


class StepCriticality(Enum):
    """How critical is getting this step right"""
    CRITICAL = "critical"   # Failure here = lesson fails
    IMPORTANT = "important" # Should get right, recoverable
    OPTIONAL = "optional"   # Nice to have


class PrerequisiteType(Enum):
    """Types of prerequisites a lesson can have"""
    LESSON = "lesson"       # Must have completed another lesson
    SKILL = "skill"         # Must have a skill (composite of lessons)
    TOOL = "tool"           # Must have access to a tool
    CONTEXT = "context"     # Must have certain context (file, repo, etc.)
    EPISTEMIC = "epistemic" # Must have epistemic state (know >= X)


class RelationType(Enum):
    """Types of relationships between lessons"""
    REQUIRES = "requires"       # Must do X before Y
    ENABLES = "enables"         # Doing X unlocks Y
    RELATED_TO = "related_to"   # Conceptually similar
    SUPERSEDES = "supersedes"   # X is newer version of Y
    DERIVED_FROM = "derived_from"  # X was created from Y


@dataclass
class EpistemicDelta:
    """
    Expected change in epistemic vectors from completing a lesson.
    This is the KEY insight - lessons don't just teach procedures,
    they predictably improve specific epistemic dimensions.
    """
    know: float = 0.0       # Domain knowledge improvement
    do: float = 0.0         # Capability improvement
    context: float = 0.0    # Situational understanding
    clarity: float = 0.0    # Task clarity
    coherence: float = 0.0  # Mental model coherence
    signal: float = 0.0     # Signal/noise discrimination
    uncertainty: float = 0.0  # Uncertainty reduction (negative = good)

    def to_dict(self) -> Dict[str, float]:
        return {
            'know': self.know,
            'do': self.do,
            'context': self.context,
            'clarity': self.clarity,
            'coherence': self.coherence,
            'signal': self.signal,
            'uncertainty': self.uncertainty
        }

    @classmethod
    def from_dict(cls, d: Dict[str, float]) -> 'EpistemicDelta':
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class LessonStep:
    """
    A single step in a procedural lesson.
    Each step has epistemic phase (noetic vs praxic) and criticality.
    """
    order: int
    phase: LessonPhase
    action: str                          # Human-readable description
    target: Optional[str] = None         # UI element, file, command target
    code: Optional[str] = None           # Executable code (JS, bash, etc.)
    critical: bool = False               # If True, must succeed
    expected_outcome: Optional[str] = None
    error_recovery: Optional[str] = None # What to do if step fails
    timeout_ms: Optional[int] = None     # Max time for this step

    def to_dict(self) -> Dict:
        return {
            'order': self.order,
            'phase': self.phase.value,
            'action': self.action,
            'target': self.target,
            'code': self.code,
            'critical': self.critical,
            'expected_outcome': self.expected_outcome,
            'error_recovery': self.error_recovery,
            'timeout_ms': self.timeout_ms
        }

    @classmethod
    def from_dict(cls, d: Dict) -> 'LessonStep':
        return cls(
            order=d['order'],
            phase=LessonPhase(d['phase']),
            action=d['action'],
            target=d.get('target'),
            code=d.get('code'),
            critical=d.get('critical', False),
            expected_outcome=d.get('expected_outcome'),
            error_recovery=d.get('error_recovery'),
            timeout_ms=d.get('timeout_ms')
        )


@dataclass
class Prerequisite:
    """A prerequisite for executing a lesson"""
    type: PrerequisiteType
    id: str                              # ID of required item
    name: str                            # Human-readable name
    required_level: float = 0.5          # Minimum level needed (0-1)

    def to_dict(self) -> Dict:
        return {
            'type': self.type.value,
            'id': self.id,
            'name': self.name,
            'required_level': self.required_level
        }

    @classmethod
    def from_dict(cls, d: Dict) -> 'Prerequisite':
        return cls(
            type=PrerequisiteType(d['type']),
            id=d['id'],
            name=d['name'],
            required_level=d.get('required_level', 0.5)
        )


@dataclass
class Correction:
    """
    A correction received during lesson creation or replay.
    Corrections are HIGH VALUE - they represent human expertise
    fixing AI mistakes.
    """
    step_order: int
    original_action: str
    corrected_action: str
    reason: str
    corrector_type: Literal['human', 'ai']
    corrector_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            'step_order': self.step_order,
            'original_action': self.original_action,
            'corrected_action': self.corrected_action,
            'reason': self.reason,
            'corrector_type': self.corrector_type,
            'corrector_id': self.corrector_id,
            'timestamp': self.timestamp
        }

    @classmethod
    def from_dict(cls, d: Dict) -> 'Correction':
        return cls(**d)


@dataclass
class LessonRelation:
    """A relationship between this lesson and another entity"""
    relation_type: RelationType
    target_type: str                     # 'lesson', 'skill', 'domain'
    target_id: str
    weight: float = 1.0                  # Relationship strength

    def to_dict(self) -> Dict:
        return {
            'relation_type': self.relation_type.value,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'weight': self.weight
        }

    @classmethod
    def from_dict(cls, d: Dict) -> 'LessonRelation':
        return cls(
            relation_type=RelationType(d['relation_type']),
            target_type=d['target_type'],
            target_id=d['target_id'],
            weight=d.get('weight', 1.0)
        )


@dataclass
class LessonValidation:
    """Validation and quality metrics for a lesson"""
    replay_count: int = 0                # Times successfully replayed
    success_rate: float = 0.0            # Success rate (0-1)
    avg_completion_time_ms: int = 0      # Average time to complete
    test_cases: List[str] = field(default_factory=list)
    success_criteria: str = ""
    last_validated: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            'replay_count': self.replay_count,
            'success_rate': self.success_rate,
            'avg_completion_time_ms': self.avg_completion_time_ms,
            'test_cases': self.test_cases,
            'success_criteria': self.success_criteria,
            'last_validated': self.last_validated
        }

    @classmethod
    def from_dict(cls, d: Dict) -> 'LessonValidation':
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class LessonEpistemic:
    """Epistemic metadata about the lesson itself"""
    source_confidence: float             # How confident was the teacher
    teaching_quality: float              # How clear is the lesson
    reproducibility: float               # How reliably can it be replayed
    expected_delta: EpistemicDelta       # What vectors it improves

    def to_dict(self) -> Dict:
        return {
            'source_confidence': self.source_confidence,
            'teaching_quality': self.teaching_quality,
            'reproducibility': self.reproducibility,
            'expected_delta': self.expected_delta.to_dict()
        }

    @classmethod
    def from_dict(cls, d: Dict) -> 'LessonEpistemic':
        return cls(
            source_confidence=d['source_confidence'],
            teaching_quality=d['teaching_quality'],
            reproducibility=d['reproducibility'],
            expected_delta=EpistemicDelta.from_dict(d['expected_delta'])
        )


@dataclass
class Lesson:
    """
    Complete lesson representation.

    A lesson is epistemic procedural knowledge - it captures:
    1. WHAT to do (steps)
    2. WHY it works (epistemic delta)
    3. WHEN to use it (prerequisites)
    4. HOW it relates (knowledge graph relations)
    5. HOW WELL it works (validation metrics)
    """
    id: str
    name: str
    version: str
    description: str

    # Epistemic metadata
    epistemic: LessonEpistemic

    # Prerequisites
    prerequisites: List[Prerequisite] = field(default_factory=list)

    # Procedural steps
    steps: List[LessonStep] = field(default_factory=list)

    # Relations in knowledge graph
    relations: List[LessonRelation] = field(default_factory=list)

    # Corrections received
    corrections: List[Correction] = field(default_factory=list)

    # Validation metrics
    validation: LessonValidation = field(default_factory=LessonValidation)

    # Pricing tier (for marketplace)
    suggested_tier: Literal['free', 'verified', 'pro', 'enterprise'] = 'free'
    suggested_price: float = 0.0

    # Metadata
    created_by: Optional[str] = None     # AI or human ID
    created_timestamp: float = field(default_factory=time.time)
    updated_timestamp: float = field(default_factory=time.time)

    # Tags for search
    tags: List[str] = field(default_factory=list)
    domain: Optional[str] = None         # e.g., 'browser-automation', 'git', 'api'

    @staticmethod
    def generate_id(name: str, version: str) -> str:
        """Generate deterministic lesson ID from name and version"""
        content = f"{name}:{version}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict:
        """Full serialization for COLD storage (YAML)"""
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'epistemic': self.epistemic.to_dict(),
            'prerequisites': [p.to_dict() for p in self.prerequisites],
            'steps': [s.to_dict() for s in self.steps],
            'relations': [r.to_dict() for r in self.relations],
            'corrections': [c.to_dict() for c in self.corrections],
            'validation': self.validation.to_dict(),
            'suggested_tier': self.suggested_tier,
            'suggested_price': self.suggested_price,
            'created_by': self.created_by,
            'created_timestamp': self.created_timestamp,
            'updated_timestamp': self.updated_timestamp,
            'tags': self.tags,
            'domain': self.domain
        }

    def to_hot_dict(self) -> Dict:
        """Minimal serialization for HOT cache (in-memory)"""
        return {
            'id': self.id,
            'name': self.name,
            'expected_delta': self.epistemic.expected_delta.to_dict(),
            'prereq_ids': [p.id for p in self.prerequisites if p.type == PrerequisiteType.LESSON],
            'enables': [r.target_id for r in self.relations if r.relation_type == RelationType.ENABLES],
            'requires': [r.target_id for r in self.relations if r.relation_type == RelationType.REQUIRES],
        }

    def to_warm_dict(self) -> Dict:
        """Metadata for WARM storage (SQLite)"""
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'domain': self.domain,
            'tags': ','.join(self.tags),
            'source_confidence': self.epistemic.source_confidence,
            'teaching_quality': self.epistemic.teaching_quality,
            'reproducibility': self.epistemic.reproducibility,
            'step_count': len(self.steps),
            'prereq_count': len(self.prerequisites),
            'replay_count': self.validation.replay_count,
            'success_rate': self.validation.success_rate,
            'suggested_tier': self.suggested_tier,
            'suggested_price': self.suggested_price,
            'created_by': self.created_by,
            'created_timestamp': self.created_timestamp,
            'updated_timestamp': self.updated_timestamp
        }

    @classmethod
    def from_dict(cls, d: Dict) -> 'Lesson':
        """Deserialize from COLD storage"""
        return cls(
            id=d['id'],
            name=d['name'],
            version=d['version'],
            description=d['description'],
            epistemic=LessonEpistemic.from_dict(d['epistemic']),
            prerequisites=[Prerequisite.from_dict(p) for p in d.get('prerequisites', [])],
            steps=[LessonStep.from_dict(s) for s in d.get('steps', [])],
            relations=[LessonRelation.from_dict(r) for r in d.get('relations', [])],
            corrections=[Correction.from_dict(c) for c in d.get('corrections', [])],
            validation=LessonValidation.from_dict(d.get('validation', {})),
            suggested_tier=d.get('suggested_tier', 'free'),
            suggested_price=d.get('suggested_price', 0.0),
            created_by=d.get('created_by'),
            created_timestamp=d.get('created_timestamp', time.time()),
            updated_timestamp=d.get('updated_timestamp', time.time()),
            tags=d.get('tags', []),
            domain=d.get('domain')
        )


# Knowledge Graph Node types for type safety
@dataclass
class KnowledgeGraphNode:
    """A node in the epistemic procedural knowledge graph"""
    id: str
    node_type: Literal['lesson', 'skill', 'domain', 'tool', 'agent']
    name: str
    epistemic_delta: Optional[EpistemicDelta] = None

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'node_type': self.node_type,
            'name': self.name,
            'epistemic_delta': self.epistemic_delta.to_dict() if self.epistemic_delta else None
        }


@dataclass
class KnowledgeGraphEdge:
    """An edge in the epistemic procedural knowledge graph"""
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0

    def to_dict(self) -> Dict:
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relation_type': self.relation_type.value,
            'weight': self.weight
        }
