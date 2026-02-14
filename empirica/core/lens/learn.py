"""
Learn — Feedback loop for --learn mode.

Takes DeltaResult and auto-logs artifacts based on chunk classification:
- Novel → finding-log
- Gap-closing → unknown-resolve + finding-log
- Partial → unknown-log
- Known but decayed → FSRS refresh (confirm_eidetic_fact)
- Contradicts existing → immune system decay

Also stores HESM belief payloads per chunk in docs collection.
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from empirica.core.lens.delta import DeltaResult, ChunkResult
from empirica.core.lens.hesm import KNOWN_THRESHOLD

logger = logging.getLogger(__name__)


@dataclass
class LearnResult:
    """Result of the learn feedback loop."""
    findings_logged: int = 0
    unknowns_logged: int = 0
    unknowns_resolved: int = 0
    eidetic_refreshed: int = 0
    beliefs_stored: int = 0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "findings_logged": self.findings_logged,
            "unknowns_logged": self.unknowns_logged,
            "unknowns_resolved": self.unknowns_resolved,
            "eidetic_refreshed": self.eidetic_refreshed,
            "beliefs_stored": self.beliefs_stored,
            "errors": self.errors,
        }


def learn_from_delta(
    project_id: str,
    delta_result: DeltaResult,
    session_id: Optional[str] = None,
    ai_id: str = "claude-code",
) -> LearnResult:
    """
    Process delta result and auto-log artifacts.

    For each chunk based on classification:
    - novel → finding-log with auto-estimated impact
    - gap_closing → unknown-resolve + finding-log
    - partial → unknown-log
    - known → eidetic refresh if retention is low

    All chunks get HESM belief stored in docs collection.

    Args:
        project_id: Project UUID
        delta_result: Computed delta result
        session_id: Optional session ID for artifact linkage
        ai_id: AI identifier

    Returns:
        LearnResult with counts of artifacts created
    """
    result = LearnResult()

    for cr in delta_result.chunk_results:
        try:
            _process_chunk_learn(
                cr=cr,
                project_id=project_id,
                source=delta_result.source,
                session_id=session_id,
                ai_id=ai_id,
                result=result,
            )
        except Exception as e:
            result.errors.append(f"Chunk {cr.index}: {e}")
            logger.warning(f"Learn failed for chunk {cr.index}: {e}")

    return result


def _process_chunk_learn(
    cr: ChunkResult,
    project_id: str,
    source: str,
    session_id: Optional[str],
    ai_id: str,
    result: LearnResult,
) -> None:
    """Process a single chunk through the learn pipeline."""
    if cr.classification == "novel":
        _log_finding(cr, project_id, source, session_id, ai_id, result)
    elif cr.classification == "gap_closing":
        _resolve_unknown(cr, project_id, session_id, ai_id, result)
        _log_finding(cr, project_id, source, session_id, ai_id, result)
    elif cr.classification == "partial":
        _log_unknown(cr, project_id, source, session_id, ai_id, result)
    elif cr.classification == "known":
        # Refresh if retention is low
        if cr.hesm.retention < 0.5:
            _refresh_eidetic(cr, project_id, session_id, result)

    # Store HESM belief for all chunks
    _store_belief(cr, project_id, source, session_id, result)


def _log_finding(
    cr: ChunkResult,
    project_id: str,
    source: str,
    session_id: Optional[str],
    ai_id: str,
    result: LearnResult,
) -> None:
    """Log a finding from a novel chunk."""
    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()

        # Auto-estimate impact from HESM
        # Low exposure + low comprehension = high impact (genuinely new)
        impact = round(max(0.3, 1.0 - cr.composite), 2)

        finding_text = cr.text_preview[:200]
        if len(finding_text) < 20:
            finding_text = f"Novel content from {source}: {finding_text}"

        finding_id = str(uuid.uuid4())
        cursor = db.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO project_findings
            (id, project_id, session_id, ai_id, finding, impact, subject, created_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            finding_id, project_id, session_id, ai_id,
            finding_text, impact, "lens-ingest", time.time(),
        ))
        db.conn.commit()
        db.close()

        result.findings_logged += 1
        logger.debug(f"Logged finding for chunk {cr.index} (impact={impact})")

        # Also embed in Qdrant
        try:
            from empirica.core.qdrant.memory import embed_single_memory_item
            embed_single_memory_item(
                project_id=project_id,
                item_id=finding_id,
                text=finding_text,
                item_type="finding",
                metadata={
                    "session_id": session_id,
                    "ai_id": ai_id,
                    "impact": impact,
                    "source": source,
                    "ingested_by": "lens",
                },
            )
        except Exception as e:
            logger.debug(f"Qdrant embed failed: {e}")

    except Exception as e:
        result.errors.append(f"Finding log: {e}")


def _resolve_unknown(
    cr: ChunkResult,
    project_id: str,
    session_id: Optional[str],
    ai_id: str,
    result: LearnResult,
) -> None:
    """Resolve a matched unknown."""
    if not cr.matched_unknown_id:
        return

    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Mark unknown as resolved
        cursor.execute("""
            UPDATE project_unknowns
            SET is_resolved = 1, resolved_by = ?, resolved_at = ?
            WHERE id = ? AND project_id = ?
        """, (
            f"lens-delta: {cr.text_preview[:100]}",
            time.time(),
            cr.matched_unknown_id,
            project_id,
        ))
        db.conn.commit()
        db.close()

        result.unknowns_resolved += 1
        logger.debug(f"Resolved unknown {cr.matched_unknown_id[:8]} via chunk {cr.index}")
    except Exception as e:
        result.errors.append(f"Unknown resolve: {e}")


def _log_unknown(
    cr: ChunkResult,
    project_id: str,
    source: str,
    session_id: Optional[str],
    ai_id: str,
    result: LearnResult,
) -> None:
    """Log a partial chunk as an unknown (needs deeper investigation)."""
    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()

        unknown_text = f"Partially known from {source}: {cr.text_preview[:150]}"
        unknown_id = str(uuid.uuid4())

        cursor = db.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO project_unknowns
            (id, project_id, session_id, ai_id, unknown, is_resolved, created_timestamp)
            VALUES (?, ?, ?, ?, ?, 0, ?)
        """, (
            unknown_id, project_id, session_id, ai_id,
            unknown_text, time.time(),
        ))
        db.conn.commit()
        db.close()

        result.unknowns_logged += 1
    except Exception as e:
        result.errors.append(f"Unknown log: {e}")


def _refresh_eidetic(
    cr: ChunkResult,
    project_id: str,
    session_id: Optional[str],
    result: LearnResult,
) -> None:
    """Refresh a known-but-decayed eidetic fact."""
    try:
        from empirica.core.qdrant.eidetic import confirm_eidetic_fact
        # Use the best match to find what to confirm
        if cr.best_match_collection == "eidetic" and cr.best_match_score > 0.7:
            # Confirm the existing fact to boost retention
            confirm_eidetic_fact(
                project_id=project_id,
                fact_text=cr.text_preview[:200],
                session_id=session_id or "lens-refresh",
            )
            result.eidetic_refreshed += 1
    except Exception as e:
        logger.debug(f"Eidetic refresh: {e}")


def _store_belief(
    cr: ChunkResult,
    project_id: str,
    source: str,
    session_id: Optional[str],
    result: LearnResult,
) -> None:
    """Store HESM belief payload for a chunk in the docs collection."""
    try:
        from empirica.core.qdrant.memory import upsert_docs

        hesm_dict = cr.hesm.to_dict()
        payload = {
            "text": cr.text_preview[:500],
            "source": source,
            "chunk_index": cr.index,
            "ingested_by": "lens",
            "hesm": hesm_dict,
            "hesm_updated_at": time.time(),
            "interaction_count": 1,
            "classification": cr.classification,
            "composite_novelty": cr.composite,
            "matched_unknown_id": cr.matched_unknown_id,
            "matched_goal_id": cr.matched_goal_id,
        }

        upsert_docs(
            project_id=project_id,
            doc_id=f"lens-belief-{uuid.uuid4().hex[:12]}",
            text=cr.text_preview[:500],
            metadata=payload,
        )
        result.beliefs_stored += 1
    except Exception as e:
        logger.debug(f"Belief storage: {e}")
