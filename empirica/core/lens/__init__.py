"""
Empirica Lens — Bidirectional Epistemic Adapter (HESM v0.1.0)

Human epistemic profiling, delta scoring, and feedback loop.

Core components:
- profile: HumanEpistemicProfile assembly from all collections
- extractors: URL/PDF/file text extraction
- chunker: Paragraph-based text chunking
- hesm: 13-vector Human Epistemic State Model
- delta: Profile-aware delta scoring engine
- learn: --learn feedback loop (artifact logging + HESM belief storage)
"""

from empirica.core.lens.profile import (
    HumanEpistemicProfile,
    HESMState,
    build_profile,
    profile_for_ai,
)
from empirica.core.lens.extractors import extract_text, ExtractedDocument
from empirica.core.lens.chunker import chunk_text, Chunk
from empirica.core.lens.hesm import compute_hesm, composite_novelty, classify_chunk
from empirica.core.lens.delta import compute_delta, DeltaResult, ChunkResult
from empirica.core.lens.learn import learn_from_delta, LearnResult

__all__ = [
    "HumanEpistemicProfile",
    "HESMState",
    "build_profile",
    "profile_for_ai",
    "extract_text",
    "ExtractedDocument",
    "chunk_text",
    "Chunk",
    "compute_hesm",
    "composite_novelty",
    "classify_chunk",
    "compute_delta",
    "DeltaResult",
    "ChunkResult",
    "learn_from_delta",
    "LearnResult",
]
