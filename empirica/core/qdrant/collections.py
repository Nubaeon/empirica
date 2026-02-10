"""
Qdrant collection naming, initialization, and migration utilities.
"""
from __future__ import annotations
import logging
from typing import Dict, List

from empirica.core.qdrant.connection import (
    _check_qdrant_available, _get_qdrant_imports, _get_qdrant_client,
    _get_vector_size, logger,
)

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

