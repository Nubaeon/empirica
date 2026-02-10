"""
Decay and lifecycle management: confidence decay, staleness signals, urgency updates.
"""
from __future__ import annotations
import logging
from typing import Dict, List, Optional

from empirica.core.qdrant.connection import (
    _check_qdrant_available, _get_qdrant_imports, _get_qdrant_client,
    _get_embedding_safe, logger,
)
from empirica.core.qdrant.collections import (
    _eidetic_collection, _memory_collection, _global_learnings_collection,
    _assumptions_collection,
)
from empirica.core.qdrant.eidetic import search_eidetic
from empirica.core.qdrant.global_sync import embed_to_global

def decay_eidetic_fact(
    project_id: str,
    content_hash: str,
    decay_amount: float = 0.05,
    min_confidence: float = 0.3,
    reason: str = None,
) -> bool:
    """Decay an eidetic fact's confidence when contradicted by new findings.

    Mirrors confirm_eidetic_fact() but decreases confidence.
    Domain-scoped: caller must ensure domain matching (central tolerance).
    """
    if not _check_qdrant_available():
        return False

    try:
        import time as _time
        client = _get_qdrant_client()
        coll = _eidetic_collection(project_id)

        if not client.collection_exists(coll):
            return False

        from qdrant_client.models import Filter, FieldCondition, MatchValue, PointStruct

        results = client.scroll(
            collection_name=coll,
            scroll_filter=Filter(
                must=[FieldCondition(key="content_hash", match=MatchValue(value=content_hash))]
            ),
            limit=1,
            with_payload=True,
            with_vectors=True,
        )

        points, _ = results
        if not points:
            return False

        point = points[0]
        payload = point.payload
        old_confidence = payload.get("confidence", 0.5)
        new_confidence = max(min_confidence, old_confidence - decay_amount)

        payload["confidence"] = new_confidence
        payload["last_decayed"] = _time.time()
        payload["decay_reason"] = reason or "contradicted by finding"

        updated_point = PointStruct(id=point.id, vector=point.vector, payload=payload)
        client.upsert(collection_name=coll, points=[updated_point])

        logger.info(f"Decayed eidetic fact: {old_confidence:.2f} → {new_confidence:.2f} ({reason or 'finding'})")
        return True
    except Exception as e:
        logger.warning(f"Failed to decay eidetic fact: {e}")
        return False


def decay_eidetic_by_finding(
    project_id: str,
    finding_text: str,
    domain: str = None,
    decay_amount: float = 0.03,
    min_confidence: float = 0.3,
    similarity_threshold: float = 0.85,
    limit: int = 5,
) -> int:
    """Decay eidetic facts semantically similar to a contradicting finding.

    CENTRAL TOLERANCE: If domain provided, only decay facts in that domain.
    Lighter decay (0.03) than lessons (0.05) — eidetic facts have higher
    inertia from multiple confirmations.

    Threshold is deliberately high (0.85) to prevent autoimmune decay —
    semantic similarity alone doesn't imply contradiction. Only near-exact
    matches with opposing content should trigger decay.

    Returns number of facts decayed.
    """
    if not _check_qdrant_available():
        return 0

    try:
        related_facts = search_eidetic(
            project_id,
            finding_text,
            domain=domain,
            min_confidence=0.0,  # Search all, even low-confidence
            limit=limit,
        )

        decayed = 0
        for fact in related_facts:
            if fact.get("score", 0) >= similarity_threshold:
                content_hash = fact.get("content_hash")
                if content_hash and decay_eidetic_fact(
                    project_id,
                    content_hash,
                    decay_amount=decay_amount,
                    min_confidence=min_confidence,
                    reason=f"contradicted: {finding_text[:100]}",
                ):
                    decayed += 1

        if decayed:
            logger.info(f"Decayed {decayed} eidetic facts by finding in domain '{domain}'")
        return decayed
    except Exception as e:
        logger.warning(f"Failed to decay eidetic by finding: {e}")
        return 0


def propagate_lesson_confidence_to_qdrant(
    project_id: str,
    lesson_name: str,
    new_confidence: float,
) -> bool:
    """Cross-layer sync: update lesson confidence in Qdrant memory collection.

    Called after decay_related_lessons() updates YAML cold storage,
    keeping Qdrant payloads consistent with the source of truth.
    """
    if not _check_qdrant_available():
        return False

    try:
        client = _get_qdrant_client()
        coll = _memory_collection(project_id)

        if not client.collection_exists(coll):
            return False

        from qdrant_client.models import Filter, FieldCondition, MatchValue, PointStruct

        # Find lesson by type + text content match
        results = client.scroll(
            collection_name=coll,
            scroll_filter=Filter(
                must=[FieldCondition(key="type", match=MatchValue(value="lesson"))]
            ),
            limit=50,  # Scan lessons
            with_payload=True,
            with_vectors=True,
        )

        points, _ = results
        for point in points:
            text = point.payload.get("text", "")
            # Match by lesson name appearing in embedded text
            if lesson_name.lower() in text.lower():
                payload = point.payload
                payload["confidence"] = new_confidence
                import time as _time
                payload["confidence_synced_at"] = _time.time()

                updated = PointStruct(id=point.id, vector=point.vector, payload=payload)
                client.upsert(collection_name=coll, points=[updated])
                logger.debug(f"Synced lesson '{lesson_name}' confidence to {new_confidence:.2f} in Qdrant")
                return True

        return False  # Lesson not found in Qdrant
    except Exception as e:
        logger.warning(f"Failed to propagate lesson confidence: {e}")
        return False


def auto_sync_session_to_global(
    project_id: str,
    session_id: str,
    min_impact: float = 0.7,
) -> int:
    """Auto-sync high-impact findings from a single session to global.

    Called at POSTFLIGHT for incremental global sync.
    O(session_findings) not O(project_findings).
    """
    if not _check_qdrant_available():
        return 0

    try:
        # Get session findings from SQLite
        from empirica.data.session_database import SessionDatabase
        from empirica.utils.session_resolver import get_active_project_path
        from pathlib import Path

        project_path = get_active_project_path()
        if not project_path:
            return 0

        db_path = Path(project_path) / '.empirica' / 'sessions' / 'sessions.db'
        if not db_path.exists():
            return 0

        db = SessionDatabase(str(db_path))
        findings = db.get_project_findings(project_id, limit=50)
        db.close()

        if not findings:
            return 0

        synced = 0
        for f in findings:
            impact = f.get('impact', 0.0)
            f_session = f.get('session_id', '')
            if impact >= min_impact and f_session == session_id:
                if embed_to_global(
                    item_id=f.get('id', f.get('finding_id', '')),
                    text=f.get('finding', f.get('text', '')),
                    item_type='finding',
                    project_id=project_id,
                    session_id=session_id,
                    impact=impact,
                    timestamp=f.get('created_timestamp', ''),
                    tags=[f.get('subject', '')],
                ):
                    synced += 1

        if synced:
            logger.info(f"Auto-synced {synced} high-impact findings to global from session {session_id[:8]}")
        return synced
    except Exception as e:
        logger.warning(f"Failed to auto-sync session to global: {e}")
        return 0


def apply_staleness_signal(
    project_id: str,
    max_age_days: int = 180,
    period_days: int = 30,
) -> int:
    """Apply staleness-based signal to memory items based on age.

    Items are NOT deleted — staleness_factor is informational for retrieval
    ranking. Formula: staleness = min(1.0, age_days / max_age_days).

    Also updates assumption urgency via update_assumption_urgency().

    Returns number of items updated.
    """
    if not _check_qdrant_available():
        return 0

    try:
        import time as _time
        client = _get_qdrant_client()
        coll = _memory_collection(project_id)

        if not client.collection_exists(coll):
            return 0

        from qdrant_client.models import PointStruct

        # Scroll all memory items
        all_points = []
        offset = None
        while True:
            results = client.scroll(
                collection_name=coll,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=True,
            )
            points, next_offset = results
            all_points.extend(points)
            if next_offset is None or not points:
                break
            offset = next_offset

        now = _time.time()
        updated = 0
        batch = []

        for point in all_points:
            ts = point.payload.get("timestamp")
            if not ts:
                continue

            # Parse timestamp
            if isinstance(ts, str):
                try:
                    from datetime import datetime
                    ts_float = datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp()
                except Exception:
                    continue
            else:
                ts_float = float(ts)

            age_days = (now - ts_float) / 86400
            if age_days < period_days:
                continue  # Too recent, skip

            new_staleness = min(1.0, age_days / max_age_days)
            old_staleness = point.payload.get("staleness_factor", 0.0)

            # Only update if staleness changed significantly (>0.05)
            if abs(new_staleness - old_staleness) > 0.05:
                payload = point.payload
                payload["staleness_factor"] = round(new_staleness, 3)
                payload["staleness_updated_at"] = now
                batch.append(PointStruct(id=point.id, vector=point.vector, payload=payload))
                updated += 1

        # Batch upsert
        if batch:
            # Upsert in chunks of 50
            for i in range(0, len(batch), 50):
                client.upsert(collection_name=coll, points=batch[i:i+50])

        # Also update assumption urgency
        assumption_updated = update_assumption_urgency(project_id)
        updated += assumption_updated

        if updated:
            logger.info(f"Applied staleness to {updated} items ({assumption_updated} assumptions)")
        return updated
    except Exception as e:
        logger.warning(f"Failed to apply staleness signal: {e}")
        return 0


def update_assumption_urgency(
    project_id: str,
    max_age_days: int = 30,
) -> int:
    """Update urgency_signal on unverified assumptions based on age.

    Urgency = age_days / max_age_days × (1 - confidence).
    Verified/falsified assumptions get urgency = 0.

    Returns number of assumptions updated.
    """
    if not _check_qdrant_available():
        return 0

    try:
        import time as _time
        client = _get_qdrant_client()
        coll = _assumptions_collection(project_id)

        if not client.collection_exists(coll):
            return 0

        from qdrant_client.models import PointStruct

        results = client.scroll(
            collection_name=coll,
            limit=200,
            with_payload=True,
            with_vectors=True,
        )

        points, _ = results
        now = _time.time()
        updated = 0
        batch = []

        for point in points:
            status = point.payload.get("status", "unverified")
            ts = point.payload.get("timestamp", now)
            confidence = point.payload.get("confidence", 0.5)

            if status != "unverified":
                # Resolved: urgency should be 0
                if point.payload.get("urgency_signal", 0) != 0:
                    payload = point.payload
                    payload["urgency_signal"] = 0.0
                    batch.append(PointStruct(id=point.id, vector=point.vector, payload=payload))
                    updated += 1
                continue

            age_days = (now - float(ts)) / 86400
            new_urgency = min(1.0, (age_days / max_age_days) * (1.0 - confidence))
            old_urgency = point.payload.get("urgency_signal", 0.0)

            if abs(new_urgency - old_urgency) > 0.05:
                payload = point.payload
                payload["urgency_signal"] = round(new_urgency, 3)
                batch.append(PointStruct(id=point.id, vector=point.vector, payload=payload))
                updated += 1

        if batch:
            for i in range(0, len(batch), 50):
                client.upsert(collection_name=coll, points=batch[i:i+50])

        return updated
    except Exception as e:
        logger.warning(f"Failed to update assumption urgency: {e}")
        return 0
