"""
Qdrant vector store for Empirica projects.
Collections per project:
- project_{project_id}_docs: documentation embeddings with metadata
- project_{project_id}_memory: findings/unknowns/mistakes/dead_ends embeddings

NOTE: This module is OPTIONAL. Empirica core works without Qdrant.
Set EMPIRICA_ENABLE_EMBEDDINGS=true to enable semantic search features.
If qdrant-client is not installed, all functions gracefully return empty/False.
"""
from __future__ import annotations
import os
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Lazy imports - Qdrant is optional
_qdrant_available = None
_qdrant_warned = False

def _check_qdrant_available() -> bool:
    """Check if Qdrant is available and enabled."""
    global _qdrant_available, _qdrant_warned

    if _qdrant_available is not None:
        return _qdrant_available

    # Check if embeddings are enabled (default: True if qdrant available)
    enable_flag = os.getenv("EMPIRICA_ENABLE_EMBEDDINGS", "").lower()
    if enable_flag == "false":
        _qdrant_available = False
        return False

    try:
        from qdrant_client import QdrantClient  # noqa
        _qdrant_available = True
        return True
    except ImportError:
        if not _qdrant_warned:
            logger.debug("qdrant-client not installed. Semantic search disabled. Install with: pip install qdrant-client")
            _qdrant_warned = True
        _qdrant_available = False
        return False


def _get_qdrant_imports():
    """Lazy import Qdrant dependencies."""
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    return QdrantClient, Distance, VectorParams, PointStruct


def _get_embedding_safe(text: str) -> Optional[List[float]]:
    """Get embedding with graceful fallback."""
    try:
        from .embeddings import get_embedding
        return get_embedding(text)
    except Exception as e:
        logger.debug(f"Embedding failed: {e}")
        return None


def _get_vector_size() -> int:
    """Get vector size from embeddings provider. Defaults to 1536 on error."""
    try:
        from .embeddings import get_vector_size
        return get_vector_size()
    except Exception as e:
        logger.debug(f"Could not get vector size: {e}, defaulting to 1536")
        return 1536


def _get_qdrant_client():
    """Get Qdrant client with lazy imports."""
    QdrantClient, _, _, _ = _get_qdrant_imports()
    url = os.getenv("EMPIRICA_QDRANT_URL")
    path = os.getenv("EMPIRICA_QDRANT_PATH", "./.qdrant_data")
    if url:
        return QdrantClient(url=url)
    return QdrantClient(path=path)


def _docs_collection(project_id: str) -> str:
    return f"project_{project_id}_docs"


def _memory_collection(project_id: str) -> str:
    return f"project_{project_id}_memory"


def _epistemics_collection(project_id: str) -> str:
    """Collection for epistemic learning trajectories (PREFLIGHT → POSTFLIGHT deltas)"""
    return f"project_{project_id}_epistemics"


def _global_learnings_collection() -> str:
    """Global collection for high-impact learnings across all projects."""
    return "global_learnings"


def init_collections(project_id: str) -> bool:
    """Initialize Qdrant collections. Returns False if Qdrant not available."""
    if not _check_qdrant_available():
        return False

    try:
        _, Distance, VectorParams, _ = _get_qdrant_imports()
        client = _get_qdrant_client()
        vector_size = _get_vector_size()
        for name in (_docs_collection(project_id), _memory_collection(project_id), _epistemics_collection(project_id)):
            if not client.collection_exists(name):
                client.create_collection(name, vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE))
                logger.info(f"Created collection {name} with vector size {vector_size}")
        return True
    except Exception as e:
        logger.debug(f"Failed to init Qdrant collections: {e}")
        return False


def embed_single_memory_item(
    project_id: str,
    item_id: str,
    text: str,
    item_type: str,
    session_id: str = None,
    goal_id: str = None,
    subtask_id: str = None,
    subject: str = None,
    impact: float = None,
    is_resolved: bool = None,
    resolved_by: str = None,
    timestamp: str = None
) -> bool:
    """
    Embed a single memory item (finding, unknown, mistake, dead_end) to Qdrant.
    Called automatically when logging epistemic breadcrumbs.

    Returns True if successful, False if Qdrant not available or embedding failed.
    This is a non-blocking operation - core Empirica works without it.
    """
    # Check if Qdrant is available (graceful degradation)
    if not _check_qdrant_available():
        return False

    try:
        _, Distance, VectorParams, PointStruct = _get_qdrant_imports()
        client = _get_qdrant_client()
        coll = _memory_collection(project_id)

        # Ensure collection exists
        if not client.collection_exists(coll):
            vector_size = _get_vector_size()
            client.create_collection(coll, vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE))

        vector = _get_embedding_safe(text)
        if vector is None:
            return False

        payload = {
            "type": item_type,
            "text": text[:500] if text else None,
            "text_full": text if len(text) <= 500 else None,
            "session_id": session_id,
            "goal_id": goal_id,
            "subtask_id": subtask_id,
            "subject": subject,
            "impact": impact,
            "is_resolved": is_resolved,
            "resolved_by": resolved_by,
            "timestamp": timestamp,
        }

        # Use hash of item_id for numeric Qdrant point ID
        import hashlib
        point_id = int(hashlib.md5(item_id.encode()).hexdigest()[:15], 16)

        point = PointStruct(id=point_id, vector=vector, payload=payload)
        client.upsert(collection_name=coll, points=[point])
        return True
    except Exception as e:
        # Log but don't fail - embedding is enhancement, not critical path
        import logging
        logging.getLogger(__name__).warning(f"Failed to embed memory item: {e}")
        return False


def upsert_docs(project_id: str, docs: List[Dict]) -> int:
    """
    Upsert documentation embeddings.
    docs: List of {id, text, metadata:{doc_path, tags, concepts, questions, use_cases}}
    Returns number of docs upserted, or 0 if Qdrant not available.
    """
    if not _check_qdrant_available():
        return 0

    try:
        _, _, _, PointStruct = _get_qdrant_imports()
        client = _get_qdrant_client()
        coll = _docs_collection(project_id)
        points = []
        for d in docs:
            vector = _get_embedding_safe(d.get("text", ""))
            if vector is None:
                continue
            payload = {
                "doc_path": d.get("metadata", {}).get("doc_path"),
                "tags": d.get("metadata", {}).get("tags", []),
                "concepts": d.get("metadata", {}).get("concepts", []),
                "questions": d.get("metadata", {}).get("questions", []),
                "use_cases": d.get("metadata", {}).get("use_cases", []),
            }
            points.append(PointStruct(id=d["id"], vector=vector, payload=payload))
        if points:
            client.upsert(collection_name=coll, points=points)
        return len(points)
    except Exception as e:
        logger.warning(f"Failed to upsert docs: {e}")
        return 0


def upsert_memory(project_id: str, items: List[Dict]) -> int:
    """
    Upsert memory embeddings (findings, unknowns, mistakes, dead_ends).
    items: List of {id, text, type, goal_id, subtask_id, session_id, timestamp, ...}
    Returns number of items upserted, or 0 if Qdrant not available.
    """
    if not _check_qdrant_available():
        return 0

    try:
        _, _, _, PointStruct = _get_qdrant_imports()
        client = _get_qdrant_client()
        coll = _memory_collection(project_id)
        points = []
        for it in items:
            text = it.get("text", "")
            vector = _get_embedding_safe(text)
            if vector is None:
                continue
            # Store full metadata for epistemic lineage tracking
            payload = {
                "type": it.get("type", "unknown"),
                "text": text[:500] if text else None,
                "text_full": text if len(text) <= 500 else None,
                "goal_id": it.get("goal_id"),
                "subtask_id": it.get("subtask_id"),
                "session_id": it.get("session_id"),
                "timestamp": it.get("timestamp"),
                "subject": it.get("subject"),
                "impact": it.get("impact"),
                "is_resolved": it.get("is_resolved"),
                "resolved_by": it.get("resolved_by"),
            }
            points.append(PointStruct(id=it["id"], vector=vector, payload=payload))
        if points:
            client.upsert(collection_name=coll, points=points)
        return len(points)
    except Exception as e:
        logger.warning(f"Failed to upsert memory: {e}")
        return 0


def _service_url() -> Optional[str]:
    return os.getenv("EMPIRICA_QDRANT_URL")


def _rest_search(collection: str, vector: List[float], limit: int) -> List[Dict]:
    """REST-based search (requires EMPIRICA_QDRANT_URL)."""
    try:
        import requests
        url = _service_url()
        if not url:
            return []
        resp = requests.post(
            f"{url}/collections/{collection}/points/search",
            json={"vector": vector, "limit": limit, "with_payload": True},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("result", [])
    except Exception as e:
        logger.debug(f"REST search failed: {e}")
        return []


def search(project_id: str, query_text: str, kind: str = "all", limit: int = 5) -> Dict[str, List[Dict]]:
    """
    Semantic search over project docs and memory.
    Returns empty results if Qdrant not available.
    """
    empty_result = {"docs": [], "memory": []} if kind == "all" else {kind: []}

    if not _check_qdrant_available():
        return empty_result

    qvec = _get_embedding_safe(query_text)
    if qvec is None:
        return empty_result

    results: Dict[str, List[Dict]] = {}
    client = _get_qdrant_client()

    # Query each collection independently (so one failure doesn't block the other)
    if kind in ("all", "docs"):
        try:
            docs_coll = _docs_collection(project_id)
            if client.collection_exists(docs_coll):
                rd = client.query_points(
                    collection_name=docs_coll,
                    query=qvec,
                    limit=limit,
                    with_payload=True
                )
                results["docs"] = [
                    {
                        "score": getattr(r, 'score', 0.0) or 0.0,
                        "doc_path": (r.payload or {}).get("doc_path"),
                        "tags": (r.payload or {}).get("tags"),
                        "concepts": (r.payload or {}).get("concepts"),
                    }
                    for r in rd.points
                ]
            else:
                results["docs"] = []
        except Exception as e:
            logger.debug(f"docs query failed: {e}")
            results["docs"] = []

    if kind in ("all", "memory"):
        try:
            mem_coll = _memory_collection(project_id)
            if client.collection_exists(mem_coll):
                rm = client.query_points(
                    collection_name=mem_coll,
                    query=qvec,
                    limit=limit,
                    with_payload=True
                )
                results["memory"] = [
                    {
                        "score": getattr(r, 'score', 0.0) or 0.0,
                        "type": (r.payload or {}).get("type"),
                        "text": (r.payload or {}).get("text"),
                        "session_id": (r.payload or {}).get("session_id"),
                        "goal_id": (r.payload or {}).get("goal_id"),
                    }
                    for r in rm.points
                ]
            else:
                results["memory"] = []
        except Exception as e:
            logger.debug(f"memory query failed: {e}")
            results["memory"] = []

    if results:
        return results

    # REST fallback only if client queries produced nothing
    logger.debug("Trying REST fallback for search")

    # REST fallback (for remote Qdrant server)
    try:
        if kind in ("all", "docs"):
            rd = _rest_search(_docs_collection(project_id), qvec, limit)
            results["docs"] = [
                {
                    "score": d.get('score', 0.0),
                    "doc_path": (d.get('payload') or {}).get('doc_path'),
                    "tags": (d.get('payload') or {}).get('tags'),
                    "concepts": (d.get('payload') or {}).get('concepts'),
                }
                for d in rd
            ]
        if kind in ("all", "memory"):
            rm = _rest_search(_memory_collection(project_id), qvec, limit)
            results["memory"] = [
                {
                    "score": m.get('score', 0.0),
                    "type": (m.get('payload') or {}).get('type'),
                }
                for m in rm
            ]
        return results
    except Exception as e:
        logger.debug(f"REST search also failed: {e}")
        return empty_result


def upsert_epistemics(project_id: str, items: List[Dict]) -> int:
    """
    Store epistemic learning trajectories (PREFLIGHT → POSTFLIGHT deltas).
    Returns number of items upserted, or 0 if Qdrant not available.
    """
    if not _check_qdrant_available():
        return 0

    try:
        _, _, _, PointStruct = _get_qdrant_imports()
        client = _get_qdrant_client()
        coll = _epistemics_collection(project_id)
        points = []

        for item in items:
            vector = _get_embedding_safe(item.get("text", ""))
            if vector is None:
                continue
            payload = item.get("metadata", {})
            points.append(PointStruct(id=item["id"], vector=vector, payload=payload))

        if points:
            client.upsert(collection_name=coll, points=points)
        return len(points)
    except Exception as e:
        logger.warning(f"Failed to upsert epistemics: {e}")
        return 0


def search_epistemics(
    project_id: str,
    query_text: str,
    filters: Optional[Dict] = None,
    limit: int = 5
) -> List[Dict]:
    """
    Search epistemic learning trajectories by semantic similarity.
    Returns empty list if Qdrant not available.
    """
    if not _check_qdrant_available():
        return []

    qvec = _get_embedding_safe(query_text)
    if qvec is None:
        return []

    try:
        client = _get_qdrant_client()
        coll = _epistemics_collection(project_id)
        results = client.query_points(
            collection_name=coll,
            query=qvec,
            limit=limit,
            with_payload=True
        )
        return [
            {
                "score": getattr(r, 'score', 0.0) or 0.0,
                **(r.payload or {})
            }
            for r in results.points
        ]
    except Exception as e:
        logger.debug(f"search_epistemics failed: {e}")

    # REST fallback
    try:
        coll = _epistemics_collection(project_id)
        rd = _rest_search(coll, qvec, limit)
        return [
            {
                "score": d.get('score', 0.0),
                **(d.get('payload') or {})
            }
            for d in rd
        ]
    except Exception as e:
        logger.debug(f"search_epistemics REST fallback failed: {e}")
        return []


# ============================================================================
# GLOBAL LEARNINGS - Cross-project knowledge aggregation
# ============================================================================

def init_global_collection() -> bool:
    """Initialize global learnings collection. Returns False if Qdrant not available."""
    if not _check_qdrant_available():
        return False

    try:
        _, Distance, VectorParams, _ = _get_qdrant_imports()
        client = _get_qdrant_client()
        coll = _global_learnings_collection()
        if not client.collection_exists(coll):
            vector_size = _get_vector_size()
            client.create_collection(coll, vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE))
            logger.info(f"Created global_learnings collection with vector size {vector_size}")
        return True
    except Exception as e:
        logger.debug(f"Failed to init global collection: {e}")
        return False


def embed_to_global(
    item_id: str,
    text: str,
    item_type: str,
    project_id: str,
    session_id: str = None,
    impact: float = None,
    resolved_by: str = None,
    timestamp: str = None,
    tags: List[str] = None
) -> bool:
    """
    Embed a high-impact item to global learnings collection.
    Use for findings with impact > 0.7, resolved unknowns, and significant dead ends.

    Returns True if successful, False if Qdrant not available.
    """
    if not _check_qdrant_available():
        return False

    try:
        _, Distance, VectorParams, PointStruct = _get_qdrant_imports()
        client = _get_qdrant_client()
        coll = _global_learnings_collection()

        # Ensure collection exists
        if not client.collection_exists(coll):
            vector_size = _get_vector_size()
            client.create_collection(coll, vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE))

        vector = _get_embedding_safe(text)
        if vector is None:
            return False

        payload = {
            "type": item_type,
            "text": text[:500] if text else None,
            "text_full": text if len(text) <= 500 else None,
            "project_id": project_id,
            "session_id": session_id,
            "impact": impact,
            "resolved_by": resolved_by,
            "timestamp": timestamp,
            "tags": tags or [],
        }

        # Use hash of item_id for numeric Qdrant point ID
        import hashlib
        point_id = int(hashlib.md5(f"global_{item_id}".encode()).hexdigest()[:15], 16)

        point = PointStruct(id=point_id, vector=vector, payload=payload)
        client.upsert(collection_name=coll, points=[point])
        return True
    except Exception as e:
        logger.warning(f"Failed to embed to global: {e}")
        return False


def search_global(
    query_text: str,
    item_types: List[str] = None,
    min_impact: float = None,
    limit: int = 10
) -> List[Dict]:
    """
    Search global learnings across all projects.

    Args:
        query_text: Semantic search query
        item_types: Filter by type (finding, unknown_resolved, dead_end)
        min_impact: Filter by minimum impact score
        limit: Maximum results

    Returns:
        List of matching items with scores and metadata
    """
    if not _check_qdrant_available():
        return []

    qvec = _get_embedding_safe(query_text)
    if qvec is None:
        return []

    try:
        client = _get_qdrant_client()
        coll = _global_learnings_collection()

        if not client.collection_exists(coll):
            return []

        # Build filter if needed
        query_filter = None
        if item_types or min_impact:
            from qdrant_client.models import Filter, FieldCondition, MatchAny, Range
            conditions = []
            if item_types:
                conditions.append(FieldCondition(key="type", match=MatchAny(any=item_types)))
            if min_impact:
                conditions.append(FieldCondition(key="impact", range=Range(gte=min_impact)))
            if conditions:
                query_filter = Filter(must=conditions)

        results = client.query_points(
            collection_name=coll,
            query=qvec,
            query_filter=query_filter,
            limit=limit,
            with_payload=True
        )

        return [
            {
                "score": getattr(r, 'score', 0.0) or 0.0,
                "type": (r.payload or {}).get("type"),
                "text": (r.payload or {}).get("text"),
                "project_id": (r.payload or {}).get("project_id"),
                "session_id": (r.payload or {}).get("session_id"),
                "impact": (r.payload or {}).get("impact"),
                "tags": (r.payload or {}).get("tags", []),
            }
            for r in results.points
        ]
    except Exception as e:
        logger.debug(f"search_global failed: {e}")
        return []


def sync_high_impact_to_global(project_id: str, min_impact: float = 0.7) -> int:
    """
    Sync high-impact findings and resolved unknowns from a project to global collection.
    Called during project-embed --global or manually.

    Returns number of items synced.
    """
    if not _check_qdrant_available():
        return 0

    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()
        synced = 0

        # Get high-impact findings
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT id, finding, impact, session_id, created_timestamp
            FROM project_findings
            WHERE project_id = ? AND impact >= ?
        """, (project_id, min_impact))

        for row in cursor.fetchall():
            if embed_to_global(
                item_id=row[0],
                text=row[1],
                item_type="finding",
                project_id=project_id,
                session_id=row[3],
                impact=row[2],
                timestamp=str(row[4])
            ):
                synced += 1

        # Get resolved unknowns (these contain valuable resolution patterns)
        cursor.execute("""
            SELECT id, unknown, resolved_by, session_id, resolved_timestamp
            FROM project_unknowns
            WHERE project_id = ? AND is_resolved = 1 AND resolved_by IS NOT NULL
        """, (project_id,))

        for row in cursor.fetchall():
            resolution_text = f"Unknown: {row[1]}\nResolved by: {row[2]}"
            if embed_to_global(
                item_id=row[0],
                text=resolution_text,
                item_type="unknown_resolved",
                project_id=project_id,
                session_id=row[3],
                resolved_by=row[2],
                timestamp=str(row[4]) if row[4] else None
            ):
                synced += 1

        # Get dead ends (anti-patterns to avoid)
        cursor.execute("""
            SELECT id, approach, why_failed, session_id, created_timestamp
            FROM project_dead_ends
            WHERE project_id = ?
        """, (project_id,))

        for row in cursor.fetchall():
            deadend_text = f"Approach: {row[1]}\nWhy failed: {row[2]}"
            if embed_to_global(
                item_id=row[0],
                text=deadend_text,
                item_type="dead_end",
                project_id=project_id,
                session_id=row[3],
                timestamp=str(row[4])
            ):
                synced += 1

        db.close()
        return synced
    except Exception as e:
        logger.warning(f"Failed to sync to global: {e}")
        return 0


# ============================================================================
# DEAD END SPECIFIC - Branch divergence and anti-pattern detection
# ============================================================================

def embed_dead_end_with_branch_context(
    project_id: str,
    dead_end_id: str,
    approach: str,
    why_failed: str,
    session_id: str = None,
    branch_id: str = None,
    winning_branch_id: str = None,
    score_diff: float = None,
    preflight_vectors: Dict = None,
    postflight_vectors: Dict = None,
    timestamp: str = None
) -> bool:
    """
    Embed a dead end with full branch context for similarity search.
    Use when a branch loses epistemic merge - captures divergence pattern.

    Args:
        project_id: Project ID
        dead_end_id: Unique ID for this dead end
        approach: Description of the approach that failed
        why_failed: Reason for failure
        session_id: Session ID
        branch_id: ID of the losing branch
        winning_branch_id: ID of the winning branch
        score_diff: Epistemic score difference
        preflight_vectors: Initial epistemic vectors
        postflight_vectors: Final epistemic vectors
        timestamp: When this dead end was recorded

    Returns:
        True if successful, False if Qdrant not available
    """
    if not _check_qdrant_available():
        return False

    try:
        _, Distance, VectorParams, PointStruct = _get_qdrant_imports()
        client = _get_qdrant_client()
        coll = _memory_collection(project_id)

        # Ensure collection exists
        if not client.collection_exists(coll):
            vector_size = _get_vector_size()
            client.create_collection(coll, vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE))

        # Rich text for embedding - captures what was tried and why it failed
        text = f"Dead end approach: {approach}\nWhy failed: {why_failed}"

        vector = _get_embedding_safe(text)
        if vector is None:
            return False

        # Rich payload for filtering and analysis
        payload = {
            "type": "dead_end",
            "text": text[:500],
            "approach": approach,
            "why_failed": why_failed,
            "session_id": session_id,
            "branch_id": branch_id,
            "winning_branch_id": winning_branch_id,
            "score_diff": score_diff,
            "preflight_vectors": preflight_vectors,
            "postflight_vectors": postflight_vectors,
            "timestamp": timestamp,
            "is_branch_deadend": branch_id is not None,
        }

        # Use hash of dead_end_id for numeric Qdrant point ID
        import hashlib
        point_id = int(hashlib.md5(dead_end_id.encode()).hexdigest()[:15], 16)

        point = PointStruct(id=point_id, vector=vector, payload=payload)
        client.upsert(collection_name=coll, points=[point])
        return True
    except Exception as e:
        logger.warning(f"Failed to embed dead end with branch context: {e}")
        return False


def search_similar_dead_ends(
    project_id: str,
    query_approach: str,
    include_branch_deadends: bool = True,
    limit: int = 5
) -> List[Dict]:
    """
    Search for similar past dead ends before starting a new approach.
    Use this in NOETIC phase to avoid repeating known failures.

    Args:
        project_id: Project ID
        query_approach: Description of the approach you're considering
        include_branch_deadends: Include dead ends from branch divergence
        limit: Maximum results

    Returns:
        List of similar dead ends with scores and context
    """
    if not _check_qdrant_available():
        return []

    qvec = _get_embedding_safe(f"Dead end approach: {query_approach}")
    if qvec is None:
        return []

    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        client = _get_qdrant_client()
        coll = _memory_collection(project_id)

        if not client.collection_exists(coll):
            return []

        # Filter for dead_end type only
        conditions = [FieldCondition(key="type", match=MatchValue(value="dead_end"))]

        # Optionally filter out branch dead ends
        if not include_branch_deadends:
            conditions.append(FieldCondition(key="is_branch_deadend", match=MatchValue(value=False)))

        query_filter = Filter(must=conditions)

        results = client.query_points(
            collection_name=coll,
            query=qvec,
            query_filter=query_filter,
            limit=limit,
            with_payload=True
        )

        return [
            {
                "score": getattr(r, 'score', 0.0) or 0.0,
                "approach": (r.payload or {}).get("approach"),
                "why_failed": (r.payload or {}).get("why_failed"),
                "session_id": (r.payload or {}).get("session_id"),
                "branch_id": (r.payload or {}).get("branch_id"),
                "score_diff": (r.payload or {}).get("score_diff"),
                "is_branch_deadend": (r.payload or {}).get("is_branch_deadend", False),
            }
            for r in results.points
        ]
    except Exception as e:
        logger.debug(f"search_similar_dead_ends failed: {e}")
        return []


def search_global_dead_ends(
    query_approach: str,
    limit: int = 5
) -> List[Dict]:
    """
    Search for similar dead ends across ALL projects (global learnings).
    Use to avoid repeating mistakes made in other projects.

    Args:
        query_approach: Description of the approach you're considering
        limit: Maximum results

    Returns:
        List of similar dead ends from any project
    """
    if not _check_qdrant_available():
        return []

    return search_global(
        query_text=f"Dead end approach: {query_approach}",
        item_types=["dead_end"],
        limit=limit
    )


# ============================================================================
# COLLECTION MIGRATION - Recreate with correct dimensions
# ============================================================================

def recreate_collection(collection_name: str) -> bool:
    """
    Delete and recreate a collection with the current embeddings provider's dimensions.
    Use when switching embedding providers (e.g., local hash -> Ollama).

    WARNING: This deletes all data in the collection!

    Returns True if successful.
    """
    if not _check_qdrant_available():
        return False

    try:
        _, Distance, VectorParams, _ = _get_qdrant_imports()
        client = _get_qdrant_client()
        vector_size = _get_vector_size()

        # Delete if exists
        if client.collection_exists(collection_name):
            client.delete_collection(collection_name)
            logger.info(f"Deleted collection {collection_name}")

        # Create with new dimensions
        client.create_collection(
            collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
        logger.info(f"Created collection {collection_name} with {vector_size} dimensions")
        return True
    except Exception as e:
        logger.warning(f"Failed to recreate collection {collection_name}: {e}")
        return False


def recreate_project_collections(project_id: str) -> dict:
    """
    Recreate all collections for a project with current embeddings dimensions.

    Returns dict with success status for each collection.
    """
    results = {}
    for coll_fn in [_docs_collection, _memory_collection, _epistemics_collection]:
        name = coll_fn(project_id)
        results[name] = recreate_collection(name)
    return results


def recreate_global_collections() -> dict:
    """
    Recreate global collections (global_learnings, personas) with current dimensions.

    Returns dict with success status for each collection.
    """
    results = {}
    for name in ["global_learnings", "personas"]:
        results[name] = recreate_collection(name)
    return results


def get_collection_info() -> List[dict]:
    """
    Get info about all Qdrant collections including dimensions and point counts.
    Useful for diagnosing dimension mismatches.
    """
    if not _check_qdrant_available():
        return []

    try:
        client = _get_qdrant_client()
        collections = client.get_collections()
        info = []
        for c in collections.collections:
            coll_info = client.get_collection(c.name)
            info.append({
                "name": c.name,
                "dimensions": coll_info.config.params.vectors.size,
                "points": coll_info.points_count,
            })
        return info
    except Exception as e:
        logger.warning(f"Failed to get collection info: {e}")
        return []
