"""
Core memory operations: embed, upsert, and search for memory items and docs.
"""
from __future__ import annotations
import logging
from typing import Dict, List, Optional

from empirica.core.qdrant.connection import (
    _check_qdrant_available, _get_qdrant_imports, _get_qdrant_client,
    _get_embedding_safe, _get_vector_size, _service_url, _rest_search, logger,
)
from empirica.core.qdrant.collections import (
    _docs_collection, _memory_collection, _eidetic_collection, _episodic_collection,
)

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

