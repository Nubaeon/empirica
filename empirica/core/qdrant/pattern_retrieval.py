"""
Pattern Retrieval for Cognitive Workflow Hooks

Provides pattern retrieval for PREFLIGHT (proactive loading) and CHECK (reactive validation).
Integrates with Qdrant memory collections for lessons, dead_ends, and findings.

Defaults:
- similarity_threshold: 0.7
- limit: 3
- optional: True (graceful fail if Qdrant unavailable)
"""
from __future__ import annotations
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Defaults
# NOTE: Threshold lowered to 0.5 because placeholder embeddings (hash-based)
# produce max scores of ~0.55-0.60. Real ML embeddings would score 0.7-0.9.
DEFAULT_THRESHOLD = 0.5
DEFAULT_LIMIT = 3

# Time gap thresholds for human context awareness (in seconds)
# These are metadata signals for Claude, not retrieval quantity controls
TIME_GAP_THRESHOLDS = {
    "continuation": 30 * 60,      # < 30 minutes = likely same work session
    "short_break": 4 * 60 * 60,   # < 4 hours = human took a break
    # > 4 hours = human was away for extended period
}


def compute_time_gap_info(last_session_timestamp: Optional[float] = None) -> Dict[str, any]:
    """
    Compute time gap information since last session.

    Returns metadata for Claude to understand human time context.
    This is a SIGNAL for awareness, not a control for retrieval quantity.

    Args:
        last_session_timestamp: Unix timestamp of last session end (or None if unknown)

    Returns:
        {
            "gap_seconds": float,
            "gap_human_readable": "4h 23m",
            "gap_category": "continuation" | "short_break" | "extended_away",
            "note": "Human-friendly context note"
        }
    """
    import time

    if last_session_timestamp is None:
        return {
            "gap_seconds": None,
            "gap_human_readable": "unknown",
            "gap_category": "unknown",
            "note": "No previous session timestamp available"
        }

    gap_seconds = time.time() - last_session_timestamp

    # Format human-readable
    hours = int(gap_seconds // 3600)
    minutes = int((gap_seconds % 3600) // 60)
    if hours > 0:
        gap_human_readable = f"{hours}h {minutes}m"
    else:
        gap_human_readable = f"{minutes}m"

    # Categorize
    if gap_seconds < TIME_GAP_THRESHOLDS["continuation"]:
        category = "continuation"
        note = "Continuing recent work session"
    elif gap_seconds < TIME_GAP_THRESHOLDS["short_break"]:
        category = "short_break"
        note = f"Returning after {gap_human_readable} break"
    else:
        category = "extended_away"
        note = f"Human was away for {gap_human_readable} - may benefit from context recap"

    return {
        "gap_seconds": gap_seconds,
        "gap_human_readable": gap_human_readable,
        "gap_category": category,
        "note": note
    }


def get_qdrant_url() -> Optional[str]:
    """Check if Qdrant is configured."""
    return os.getenv("EMPIRICA_QDRANT_URL")


def _search_memory_by_type(
    project_id: str,
    query_text: str,
    memory_type: str,
    limit: int = DEFAULT_LIMIT,
    min_score: float = DEFAULT_THRESHOLD
) -> List[Dict]:
    """
    Search memory collection filtered by type.
    Returns empty list if Qdrant not available (optional behavior).
    """
    try:
        from .vector_store import _check_qdrant_available, _get_embedding_safe, _get_qdrant_client, _memory_collection

        if not _check_qdrant_available():
            return []

        qvec = _get_embedding_safe(query_text)
        if qvec is None:
            return []

        from qdrant_client.models import Filter, FieldCondition, MatchValue
        client = _get_qdrant_client()
        coll = _memory_collection(project_id)

        if not client.collection_exists(coll):
            return []

        query_filter = Filter(must=[
            FieldCondition(key="type", match=MatchValue(value=memory_type))
        ])

        results = client.query_points(
            collection_name=coll,
            query=qvec,
            query_filter=query_filter,
            limit=limit,
            with_payload=True
        )

        # Filter by min_score and return
        return [
            {
                "score": getattr(r, 'score', 0.0) or 0.0,
                **{k: v for k, v in (r.payload or {}).items()}
            }
            for r in results.points
            if (getattr(r, 'score', 0.0) or 0.0) >= min_score
        ]
    except Exception as e:
        logger.debug(f"_search_memory_by_type({memory_type}) failed: {e}")
        return []


def _search_calibration_for_task(
    project_id: str,
    task_context: str,
    limit: int = DEFAULT_LIMIT,
) -> List[Dict]:
    """
    Search calibration collection for relevant patterns from similar past tasks.

    Returns calibration warnings like:
    - "For similar tasks, you overestimated completion by 0.31"
    - "Your know vector was accurate for this type of work"
    """
    try:
        from .vector_store import search_calibration_patterns

        results = search_calibration_patterns(
            project_id=project_id,
            query=task_context,
            entry_type="grounded_verification",
            limit=limit,
        )

        warnings = []
        for r in results:
            gaps = r.get("calibration_gaps", {})
            significant_gaps = {
                v: g for v, g in gaps.items() if abs(g) > 0.15
            }
            if significant_gaps:
                overestimates = [f"{v} by +{g:.2f}" for v, g in significant_gaps.items() if g > 0]
                underestimates = [f"{v} by {g:.2f}" for v, g in significant_gaps.items() if g < 0]

                warning = {
                    "session_id": r.get("session_id"),
                    "score": r.get("calibration_score"),
                    "similarity": r.get("score"),
                }
                if overestimates:
                    warning["overestimates"] = f"Overestimated: {', '.join(overestimates)}"
                if underestimates:
                    warning["underestimates"] = f"Underestimated: {', '.join(underestimates)}"
                warnings.append(warning)

        return warnings
    except Exception as e:
        logger.debug(f"_search_calibration_for_task failed: {e}")
        return []


def _check_calibration_bias(
    project_id: str,
    approach: str,
    vectors: Optional[Dict] = None,
) -> Optional[str]:
    """
    Check if historical calibration data suggests systematic bias for this type of work.

    Returns a warning string if bias detected, None otherwise.
    """
    try:
        from .vector_store import search_calibration_patterns

        results = search_calibration_patterns(
            project_id=project_id,
            query=approach,
            entry_type="grounded_verification",
            limit=5,
        )

        if len(results) < 2:
            return None  # Not enough data for pattern detection

        # Aggregate gaps across similar sessions
        gap_totals: Dict[str, List[float]] = {}
        for r in results:
            for v, g in r.get("calibration_gaps", {}).items():
                if v not in gap_totals:
                    gap_totals[v] = []
                gap_totals[v].append(g)

        # Find vectors with consistent bias (same direction across sessions)
        biases = []
        for v, gaps in gap_totals.items():
            if len(gaps) < 2:
                continue
            avg_gap = sum(gaps) / len(gaps)
            # All gaps same sign and average > 0.1
            if abs(avg_gap) > 0.1 and all(g > 0 for g in gaps):
                biases.append(f"{v}: consistently overestimate by +{avg_gap:.2f}")
            elif abs(avg_gap) > 0.1 and all(g < 0 for g in gaps):
                biases.append(f"{v}: consistently underestimate by {avg_gap:.2f}")

        if biases:
            return (
                f"Calibration bias detected for similar tasks ({len(results)} past sessions): "
                + "; ".join(biases)
                + ". Consider applying corrections to your self-assessment."
            )

        return None
    except Exception as e:
        logger.debug(f"_check_calibration_bias failed: {e}")
        return None


def retrieve_task_patterns(
    project_id: str,
    task_context: str,
    threshold: float = DEFAULT_THRESHOLD,
    limit: int = DEFAULT_LIMIT,
    last_session_timestamp: Optional[float] = None,
    include_eidetic: bool = False,
    include_episodic: bool = False,
) -> Dict[str, any]:
    """
    PREFLIGHT hook: Retrieve relevant patterns for a task.

    Returns patterns that should inform the AI before starting work:
    - lessons: Procedural knowledge (HOW to do things)
    - dead_ends: Failed approaches (what NOT to try)
    - relevant_findings: High-impact facts
    - eidetic_facts: Stable facts with confidence (optional)
    - episodic_narratives: Recent session arcs (optional)
    - time_gap: Metadata about time since last session (for human context awareness)

    Args:
        project_id: Project ID
        task_context: Description of the task being undertaken
        threshold: Minimum similarity score (default 0.5)
        limit: Max patterns per type (default 3)
        last_session_timestamp: Used to compute time gap metadata
        include_eidetic: Include eidetic facts in retrieval
        include_episodic: Include episodic narratives in retrieval

    Returns:
        {
            "lessons": [{name, description, domain, confidence, score}],
            "dead_ends": [{approach, why_failed, score}],
            "relevant_findings": [{finding, impact, score}],
            "calibration_warnings": [...],
            "eidetic_facts": [...],  # if include_eidetic
            "episodic_narratives": [...],  # if include_episodic
            "time_gap": {gap_seconds, gap_human_readable, gap_category, note}
        }
    """
    # Compute time gap metadata (signal for Claude, not retrieval control)
    time_gap_info = compute_time_gap_info(last_session_timestamp)

    if not get_qdrant_url():
        return {"lessons": [], "dead_ends": [], "relevant_findings": [], "time_gap": time_gap_info}

    # Search for lessons (procedural knowledge)
    lessons_raw = _search_memory_by_type(
        project_id,
        f"How to: {task_context}",
        "lesson",
        limit,
        threshold
    )
    lessons = [
        {
            "name": l.get("text", "").replace("LESSON: ", "").split(" - ")[0] if l.get("text") else "",
            "description": l.get("text", "").split(" - ")[1].split(" Domain:")[0] if " - " in l.get("text", "") else "",
            "domain": l.get("domain", ""),
            "confidence": l.get("confidence", 0.8),
            "score": l.get("score", 0.0)
        }
        for l in lessons_raw
    ]

    # Search for dead ends (what NOT to try)
    dead_ends_raw = _search_memory_by_type(
        project_id,
        f"Approach for: {task_context}",
        "dead_end",
        limit,
        threshold
    )
    dead_ends = [
        {
            "approach": d.get("text", "").replace("DEAD END: ", "").split(" Why failed:")[0] if d.get("text") else "",
            "why_failed": d.get("text", "").split("Why failed: ")[1] if "Why failed:" in d.get("text", "") else "",
            "score": d.get("score", 0.0)
        }
        for d in dead_ends_raw
    ]

    # Search for relevant findings (high-impact facts)
    findings_raw = _search_memory_by_type(
        project_id,
        task_context,
        "finding",
        limit,
        threshold
    )
    relevant_findings = [
        {
            "finding": f.get("text", ""),
            "impact": f.get("impact", 0.5),
            "score": f.get("score", 0.0)
        }
        for f in findings_raw
    ]

    # Search for calibration warnings (grounded verification gaps from similar tasks)
    calibration_warnings = _search_calibration_for_task(project_id, task_context, limit)

    # Build result
    result = {
        "lessons": lessons,
        "dead_ends": dead_ends,
        "relevant_findings": relevant_findings,
        "calibration_warnings": calibration_warnings,
        "time_gap": time_gap_info,
    }

    # Optional: Include eidetic facts (stable facts with confidence)
    if include_eidetic:
        try:
            from .vector_store import search_eidetic
            eidetic_raw = search_eidetic(
                project_id,
                task_context,
                min_confidence=0.5,
                limit=limit
            )
            result["eidetic_facts"] = [
                {
                    "content": e.get("content", ""),
                    "confidence": e.get("confidence", 0.5),
                    "domain": e.get("domain"),
                    "confirmation_count": e.get("confirmation_count", 1),
                    "score": e.get("score", 0.0)
                }
                for e in eidetic_raw
            ]
        except Exception as e:
            logger.debug(f"Eidetic retrieval failed: {e}")
            result["eidetic_facts"] = []

    # Optional: Include episodic narratives (session arcs with recency decay)
    if include_episodic:
        try:
            from .vector_store import search_episodic
            episodic_raw = search_episodic(
                project_id,
                task_context,
                limit=limit,
                apply_recency_decay=True
            )
            result["episodic_narratives"] = [
                {
                    "narrative": ep.get("narrative", ""),
                    "outcome": ep.get("outcome"),
                    "learning_delta": ep.get("learning_delta", {}),
                    "recency_weight": ep.get("recency_weight", 1.0),
                    "score": ep.get("score", 0.0)
                }
                for ep in episodic_raw
            ]
        except Exception as e:
            logger.debug(f"Episodic retrieval failed: {e}")
            result["episodic_narratives"] = []

    return result


def check_against_patterns(
    project_id: str,
    current_approach: str,
    vectors: Optional[Dict] = None,
    threshold: float = DEFAULT_THRESHOLD,
    limit: int = DEFAULT_LIMIT
) -> Dict[str, any]:
    """
    CHECK hook: Validate current approach against known patterns.

    Returns warnings if the approach matches known failures or
    if vector patterns indicate risk.

    Args:
        project_id: Project ID
        current_approach: Description of current approach/plan
        vectors: Current epistemic vectors (know, uncertainty, etc.)
        threshold: Minimum similarity for dead_end match (default 0.7)
        limit: Max warnings to return (default 3)

    Returns:
        {
            "dead_end_matches": [{approach, why_failed, similarity}],
            "mistake_risk": str or None,
            "has_warnings": bool
        }
    """
    if not get_qdrant_url():
        return {"dead_end_matches": [], "mistake_risk": None, "has_warnings": False}

    warnings = {
        "dead_end_matches": [],
        "mistake_risk": None,
        "has_warnings": False
    }

    # Check if current approach matches known dead ends
    if current_approach:
        dead_ends = _search_memory_by_type(
            project_id,
            f"Approach: {current_approach}",
            "dead_end",
            limit,
            threshold
        )

        warnings["dead_end_matches"] = [
            {
                "approach": d.get("text", "").replace("DEAD END: ", "").split(" Why failed:")[0] if d.get("text") else "",
                "why_failed": d.get("text", "").split("Why failed: ")[1] if "Why failed:" in d.get("text", "") else "",
                "similarity": d.get("score", 0.0)
            }
            for d in dead_ends
        ]

    # Check vector patterns for mistake risk
    if vectors:
        know = vectors.get("know", 0.5)
        uncertainty = vectors.get("uncertainty", 0.5)

        # High uncertainty + low know = historical mistake pattern
        if uncertainty >= 0.5 and know <= 0.4:
            warnings["mistake_risk"] = (
                f"High risk pattern: uncertainty={uncertainty:.2f}, know={know:.2f}. "
                "Historical data shows mistakes occur when acting with high uncertainty and low knowledge. "
                "Consider more investigation before proceeding."
            )
        # Acting with very low context awareness
        elif vectors.get("context", 0.5) <= 0.3:
            warnings["mistake_risk"] = (
                f"Low context awareness ({vectors.get('context', 0):.2f}). "
                "Proceeding without understanding current state increases mistake probability."
            )

    # Check calibration history for systematic bias
    calibration_bias = _check_calibration_bias(project_id, current_approach, vectors)
    if calibration_bias:
        warnings["calibration_bias"] = calibration_bias

    # Set has_warnings flag
    warnings["has_warnings"] = (
        bool(warnings["dead_end_matches"])
        or bool(warnings["mistake_risk"])
        or bool(warnings.get("calibration_bias"))
    )

    return warnings


def search_lessons_for_task(
    project_id: str,
    task_context: str,
    domain: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
    min_score: float = DEFAULT_THRESHOLD
) -> List[Dict]:
    """
    Search for relevant lessons for a specific task.
    Optionally filter by domain.

    Args:
        project_id: Project ID
        task_context: What you're trying to do
        domain: Optional domain filter (e.g., "notebooklm", "git")
        limit: Max results
        min_score: Minimum similarity score

    Returns:
        List of lessons with name, description, domain, confidence, score
    """
    try:
        from .vector_store import _check_qdrant_available, _get_embedding_safe, _get_qdrant_client, _memory_collection

        if not _check_qdrant_available():
            return []

        qvec = _get_embedding_safe(f"Lesson for: {task_context}")
        if qvec is None:
            return []

        from qdrant_client.models import Filter, FieldCondition, MatchValue
        client = _get_qdrant_client()
        coll = _memory_collection(project_id)

        if not client.collection_exists(coll):
            return []

        # Build filter
        conditions = [FieldCondition(key="type", match=MatchValue(value="lesson"))]
        if domain:
            conditions.append(FieldCondition(key="domain", match=MatchValue(value=domain)))

        query_filter = Filter(must=conditions)

        results = client.query_points(
            collection_name=coll,
            query=qvec,
            query_filter=query_filter,
            limit=limit,
            with_payload=True
        )

        lessons = []
        for r in results.points:
            score = getattr(r, 'score', 0.0) or 0.0
            if score < min_score:
                continue

            payload = r.payload or {}
            text = payload.get("text", "")

            # Parse the embedded text format: "LESSON: name - description Domain: domain"
            name = text.replace("LESSON: ", "").split(" - ")[0] if text else ""
            desc = text.split(" - ")[1].split(" Domain:")[0] if " - " in text else ""

            lessons.append({
                "name": name,
                "description": desc,
                "domain": payload.get("domain", ""),
                "confidence": payload.get("confidence", 0.8),
                "tags": payload.get("tags", []),
                "score": score
            })

        return lessons
    except Exception as e:
        logger.debug(f"search_lessons_for_task failed: {e}")
        return []
