"""
Provider-agnostic embeddings adapter.
Reads provider/model from env (or defaults) and returns float vectors.

ENV:
- EMPIRICA_EMBEDDINGS_PROVIDER: openai|azure|openrouter|local (default: openai)
- EMPIRICA_EMBEDDINGS_MODEL: model name (default: text-embedding-3-small)
- OPENAI_API_KEY (for provider=openai)

Note: For Path A, we implement OpenAI only; others can be added later.
"""
from __future__ import annotations
import os
from typing import List

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # lazy import guard


class EmbeddingsProvider:
    def __init__(self) -> None:
        self.provider = os.getenv("EMPIRICA_EMBEDDINGS_PROVIDER", "local").lower()
        self.model = os.getenv("EMPIRICA_EMBEDDINGS_MODEL", "text-embedding-3-small")
        self._client = None
        if self.provider == "openai":
            if OpenAI is None:
                raise RuntimeError("openai package not available; install openai>=1.0")
            self._client = OpenAI()
        elif self.provider == "local":
            # No external dependency; simple hashing-based embedding (for testing)
            self._client = None
        else:
            raise RuntimeError(f"Unsupported provider '{self.provider}'. Set EMPIRICA_EMBEDDINGS_PROVIDER=openai|local")

    def embed(self, text: str) -> List[float]:
        text = text or ""
        if self.provider == "openai":
            resp = self._client.embeddings.create(model=self.model, input=text)
            return resp.data[0].embedding  # type: ignore
        if self.provider == "local":
            # Very simple hashing embedding to 1536 dims for dev/tests
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
        raise RuntimeError(f"Unsupported provider '{self.provider}'.")


_provider_singleton: EmbeddingsProvider | None = None

def get_embedding(text: str) -> List[float]:
    global _provider_singleton
    if _provider_singleton is None:
        _provider_singleton = EmbeddingsProvider()
    return _provider_singleton.embed(text)
