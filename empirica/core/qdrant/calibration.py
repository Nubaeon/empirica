"""
Grounded calibration: verification embedding and trajectory analysis.
"""
from __future__ import annotations
import logging
from typing import Dict, List, Optional

from empirica.core.qdrant.connection import (
    _check_qdrant_available, _get_qdrant_imports, _get_qdrant_client,
    _get_embedding_safe, _get_vector_size, logger,
)
from empirica.core.qdrant.collections import _calibration_collection

def embed_grounded_verification(
    project_id: str,
    verification_id: str,
    session_id: str,
    ai_id: str = "claude-code",
    self_assessed: Dict[str, float] = None,
    grounded_vectors: Dict[str, float] = None,
    calibration_gaps: Dict[str, float] = None,
    grounded_coverage: float = 0.0,
    calibration_score: float = 0.0,
    evidence_count: int = 0,
    sources: List[str] = None,
    goal_id: str = None,
    timestamp: float = None,
) -> bool:
    """
    Embed a grounded verification summary to the calibration collection.

    Enables semantic search for calibration patterns:
    - "Find sessions where I overestimated completion"
    - "Show calibration gaps similar to this task"
    - "When was my know vector most accurate?"

    Returns True if successful, False if Qdrant not available.
    """
    if not _check_qdrant_available():
        return False

    try:
        _, Distance, VectorParams, PointStruct = _get_qdrant_imports()
        client = _get_qdrant_client()
        coll = _calibration_collection(project_id)

        if not client.collection_exists(coll):
            vector_size = _get_vector_size()
            client.create_collection(coll, vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE))

        # Build semantic text from calibration gaps for embedding
        gap_descriptions = []
        for vector_name, gap in (calibration_gaps or {}).items():
            direction = "overestimated" if gap > 0.05 else "underestimated" if gap < -0.05 else "accurate"
            gap_descriptions.append(f"{vector_name}: {direction} by {abs(gap):.2f}")

        text = (
            f"Grounded calibration verification. "
            f"Coverage: {grounded_coverage:.0%}. "
            f"Overall calibration score: {calibration_score:.3f}. "
            f"Evidence sources: {', '.join(sources or [])}. "
            f"Gaps: {'; '.join(gap_descriptions)}"
        )

        vector = _get_embedding_safe(text)
        if vector is None:
            return False

        import hashlib
        import time as time_mod

        payload = {
            "type": "grounded_verification",
            "session_id": session_id,
            "ai_id": ai_id,
            "goal_id": goal_id,
            "self_assessed": self_assessed or {},
            "grounded_vectors": grounded_vectors or {},
            "calibration_gaps": calibration_gaps or {},
            "grounded_coverage": grounded_coverage,
            "calibration_score": calibration_score,
            "evidence_count": evidence_count,
            "sources": sources or [],
            "timestamp": timestamp or time_mod.time(),
        }

        point_id = int(hashlib.md5(verification_id.encode()).hexdigest()[:15], 16)
        point = PointStruct(id=point_id, vector=vector, payload=payload)
        client.upsert(collection_name=coll, points=[point])
        return True
    except Exception as e:
        logger.warning(f"Failed to embed grounded verification: {e}")
        return False


def embed_calibration_trajectory(
    project_id: str,
    session_id: str,
    ai_id: str = "claude-code",
    self_assessed: Dict[str, float] = None,
    grounded_vectors: Dict[str, float] = None,
    calibration_gaps: Dict[str, float] = None,
    goal_id: str = None,
    timestamp: float = None,
) -> bool:
    """
    Embed a calibration trajectory point — one per POSTFLIGHT.

    Trajectory points enable trend detection:
    - "Is my calibration improving over time?"
    - "Which vectors am I getting better/worse at?"
    - "Show my accuracy trajectory for security tasks"

    Returns True if successful, False if Qdrant not available.
    """
    if not _check_qdrant_available():
        return False

    try:
        _, Distance, VectorParams, PointStruct = _get_qdrant_imports()
        client = _get_qdrant_client()
        coll = _calibration_collection(project_id)

        if not client.collection_exists(coll):
            vector_size = _get_vector_size()
            client.create_collection(coll, vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE))

        # Build semantic text for trajectory point
        improving = []
        worsening = []
        for v, gap in (calibration_gaps or {}).items():
            if abs(gap) < 0.1:
                improving.append(v)
            elif abs(gap) > 0.25:
                worsening.append(v)

        text = (
            f"Calibration trajectory point. "
            f"Well-calibrated: {', '.join(improving) if improving else 'none'}. "
            f"Needs work: {', '.join(worsening) if worsening else 'none'}. "
            f"Vectors assessed: {', '.join((self_assessed or {}).keys())}"
        )

        vector = _get_embedding_safe(text)
        if vector is None:
            return False

        import hashlib
        import time as time_mod

        now = timestamp or time_mod.time()

        payload = {
            "type": "calibration_trajectory",
            "session_id": session_id,
            "ai_id": ai_id,
            "goal_id": goal_id,
            "self_assessed": self_assessed or {},
            "grounded_vectors": grounded_vectors or {},
            "calibration_gaps": calibration_gaps or {},
            "timestamp": now,
        }

        # Use session_id + "trajectory" for deterministic point ID
        point_id = int(hashlib.md5(f"{session_id}_trajectory".encode()).hexdigest()[:15], 16)
        point = PointStruct(id=point_id, vector=vector, payload=payload)
        client.upsert(collection_name=coll, points=[point])
        return True
    except Exception as e:
        logger.warning(f"Failed to embed calibration trajectory: {e}")
        return False


def search_calibration_patterns(
    project_id: str,
    query: str,
    ai_id: str = None,
    entry_type: str = None,
    min_calibration_score: float = None,
    limit: int = 5,
) -> List[Dict]:
    """
    Search calibration data for patterns.

    Use cases:
    - "overconfident about completion" → finds sessions with positive completion gaps
    - "security task calibration" → finds calibration for similar tasks
    - "when was I most accurate" → finds low calibration_score entries

    Args:
        project_id: Project UUID
        query: Semantic search query
        ai_id: Filter by AI ID
        entry_type: Filter by type (grounded_verification, calibration_trajectory)
        min_calibration_score: Minimum calibration score threshold
        limit: Max results

    Returns:
        List of matching calibration entries with scores
    """
    if not _check_qdrant_available():
        return []

    try:
        client = _get_qdrant_client()
        coll = _calibration_collection(project_id)

        if not client.collection_exists(coll):
            return []

        vector = _get_embedding_safe(query)
        if vector is None:
            return []

        from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

        conditions = []
        if ai_id:
            conditions.append(FieldCondition(key="ai_id", match=MatchValue(value=ai_id)))
        if entry_type:
            conditions.append(FieldCondition(key="type", match=MatchValue(value=entry_type)))
        if min_calibration_score is not None:
            conditions.append(FieldCondition(key="calibration_score", range=Range(gte=min_calibration_score)))

        query_filter = Filter(must=conditions) if conditions else None

        results = client.query_points(
            collection_name=coll,
            query=vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )

        return [
            {
                "id": str(r.id),
                "score": r.score,
                "type": r.payload.get("type"),
                "session_id": r.payload.get("session_id"),
                "ai_id": r.payload.get("ai_id"),
                "calibration_gaps": r.payload.get("calibration_gaps", {}),
                "calibration_score": r.payload.get("calibration_score"),
                "grounded_coverage": r.payload.get("grounded_coverage"),
                "self_assessed": r.payload.get("self_assessed", {}),
                "grounded_vectors": r.payload.get("grounded_vectors", {}),
                "sources": r.payload.get("sources", []),
                "timestamp": r.payload.get("timestamp"),
            }
            for r in results.points
        ]
    except Exception as e:
        logger.warning(f"Failed to search calibration patterns: {e}")
        return []


# =============================================================================
# NOETIC RAG: Forward-Compatible Intent Layer Collections
# =============================================================================
# These embed/search functions are ready for use when CLI commands
# (assumption-log, decision-log, intent-forward/reverse) are implemented.
# Until then, collections exist but are empty — zero overhead.

