"""
Emerged Personas - Extract persona patterns from successful investigation branches.

When an investigation branch successfully converges, extract:
- Initial epistemic vector state
- Delta pattern over loops (how knowledge evolved)
- Convergence thresholds that worked
- Task characteristics that led to success

This creates data-driven personas that can inform future Sentinel orchestration.
"""

import json
import logging
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class EmergedPersona:
    """A persona derived from successful investigation patterns."""
    persona_id: str
    name: str
    source_session_id: str
    source_branch_id: Optional[str] = None

    # Vector profile
    initial_vectors: Dict[str, float] = field(default_factory=dict)
    final_vectors: Dict[str, float] = field(default_factory=dict)
    delta_pattern: Dict[str, float] = field(default_factory=dict)

    # Convergence characteristics
    loops_to_converge: int = 0
    convergence_threshold: float = 0.03
    scope_breadth: float = 0.5
    scope_duration: float = 0.5

    # Task characteristics
    task_domains: List[str] = field(default_factory=list)
    task_keywords: List[str] = field(default_factory=list)

    # Provenance
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    findings_count: int = 0
    unknowns_resolved: int = 0

    # Reputation (can be updated over time)
    reputation_score: float = 0.5
    uses_count: int = 0
    success_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmergedPersona':
        return cls(**data)

    def to_yaml(self) -> str:
        """Export as YAML for storage."""
        import yaml
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)


def extract_persona_from_loop_tracker(
    session_id: str,
    loop_tracker: 'EpistemicLoopTracker',
    task_description: str = "",
    branch_id: str = None
) -> Optional[EmergedPersona]:
    """
    Extract an emerged persona from a successful loop tracker.

    Call this after a successful investigation branch completion
    (when loop_tracker.is_converged() or all loops completed successfully).

    Args:
        session_id: The session where this persona emerged
        loop_tracker: The EpistemicLoopTracker with completed loop history
        task_description: Original task for domain extraction
        branch_id: Optional branch ID for provenance

    Returns:
        EmergedPersona if extraction successful, None otherwise
    """
    if not loop_tracker.loop_history:
        logger.debug("No loop history to extract persona from")
        return None

    # Get initial and final states
    first_loop = loop_tracker.loop_history[0]
    last_loop = loop_tracker.loop_history[-1]

    initial_vectors = first_loop.preflight_vectors or {}
    final_vectors = last_loop.postflight_vectors or {}

    # Calculate delta pattern (how each vector evolved)
    delta_pattern = {}
    for key in set(initial_vectors.keys()) | set(final_vectors.keys()):
        initial = initial_vectors.get(key, 0.5)
        final = final_vectors.get(key, 0.5)
        delta_pattern[key] = final - initial

    # Calculate total findings and unknowns resolved
    total_findings = sum(loop.findings_count or 0 for loop in loop_tracker.loop_history)
    total_unknowns_resolved = sum(
        (loop.unknowns_start or 0) - (loop.unknowns_count or 0)
        for loop in loop_tracker.loop_history
        if loop.unknowns_start is not None and loop.unknowns_count is not None
    )

    # Extract domains from task description
    task_domains = _extract_domains(task_description)
    task_keywords = _extract_keywords(task_description)

    # Generate persona name
    primary_domain = task_domains[0] if task_domains else "general"
    persona_name = f"{primary_domain.title()} Investigator ({len(loop_tracker.loop_history)} loops)"

    persona = EmergedPersona(
        persona_id=f"emerged_{str(uuid.uuid4())[:8]}",
        name=persona_name,
        source_session_id=session_id,
        source_branch_id=branch_id,
        initial_vectors=initial_vectors,
        final_vectors=final_vectors,
        delta_pattern=delta_pattern,
        loops_to_converge=len(loop_tracker.loop_history),
        convergence_threshold=loop_tracker.convergence_threshold,
        scope_breadth=loop_tracker.scope_breadth,
        scope_duration=loop_tracker.scope_duration,
        task_domains=task_domains,
        task_keywords=task_keywords,
        findings_count=total_findings,
        unknowns_resolved=max(0, total_unknowns_resolved),
        reputation_score=0.5 + (0.1 * min(total_findings, 5))  # Initial boost from findings
    )

    return persona


def _extract_domains(task: str) -> List[str]:
    """Extract domain signals from task description."""
    from empirica.core.sentinel.decision_logic import DOMAIN_PATTERNS
    import re

    task_lower = task.lower()
    domains = []

    for domain, patterns in DOMAIN_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, task_lower):
                if domain not in domains:
                    domains.append(domain)
                break

    return domains or ["general"]


def _extract_keywords(task: str) -> List[str]:
    """Extract significant keywords from task description."""
    # Simple keyword extraction - could be enhanced with NLP
    import re

    # Remove common words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'this',
        'that', 'these', 'those', 'it', 'its', 'i', 'we', 'you', 'he', 'she',
        'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how'
    }

    words = re.findall(r'\b[a-z]{3,}\b', task.lower())
    keywords = [w for w in words if w not in stop_words]

    # Return unique keywords, limited to 10
    seen = set()
    unique = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)
            if len(unique) >= 10:
                break

    return unique


class EmergedPersonaStore:
    """
    Store and retrieve emerged personas.

    Storage location: .empirica/personas/
    Format: emerged_{persona_id}.yaml
    """

    def __init__(self, base_path: str = None):
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = Path.cwd() / ".empirica" / "personas"
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, persona: EmergedPersona) -> str:
        """Save persona to storage. Returns file path."""
        filename = f"emerged_{persona.persona_id}.yaml"
        filepath = self.base_path / filename

        with open(filepath, 'w') as f:
            f.write(persona.to_yaml())

        logger.info(f"Saved emerged persona: {filepath}")
        return str(filepath)

    def load(self, persona_id: str) -> Optional[EmergedPersona]:
        """Load persona by ID."""
        # Try with and without emerged_ prefix
        for pattern in [f"emerged_{persona_id}.yaml", f"{persona_id}.yaml"]:
            filepath = self.base_path / pattern
            if filepath.exists():
                return self._load_file(filepath)
        return None

    def _load_file(self, filepath: Path) -> Optional[EmergedPersona]:
        """Load persona from file."""
        try:
            import yaml
            with open(filepath) as f:
                data = yaml.safe_load(f)
            return EmergedPersona.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load persona from {filepath}: {e}")
            return None

    def list_all(self) -> List[EmergedPersona]:
        """List all emerged personas."""
        personas = []
        for filepath in self.base_path.glob("emerged_*.yaml"):
            persona = self._load_file(filepath)
            if persona:
                personas.append(persona)
        return sorted(personas, key=lambda p: p.extracted_at, reverse=True)

    def find_by_domain(self, domain: str) -> List[EmergedPersona]:
        """Find personas that match a domain."""
        return [p for p in self.list_all() if domain in p.task_domains]

    def find_similar(self, task: str, limit: int = 5) -> List[EmergedPersona]:
        """Find personas similar to a task description."""
        task_domains = _extract_domains(task)
        task_keywords = set(_extract_keywords(task))

        scored = []
        for persona in self.list_all():
            # Score by domain overlap
            domain_score = len(set(persona.task_domains) & set(task_domains)) / max(len(task_domains), 1)

            # Score by keyword overlap
            keyword_score = len(set(persona.task_keywords) & task_keywords) / max(len(task_keywords), 1)

            # Combined score (weighted)
            score = 0.6 * domain_score + 0.4 * keyword_score

            if score > 0:
                scored.append((score, persona))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:limit]]

    def update_reputation(self, persona_id: str, success: bool) -> bool:
        """Update persona reputation after use."""
        persona = self.load(persona_id)
        if not persona:
            return False

        persona.uses_count += 1
        if success:
            persona.success_count += 1

        # Update reputation: Bayesian-ish update
        success_rate = persona.success_count / persona.uses_count
        persona.reputation_score = 0.3 + 0.7 * success_rate  # Range 0.3 - 1.0

        self.save(persona)
        return True


def extract_and_store_persona(
    session_id: str,
    loop_tracker: 'EpistemicLoopTracker',
    task_description: str = "",
    branch_id: str = None,
    store_path: str = None
) -> Optional[str]:
    """
    Convenience function to extract and store a persona in one call.

    Returns persona_id if successful, None otherwise.
    """
    persona = extract_persona_from_loop_tracker(
        session_id=session_id,
        loop_tracker=loop_tracker,
        task_description=task_description,
        branch_id=branch_id
    )

    if not persona:
        return None

    store = EmergedPersonaStore(store_path)
    store.save(persona)

    logger.info(f"Extracted and stored emerged persona: {persona.persona_id}")
    return persona.persona_id


def sentinel_match_persona(
    task: str,
    grounding_vectors: Dict[str, float] = None,
    min_reputation: float = 0.5,
    store_path: str = None
) -> Optional[EmergedPersona]:
    """
    Sentinel-level persona matching: finds best persona for task + grounding.

    Args:
        task: Task description
        grounding_vectors: Current epistemic grounding (know, uncertainty, etc.)
        min_reputation: Minimum reputation score to consider
        store_path: Custom store path

    Returns:
        Best matching EmergedPersona or None

    The matching considers:
    1. Task similarity (domain + keyword matching)
    2. Vector compatibility (if grounding provided)
    3. Reputation score
    """
    store = EmergedPersonaStore(store_path)
    candidates = store.find_similar(task, limit=10)

    if not candidates:
        return None

    # Filter by reputation
    candidates = [p for p in candidates if p.reputation_score >= min_reputation]

    if not candidates:
        return None

    # If no grounding provided, just return best by reputation
    if not grounding_vectors:
        candidates.sort(key=lambda p: p.reputation_score, reverse=True)
        return candidates[0]

    # Score by vector compatibility: prefer personas whose initial_vectors
    # are similar to current grounding (they started from similar state)
    scored = []
    for persona in candidates:
        # Vector distance (lower is better)
        vector_diff = 0
        count = 0
        for key, value in grounding_vectors.items():
            if key in persona.initial_vectors:
                vector_diff += abs(persona.initial_vectors[key] - value)
                count += 1
        avg_diff = vector_diff / max(count, 1)

        # Combined score: reputation + vector compatibility
        compatibility = 1.0 - min(avg_diff, 1.0)
        combined_score = 0.4 * persona.reputation_score + 0.6 * compatibility

        scored.append((combined_score, persona))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored else None
