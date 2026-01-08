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


def retrieve_task_patterns(
    project_id: str,
    task_context: str,
    threshold: float = DEFAULT_THRESHOLD,
    limit: int = DEFAULT_LIMIT
) -> Dict[str, List[Dict]]:
    """
    PREFLIGHT hook: Retrieve relevant patterns for a task.

    Returns patterns that should inform the AI before starting work:
    - lessons: Procedural knowledge (HOW to do things)
    - dead_ends: Failed approaches (what NOT to try)
    - relevant_findings: High-impact facts

    Args:
        project_id: Project ID
        task_context: Description of the task being undertaken
        threshold: Minimum similarity score (default 0.7)
        limit: Max patterns per type (default 3)

    Returns:
        {
            "lessons": [{name, description, domain, confidence, score}],
            "dead_ends": [{approach, why_failed, score}],
            "relevant_findings": [{finding, impact, score}]
        }
    """
    if not get_qdrant_url():
        return {"lessons": [], "dead_ends": [], "relevant_findings": []}

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

    return {
        "lessons": lessons,
        "dead_ends": dead_ends,
        "relevant_findings": relevant_findings
    }


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

    # Set has_warnings flag
    warnings["has_warnings"] = bool(warnings["dead_end_matches"]) or bool(warnings["mistake_risk"])

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
