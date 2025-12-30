"""
Qdrant vector store for Empirica projects.
Collections per project:
- project_{project_id}_docs: documentation embeddings with metadata
- project_{project_id}_memory: findings/unknowns/mistakes/dead_ends embeddings
"""
from __future__ import annotations
import os
import json
from typing import Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue  # type: ignore
import requests

from .embeddings import get_embedding


def _get_qdrant_client() -> QdrantClient:
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


def init_collections(project_id: str) -> None:
    client = _get_qdrant_client()
    for name in (_docs_collection(project_id), _memory_collection(project_id), _epistemics_collection(project_id)):
        if not client.collection_exists(name):
            client.create_collection(name, vectors_config=VectorParams(size=1536, distance=Distance.COSINE))


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

    Returns True if successful, False otherwise.
    """
    try:
        client = _get_qdrant_client()
        coll = _memory_collection(project_id)

        # Ensure collection exists
        if not client.collection_exists(coll):
            client.create_collection(coll, vectors_config=VectorParams(size=1536, distance=Distance.COSINE))

        vector = get_embedding(text)
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


def upsert_docs(project_id: str, docs: List[Dict]) -> None:
    """
    docs: List of {id, text, metadata:{doc_path, tags, concepts, questions, use_cases}}
    """
    client = _get_qdrant_client()
    coll = _docs_collection(project_id)
    points: List[PointStruct] = []
    for d in docs:
        vector = get_embedding(d.get("text", ""))
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


def upsert_memory(project_id: str, items: List[Dict]) -> None:
    """
    items: List of {id, text, type, goal_id, subtask_id, session_id, timestamp, ...}
    Stores full epistemic lineage metadata for filtering and analysis.
    Text is stored in payload for search result display.
    """
    client = _get_qdrant_client()
    coll = _memory_collection(project_id)
    points: List[PointStruct] = []
    for it in items:
        text = it.get("text", "")
        vector = get_embedding(text)
        # Store full metadata for epistemic lineage tracking
        # Include text for search result display (truncated to avoid bloat)
        payload = {
            "type": it.get("type", "unknown"),
            "text": text[:500] if text else None,  # Truncate for storage efficiency
            "text_full": text if len(text) <= 500 else None,  # Full text if short
            "goal_id": it.get("goal_id"),
            "subtask_id": it.get("subtask_id"),
            "session_id": it.get("session_id"),
            "timestamp": it.get("timestamp"),
            "subject": it.get("subject"),
            "impact": it.get("impact"),  # Epistemic impact score
            # Type-specific metadata
            "is_resolved": it.get("is_resolved"),  # For unknowns
            "resolved_by": it.get("resolved_by"),  # Resolution explanation
        }
        points.append(PointStruct(id=it["id"], vector=vector, payload=payload))
    if points:
        client.upsert(collection_name=coll, points=points)


def _service_url() -> Optional[str]:
    return os.getenv("EMPIRICA_QDRANT_URL")


def _rest_search(collection: str, vector: List[float], limit: int) -> List[Dict]:
    url = _service_url()
    assert url, "EMPIRICA_QDRANT_URL must be set for REST search"
    resp = requests.post(
        f"{url}/collections/{collection}/points/search",
        json={"vector": vector, "limit": limit, "with_payload": True},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("result", [])


def search(project_id: str, query_text: str, kind: str = "all", limit: int = 5) -> Dict[str, List[Dict]]:
    client = _get_qdrant_client()
    qvec = get_embedding(query_text)
    results: Dict[str, List[Dict]] = {}

    # Use query_points API (works with both local and server clients)
    try:
        if kind in ("all", "docs"):
            rd = client.query_points(
                collection_name=_docs_collection(project_id),
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
        if kind in ("all", "memory"):
            rm = client.query_points(
                collection_name=_memory_collection(project_id),
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
        return results
    except Exception as e:
        # Fall back to REST if query_points fails
        pass

    # REST fallback (for remote Qdrant server)
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


def upsert_epistemics(project_id: str, items: List[Dict]) -> None:
    """
    Store epistemic learning trajectories (PREFLIGHT → POSTFLIGHT deltas).
    
    items: List of {
        id: "session_{uuid}",
        text: "Combined reasoning from PREFLIGHT + POSTFLIGHT",
        metadata: {
            session_id, ai_id, timestamp, task_description,
            preflight: {engagement, know, do, context, ...},
            postflight: {engagement, know, do, context, ...},
            deltas: {know: +0.25, uncertainty: -0.2, ...},
            calibration_accuracy: "good"|"fair"|"poor",
            investigation_phase: bool,
            mistakes_count: int,
            completion: float,
            impact: float
        }
    }
    """
    client = _get_qdrant_client()
    coll = _epistemics_collection(project_id)
    points: List[PointStruct] = []
    
    for item in items:
        vector = get_embedding(item.get("text", ""))
        payload = item.get("metadata", {})
        points.append(PointStruct(id=item["id"], vector=vector, payload=payload))
    
    if points:
        client.upsert(collection_name=coll, points=points)


def search_epistemics(
    project_id: str, 
    query_text: str, 
    filters: Optional[Dict] = None,
    limit: int = 5
) -> List[Dict]:
    """
    Search epistemic learning trajectories by semantic similarity + optional filters.
    
    Args:
        project_id: Project UUID
        query_text: Semantic query (e.g., "OAuth2 authentication learning")
        filters: Qdrant filter conditions (e.g., {"deltas.know": {"$gte": 0.2}})
        limit: Max results
        
    Returns:
        List of {score, session_id, task_description, preflight, postflight, deltas, ...}
    """
    client = _get_qdrant_client()
    qvec = get_embedding(query_text)
    coll = _epistemics_collection(project_id)
    
    # Build Qdrant filter if provided
    query_filter = None
    if filters:
        # Convert simple dict filters to Qdrant Filter objects
        # For now, pass through - full filter support can be added later
        pass
    
    try:
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
    except Exception:
        # Fall back to REST if needed
        pass
    
    # REST fallback
    rd = _rest_search(coll, qvec, limit)
    return [
        {
            "score": d.get('score', 0.0),
            **(d.get('payload') or {})
        }
        for d in rd
    ]
