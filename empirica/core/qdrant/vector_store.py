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


def init_collections(project_id: str) -> bool:
    """Initialize Qdrant collections. Returns False if Qdrant not available."""
    if not _check_qdrant_available():
        return False

    try:
        _, Distance, VectorParams, _ = _get_qdrant_imports()
        client = _get_qdrant_client()
        for name in (_docs_collection(project_id), _memory_collection(project_id), _epistemics_collection(project_id)):
            if not client.collection_exists(name):
                client.create_collection(name, vectors_config=VectorParams(size=1536, distance=Distance.COSINE))
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
            client.create_collection(coll, vectors_config=VectorParams(size=1536, distance=Distance.COSINE))

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
