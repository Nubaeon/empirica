"""
Provider-agnostic embeddings adapter.
Reads provider/model from env (or defaults) and returns float vectors.

ENV:
- EMPIRICA_EMBEDDINGS_PROVIDER: openai|ollama|local|auto (default: auto)
- EMPIRICA_EMBEDDINGS_MODEL: model name (default varies by provider)
- EMPIRICA_OLLAMA_URL: Ollama server URL (default: http://localhost:11434)
- OPENAI_API_KEY (for provider=openai)

Providers:
- auto: Auto-detect best available (ollama if running, else local)
- openai: OpenAI API (requires openai package + API key)
- ollama: Local Ollama server (phi3, nomic-embed-text, etc.)
- local: Hash-based fallback for testing (no external deps)
"""
from __future__ import annotations
import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Cache for Ollama availability check
_ollama_available: Optional[bool] = None

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # lazy import guard

# Default models and their vector dimensions per provider
DEFAULT_MODELS = {
    "openai": "text-embedding-3-small",
    "ollama": "nomic-embed-text",  # 768-dim, good semantic quality
    "local": "hash-1536",
}

# Known vector dimensions per model
MODEL_DIMENSIONS = {
    # OpenAI
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
    # Ollama
    "nomic-embed-text": 768,
    "mxbai-embed-large": 1024,
    "all-minilm": 384,
    "phi3": 3072,
    "phi3:latest": 3072,
    "llama3.1:8b": 4096,
    # Local
    "hash-1536": 1536,
}


def _check_ollama_available(ollama_url: str = "http://localhost:11434") -> bool:
    """Check if Ollama server is running and has embedding models."""
    global _ollama_available

    if _ollama_available is not None:
        return _ollama_available

    try:
        import requests
        # Quick health check
        resp = requests.get(f"{ollama_url}/api/tags", timeout=2)
        if resp.status_code == 200:
            # Check if nomic-embed-text is available
            models = resp.json().get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models]
            if "nomic-embed-text" in model_names:
                _ollama_available = True
                logger.info("Ollama detected with nomic-embed-text - using semantic embeddings")
                return True
            # If nomic-embed-text not available, still use Ollama if any embedding model exists
            for name in model_names:
                if name in MODEL_DIMENSIONS:
                    _ollama_available = True
                    logger.info(f"Ollama detected with {name} - using semantic embeddings")
                    return True
        _ollama_available = False
        return False
    except Exception:
        _ollama_available = False
        return False


def _resolve_auto_provider(ollama_url: str) -> str:
    """Resolve 'auto' provider to actual provider based on availability."""
    if _check_ollama_available(ollama_url):
        return "ollama"
    return "local"


class EmbeddingsProvider:
    def __init__(self) -> None:
        self.ollama_url = os.getenv("EMPIRICA_OLLAMA_URL", "http://localhost:11434")

        # Get provider from env, default to "auto"
        provider_env = os.getenv("EMPIRICA_EMBEDDINGS_PROVIDER", "auto").lower()

        # Resolve "auto" to actual provider
        if provider_env == "auto":
            self.provider = _resolve_auto_provider(self.ollama_url)
        else:
            self.provider = provider_env

        self.model = os.getenv("EMPIRICA_EMBEDDINGS_MODEL", DEFAULT_MODELS.get(self.provider, "nomic-embed-text"))
        self._client = None
        self._vector_size: Optional[int] = None

        if self.provider == "openai":
            if OpenAI is None:
                raise RuntimeError("openai package not available; install openai>=1.0")
            self._client = OpenAI()
            self._vector_size = MODEL_DIMENSIONS.get(self.model, 1536)
        elif self.provider == "ollama":
            # Ollama uses REST API - no special client needed
            self._client = None
            # Vector size from MODEL_DIMENSIONS or determined on first embed
            self._vector_size = MODEL_DIMENSIONS.get(self.model)
        elif self.provider == "local":
            # No external dependency; simple hashing-based embedding (for testing)
            self._client = None
            self._vector_size = 1536
        else:
            raise RuntimeError(f"Unsupported provider '{self.provider}'. Set EMPIRICA_EMBEDDINGS_PROVIDER=openai|ollama|local|auto")

        logger.debug(f"Embeddings provider: {self.provider}, model: {self.model}")

    def embed(self, text: str) -> List[float]:
        text = text or ""

        if self.provider == "openai":
            resp = self._client.embeddings.create(model=self.model, input=text)
            return resp.data[0].embedding  # type: ignore

        if self.provider == "ollama":
            return self._embed_ollama(text)

        if self.provider == "local":
            return self._embed_local_hash(text)

        raise RuntimeError(f"Unsupported provider '{self.provider}'.")

    def _embed_ollama(self, text: str) -> List[float]:
        """Embed using local Ollama server."""
        import requests

        url = f"{self.ollama_url}/api/embeddings"
        payload = {
            "model": self.model,
            "prompt": text
        }

        try:
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            embedding = data.get("embedding", [])

            if not embedding:
                logger.warning(f"Ollama returned empty embedding for model {self.model}")
                return self._embed_local_hash(text)  # Fallback

            # Cache vector size for consistency checks
            if self._vector_size is None:
                self._vector_size = len(embedding)
                logger.info(f"Ollama {self.model} vector size: {self._vector_size}")

            return embedding

        except requests.exceptions.ConnectionError:
            logger.warning(f"Cannot connect to Ollama at {self.ollama_url} - falling back to local hash")
            return self._embed_local_hash(text)
        except Exception as e:
            logger.warning(f"Ollama embedding failed: {e} - falling back to local hash")
            return self._embed_local_hash(text)

    def _embed_local_hash(self, text: str) -> List[float]:
        """Simple hashing embedding for testing (no external deps)."""
        import hashlib
        import math

        vec = [0.0] * 1536
        for tok in text.split():
            h = int(hashlib.sha256(tok.encode()).hexdigest(), 16)
            idx = h % 1536
            vec[idx] += 1.0
        # L2 normalize
        norm = math.sqrt(sum(v*v for v in vec)) or 1.0
        return [v / norm for v in vec]

    @property
    def vector_size(self) -> int:
        """Get the vector size for this provider/model."""
        if self._vector_size is None:
            # Determine by doing a test embed
            test_vec = self.embed("test")
            self._vector_size = len(test_vec)
        return self._vector_size


_provider_singleton: EmbeddingsProvider | None = None

def get_embedding(text: str) -> List[float]:
    global _provider_singleton
    if _provider_singleton is None:
        _provider_singleton = EmbeddingsProvider()
    return _provider_singleton.embed(text)


def get_vector_size() -> int:
    """
    Get the vector dimension for the current embeddings provider/model.
    Used by vector_store.py to create collections with correct dimensions.
    """
    global _provider_singleton
    if _provider_singleton is None:
        _provider_singleton = EmbeddingsProvider()
    return _provider_singleton.vector_size


def get_provider_info() -> dict:
    """Get current embeddings provider configuration info."""
    global _provider_singleton
    if _provider_singleton is None:
        _provider_singleton = EmbeddingsProvider()
    return {
        "provider": _provider_singleton.provider,
        "model": _provider_singleton.model,
        "vector_size": _provider_singleton.vector_size,
    }
