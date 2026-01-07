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
    """Get Qdrant client with lazy imports.

    Priority:
    1. EMPIRICA_QDRANT_URL environment variable (explicit URL)
    2. localhost:6333 if Qdrant server is running
    3. EMPIRICA_QDRANT_PATH for file-based storage (fallback)
    """
    QdrantClient, _, _, _ = _get_qdrant_imports()

    # Priority 1: Explicit URL
    url = os.getenv("EMPIRICA_QDRANT_URL")
    if url:
        return QdrantClient(url=url)

    # Priority 2: Check if Qdrant server is running on localhost:6333
    default_url = "http://localhost:6333"
    try:
        import urllib.request
        req = urllib.request.Request(f"{default_url}/collections", method='GET')
        with urllib.request.urlopen(req, timeout=1) as resp:
            if resp.status == 200:
                return QdrantClient(url=default_url)
    except Exception:
        pass  # Server not available, fall through to file storage

    # Priority 3: File-based storage (fallback)
    path = os.getenv("EMPIRICA_QDRANT_PATH", "./.qdrant_data")
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


def _eidetic_collection(project_id: str) -> str:
    """Collection for eidetic memory (stable facts with confidence scoring)."""
    return f"project_{project_id}_eidetic"


def _episodic_collection(project_id: str) -> str:
    """Collection for episodic memory (session narratives with temporal decay)."""
    return f"project_{project_id}_episodic"


def _global_eidetic_collection() -> str:
    """Global eidetic facts (high-confidence cross-project knowledge)."""
    return "global_eidetic"


def init_collections(project_id: str) -> bool:
    """Initialize Qdrant collections. Returns False if Qdrant not available."""
    if not _check_qdrant_available():
        return False

    try:
        _, Distance, VectorParams, _ = _get_qdrant_imports()
        client = _get_qdrant_client()
        vector_size = _get_vector_size()
        collections = [
            _docs_collection(project_id),
            _memory_collection(project_id),
            _epistemics_collection(project_id),
            _eidetic_collection(project_id),
            _episodic_collection(project_id),
        ]
        for name in collections:
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


# =============================================================================
# EIDETIC MEMORY (Stable Facts with Confidence Scoring)
# =============================================================================

def embed_eidetic(
    project_id: str,
    fact_id: str,
    content: str,
    fact_type: str = "fact",
    domain: str = None,
    confidence: float = 0.5,
    confirmation_count: int = 1,
    source_sessions: List[str] = None,
    source_findings: List[str] = None,
    tags: List[str] = None,
    timestamp: str = None,
) -> bool:
    """
    Embed an eidetic memory entry (stable fact with confidence).

    Eidetic memory stores facts that persist across sessions:
    - Facts confirmed multiple times have higher confidence
    - Confidence grows with confirmation_count
    - Domain tagging enables domain-specific retrieval

    Returns True if successful, False if Qdrant not available.
    """
    if not _check_qdrant_available():
        return False

    try:
        _, Distance, VectorParams, PointStruct = _get_qdrant_imports()
        client = _get_qdrant_client()
        coll = _eidetic_collection(project_id)

        # Ensure collection exists
        if not client.collection_exists(coll):
            vector_size = _get_vector_size()
            client.create_collection(coll, vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE))

        vector = _get_embedding_safe(content)
        if vector is None:
            return False

        import hashlib
        import time

        payload = {
            "type": fact_type,  # fact, pattern, signature, behavior, constraint
            "content": content[:500] if content else None,
            "content_full": content if len(content) <= 500 else None,
            "content_hash": hashlib.md5(content.encode()).hexdigest(),
            "domain": domain,
            "confidence": confidence,
            "confirmation_count": confirmation_count,
            "first_seen": timestamp or time.time(),
            "last_confirmed": timestamp or time.time(),
            "source_sessions": source_sessions or [],
            "source_findings": source_findings or [],
            "tags": tags or [],
        }

        point_id = int(hashlib.md5(fact_id.encode()).hexdigest()[:15], 16)
        point = PointStruct(id=point_id, vector=vector, payload=payload)
        client.upsert(collection_name=coll, points=[point])
        return True
    except Exception as e:
        logger.warning(f"Failed to embed eidetic: {e}")
        return False


def search_eidetic(
    project_id: str,
    query: str,
    fact_type: str = None,
    domain: str = None,
    min_confidence: float = 0.0,
    limit: int = 5,
) -> List[Dict]:
    """
    Search eidetic memory for relevant facts.

    Args:
        project_id: Project UUID
        query: Semantic search query
        fact_type: Filter by type (fact, pattern, signature, etc.)
        domain: Filter by domain (auth, api, db, etc.)
        min_confidence: Minimum confidence threshold
        limit: Max results

    Returns:
        List of matching eidetic entries with scores
    """
    if not _check_qdrant_available():
        return []

    try:
        client = _get_qdrant_client()
        coll = _eidetic_collection(project_id)

        if not client.collection_exists(coll):
            return []

        vector = _get_embedding_safe(query)
        if vector is None:
            return []

        # Build filter conditions
        from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

        conditions = []
        if fact_type:
            conditions.append(FieldCondition(key="type", match=MatchValue(value=fact_type)))
        if domain:
            conditions.append(FieldCondition(key="domain", match=MatchValue(value=domain)))
        if min_confidence > 0:
            conditions.append(FieldCondition(key="confidence", range=Range(gte=min_confidence)))

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
                "content": r.payload.get("content_full") or r.payload.get("content"),
                "type": r.payload.get("type"),
                "domain": r.payload.get("domain"),
                "confidence": r.payload.get("confidence"),
                "confirmation_count": r.payload.get("confirmation_count"),
                "source_sessions": r.payload.get("source_sessions", []),
                "tags": r.payload.get("tags", []),
            }
            for r in results.points
        ]
    except Exception as e:
        logger.warning(f"Failed to search eidetic: {e}")
        return []


def confirm_eidetic_fact(
    project_id: str,
    content_hash: str,
    session_id: str,
    confidence_boost: float = 0.1,
) -> bool:
    """
    Confirm an existing eidetic fact, boosting its confidence.

    When the same fact is observed again, we boost confidence
    rather than creating a duplicate.

    Args:
        project_id: Project UUID
        content_hash: MD5 hash of the fact content
        session_id: Session confirming this fact
        confidence_boost: Amount to increase confidence (default 0.1)

    Returns:
        True if fact was found and updated, False otherwise
    """
    if not _check_qdrant_available():
        return False

    try:
        client = _get_qdrant_client()
        coll = _eidetic_collection(project_id)

        if not client.collection_exists(coll):
            return False

        from qdrant_client.models import Filter, FieldCondition, MatchValue

        # Find existing fact by content hash
        results = client.scroll(
            collection_name=coll,
            scroll_filter=Filter(
                must=[FieldCondition(key="content_hash", match=MatchValue(value=content_hash))]
            ),
            limit=1,
            with_payload=True,
            with_vectors=True,
        )

        points, _ = results
        if not points:
            return False

        point = points[0]
        payload = point.payload

        # Update confidence (max 0.95)
        new_confidence = min(0.95, payload.get("confidence", 0.5) + confidence_boost)

        # Update confirmation count
        new_count = payload.get("confirmation_count", 1) + 1

        # Add session to source list
        sessions = payload.get("source_sessions", [])
        if session_id not in sessions:
            sessions.append(session_id)

        import time
        payload["confidence"] = new_confidence
        payload["confirmation_count"] = new_count
        payload["source_sessions"] = sessions
        payload["last_confirmed"] = time.time()

        from qdrant_client.models import PointStruct
        updated_point = PointStruct(id=point.id, vector=point.vector, payload=payload)
        client.upsert(collection_name=coll, points=[updated_point])

        logger.info(f"Confirmed eidetic fact: confidence {new_confidence:.2f}, confirmations {new_count}")
        return True
    except Exception as e:
        logger.warning(f"Failed to confirm eidetic fact: {e}")
        return False


# =============================================================================
# EPISODIC MEMORY (Session Narratives with Temporal Decay)
# =============================================================================

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
