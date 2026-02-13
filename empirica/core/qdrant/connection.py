"""
Qdrant connection infrastructure and embedding utilities.

This module is OPTIONAL. Empirica core works without Qdrant.
Set EMPIRICA_ENABLE_EMBEDDINGS=true to enable semantic search features.
"""
from __future__ import annotations
import os
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

