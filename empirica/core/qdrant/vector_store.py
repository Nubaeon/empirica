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


def _goals_collection(project_id: str) -> str:
    """Collection for goals and subtasks (semantic search across sessions)."""
    return f"project_{project_id}_goals"


def _calibration_collection(project_id: str) -> str:
    """Collection for grounded calibration data (verification summaries + trajectory)."""
    return f"project_{project_id}_calibration"


# --- Forward-compatible collections for Epistemic Intent Layer ---

def _assumptions_collection(project_id: str) -> str:
    """Collection for assumptions (unverified beliefs with urgency decay)."""
    return f"project_{project_id}_assumptions"


def _decisions_collection(project_id: str) -> str:
    """Collection for decisions (recorded choice points with rationale)."""
    return f"project_{project_id}_decisions"


def _intents_collection(project_id: str) -> str:
    """Collection for IntentEdges (provenance graph: noetic↔praxic transforms)."""
    return f"project_{project_id}_intents"


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
            _goals_collection(project_id),
            _calibration_collection(project_id),
            # Forward-compatible: Epistemic Intent Layer (populated when CLI commands exist)
            _assumptions_collection(project_id),
            _decisions_collection(project_id),
            _intents_collection(project_id),
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


def search(project_id: str, query_text: str, kind: str = "focused", limit: int = 5) -> Dict[str, List[Dict]]:
    """
    Semantic search over project knowledge.

    Args:
        project_id: Project UUID
        query_text: Search query
        kind: "focused" (default: eidetic + episodic), "all", "docs", "memory", "eidetic", "episodic"
        limit: Max results per collection

    Returns empty results if Qdrant not available.
    """
    # Focused = eidetic + episodic (refined knowledge, no raw duplicates)
    if kind == "focused":
        search_kinds = ["eidetic", "episodic"]
    elif kind == "all":
        search_kinds = ["docs", "memory", "eidetic", "episodic"]
    else:
        search_kinds = [kind]
    empty_result = {k: [] for k in search_kinds}

    if not _check_qdrant_available():
        return empty_result

    qvec = _get_embedding_safe(query_text)
    if qvec is None:
        return empty_result

    results: Dict[str, List[Dict]] = {}
    client = _get_qdrant_client()

    # Query each collection independently (so one failure doesn't block the other)
    if "docs" in search_kinds:
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

    if "memory" in search_kinds:
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
                        "timestamp": (r.payload or {}).get("timestamp"),
                        "impact": (r.payload or {}).get("impact"),
                    }
                    for r in rm.points
                ]
            else:
                results["memory"] = []
        except Exception as e:
            logger.debug(f"memory query failed: {e}")
            results["memory"] = []

    if "eidetic" in search_kinds:
        try:
            eidetic_coll = _eidetic_collection(project_id)
            if client.collection_exists(eidetic_coll):
                re = client.query_points(
                    collection_name=eidetic_coll,
                    query=qvec,
                    limit=limit,
                    with_payload=True
                )
                results["eidetic"] = [
                    {
                        "score": getattr(r, 'score', 0.0) or 0.0,
                        "type": (r.payload or {}).get("type"),
                        "content": (r.payload or {}).get("content"),
                        "confidence": (r.payload or {}).get("confidence"),
                        "domain": (r.payload or {}).get("domain"),
                    }
                    for r in re.points
                ]
            else:
                results["eidetic"] = []
        except Exception as e:
            logger.debug(f"eidetic query failed: {e}")
            results["eidetic"] = []

    if "episodic" in search_kinds:
        try:
            episodic_coll = _episodic_collection(project_id)
            if client.collection_exists(episodic_coll):
                rep = client.query_points(
                    collection_name=episodic_coll,
                    query=qvec,
                    limit=limit,
                    with_payload=True
                )
                results["episodic"] = [
                    {
                        "score": getattr(r, 'score', 0.0) or 0.0,
                        "type": (r.payload or {}).get("type"),
                        "narrative": (r.payload or {}).get("narrative"),
                        "session_id": (r.payload or {}).get("session_id"),
                        "outcome": (r.payload or {}).get("outcome"),
                    }
                    for r in rep.points
                ]
            else:
                results["episodic"] = []
        except Exception as e:
            logger.debug(f"episodic query failed: {e}")
            results["episodic"] = []

    if results:
        return results

    # REST fallback only if client queries produced nothing
    logger.debug("Trying REST fallback for search")

    # REST fallback (for remote Qdrant server)
    try:
        if "docs" in search_kinds:
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
        if "memory" in search_kinds:
            rm = _rest_search(_memory_collection(project_id), qvec, limit)
            results["memory"] = [
                {
                    "score": m.get('score', 0.0),
                    "type": (m.get('payload') or {}).get('type'),
                }
                for m in rm
            ]
        if "eidetic" in search_kinds:
            re = _rest_search(_eidetic_collection(project_id), qvec, limit)
            results["eidetic"] = [
                {
                    "score": e.get('score', 0.0),
                    "type": (e.get('payload') or {}).get('type'),
                    "content": (e.get('payload') or {}).get('content'),
                    "confidence": (e.get('payload') or {}).get('confidence'),
                }
                for e in re
            ]
        if "episodic" in search_kinds:
            rep = _rest_search(_episodic_collection(project_id), qvec, limit)
            results["episodic"] = [
                {
                    "score": ep.get('score', 0.0),
                    "type": (ep.get('payload') or {}).get('type'),
                    "narrative": (ep.get('payload') or {}).get('narrative'),
                    "session_id": (ep.get('payload') or {}).get('session_id'),
                }
                for ep in rep
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
                "content_hash": r.payload.get("content_hash"),
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


# =============================================================================
# GOALS & SUBTASKS (Semantic Search Across Sessions)
# =============================================================================

def embed_goal(
    project_id: str,
    goal_id: str,
    objective: str,
    session_id: str = None,
    ai_id: str = None,
    scope_breadth: float = None,
    scope_duration: float = None,
    scope_coordination: float = None,
    estimated_complexity: float = None,
    success_criteria: List[str] = None,
    status: str = "in_progress",
    tags: List[str] = None,
    timestamp: float = None,
) -> bool:
    """
    Embed a goal to Qdrant for semantic search across sessions.

    Called automatically when goals are created. Enables:
    - "Find goals similar to this task"
    - "What goals have been completed for similar objectives?"
    - Post-compact context recovery via semantic retrieval

    Args:
        project_id: Project UUID
        goal_id: Goal UUID
        objective: Goal objective/description (main searchable text)
        session_id: Session where goal was created
        ai_id: AI that created the goal
        scope_breadth: How wide the goal spans (0-1)
        scope_duration: Expected lifetime (0-1)
        scope_coordination: Multi-agent coordination needed (0-1)
        estimated_complexity: Complexity estimate (0-1)
        success_criteria: List of success criteria descriptions
        status: Goal status (in_progress, complete, blocked)
        tags: Optional tags for filtering
        timestamp: Creation timestamp

    Returns:
        True if successful, False if Qdrant not available
    """
    if not _check_qdrant_available():
        return False

    try:
        _, Distance, VectorParams, PointStruct = _get_qdrant_imports()
        client = _get_qdrant_client()
        coll = _goals_collection(project_id)

        # Ensure collection exists
        if not client.collection_exists(coll):
            vector_size = _get_vector_size()
            client.create_collection(coll, vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE))

        # Build rich text for embedding - combines objective and criteria
        text_parts = [objective]
        if success_criteria:
            text_parts.append("Success criteria: " + "; ".join(success_criteria[:5]))
        embed_text = ". ".join(text_parts)

        vector = _get_embedding_safe(embed_text)
        if vector is None:
            return False

        import hashlib
        import time

        payload = {
            "type": "goal",
            "objective": objective[:500] if objective else None,
            "objective_full": objective if len(objective) <= 500 else None,
            "session_id": session_id,
            "ai_id": ai_id,
            "scope": {
                "breadth": scope_breadth,
                "duration": scope_duration,
                "coordination": scope_coordination,
            },
            "estimated_complexity": estimated_complexity,
            "success_criteria": success_criteria or [],
            "status": status,
            "tags": tags or [],
            "timestamp": timestamp or time.time(),
            "is_completed": status == "complete",
        }

        point_id = int(hashlib.md5(goal_id.encode()).hexdigest()[:15], 16)
        point = PointStruct(id=point_id, vector=vector, payload=payload)
        client.upsert(collection_name=coll, points=[point])
        return True
    except Exception as e:
        logger.warning(f"Failed to embed goal: {e}")
        return False


def embed_subtask(
    project_id: str,
    subtask_id: str,
    description: str,
    goal_id: str,
    goal_objective: str = None,
    session_id: str = None,
    ai_id: str = None,
    epistemic_importance: str = "medium",
    status: str = "pending",
    completion_evidence: str = None,
    findings: List[str] = None,
    unknowns: List[str] = None,
    timestamp: float = None,
) -> bool:
    """
    Embed a subtask to Qdrant for semantic search.

    Subtasks are linked to goals. Enables:
    - "What subtasks have been done for similar objectives?"
    - "Find completed work related to this task"

    Args:
        project_id: Project UUID
        subtask_id: Subtask UUID
        description: Subtask description (main searchable text)
        goal_id: Parent goal UUID
        goal_objective: Parent goal objective (for richer embedding)
        session_id: Session where subtask was created
        ai_id: AI that created the subtask
        epistemic_importance: critical/high/medium/low
        status: pending/in_progress/completed/blocked/skipped
        completion_evidence: Evidence of completion (commit hash, etc.)
        findings: Findings discovered while working on subtask
        unknowns: Unknowns discovered while working on subtask
        timestamp: Creation timestamp

    Returns:
        True if successful, False if Qdrant not available
    """
    if not _check_qdrant_available():
        return False

    try:
        _, Distance, VectorParams, PointStruct = _get_qdrant_imports()
        client = _get_qdrant_client()
        coll = _goals_collection(project_id)

        # Ensure collection exists
        if not client.collection_exists(coll):
            vector_size = _get_vector_size()
            client.create_collection(coll, vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE))

        # Build rich text for embedding - combines subtask + goal context
        text_parts = [description]
        if goal_objective:
            text_parts.append(f"Part of goal: {goal_objective}")
        if findings:
            text_parts.append("Findings: " + "; ".join(findings[:3]))
        embed_text = ". ".join(text_parts)

        vector = _get_embedding_safe(embed_text)
        if vector is None:
            return False

        import hashlib
        import time

        payload = {
            "type": "subtask",
            "description": description[:500] if description else None,
            "description_full": description if len(description) <= 500 else None,
            "goal_id": goal_id,
            "goal_objective": goal_objective[:200] if goal_objective else None,
            "session_id": session_id,
            "ai_id": ai_id,
            "epistemic_importance": epistemic_importance,
            "status": status,
            "completion_evidence": completion_evidence,
            "findings": findings or [],
            "unknowns": unknowns or [],
            "timestamp": timestamp or time.time(),
            "is_completed": status == "completed",
        }

        point_id = int(hashlib.md5(subtask_id.encode()).hexdigest()[:15], 16)
        point = PointStruct(id=point_id, vector=vector, payload=payload)
        client.upsert(collection_name=coll, points=[point])
        return True
    except Exception as e:
        logger.warning(f"Failed to embed subtask: {e}")
        return False


def search_goals(
    project_id: str,
    query: str,
    item_type: str = None,
    status: str = None,
    ai_id: str = None,
    include_subtasks: bool = True,
    limit: int = 10,
) -> List[Dict]:
    """
    Semantic search for goals and subtasks across all sessions.

    Use this for:
    - Post-compact context recovery: "What was I working on?"
    - Task discovery: "Find goals similar to this task"
    - Progress tracking: "What's been completed for X?"

    Args:
        project_id: Project UUID
        query: Semantic search query (e.g., "authentication system")
        item_type: Filter by type ("goal" or "subtask"), None for both
        status: Filter by status (in_progress, complete, pending, etc.)
        ai_id: Filter by AI that created it
        include_subtasks: If False, only return goals
        limit: Maximum results

    Returns:
        List of matching goals/subtasks with scores and metadata
    """
    if not _check_qdrant_available():
        return []

    try:
        client = _get_qdrant_client()
        coll = _goals_collection(project_id)

        if not client.collection_exists(coll):
            return []

        vector = _get_embedding_safe(query)
        if vector is None:
            return []

        from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny

        conditions = []

        # Filter by type
        if item_type:
            conditions.append(FieldCondition(key="type", match=MatchValue(value=item_type)))
        elif not include_subtasks:
            conditions.append(FieldCondition(key="type", match=MatchValue(value="goal")))

        # Filter by status
        if status:
            conditions.append(FieldCondition(key="status", match=MatchValue(value=status)))

        # Filter by AI
        if ai_id:
            conditions.append(FieldCondition(key="ai_id", match=MatchValue(value=ai_id)))

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
                "score": getattr(r, 'score', 0.0) or 0.0,
                "type": (r.payload or {}).get("type"),
                "objective": (r.payload or {}).get("objective_full") or (r.payload or {}).get("objective"),
                "description": (r.payload or {}).get("description_full") or (r.payload or {}).get("description"),
                "goal_id": (r.payload or {}).get("goal_id"),
                "session_id": (r.payload or {}).get("session_id"),
                "ai_id": (r.payload or {}).get("ai_id"),
                "status": (r.payload or {}).get("status"),
                "is_completed": (r.payload or {}).get("is_completed", False),
                "scope": (r.payload or {}).get("scope"),
                "success_criteria": (r.payload or {}).get("success_criteria", []),
                "findings": (r.payload or {}).get("findings", []),
                "tags": (r.payload or {}).get("tags", []),
                "timestamp": (r.payload or {}).get("timestamp"),
            }
            for r in results.points
        ]
    except Exception as e:
        logger.debug(f"search_goals failed: {e}")
        return []


def update_goal_status(
    project_id: str,
    goal_id: str,
    status: str,
    completion_evidence: str = None,
) -> bool:
    """
    Update goal status in Qdrant (e.g., when completed).

    Args:
        project_id: Project UUID
        goal_id: Goal UUID
        status: New status (in_progress, complete, blocked)
        completion_evidence: Evidence of completion

    Returns:
        True if updated successfully
    """
    if not _check_qdrant_available():
        return False

    try:
        client = _get_qdrant_client()
        coll = _goals_collection(project_id)

        if not client.collection_exists(coll):
            return False

        import hashlib
        point_id = int(hashlib.md5(goal_id.encode()).hexdigest()[:15], 16)

        # Get existing point
        points = client.retrieve(collection_name=coll, ids=[point_id], with_payload=True, with_vectors=True)
        if not points:
            return False

        point = points[0]
        payload = point.payload or {}
        payload["status"] = status
        payload["is_completed"] = status == "complete"
        if completion_evidence:
            payload["completion_evidence"] = completion_evidence

        from qdrant_client.models import PointStruct
        updated_point = PointStruct(id=point_id, vector=point.vector, payload=payload)
        client.upsert(collection_name=coll, points=[updated_point])
        return True
    except Exception as e:
        logger.warning(f"Failed to update goal status: {e}")
        return False


def sync_goals_to_qdrant(project_id: str) -> int:
    """
    Sync all goals and subtasks from SQLite to Qdrant.

    Use this for:
    - Initial setup when enabling Qdrant
    - Re-sync after switching embedding providers

    Returns:
        Number of items synced
    """
    if not _check_qdrant_available():
        return 0

    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()
        synced = 0

        cursor = db.conn.cursor()

        # Sync goals
        cursor.execute("""
            SELECT g.id, g.objective, g.session_id, g.scope, g.estimated_complexity,
                   g.status, g.created_timestamp, s.ai_id
            FROM goals g
            LEFT JOIN sessions s ON g.session_id = s.session_id
            WHERE g.session_id IN (
                SELECT session_id FROM sessions WHERE project_id = ?
            )
        """, (project_id,))

        for row in cursor.fetchall():
            goal_id, objective, session_id, scope_json, complexity, status, ts, ai_id = row

            scope = json.loads(scope_json) if scope_json else {}

            # Get success criteria
            cursor.execute("SELECT description FROM success_criteria WHERE goal_id = ?", (goal_id,))
            criteria = [r[0] for r in cursor.fetchall()]

            if embed_goal(
                project_id=project_id,
                goal_id=goal_id,
                objective=objective,
                session_id=session_id,
                ai_id=ai_id,
                scope_breadth=scope.get("breadth"),
                scope_duration=scope.get("duration"),
                scope_coordination=scope.get("coordination"),
                estimated_complexity=complexity,
                success_criteria=criteria,
                status=status or "in_progress",
                timestamp=ts,
            ):
                synced += 1

        # Sync subtasks
        cursor.execute("""
            SELECT st.id, st.description, st.goal_id, g.objective, st.status,
                   st.epistemic_importance, st.completion_evidence, st.created_timestamp,
                   g.session_id
            FROM subtasks st
            JOIN goals g ON st.goal_id = g.id
            WHERE g.session_id IN (
                SELECT session_id FROM sessions WHERE project_id = ?
            )
        """, (project_id,))

        for row in cursor.fetchall():
            subtask_id, desc, goal_id, goal_obj, status, importance, evidence, ts, session_id = row

            if embed_subtask(
                project_id=project_id,
                subtask_id=subtask_id,
                description=desc,
                goal_id=goal_id,
                goal_objective=goal_obj,
                session_id=session_id,
                epistemic_importance=importance or "medium",
                status=status or "pending",
                completion_evidence=evidence,
                timestamp=ts,
            ):
                synced += 1

        db.close()
        return synced
    except Exception as e:
        logger.warning(f"Failed to sync goals to Qdrant: {e}")
        return 0


# =============================================================================
# GROUNDED CALIBRATION EMBEDDING (v1.5.0)
# =============================================================================


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

def embed_assumption(
    project_id: str,
    assumption_id: str,
    assumption: str,
    confidence: float = 0.5,
    status: str = "unverified",
    resolution_finding_id: str = None,
    entity_type: str = "project",
    entity_id: str = None,
    session_id: str = None,
    transaction_id: str = None,
    domain: str = None,
    timestamp: float = None,
) -> bool:
    """Embed an assumption (unverified belief) for semantic search.

    Assumptions have an urgency_signal that increases with age for unverified
    items: older unverified = higher risk. Resolved assumptions: urgency=0.
    """
    if not _check_qdrant_available():
        return False

    try:
        import hashlib
        import time as _time
        _, _, VectorParams, PointStruct = _get_qdrant_imports()
        client = _get_qdrant_client()
        coll = _assumptions_collection(project_id)

        if not client.collection_exists(coll):
            vector_size = _get_vector_size()
            from qdrant_client.models import Distance
            client.create_collection(coll, vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE))

        ts = timestamp or _time.time()
        # Urgency: increases with age for unverified assumptions
        urgency = 0.0
        if status == "unverified":
            age_days = (_time.time() - ts) / 86400
            urgency = min(1.0, (age_days / 30.0) * (1.0 - confidence))

        vector = _get_embedding_safe(assumption)
        if vector is None:
            return False

        payload = {
            "type": "assumption",
            "assumption": assumption[:500],
            "assumption_full": assumption if len(assumption) <= 500 else None,
            "confidence": confidence,
            "status": status,
            "resolution_finding_id": resolution_finding_id,
            "entity_type": entity_type,
            "entity_id": entity_id or project_id,
            "session_id": session_id,
            "transaction_id": transaction_id,
            "domain": domain,
            "timestamp": ts,
            "urgency_signal": urgency,
        }

        point_id = int(hashlib.md5(assumption_id.encode()).hexdigest()[:15], 16)
        point = PointStruct(id=point_id, vector=vector, payload=payload)
        client.upsert(collection_name=coll, points=[point])
        return True
    except Exception as e:
        logger.warning(f"Failed to embed assumption: {e}")
        return False


def embed_decision(
    project_id: str,
    decision_id: str,
    choice: str,
    rationale: str,
    alternatives: str = None,
    confidence_at_decision: float = None,
    reversibility: str = "committal",
    entity_type: str = "project",
    entity_id: str = None,
    session_id: str = None,
    transaction_id: str = None,
    timestamp: float = None,
) -> bool:
    """Embed a decision (recorded choice point) for semantic search.

    Decisions are permanent audit trail — no decay applied.
    """
    if not _check_qdrant_available():
        return False

    try:
        import hashlib
        import time as _time
        _, _, VectorParams, PointStruct = _get_qdrant_imports()
        client = _get_qdrant_client()
        coll = _decisions_collection(project_id)

        if not client.collection_exists(coll):
            vector_size = _get_vector_size()
            from qdrant_client.models import Distance
            client.create_collection(coll, vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE))

        # Rich text for embedding: choice + rationale + alternatives
        embed_text = f"{choice}. Rationale: {rationale}"
        if alternatives:
            embed_text += f". Alternatives: {alternatives}"

        vector = _get_embedding_safe(embed_text)
        if vector is None:
            return False

        payload = {
            "type": "decision",
            "choice": choice[:500],
            "choice_full": choice if len(choice) <= 500 else None,
            "rationale": rationale[:500] if rationale else None,
            "alternatives": alternatives,
            "confidence_at_decision": confidence_at_decision,
            "reversibility": reversibility,
            "entity_type": entity_type,
            "entity_id": entity_id or project_id,
            "session_id": session_id,
            "transaction_id": transaction_id,
            "timestamp": timestamp or _time.time(),
        }

        point_id = int(hashlib.md5(decision_id.encode()).hexdigest()[:15], 16)
        point = PointStruct(id=point_id, vector=vector, payload=payload)
        client.upsert(collection_name=coll, points=[point])
        return True
    except Exception as e:
        logger.warning(f"Failed to embed decision: {e}")
        return False


def embed_intent_edge(
    project_id: str,
    intent_id: str,
    direction: str,
    source_artifact_id: str,
    source_artifact_type: str,
    target_artifact_id: str,
    target_artifact_type: str,
    confidence_at_crossing: float,
    reversibility: str = "exploratory",
    cascade_phase: str = "check",
    reasoning: str = None,
    vectors_snapshot: dict = None,
    entity_type: str = "project",
    entity_id: str = None,
    session_id: str = None,
    transaction_id: str = None,
    timestamp: float = None,
) -> bool:
    """Embed an IntentEdge (provenance graph: noetic↔praxic transform).

    IntentEdges are permanent provenance — no decay. Retrieval ranks by recency.
    """
    if not _check_qdrant_available():
        return False

    try:
        import hashlib
        import time as _time
        import json as _json
        _, _, VectorParams, PointStruct = _get_qdrant_imports()
        client = _get_qdrant_client()
        coll = _intents_collection(project_id)

        if not client.collection_exists(coll):
            vector_size = _get_vector_size()
            from qdrant_client.models import Distance
            client.create_collection(coll, vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE))

        # Rich text for semantic search over intent reasoning
        embed_text = (
            f"{direction} intent: {reasoning or 'no reasoning provided'}. "
            f"{source_artifact_type} → {target_artifact_type} at confidence {confidence_at_crossing:.2f}"
        )

        vector = _get_embedding_safe(embed_text)
        if vector is None:
            return False

        payload = {
            "type": "intent_edge",
            "direction": direction,
            "source_artifact_id": source_artifact_id,
            "source_artifact_type": source_artifact_type,
            "target_artifact_id": target_artifact_id,
            "target_artifact_type": target_artifact_type,
            "confidence_at_crossing": confidence_at_crossing,
            "reversibility": reversibility,
            "cascade_phase": cascade_phase,
            "reasoning": reasoning[:500] if reasoning else None,
            "vectors_snapshot": _json.dumps(vectors_snapshot) if vectors_snapshot else None,
            "entity_type": entity_type,
            "entity_id": entity_id or project_id,
            "session_id": session_id,
            "transaction_id": transaction_id,
            "timestamp": timestamp or _time.time(),
        }

        point_id = int(hashlib.md5(intent_id.encode()).hexdigest()[:15], 16)
        point = PointStruct(id=point_id, vector=vector, payload=payload)
        client.upsert(collection_name=coll, points=[point])
        return True
    except Exception as e:
        logger.warning(f"Failed to embed intent edge: {e}")
        return False


# --- Search functions for Intent Layer artifacts ---

def search_assumptions(
    project_id: str,
    query: str,
    status: str = None,
    entity_type: str = None,
    min_urgency: float = 0.0,
    limit: int = 5,
) -> List[Dict]:
    """Search assumptions by semantic similarity with optional filters.

    Args:
        status: Filter by 'unverified', 'verified', 'falsified'
        entity_type: Filter by entity type
        min_urgency: Minimum urgency_signal threshold (0.0-1.0)
    """
    if not _check_qdrant_available():
        return []

    try:
        client = _get_qdrant_client()
        coll = _assumptions_collection(project_id)

        if not client.collection_exists(coll):
            return []

        vector = _get_embedding_safe(query)
        if vector is None:
            return []

        conditions = []
        if status:
            from qdrant_client.models import FieldCondition, MatchValue
            conditions.append(FieldCondition(key="status", match=MatchValue(value=status)))
        if entity_type:
            from qdrant_client.models import FieldCondition, MatchValue
            conditions.append(FieldCondition(key="entity_type", match=MatchValue(value=entity_type)))

        query_filter = None
        if conditions:
            from qdrant_client.models import Filter
            query_filter = Filter(must=conditions)

        results = client.query_points(
            collection_name=coll,
            query=vector,
            query_filter=query_filter,
            limit=limit * 2 if min_urgency > 0 else limit,
            with_payload=True,
        )

        items = [
            {
                "assumption": r.payload.get("assumption", ""),
                "confidence": r.payload.get("confidence", 0.5),
                "status": r.payload.get("status", "unverified"),
                "urgency_signal": r.payload.get("urgency_signal", 0.0),
                "domain": r.payload.get("domain"),
                "entity_type": r.payload.get("entity_type"),
                "entity_id": r.payload.get("entity_id"),
                "score": r.score,
            }
            for r in results.points
        ]

        # Filter by urgency threshold
        if min_urgency > 0:
            items = [i for i in items if i["urgency_signal"] >= min_urgency]

        return items[:limit]
    except Exception as e:
        logger.warning(f"Failed to search assumptions: {e}")
        return []


def search_decisions(
    project_id: str,
    query: str,
    reversibility: str = None,
    entity_type: str = None,
    limit: int = 5,
) -> List[Dict]:
    """Search decisions by semantic similarity with optional filters."""
    if not _check_qdrant_available():
        return []

    try:
        client = _get_qdrant_client()
        coll = _decisions_collection(project_id)

        if not client.collection_exists(coll):
            return []

        vector = _get_embedding_safe(query)
        if vector is None:
            return []

        conditions = []
        if reversibility:
            from qdrant_client.models import FieldCondition, MatchValue
            conditions.append(FieldCondition(key="reversibility", match=MatchValue(value=reversibility)))
        if entity_type:
            from qdrant_client.models import FieldCondition, MatchValue
            conditions.append(FieldCondition(key="entity_type", match=MatchValue(value=entity_type)))

        query_filter = None
        if conditions:
            from qdrant_client.models import Filter
            query_filter = Filter(must=conditions)

        results = client.query_points(
            collection_name=coll,
            query=vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )

        return [
            {
                "choice": r.payload.get("choice", ""),
                "rationale": r.payload.get("rationale", ""),
                "alternatives": r.payload.get("alternatives"),
                "confidence_at_decision": r.payload.get("confidence_at_decision"),
                "reversibility": r.payload.get("reversibility"),
                "entity_type": r.payload.get("entity_type"),
                "score": r.score,
            }
            for r in results.points
        ]
    except Exception as e:
        logger.warning(f"Failed to search decisions: {e}")
        return []


def search_intents(
    project_id: str,
    query: str,
    direction: str = None,
    cascade_phase: str = None,
    limit: int = 5,
) -> List[Dict]:
    """Search IntentEdges by semantic similarity with optional filters."""
    if not _check_qdrant_available():
        return []

    try:
        client = _get_qdrant_client()
        coll = _intents_collection(project_id)

        if not client.collection_exists(coll):
            return []

        vector = _get_embedding_safe(query)
        if vector is None:
            return []

        conditions = []
        if direction:
            from qdrant_client.models import FieldCondition, MatchValue
            conditions.append(FieldCondition(key="direction", match=MatchValue(value=direction)))
        if cascade_phase:
            from qdrant_client.models import FieldCondition, MatchValue
            conditions.append(FieldCondition(key="cascade_phase", match=MatchValue(value=cascade_phase)))

        query_filter = None
        if conditions:
            from qdrant_client.models import Filter
            query_filter = Filter(must=conditions)

        results = client.query_points(
            collection_name=coll,
            query=vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )

        return [
            {
                "direction": r.payload.get("direction"),
                "reasoning": r.payload.get("reasoning", ""),
                "source_artifact_type": r.payload.get("source_artifact_type"),
                "target_artifact_type": r.payload.get("target_artifact_type"),
                "confidence_at_crossing": r.payload.get("confidence_at_crossing"),
                "reversibility": r.payload.get("reversibility"),
                "cascade_phase": r.payload.get("cascade_phase"),
                "score": r.score,
            }
            for r in results.points
        ]
    except Exception as e:
        logger.warning(f"Failed to search intents: {e}")
        return []


# =============================================================================
# NOETIC RAG: Decay & Cross-Layer Sync Functions
# =============================================================================

def decay_eidetic_fact(
    project_id: str,
    content_hash: str,
    decay_amount: float = 0.05,
    min_confidence: float = 0.3,
    reason: str = None,
) -> bool:
    """Decay an eidetic fact's confidence when contradicted by new findings.

    Mirrors confirm_eidetic_fact() but decreases confidence.
    Domain-scoped: caller must ensure domain matching (central tolerance).
    """
    if not _check_qdrant_available():
        return False

    try:
        import time as _time
        client = _get_qdrant_client()
        coll = _eidetic_collection(project_id)

        if not client.collection_exists(coll):
            return False

        from qdrant_client.models import Filter, FieldCondition, MatchValue, PointStruct

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
        old_confidence = payload.get("confidence", 0.5)
        new_confidence = max(min_confidence, old_confidence - decay_amount)

        payload["confidence"] = new_confidence
        payload["last_decayed"] = _time.time()
        payload["decay_reason"] = reason or "contradicted by finding"

        updated_point = PointStruct(id=point.id, vector=point.vector, payload=payload)
        client.upsert(collection_name=coll, points=[updated_point])

        logger.info(f"Decayed eidetic fact: {old_confidence:.2f} → {new_confidence:.2f} ({reason or 'finding'})")
        return True
    except Exception as e:
        logger.warning(f"Failed to decay eidetic fact: {e}")
        return False


def decay_eidetic_by_finding(
    project_id: str,
    finding_text: str,
    domain: str = None,
    decay_amount: float = 0.03,
    min_confidence: float = 0.3,
    similarity_threshold: float = 0.6,
    limit: int = 5,
) -> int:
    """Decay eidetic facts semantically similar to a contradicting finding.

    CENTRAL TOLERANCE: If domain provided, only decay facts in that domain.
    Lighter decay (0.03) than lessons (0.05) — eidetic facts have higher
    inertia from multiple confirmations.

    Returns number of facts decayed.
    """
    if not _check_qdrant_available():
        return 0

    try:
        related_facts = search_eidetic(
            project_id,
            finding_text,
            domain=domain,
            min_confidence=0.0,  # Search all, even low-confidence
            limit=limit,
        )

        decayed = 0
        for fact in related_facts:
            if fact.get("score", 0) >= similarity_threshold:
                content_hash = fact.get("content_hash")
                if content_hash and decay_eidetic_fact(
                    project_id,
                    content_hash,
                    decay_amount=decay_amount,
                    min_confidence=min_confidence,
                    reason=f"contradicted: {finding_text[:100]}",
                ):
                    decayed += 1

        if decayed:
            logger.info(f"Decayed {decayed} eidetic facts by finding in domain '{domain}'")
        return decayed
    except Exception as e:
        logger.warning(f"Failed to decay eidetic by finding: {e}")
        return 0


def propagate_lesson_confidence_to_qdrant(
    project_id: str,
    lesson_name: str,
    new_confidence: float,
) -> bool:
    """Cross-layer sync: update lesson confidence in Qdrant memory collection.

    Called after decay_related_lessons() updates YAML cold storage,
    keeping Qdrant payloads consistent with the source of truth.
    """
    if not _check_qdrant_available():
        return False

    try:
        client = _get_qdrant_client()
        coll = _memory_collection(project_id)

        if not client.collection_exists(coll):
            return False

        from qdrant_client.models import Filter, FieldCondition, MatchValue, PointStruct

        # Find lesson by type + text content match
        results = client.scroll(
            collection_name=coll,
            scroll_filter=Filter(
                must=[FieldCondition(key="type", match=MatchValue(value="lesson"))]
            ),
            limit=50,  # Scan lessons
            with_payload=True,
            with_vectors=True,
        )

        points, _ = results
        for point in points:
            text = point.payload.get("text", "")
            # Match by lesson name appearing in embedded text
            if lesson_name.lower() in text.lower():
                payload = point.payload
                payload["confidence"] = new_confidence
                import time as _time
                payload["confidence_synced_at"] = _time.time()

                updated = PointStruct(id=point.id, vector=point.vector, payload=payload)
                client.upsert(collection_name=coll, points=[updated])
                logger.debug(f"Synced lesson '{lesson_name}' confidence to {new_confidence:.2f} in Qdrant")
                return True

        return False  # Lesson not found in Qdrant
    except Exception as e:
        logger.warning(f"Failed to propagate lesson confidence: {e}")
        return False


def auto_sync_session_to_global(
    project_id: str,
    session_id: str,
    min_impact: float = 0.7,
) -> int:
    """Auto-sync high-impact findings from a single session to global.

    Called at POSTFLIGHT for incremental global sync.
    O(session_findings) not O(project_findings).
    """
    if not _check_qdrant_available():
        return 0

    try:
        # Get session findings from SQLite
        from empirica.data.session_database import SessionDatabase
        from empirica.utils.session_resolver import get_active_project_path
        from pathlib import Path

        project_path = get_active_project_path()
        if not project_path:
            return 0

        db_path = Path(project_path) / '.empirica' / 'sessions' / 'sessions.db'
        if not db_path.exists():
            return 0

        db = SessionDatabase(str(db_path))
        findings = db.get_project_findings(project_id, limit=50)
        db.close()

        if not findings:
            return 0

        synced = 0
        for f in findings:
            impact = f.get('impact', 0.0)
            f_session = f.get('session_id', '')
            if impact >= min_impact and f_session == session_id:
                if embed_to_global(
                    item_id=f.get('id', f.get('finding_id', '')),
                    text=f.get('finding', f.get('text', '')),
                    item_type='finding',
                    project_id=project_id,
                    session_id=session_id,
                    impact=impact,
                    timestamp=f.get('created_timestamp', ''),
                    tags=[f.get('subject', '')],
                ):
                    synced += 1

        if synced:
            logger.info(f"Auto-synced {synced} high-impact findings to global from session {session_id[:8]}")
        return synced
    except Exception as e:
        logger.warning(f"Failed to auto-sync session to global: {e}")
        return 0


def apply_staleness_signal(
    project_id: str,
    max_age_days: int = 180,
    period_days: int = 30,
) -> int:
    """Apply staleness-based signal to memory items based on age.

    Items are NOT deleted — staleness_factor is informational for retrieval
    ranking. Formula: staleness = min(1.0, age_days / max_age_days).

    Also updates assumption urgency via update_assumption_urgency().

    Returns number of items updated.
    """
    if not _check_qdrant_available():
        return 0

    try:
        import time as _time
        client = _get_qdrant_client()
        coll = _memory_collection(project_id)

        if not client.collection_exists(coll):
            return 0

        from qdrant_client.models import PointStruct

        # Scroll all memory items
        all_points = []
        offset = None
        while True:
            results = client.scroll(
                collection_name=coll,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=True,
            )
            points, next_offset = results
            all_points.extend(points)
            if next_offset is None or not points:
                break
            offset = next_offset

        now = _time.time()
        updated = 0
        batch = []

        for point in all_points:
            ts = point.payload.get("timestamp")
            if not ts:
                continue

            # Parse timestamp
            if isinstance(ts, str):
                try:
                    from datetime import datetime
                    ts_float = datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp()
                except Exception:
                    continue
            else:
                ts_float = float(ts)

            age_days = (now - ts_float) / 86400
            if age_days < period_days:
                continue  # Too recent, skip

            new_staleness = min(1.0, age_days / max_age_days)
            old_staleness = point.payload.get("staleness_factor", 0.0)

            # Only update if staleness changed significantly (>0.05)
            if abs(new_staleness - old_staleness) > 0.05:
                payload = point.payload
                payload["staleness_factor"] = round(new_staleness, 3)
                payload["staleness_updated_at"] = now
                batch.append(PointStruct(id=point.id, vector=point.vector, payload=payload))
                updated += 1

        # Batch upsert
        if batch:
            # Upsert in chunks of 50
            for i in range(0, len(batch), 50):
                client.upsert(collection_name=coll, points=batch[i:i+50])

        # Also update assumption urgency
        assumption_updated = update_assumption_urgency(project_id)
        updated += assumption_updated

        if updated:
            logger.info(f"Applied staleness to {updated} items ({assumption_updated} assumptions)")
        return updated
    except Exception as e:
        logger.warning(f"Failed to apply staleness signal: {e}")
        return 0


def update_assumption_urgency(
    project_id: str,
    max_age_days: int = 30,
) -> int:
    """Update urgency_signal on unverified assumptions based on age.

    Urgency = age_days / max_age_days × (1 - confidence).
    Verified/falsified assumptions get urgency = 0.

    Returns number of assumptions updated.
    """
    if not _check_qdrant_available():
        return 0

    try:
        import time as _time
        client = _get_qdrant_client()
        coll = _assumptions_collection(project_id)

        if not client.collection_exists(coll):
            return 0

        from qdrant_client.models import PointStruct

        results = client.scroll(
            collection_name=coll,
            limit=200,
            with_payload=True,
            with_vectors=True,
        )

        points, _ = results
        now = _time.time()
        updated = 0
        batch = []

        for point in points:
            status = point.payload.get("status", "unverified")
            ts = point.payload.get("timestamp", now)
            confidence = point.payload.get("confidence", 0.5)

            if status != "unverified":
                # Resolved: urgency should be 0
                if point.payload.get("urgency_signal", 0) != 0:
                    payload = point.payload
                    payload["urgency_signal"] = 0.0
                    batch.append(PointStruct(id=point.id, vector=point.vector, payload=payload))
                    updated += 1
                continue

            age_days = (now - float(ts)) / 86400
            new_urgency = min(1.0, (age_days / max_age_days) * (1.0 - confidence))
            old_urgency = point.payload.get("urgency_signal", 0.0)

            if abs(new_urgency - old_urgency) > 0.05:
                payload = point.payload
                payload["urgency_signal"] = round(new_urgency, 3)
                batch.append(PointStruct(id=point.id, vector=point.vector, payload=payload))
                updated += 1

        if batch:
            for i in range(0, len(batch), 50):
                client.upsert(collection_name=coll, points=batch[i:i+50])

        return updated
    except Exception as e:
        logger.warning(f"Failed to update assumption urgency: {e}")
        return 0
