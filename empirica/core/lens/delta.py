"""
Delta Engine — Profile-aware epistemic delta scoring.

Orchestrates: extract → chunk → embed → multi-collection search →
match unknowns/goals → HESM → classify → DeltaResult.

Reuses:
- connection.py: _get_embedding_safe(), _get_qdrant_client()
- collections.py: collection name functions
- pattern_retrieval.py: multi-collection search pattern
- information_gain.py: novelty_score() for dedup
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from empirica.core.lens.profile import (
    HumanEpistemicProfile, HESMState, Unknown, build_profile,
)
from empirica.core.lens.chunker import Chunk
from empirica.core.lens.hesm import (
    ChunkSearchResults, compute_hesm, composite_novelty, classify_chunk,
    UNKNOWN_MATCH_THRESHOLD,
)

logger = logging.getLogger(__name__)

DEFAULT_SEARCH_LIMIT = 5


@dataclass
class ChunkResult:
    """Delta result for a single chunk."""
    index: int
    text_preview: str
    hesm: HESMState
    composite: float  # 0.0 (novel) to 1.0 (known)
    classification: str  # novel, partial, known, gap_closing
    matched_unknown_id: Optional[str] = None
    matched_unknown_text: Optional[str] = None
    matched_goal_id: Optional[str] = None
    matched_goal_text: Optional[str] = None
    best_match_collection: Optional[str] = None
    best_match_score: float = 0.0


@dataclass
class DeltaResult:
    """Complete delta analysis result."""
    source: str
    source_type: str
    title: Optional[str] = None
    chunks_total: int = 0
    chunks_novel: int = 0
    chunks_partial: int = 0
    chunks_known: int = 0
    chunks_gap_closing: int = 0
    novelty_pct: float = 0.0
    gaps_matched: int = 0
    chunk_results: List[ChunkResult] = field(default_factory=list)
    profile_summary: Dict[str, Any] = field(default_factory=dict)
    elapsed_ms: int = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "source_type": self.source_type,
            "title": self.title,
            "chunks_total": self.chunks_total,
            "chunks_novel": self.chunks_novel,
            "chunks_partial": self.chunks_partial,
            "chunks_known": self.chunks_known,
            "chunks_gap_closing": self.chunks_gap_closing,
            "novelty_pct": self.novelty_pct,
            "gaps_matched": self.gaps_matched,
            "chunk_results": [
                {
                    "index": cr.index,
                    "text_preview": cr.text_preview,
                    "composite": cr.composite,
                    "classification": cr.classification,
                    "hesm": cr.hesm.to_dict(),
                    "matched_unknown_id": cr.matched_unknown_id,
                    "matched_goal_id": cr.matched_goal_id,
                }
                for cr in self.chunk_results
            ],
            "elapsed_ms": self.elapsed_ms,
            "error": self.error,
        }


def compute_delta(
    project_id: str,
    chunks: List[Chunk],
    source: str,
    source_type: str = "unknown",
    title: Optional[str] = None,
    profile: Optional[HumanEpistemicProfile] = None,
    gaps_only: bool = False,
) -> DeltaResult:
    """
    Compute epistemic delta for a list of chunks against the human's profile.

    Args:
        project_id: Project UUID or name
        chunks: Pre-chunked text segments
        source: Source identifier (URL, path, etc.)
        source_type: Source type string
        title: Document title
        profile: Pre-built profile (built if not provided)
        gaps_only: If True, only return gap-closing chunks

    Returns:
        DeltaResult with per-chunk HESM scores and classifications
    """
    start = time.time()
    result = DeltaResult(
        source=source,
        source_type=source_type,
        title=title,
        chunks_total=len(chunks),
    )

    if not chunks:
        result.elapsed_ms = int((time.time() - start) * 1000)
        return result

    # Build profile if not provided
    if profile is None:
        profile = build_profile(project_id)

    result.profile_summary = {
        "total_findings": profile.total_findings,
        "open_unknowns": len(profile.open_unknowns),
        "active_goals": len(profile.active_goals),
        "domains": len(profile.domain_strengths),
    }

    # Check Qdrant availability
    qdrant_available = False
    client = None
    try:
        from empirica.core.qdrant.connection import (
            _check_qdrant_available, _get_qdrant_client, _get_embedding_safe,
        )
        qdrant_available = _check_qdrant_available()
        if qdrant_available:
            client = _get_qdrant_client()
    except ImportError:
        logger.debug("Qdrant not available")

    # Process each chunk
    for chunk in chunks:
        chunk_result = _process_chunk(
            chunk=chunk,
            profile=profile,
            project_id=project_id,
            client=client,
            qdrant_available=qdrant_available,
        )

        # Apply gaps_only filter
        if gaps_only and chunk_result.classification not in ("gap_closing",):
            continue

        result.chunk_results.append(chunk_result)

        # Count classifications
        if chunk_result.classification == "novel":
            result.chunks_novel += 1
        elif chunk_result.classification == "partial":
            result.chunks_partial += 1
        elif chunk_result.classification == "known":
            result.chunks_known += 1
        elif chunk_result.classification == "gap_closing":
            result.chunks_gap_closing += 1
            result.gaps_matched += 1

    # Compute novelty percentage
    if result.chunks_total > 0:
        result.novelty_pct = round(
            (result.chunks_novel + result.chunks_gap_closing) / result.chunks_total * 100, 1
        )

    # Sort: gap-closing first, then by novelty (lowest composite = most novel)
    result.chunk_results.sort(
        key=lambda cr: (
            0 if cr.classification == "gap_closing" else 1,
            cr.composite,
        )
    )

    result.elapsed_ms = int((time.time() - start) * 1000)
    return result


def _process_chunk(
    chunk: Chunk,
    profile: HumanEpistemicProfile,
    project_id: str,
    client,
    qdrant_available: bool,
) -> ChunkResult:
    """Process a single chunk: embed, search, compute HESM, classify."""
    preview = chunk.text[:100].replace("\n", " ")

    # If Qdrant not available, all chunks are novel
    if not qdrant_available or client is None:
        hesm = HESMState(uncertainty=0.8)
        return ChunkResult(
            index=chunk.index,
            text_preview=preview,
            hesm=hesm,
            composite=0.0,
            classification="novel",
        )

    # Embed chunk
    try:
        from empirica.core.qdrant.connection import _get_embedding_safe
        vector = _get_embedding_safe(chunk.text)
        if vector is None:
            hesm = HESMState(uncertainty=0.8)
            return ChunkResult(
                index=chunk.index, text_preview=preview,
                hesm=hesm, composite=0.0, classification="novel",
            )
    except Exception as e:
        logger.debug(f"Embedding failed for chunk {chunk.index}: {e}")
        hesm = HESMState(uncertainty=0.8)
        return ChunkResult(
            index=chunk.index, text_preview=preview,
            hesm=hesm, composite=0.0, classification="novel",
        )

    # Multi-collection search
    search_results = _search_collections(
        vector=vector,
        project_id=project_id,
        client=client,
        profile=profile,
        chunk_text=chunk.text,
    )

    # Compute HESM
    hesm = compute_hesm(profile, chunk.text, search_results)

    # Classify
    has_unknown_match = bool(search_results.unknown_matches)
    has_goal_match = bool(search_results.goal_matches)
    classification = classify_chunk(hesm, unknown_match=has_unknown_match)

    # Find best match info
    best_collection = None
    best_score = 0.0
    for coll_name, hits in [
        ("docs", search_results.docs_hits),
        ("memory", search_results.memory_hits),
        ("eidetic", search_results.eidetic_hits),
        ("episodic", search_results.episodic_hits),
    ]:
        for hit in hits:
            if hit.get("score", 0.0) > best_score:
                best_score = hit["score"]
                best_collection = coll_name

    cr = ChunkResult(
        index=chunk.index,
        text_preview=preview,
        hesm=hesm,
        composite=composite_novelty(hesm),
        classification=classification,
        best_match_collection=best_collection,
        best_match_score=best_score,
    )

    # Attach matched unknown/goal info
    if search_results.unknown_matches:
        best_um = search_results.unknown_matches[0]
        cr.matched_unknown_id = best_um.get("id")
        cr.matched_unknown_text = best_um.get("text", "")[:80]

    if search_results.goal_matches:
        best_gm = search_results.goal_matches[0]
        cr.matched_goal_id = best_gm.get("id")
        cr.matched_goal_text = best_gm.get("text", "")[:80]

    return cr


def _search_collections(
    vector: list,
    project_id: str,
    client,
    profile: HumanEpistemicProfile,
    chunk_text: str,
) -> ChunkSearchResults:
    """Search across 4+ Qdrant collections for a chunk's embedding."""
    from empirica.core.qdrant.collections import (
        _docs_collection, _memory_collection, _eidetic_collection,
        _episodic_collection, _goals_collection,
    )

    limit = DEFAULT_SEARCH_LIMIT

    docs_hits = _safe_search(client, _docs_collection(project_id), vector, limit)
    memory_hits = _safe_search(client, _memory_collection(project_id), vector, limit)
    eidetic_hits = _safe_search(client, _eidetic_collection(project_id), vector, limit)
    episodic_hits = _safe_search(client, _episodic_collection(project_id), vector, limit)

    # Match against open unknowns (via embedding similarity)
    unknown_matches = _match_unknowns(vector, profile.open_unknowns, client, project_id)

    # Match against active goals
    goal_matches = _safe_search(client, _goals_collection(project_id), vector, 3)

    return ChunkSearchResults(
        docs_hits=docs_hits,
        memory_hits=memory_hits,
        eidetic_hits=eidetic_hits,
        episodic_hits=episodic_hits,
        unknown_matches=unknown_matches,
        goal_matches=goal_matches,
    )


def _safe_search(client, collection_name: str, vector: list, limit: int) -> List[Dict]:
    """Search a Qdrant collection, returning empty list on failure."""
    try:
        if not client.collection_exists(collection_name):
            return []

        results = client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=limit,
            with_payload=True,
        )

        return [
            {
                "score": r.score,
                "text": (r.payload.get("text") or r.payload.get("finding")
                         or r.payload.get("narrative") or "")[:200],
                "timestamp": r.payload.get("timestamp", 0),
                "type": r.payload.get("type", ""),
                "domain": r.payload.get("domain", ""),
                "id": str(r.id),
            }
            for r in results.points
        ]
    except Exception as e:
        logger.debug(f"Search failed for {collection_name}: {e}")
        return []


def _match_unknowns(
    vector: list,
    open_unknowns: List[Unknown],
    client,
    project_id: str,
) -> List[Dict]:
    """
    Match chunk vector against embedded unknowns.

    If unknowns aren't embedded, falls back to text similarity
    via the memory collection with type=unknown filter.
    """
    if not open_unknowns:
        return []

    # Search memory collection filtered by type=unknown
    try:
        from empirica.core.qdrant.collections import _memory_collection
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        coll = _memory_collection(project_id)
        if not client.collection_exists(coll):
            return []

        results = client.query_points(
            collection_name=coll,
            query=vector,
            query_filter=Filter(must=[
                FieldCondition(key="type", match=MatchValue(value="unknown")),
            ]),
            limit=3,
            with_payload=True,
        )

        matches = []
        for r in results.points:
            if r.score >= UNKNOWN_MATCH_THRESHOLD:
                matches.append({
                    "id": str(r.id),
                    "text": r.payload.get("text", "")[:200],
                    "score": r.score,
                })
        return matches
    except Exception as e:
        logger.debug(f"Unknown matching failed: {e}")
        return []
