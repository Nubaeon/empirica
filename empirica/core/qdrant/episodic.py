"""
Episodic memory: session narratives with temporal decay.
"""
from __future__ import annotations
import logging
from typing import Dict, List, Optional

from empirica.core.qdrant.connection import (
    _check_qdrant_available, _get_qdrant_imports, _get_qdrant_client,
    _get_embedding_safe, _get_vector_size, logger,
)
from empirica.core.qdrant.collections import _episodic_collection

def embed_episodic(
    project_id: str,
    episode_id: str,
    narrative: str,
    episode_type: str = "session_arc",
    session_id: str = None,
    ai_id: str = None,
    goal_id: str = None,
    learning_delta: Dict[str, float] = None,
    outcome: str = None,
    key_moments: List[str] = None,
    tags: List[str] = None,
    timestamp: float = None,
) -> bool:
    """
    Embed an episodic memory entry (session narrative with temporal decay).

    Episodic memory stores contextual narratives:
    - Session arcs, decisions, investigations, discoveries
    - Includes learning delta (PREFLIGHT → POSTFLIGHT)
    - Recency weight decays over time

    Returns True if successful, False if Qdrant not available.
    """
    if not _check_qdrant_available():
        return False

    try:
        _, Distance, VectorParams, PointStruct = _get_qdrant_imports()
        client = _get_qdrant_client()
        coll = _episodic_collection(project_id)

        if not client.collection_exists(coll):
            vector_size = _get_vector_size()
            client.create_collection(coll, vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE))

        vector = _get_embedding_safe(narrative)
        if vector is None:
            return False

        import hashlib
        import time

        now = timestamp or time.time()

        payload = {
            "type": episode_type,  # session_arc, decision, investigation, discovery, mistake
            "narrative": narrative[:1000] if narrative else None,
            "narrative_full": narrative if len(narrative) <= 1000 else None,
            "session_id": session_id,
            "ai_id": ai_id,
            "goal_id": goal_id,
            "timestamp": now,
            "learning_delta": learning_delta or {},
            "outcome": outcome,  # success, partial, failure, abandoned
            "key_moments": key_moments or [],
            "tags": tags or [],
            "recency_weight": 1.0,  # Starts at 1.0, decays over time
        }

        point_id = int(hashlib.md5(episode_id.encode()).hexdigest()[:15], 16)
        point = PointStruct(id=point_id, vector=vector, payload=payload)
        client.upsert(collection_name=coll, points=[point])
        return True
    except Exception as e:
        logger.warning(f"Failed to embed episodic: {e}")
        return False


def search_episodic(
    project_id: str,
    query: str,
    episode_type: str = None,
    ai_id: str = None,
    outcome: str = None,
    min_recency_weight: float = 0.0,
    limit: int = 5,
    apply_recency_decay: bool = True,
) -> List[Dict]:
    """
    Search episodic memory for relevant narratives.

    Args:
        project_id: Project UUID
        query: Semantic search query
        episode_type: Filter by type (session_arc, decision, etc.)
        ai_id: Filter by AI ID
        outcome: Filter by outcome (success, failure, etc.)
        min_recency_weight: Minimum recency threshold (filters old episodes)
        limit: Max results
        apply_recency_decay: If True, multiply score by recency weight

    Returns:
        List of matching episodic entries with scores
    """
    if not _check_qdrant_available():
        return []

    try:
        client = _get_qdrant_client()
        coll = _episodic_collection(project_id)

        if not client.collection_exists(coll):
            return []

        vector = _get_embedding_safe(query)
        if vector is None:
            return []

        from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

        conditions = []
        if episode_type:
            conditions.append(FieldCondition(key="type", match=MatchValue(value=episode_type)))
        if ai_id:
            conditions.append(FieldCondition(key="ai_id", match=MatchValue(value=ai_id)))
        if outcome:
            conditions.append(FieldCondition(key="outcome", match=MatchValue(value=outcome)))

        query_filter = Filter(must=conditions) if conditions else None

        # Get more results than needed to apply recency filtering
        results = client.query_points(
            collection_name=coll,
            query=vector,
            query_filter=query_filter,
            limit=limit * 2,  # Get extra for filtering
            with_payload=True,
        )

        import time
        now = time.time()

        processed = []
        for r in results.points:
            timestamp = r.payload.get("timestamp", now)

            # Calculate recency weight based on age
            age_days = (now - timestamp) / 86400  # seconds to days

            # Decay formula: starts at 1.0, decays to 0.05 over ~1 year
            if age_days <= 1:
                recency = 1.0
            elif age_days <= 7:
                recency = 0.95 - (0.15 * (age_days - 1) / 6)  # 0.95 → 0.80
            elif age_days <= 30:
                recency = 0.80 - (0.30 * (age_days - 7) / 23)  # 0.80 → 0.50
            elif age_days <= 90:
                recency = 0.50 - (0.25 * (age_days - 30) / 60)  # 0.50 → 0.25
            elif age_days <= 365:
                recency = 0.25 - (0.15 * (age_days - 90) / 275)  # 0.25 → 0.10
            else:
                recency = max(0.05, 0.10 - (0.05 * (age_days - 365) / 365))  # → 0.05 min

            if recency < min_recency_weight:
                continue

            # Apply recency to score if enabled
            effective_score = r.score * recency if apply_recency_decay else r.score

            processed.append({
                "id": str(r.id),
                "score": effective_score,
                "raw_score": r.score,
                "recency_weight": recency,
                "narrative": r.payload.get("narrative_full") or r.payload.get("narrative"),
                "type": r.payload.get("type"),
                "session_id": r.payload.get("session_id"),
                "ai_id": r.payload.get("ai_id"),
                "goal_id": r.payload.get("goal_id"),
                "learning_delta": r.payload.get("learning_delta", {}),
                "outcome": r.payload.get("outcome"),
                "key_moments": r.payload.get("key_moments", []),
                "tags": r.payload.get("tags", []),
                "timestamp": timestamp,
            })

        # Sort by effective score and limit
        processed.sort(key=lambda x: x["score"], reverse=True)
        return processed[:limit]
    except Exception as e:
        logger.warning(f"Failed to search episodic: {e}")
        return []


def create_session_episode(
    project_id: str,
    session_id: str,
    ai_id: str,
    goal_objective: str = None,
    preflight_vectors: Dict[str, float] = None,
    postflight_vectors: Dict[str, float] = None,
    findings: List[str] = None,
    unknowns: List[str] = None,
    outcome: str = None,
) -> bool:
    """
    Create an episodic entry from a completed session.

    Called automatically after POSTFLIGHT to capture the session narrative.
    Generates a narrative summary from the session data.

    Args:
        project_id: Project UUID
        session_id: Session UUID
        ai_id: AI identifier
        goal_objective: What was being worked on
        preflight_vectors: Starting epistemic state
        postflight_vectors: Ending epistemic state
        findings: Key findings from session
        unknowns: Remaining unknowns
        outcome: Session outcome (success, partial, failure)

    Returns:
        True if episode created successfully
    """
    import uuid
    import time

    # Calculate learning delta
    learning_delta = {}
    if preflight_vectors and postflight_vectors:
        for key in ["know", "uncertainty", "context", "completion"]:
            pre = preflight_vectors.get(key, 0.5)
            post = postflight_vectors.get(key, 0.5)
            delta = post - pre
            if abs(delta) >= 0.05:  # Only track meaningful changes
                learning_delta[key] = round(delta, 2)

    # Generate narrative
    narrative_parts = []

    if goal_objective:
        narrative_parts.append(f"Working on: {goal_objective}")

    if learning_delta:
        delta_str = ", ".join([f"{k}: {'+' if v > 0 else ''}{v}" for k, v in learning_delta.items()])
        narrative_parts.append(f"Learning: {delta_str}")

    if findings:
        narrative_parts.append(f"Key findings: {'; '.join(findings[:3])}")

    if unknowns:
        narrative_parts.append(f"Open questions: {'; '.join(unknowns[:2])}")

    if outcome:
        narrative_parts.append(f"Outcome: {outcome}")

    narrative = ". ".join(narrative_parts)

    # Key moments from significant learning
    key_moments = []
    if learning_delta.get("know", 0) > 0.15:
        key_moments.append("significant_knowledge_gain")
    if learning_delta.get("uncertainty", 0) < -0.15:
        key_moments.append("uncertainty_reduced")
    if outcome == "failure":
        key_moments.append("learning_from_failure")

    return embed_episodic(
        project_id=project_id,
        episode_id=str(uuid.uuid4()),
        narrative=narrative,
        episode_type="session_arc",
        session_id=session_id,
        ai_id=ai_id,
        goal_id=None,  # Could be linked if passed
        learning_delta=learning_delta,
        outcome=outcome,
        key_moments=key_moments,
        tags=[ai_id] if ai_id else [],
        timestamp=time.time(),
    )
