"""
Epistemic Rollup Gate - Score, deduplicate, and gate findings from sub-agents.

When parallel epistemic agents complete work, their findings flow through this
gate before being logged to the parent session. The gate:

1. Scores each finding by confidence x novelty x domain_relevance
2. Deduplicates findings (Jaccard similarity, optional Qdrant semantic)
3. Gates findings against the attention budget (accept/reject)
4. Logs decisions to rollup_logs for auditability

This is the quality control mechanism for multi-agent epistemic rollup.
"""

import hashlib
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from empirica.core.information_gain import novelty_score

logger = logging.getLogger(__name__)


@dataclass
class ScoredFinding:
    """A finding scored for rollup quality."""
    finding: str
    score: float  # Combined score (0.0-1.0)
    agent_name: str
    domain: str
    novelty: float  # Novelty vs existing findings (0.0-1.0)
    confidence: float  # Agent's confidence in this finding
    domain_relevance: float  # How relevant to investigation domain (0.0-1.0)
    finding_hash: str = ""  # SHA256 hash for dedup tracking
    accepted: bool = False
    reject_reason: Optional[str] = None

    def __post_init__(self):
        if not self.finding_hash:
            self.finding_hash = hashlib.sha256(
                self.finding.encode('utf-8')
            ).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding": self.finding,
            "score": self.score,
            "agent_name": self.agent_name,
            "domain": self.domain,
            "novelty": self.novelty,
            "confidence": self.confidence,
            "domain_relevance": self.domain_relevance,
            "finding_hash": self.finding_hash,
            "accepted": self.accepted,
            "reject_reason": self.reject_reason,
        }


@dataclass
class RollupResult:
    """Result of running findings through the rollup gate."""
    accepted: List[ScoredFinding] = field(default_factory=list)
    rejected: List[ScoredFinding] = field(default_factory=list)
    total_score: float = 0.0
    budget_consumed: int = 0
    budget_remaining: int = 0

    @property
    def acceptance_rate(self) -> float:
        total = len(self.accepted) + len(self.rejected)
        return len(self.accepted) / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accepted": [f.to_dict() for f in self.accepted],
            "rejected": [f.to_dict() for f in self.rejected],
            "total_score": self.total_score,
            "budget_consumed": self.budget_consumed,
            "budget_remaining": self.budget_remaining,
            "acceptance_rate": self.acceptance_rate,
        }


class EpistemicRollupGate:
    """
    Gate for filtering and scoring findings from epistemic sub-agents.

    Scoring formula:
        score = confidence * novelty * domain_relevance

    Findings below min_score are rejected.
    Findings above min_score consume budget and are accepted.
    """

    def __init__(
        self,
        min_score: float = 0.3,
        jaccard_threshold: float = 0.7,
        use_semantic_dedup: bool = False,
    ):
        """
        Args:
            min_score: Minimum score to accept a finding
            jaccard_threshold: Jaccard similarity threshold for deduplication
            use_semantic_dedup: Whether to use Qdrant semantic dedup (optional)
        """
        self.min_score = min_score
        self.jaccard_threshold = jaccard_threshold
        self.use_semantic_dedup = use_semantic_dedup

    def score_finding(
        self,
        finding: str,
        agent_name: str,
        domain: str,
        confidence: float,
        existing_findings: List[str],
        domain_relevance: float = 1.0,
    ) -> ScoredFinding:
        """
        Score a single finding.

        Args:
            finding: The finding text
            agent_name: Which agent produced this
            domain: Investigation domain
            confidence: Agent's confidence (0.0-1.0)
            existing_findings: Already-accepted findings for dedup
            domain_relevance: How relevant to investigation (0.0-1.0)

        Returns:
            ScoredFinding with computed score
        """
        # Calculate novelty
        novel = novelty_score(finding, existing_findings, self.jaccard_threshold)

        # Combined score
        score = confidence * novel * domain_relevance

        scored = ScoredFinding(
            finding=finding,
            score=score,
            agent_name=agent_name,
            domain=domain,
            novelty=novel,
            confidence=confidence,
            domain_relevance=domain_relevance,
        )

        logger.debug(
            f"Scored finding: score={score:.3f} "
            f"(conf={confidence:.2f} * novel={novel:.2f} * rel={domain_relevance:.2f}) "
            f"agent={agent_name}"
        )

        return scored

    def deduplicate(
        self,
        findings: List[ScoredFinding],
        project_id: Optional[str] = None,
    ) -> List[ScoredFinding]:
        """
        Deduplicate findings using hash and optionally Qdrant semantic similarity.

        Findings with duplicate hashes are removed (keeps highest-scored).
        If use_semantic_dedup and Qdrant is available, also checks semantic similarity.

        Returns deduplicated list.
        """
        # Hash-based dedup: keep highest score per hash
        by_hash: Dict[str, ScoredFinding] = {}
        for f in findings:
            if f.finding_hash not in by_hash or f.score > by_hash[f.finding_hash].score:
                by_hash[f.finding_hash] = f

        deduped = list(by_hash.values())

        # Jaccard-based dedup across different hashes
        if len(deduped) > 1:
            deduped = self._jaccard_dedup(deduped)

        # Optional semantic dedup via Qdrant
        if self.use_semantic_dedup and project_id:
            deduped = self._semantic_dedup(deduped, project_id)

        removed = len(findings) - len(deduped)
        if removed > 0:
            logger.info(f"Deduplication removed {removed} findings ({len(findings)} -> {len(deduped)})")

        return deduped

    def _jaccard_dedup(self, findings: List[ScoredFinding]) -> List[ScoredFinding]:
        """Remove findings that are Jaccard-similar to higher-scored findings."""
        # Sort by score descending (keep higher-scored ones)
        sorted_findings = sorted(findings, key=lambda f: f.score, reverse=True)
        kept = []

        for candidate in sorted_findings:
            is_dup = False
            for existing in kept:
                similarity = 1.0 - novelty_score(
                    candidate.finding, [existing.finding], self.jaccard_threshold
                )
                if similarity >= self.jaccard_threshold:
                    is_dup = True
                    break

            if not is_dup:
                kept.append(candidate)

        return kept

    def _semantic_dedup(
        self,
        findings: List[ScoredFinding],
        project_id: str,
    ) -> List[ScoredFinding]:
        """Semantic dedup via Qdrant (graceful degradation if unavailable)."""
        try:
            from empirica.core.qdrant.vector_store import search_similar
            kept = []
            for f in findings:
                results = search_similar(
                    project_id=project_id,
                    query=f.finding,
                    collection="eidetic",
                    limit=1,
                    threshold=0.9,  # Very high threshold = near-duplicate
                )
                if not results:
                    kept.append(f)
                else:
                    logger.debug(f"Semantic dedup: dropped '{f.finding[:50]}...'")
            return kept
        except Exception as e:
            logger.debug(f"Semantic dedup unavailable ({e}), using Jaccard only")
            return findings

    def gate(
        self,
        findings: List[ScoredFinding],
        budget_remaining: int,
    ) -> RollupResult:
        """
        Gate findings against budget and quality threshold.

        Accepts highest-scored findings first until budget exhausted.

        Args:
            findings: Scored (and optionally deduplicated) findings
            budget_remaining: How many findings we can still accept

        Returns:
            RollupResult with accepted/rejected findings
        """
        # Sort by score descending
        sorted_findings = sorted(findings, key=lambda f: f.score, reverse=True)

        result = RollupResult(budget_remaining=budget_remaining)

        for finding in sorted_findings:
            if finding.score < self.min_score:
                finding.accepted = False
                finding.reject_reason = f"Below min_score ({finding.score:.3f} < {self.min_score})"
                result.rejected.append(finding)
            elif result.budget_consumed >= budget_remaining:
                finding.accepted = False
                finding.reject_reason = "Budget exhausted"
                result.rejected.append(finding)
            else:
                finding.accepted = True
                result.accepted.append(finding)
                result.total_score += finding.score
                result.budget_consumed += 1

        result.budget_remaining = budget_remaining - result.budget_consumed

        logger.info(
            f"Rollup gate: {len(result.accepted)} accepted, "
            f"{len(result.rejected)} rejected "
            f"(budget: {result.budget_consumed}/{budget_remaining})"
        )

        return result

    def process(
        self,
        raw_findings: List[Any],
        agent_name: str,
        domain: str,
        confidence: float,
        existing_findings: List[str],
        budget_remaining: int,
        domain_relevance: float = 1.0,
        project_id: Optional[str] = None,
    ) -> RollupResult:
        """
        Full pipeline: score -> deduplicate -> gate.

        Convenience method that runs the complete rollup pipeline.

        Args:
            raw_findings: List of {"finding": "..."} dicts
            agent_name: Agent that produced findings
            domain: Investigation domain
            confidence: Agent's confidence
            existing_findings: Already-accepted findings
            budget_remaining: Budget remaining
            domain_relevance: Domain relevance score
            project_id: For semantic dedup (optional)

        Returns:
            RollupResult
        """
        # Score all findings
        scored = []
        for item in raw_findings:
            text = item.get("finding", "") if isinstance(item, dict) else str(item)
            sf = self.score_finding(
                finding=text,
                agent_name=agent_name,
                domain=domain,
                confidence=confidence,
                existing_findings=existing_findings + [f.finding for f in scored],
                domain_relevance=domain_relevance,
            )
            scored.append(sf)

        # Deduplicate
        deduped = self.deduplicate(scored, project_id)

        # Gate
        return self.gate(deduped, budget_remaining)


def log_rollup_decision(
    session_id: str,
    budget_id: Optional[str],
    result: RollupResult,
) -> int:
    """
    Log rollup decisions to the rollup_logs table.

    Returns count of logged entries.
    """
    logged = 0
    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()
        cursor = db.conn.cursor()

        all_findings = result.accepted + result.rejected
        for finding in all_findings:
            cursor.execute("""
                INSERT INTO rollup_logs
                (id, session_id, budget_id, agent_name, finding_hash, finding_text,
                 score, accepted, reason, novelty, domain_relevance, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                session_id,
                budget_id,
                finding.agent_name,
                finding.finding_hash,
                finding.finding[:500],
                finding.score,
                finding.accepted,
                finding.reject_reason,
                finding.novelty,
                finding.domain_relevance,
                time.time(),
            ))
            logged += 1

        db.conn.commit()
        db.close()
    except Exception as e:
        logger.error(f"Failed to log rollup decisions: {e}")

    return logged
