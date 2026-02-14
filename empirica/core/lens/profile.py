"""
Human Epistemic Profile - Assembles what Empirica knows about a human.

Reads across all Qdrant collections + SQLite to build a unified profile
of the human's knowledge state: strengths, gaps, stale assumptions,
calibration biases, and computed HESM baseline.

Reuses pattern_retrieval.py multi-collection search patterns and
persona_profile.py EpistemicConfig structure.
"""

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# All 13 Empirica vectors
ALL_VECTORS = [
    "engagement", "know", "do", "context", "clarity", "coherence",
    "signal", "density", "state", "change", "completion", "impact", "uncertainty"
]

# Human-readable aliases
HUMAN_VECTOR_NAMES = {
    "engagement": "exposure",
    "know": "comprehension",
    "do": "fluency",
    "context": "context",
    "clarity": "clarity",
    "coherence": "integration",
    "signal": "interest",
    "density": "density",
    "state": "retention",
    "change": "velocity",
    "completion": "completion",
    "impact": "impact",
    "uncertainty": "uncertainty",
}


@dataclass
class Unknown:
    """An open knowledge gap."""
    id: str
    text: str
    created_at: float = 0.0
    goal_id: Optional[str] = None
    domain: Optional[str] = None


@dataclass
class Assumption:
    """An unverified belief with urgency signal."""
    id: str
    text: str
    confidence: float = 0.5
    urgency: float = 0.0
    domain: Optional[str] = None
    created_at: float = 0.0


@dataclass
class Goal:
    """An active pursuit."""
    id: str
    objective: str
    status: str = "in_progress"
    completion: float = 0.0


@dataclass
class HESMState:
    """Human Epistemic State Model - 13 vectors."""
    exposure: float = 0.0
    comprehension: float = 0.0
    fluency: float = 0.0
    context: float = 0.0
    clarity: float = 0.0
    integration: float = 0.0
    interest: float = 0.0
    density: float = 0.0
    retention: float = 0.0
    velocity: float = 0.0
    completion: float = 0.0
    impact: float = 0.0
    uncertainty: float = 0.5

    def to_dict(self) -> Dict[str, float]:
        return {
            "exposure": self.exposure,
            "comprehension": self.comprehension,
            "fluency": self.fluency,
            "context": self.context,
            "clarity": self.clarity,
            "integration": self.integration,
            "interest": self.interest,
            "density": self.density,
            "retention": self.retention,
            "velocity": self.velocity,
            "completion": self.completion,
            "impact": self.impact,
            "uncertainty": self.uncertainty,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, float]) -> "HESMState":
        return cls(**{k: d.get(k, 0.0) for k in [
            "exposure", "comprehension", "fluency", "context", "clarity",
            "integration", "interest", "density", "retention", "velocity",
            "completion", "impact", "uncertainty"
        ]})


@dataclass
class HumanEpistemicProfile:
    """Unified human epistemic profile assembled from all Empirica collections."""

    # Domain expertise
    domain_strengths: Dict[str, float] = field(default_factory=dict)
    domain_weaknesses: Dict[str, float] = field(default_factory=dict)

    # Active state
    open_unknowns: List[Unknown] = field(default_factory=list)
    stale_assumptions: List[Assumption] = field(default_factory=list)
    active_goals: List[Goal] = field(default_factory=list)

    # Calibration profile
    calibration_biases: Dict[str, float] = field(default_factory=dict)
    confabulation_risk: float = 0.0

    # Exposure history
    domain_exposure_counts: Dict[str, int] = field(default_factory=dict)
    last_active_domains: List[str] = field(default_factory=list)

    # Collection stats
    total_findings: int = 0
    total_eidetic_facts: int = 0
    total_docs: int = 0
    total_episodes: int = 0

    # Computed baseline
    baseline_hesm: HESMState = field(default_factory=HESMState)

    # Metadata
    project_id: str = ""
    project_name: str = ""
    built_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain_strengths": self.domain_strengths,
            "domain_weaknesses": self.domain_weaknesses,
            "open_unknowns": [{"id": u.id, "text": u.text, "domain": u.domain} for u in self.open_unknowns],
            "stale_assumptions": [{"id": a.id, "text": a.text, "urgency": a.urgency} for a in self.stale_assumptions],
            "active_goals": [{"id": g.id, "objective": g.objective} for g in self.active_goals],
            "calibration_biases": self.calibration_biases,
            "confabulation_risk": self.confabulation_risk,
            "domain_exposure_counts": self.domain_exposure_counts,
            "total_findings": self.total_findings,
            "total_eidetic_facts": self.total_eidetic_facts,
            "total_docs": self.total_docs,
            "baseline_hesm": self.baseline_hesm.to_dict(),
            "project_id": self.project_id,
            "project_name": self.project_name,
            "built_at": self.built_at,
        }


def build_profile(project_id: str, db=None) -> HumanEpistemicProfile:
    """
    Build a HumanEpistemicProfile from all available Empirica data.

    Assembles findings, eidetic facts, unknowns, assumptions, goals,
    calibration data, and episodic memory into a unified profile.

    Args:
        project_id: Project UUID or name
        db: Optional SessionDatabase instance (created if not provided)

    Returns:
        HumanEpistemicProfile
    """
    profile = HumanEpistemicProfile(
        project_id=project_id,
        built_at=time.time(),
    )

    # Resolve project
    if db is None:
        try:
            from empirica.data.session_database import SessionDatabase
            db = SessionDatabase()
        except Exception as e:
            logger.warning(f"Could not open database: {e}")
            return profile

    try:
        project = db._resolve_and_validate_project(project_id)
        if project:
            profile.project_id = project["id"]
            profile.project_name = project.get("name", "")
    except Exception as e:
        logger.debug(f"Project resolution: {e}")

    resolved_id = profile.project_id or project_id

    # Load from SQLite
    _load_goals(profile, resolved_id, db)
    _load_unknowns(profile, resolved_id, db)
    _load_calibration(profile, resolved_id, db)
    _load_findings_stats(profile, resolved_id, db)

    # Load from Qdrant (non-blocking)
    _load_qdrant_data(profile, resolved_id)

    # Compute baseline HESM
    _compute_baseline_hesm(profile)

    return profile


def _load_goals(profile: HumanEpistemicProfile, project_id: str, db) -> None:
    """Load active goals from SQLite."""
    try:
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT goal_id, objective, status, completion
            FROM goals
            WHERE project_id = ? AND is_completed = 0
            ORDER BY created_timestamp DESC
            LIMIT 20
        """, (project_id,))
        for row in cursor.fetchall():
            profile.active_goals.append(Goal(
                id=row[0],
                objective=row[1] or "",
                status=row[2] or "in_progress",
                completion=row[3] or 0.0,
            ))
    except Exception as e:
        logger.debug(f"Goals load: {e}")


def _load_unknowns(profile: HumanEpistemicProfile, project_id: str, db) -> None:
    """Load open unknowns from SQLite."""
    try:
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT id, unknown, created_timestamp, goal_id
            FROM project_unknowns
            WHERE project_id = ? AND is_resolved = 0
            ORDER BY created_timestamp DESC
            LIMIT 50
        """, (project_id,))
        for row in cursor.fetchall():
            profile.open_unknowns.append(Unknown(
                id=row[0],
                text=row[1] or "",
                created_at=float(row[2]) if row[2] else 0.0,
                goal_id=row[3],
            ))
    except Exception as e:
        logger.debug(f"Unknowns load: {e}")


def _load_calibration(profile: HumanEpistemicProfile, project_id: str, db) -> None:
    """Load calibration biases from SQLite."""
    try:
        cursor = db.conn.cursor()
        # Get most recent calibration entries per vector
        cursor.execute("""
            SELECT vector_name, AVG(bias) as avg_bias
            FROM calibration
            WHERE project_id = ?
            GROUP BY vector_name
        """, (project_id,))
        for row in cursor.fetchall():
            if row[0] and row[1] is not None:
                profile.calibration_biases[row[0]] = round(row[1], 3)
    except Exception as e:
        logger.debug(f"Calibration load: {e}")


def _load_findings_stats(profile: HumanEpistemicProfile, project_id: str, db) -> None:
    """Load findings count and domain distribution from SQLite."""
    try:
        cursor = db.conn.cursor()

        # Total findings
        cursor.execute("""
            SELECT COUNT(*) FROM project_findings WHERE project_id = ?
        """, (project_id,))
        row = cursor.fetchone()
        profile.total_findings = row[0] if row else 0

        # Domain distribution from findings (using subject as domain proxy)
        cursor.execute("""
            SELECT subject, COUNT(*) as cnt, AVG(COALESCE(impact, 0.5)) as avg_impact
            FROM project_findings
            WHERE project_id = ? AND subject IS NOT NULL AND subject != ''
            GROUP BY subject
            ORDER BY cnt DESC
            LIMIT 20
        """, (project_id,))
        for row in cursor.fetchall():
            domain = row[0]
            count = row[1]
            avg_impact = row[2] or 0.5
            profile.domain_exposure_counts[domain] = count
            # Strength = normalized count * average impact
            strength = min(1.0, (count / max(1, profile.total_findings)) * 3.0) * avg_impact
            profile.domain_strengths[domain] = round(strength, 3)

        # Last active domains (from recent findings)
        cursor.execute("""
            SELECT DISTINCT subject FROM project_findings
            WHERE project_id = ? AND subject IS NOT NULL AND subject != ''
            ORDER BY created_timestamp DESC
            LIMIT 5
        """, (project_id,))
        profile.last_active_domains = [row[0] for row in cursor.fetchall()]

    except Exception as e:
        logger.debug(f"Findings stats: {e}")


def _load_qdrant_data(profile: HumanEpistemicProfile, project_id: str) -> None:
    """Load collection stats and assumptions from Qdrant."""
    try:
        from empirica.core.qdrant.connection import _check_qdrant_available, _get_qdrant_client
        if not _check_qdrant_available():
            return

        client = _get_qdrant_client()
        from empirica.core.qdrant.collections import (
            _memory_collection, _eidetic_collection, _docs_collection,
            _episodic_collection, _assumptions_collection,
        )

        # Collection point counts
        for coll_fn, attr in [
            (_memory_collection, "total_findings"),
            (_eidetic_collection, "total_eidetic_facts"),
            (_docs_collection, "total_docs"),
            (_episodic_collection, "total_episodes"),
        ]:
            try:
                coll_name = coll_fn(project_id)
                if client.collection_exists(coll_name):
                    info = client.get_collection(coll_name)
                    count = info.points_count
                    if attr == "total_findings":
                        # Don't overwrite SQLite count, use max
                        profile.total_findings = max(profile.total_findings, count)
                    else:
                        setattr(profile, attr, count)
            except Exception:
                pass

        # Load stale assumptions
        try:
            coll_name = _assumptions_collection(project_id)
            if client.collection_exists(coll_name):
                results = client.scroll(
                    collection_name=coll_name,
                    limit=50,
                    with_payload=True,
                    with_vectors=False,
                )
                points, _ = results
                for point in points:
                    status = point.payload.get("status", "unverified")
                    if status != "unverified":
                        continue
                    urgency = point.payload.get("urgency_signal", 0.0)
                    if urgency < 0.3:
                        continue  # Only include stale ones
                    profile.stale_assumptions.append(Assumption(
                        id=str(point.id),
                        text=point.payload.get("assumption", "")[:200],
                        confidence=point.payload.get("confidence", 0.5),
                        urgency=urgency,
                        domain=point.payload.get("domain"),
                        created_at=float(point.payload.get("timestamp", 0)),
                    ))
                # Sort by urgency descending
                profile.stale_assumptions.sort(key=lambda a: a.urgency, reverse=True)
        except Exception as e:
            logger.debug(f"Assumptions load: {e}")

    except ImportError:
        logger.debug("Qdrant not available for profile assembly")
    except Exception as e:
        logger.debug(f"Qdrant data load: {e}")


def _compute_baseline_hesm(profile: HumanEpistemicProfile) -> None:
    """Compute aggregate HESM baseline from profile data."""
    total = max(1, profile.total_findings + profile.total_eidetic_facts)

    # Exposure: based on total content interacted with
    exposure = min(1.0, total / 100.0)  # Normalize: 100 items = max exposure

    # Comprehension: ratio of eidetic (confirmed) to total
    comprehension = profile.total_eidetic_facts / max(1, total)

    # Retention: penalize for stale assumptions and old content
    staleness_penalty = len(profile.stale_assumptions) * 0.05
    retention = max(0.0, exposure * (1.0 - staleness_penalty))

    # Interest: based on active goals
    interest = min(1.0, len(profile.active_goals) * 0.2)

    # Integration: based on domain diversity
    integration = min(1.0, len(profile.domain_strengths) * 0.1)

    # Uncertainty: based on open unknowns vs total knowledge
    if total > 0:
        uncertainty = min(1.0, len(profile.open_unknowns) / (total * 0.1 + 1))
    else:
        uncertainty = 0.8  # High uncertainty when no data

    # Fluency: proxy from findings count per domain
    avg_strength = sum(profile.domain_strengths.values()) / max(1, len(profile.domain_strengths))
    fluency = avg_strength

    profile.baseline_hesm = HESMState(
        exposure=round(exposure, 3),
        comprehension=round(comprehension, 3),
        fluency=round(fluency, 3),
        context=round(min(1.0, profile.total_docs / 50.0), 3),
        clarity=round(comprehension * 0.8, 3),
        integration=round(integration, 3),
        interest=round(interest, 3),
        density=round(min(1.0, total / 200.0), 3),
        retention=round(retention, 3),
        velocity=0.0,  # Requires temporal data
        completion=0.0,  # Task-specific
        impact=0.0,  # Task-specific
        uncertainty=round(uncertainty, 3),
    )


def profile_for_ai(project_id: str, db=None) -> str:
    """
    Generate a compact text summary of the human's epistemic profile
    for injection into AI bootstrap context.

    Args:
        project_id: Project UUID or name
        db: Optional SessionDatabase

    Returns:
        Compact text summary for AI consumption
    """
    profile = build_profile(project_id, db=db)
    lines = []

    lines.append(f"Human Epistemic Profile ({profile.project_name or project_id})")
    lines.append(f"  Findings: {profile.total_findings} | Eidetic: {profile.total_eidetic_facts} | Docs: {profile.total_docs}")

    if profile.domain_strengths:
        top = sorted(profile.domain_strengths.items(), key=lambda x: x[1], reverse=True)[:5]
        strengths = ", ".join(f"{d} ({v:.2f})" for d, v in top)
        lines.append(f"  Domain strengths: {strengths}")

    if profile.open_unknowns:
        lines.append(f"  Knowledge gaps: {len(profile.open_unknowns)} open unknowns")
        for u in profile.open_unknowns[:3]:
            lines.append(f"    - {u.text[:80]}")

    if profile.stale_assumptions:
        lines.append(f"  Stale assumptions: {len(profile.stale_assumptions)} (urgency > 0.3)")
        for a in profile.stale_assumptions[:2]:
            lines.append(f"    - \"{a.text[:60]}\" (conf={a.confidence:.2f}, urgency={a.urgency:.2f})")

    if profile.calibration_biases:
        biases = ", ".join(f"{k}: {'+' if v > 0 else ''}{v:.2f}" for k, v in profile.calibration_biases.items() if abs(v) > 0.05)
        if biases:
            lines.append(f"  Calibration biases: {biases}")

    if profile.confabulation_risk > 0.2:
        lines.append(f"  Confabulation risk: {profile.confabulation_risk:.2f}")

    if profile.active_goals:
        lines.append(f"  Active goals: {len(profile.active_goals)}")
        for g in profile.active_goals[:3]:
            lines.append(f"    - {g.objective[:80]}")

    return "\n".join(lines)
