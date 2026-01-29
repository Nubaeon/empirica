"""
Epistemic Attention Budget - Allocate investigation resources by information gain.

The attention budget system manages how many resources (measured in findings count)
are allocated to parallel epistemic agents. It uses Shannon information gain to
prioritize high-uncertainty domains and applies diminishing returns to domains
that have already been explored.

Usage:
    from empirica.core.attention_budget import AttentionBudgetCalculator, AttentionBudget

    calculator = AttentionBudgetCalculator(session_id="abc123")
    budget = calculator.create_budget(
        total_budget=20,
        domains=["security", "architecture", "performance"],
        current_vectors={"know": 0.5, "uncertainty": 0.6},
        prior_findings_by_domain={"security": 3, "architecture": 0}
    )
    # budget.allocations: security=5, architecture=10, performance=5
"""

import json
import logging
import math
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class DomainAllocation:
    """Budget allocation for a single investigation domain."""
    domain: str
    budget: int  # Max findings to accept from this domain
    priority: float  # 0.0-1.0, higher = more important
    expected_gain: float  # Estimated information gain (Shannon entropy reduction)
    prior_findings: int = 0  # Findings already logged for this domain
    dead_ends: int = 0  # Dead ends encountered in this domain

    @property
    def effective_budget(self) -> int:
        """Budget remaining after accounting for prior findings."""
        return max(0, self.budget - self.prior_findings)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AttentionBudget:
    """Tracks the attention budget for a parallel investigation session."""
    id: str
    session_id: str
    total_budget: int  # Total findings to accept across all domains
    allocated: int = 0  # Findings allocated so far
    remaining: int = 0  # Budget remaining
    strategy: str = "information_gain"
    allocations: List[DomainAllocation] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if self.remaining == 0 and self.total_budget > 0:
            self.remaining = self.total_budget - self.allocated

    def consume(self, count: int = 1) -> bool:
        """Consume budget. Returns False if budget exhausted."""
        if self.remaining < count:
            return False
        self.allocated += count
        self.remaining -= count
        self.updated_at = time.time()
        return True

    @property
    def exhausted(self) -> bool:
        return self.remaining <= 0

    @property
    def utilization(self) -> float:
        """Budget utilization ratio (0.0-1.0)."""
        if self.total_budget == 0:
            return 0.0
        return self.allocated / self.total_budget

    def get_domain_allocation(self, domain: str) -> Optional[DomainAllocation]:
        """Get allocation for a specific domain."""
        for alloc in self.allocations:
            if alloc.domain == domain:
                return alloc
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "total_budget": self.total_budget,
            "allocated": self.allocated,
            "remaining": self.remaining,
            "strategy": self.strategy,
            "allocations": [a.to_dict() for a in self.allocations],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class AttentionBudgetCalculator:
    """
    Calculate attention budget allocations using information gain heuristics.

    Strategy: Domains with higher uncertainty get more budget.
    Prior findings reduce allocation (diminishing returns).
    Dead ends heavily reduce allocation (avoid re-exploration).
    """

    def __init__(
        self,
        session_id: str,
        default_total: int = 20,
        dead_end_penalty: float = 0.5,
        diminishing_rate: float = 0.3,
    ):
        self.session_id = session_id
        self.default_total = default_total
        self.dead_end_penalty = dead_end_penalty
        self.diminishing_rate = diminishing_rate

    def create_budget(
        self,
        domains: List[str],
        current_vectors: Optional[Dict[str, float]] = None,
        prior_findings_by_domain: Optional[Dict[str, int]] = None,
        dead_ends_by_domain: Optional[Dict[str, int]] = None,
        total_budget: Optional[int] = None,
    ) -> AttentionBudget:
        """
        Create an attention budget with domain allocations.

        Args:
            domains: Investigation domains (e.g., ["security", "architecture"])
            current_vectors: Current epistemic state vectors
            prior_findings_by_domain: Count of existing findings per domain
            dead_ends_by_domain: Count of dead ends per domain
            total_budget: Override total budget (default: self.default_total)

        Returns:
            AttentionBudget with per-domain allocations
        """
        total = total_budget or self.default_total
        prior_findings = prior_findings_by_domain or {}
        dead_ends = dead_ends_by_domain or {}
        vectors = current_vectors or {}

        # Calculate raw information gain per domain
        raw_gains = {}
        for domain in domains:
            gain = self._estimate_domain_gain(
                domain=domain,
                vectors=vectors,
                prior_findings=prior_findings.get(domain, 0),
                dead_ends=dead_ends.get(domain, 0),
            )
            raw_gains[domain] = gain

        # Normalize gains to allocations
        total_gain = sum(raw_gains.values())
        allocations = []

        for domain in domains:
            if total_gain > 0:
                share = raw_gains[domain] / total_gain
            else:
                share = 1.0 / len(domains)

            domain_budget = max(1, round(share * total))  # At least 1 per domain
            priority = raw_gains[domain] / max(max(raw_gains.values()), 0.01)

            allocations.append(DomainAllocation(
                domain=domain,
                budget=domain_budget,
                priority=priority,
                expected_gain=raw_gains[domain],
                prior_findings=prior_findings.get(domain, 0),
                dead_ends=dead_ends.get(domain, 0),
            ))

        # Adjust to fit total budget exactly
        allocated_sum = sum(a.budget for a in allocations)
        if allocated_sum > total and allocations:
            # Reduce lowest-priority domains
            allocations.sort(key=lambda a: a.priority)
            diff = allocated_sum - total
            for alloc in allocations:
                if diff <= 0:
                    break
                reduce = min(alloc.budget - 1, diff)  # Keep at least 1
                alloc.budget -= reduce
                diff -= reduce
        elif allocated_sum < total and allocations:
            # Give surplus to highest-priority domain
            allocations.sort(key=lambda a: a.priority, reverse=True)
            allocations[0].budget += total - allocated_sum

        budget = AttentionBudget(
            id=str(uuid.uuid4()),
            session_id=self.session_id,
            total_budget=total,
            allocated=0,
            remaining=total,
            strategy="information_gain",
            allocations=allocations,
        )

        logger.info(
            f"Created attention budget: total={total}, "
            f"domains={[(a.domain, a.budget) for a in allocations]}"
        )

        return budget

    def _estimate_domain_gain(
        self,
        domain: str,
        vectors: Dict[str, float],
        prior_findings: int,
        dead_ends: int,
    ) -> float:
        """
        Estimate information gain for investigating a domain.

        Uses Shannon entropy: high uncertainty = high potential gain.
        Diminishing returns from prior findings.
        Dead ends heavily penalize the domain.
        """
        # Base gain from uncertainty (Shannon-inspired)
        uncertainty = vectors.get("uncertainty", 0.5)
        know = vectors.get("know", 0.5)

        # Higher uncertainty = more to learn = higher gain
        # Lower know = more to learn = higher gain
        base_gain = self._shannon_gain(uncertainty, know)

        # Diminishing returns from prior findings
        diminishing = self._diminishing_returns(prior_findings)

        # Dead end penalty
        dead_end_factor = max(0.1, 1.0 - (dead_ends * self.dead_end_penalty))

        gain = base_gain * diminishing * dead_end_factor

        logger.debug(
            f"Domain '{domain}': base={base_gain:.3f}, "
            f"diminish={diminishing:.3f}, dead_end={dead_end_factor:.3f}, "
            f"final={gain:.3f}"
        )

        return gain

    def _shannon_gain(self, uncertainty: float, know: float) -> float:
        """
        Shannon-inspired information gain estimate.

        H(X) = -p*log2(p) - (1-p)*log2(1-p)
        We use uncertainty as the entropy proxy.
        """
        # Clamp to avoid log(0)
        p = max(0.01, min(0.99, uncertainty))
        entropy = -p * math.log2(p) - (1 - p) * math.log2(1 - p)

        # Scale by knowledge gap (less knowledge = more potential gain)
        knowledge_gap = max(0.01, 1.0 - know)

        return entropy * knowledge_gap

    def _diminishing_returns(self, prior_findings: int) -> float:
        """
        Exponential decay for diminishing returns.

        First findings are highly valuable, later ones less so.
        f(n) = e^(-rate * n)
        """
        return math.exp(-self.diminishing_rate * prior_findings)


def persist_budget(budget: AttentionBudget) -> bool:
    """Persist an attention budget to the database."""
    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()
        cursor = db.conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO attention_budgets
            (id, session_id, total_budget, allocated, remaining, strategy, domain_allocations, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            budget.id,
            budget.session_id,
            budget.total_budget,
            budget.allocated,
            budget.remaining,
            budget.strategy,
            json.dumps([a.to_dict() for a in budget.allocations]),
            budget.created_at,
            budget.updated_at,
        ))

        db.conn.commit()
        db.close()
        return True
    except Exception as e:
        logger.error(f"Failed to persist budget: {e}")
        return False


def load_budget(budget_id: str) -> Optional[AttentionBudget]:
    """Load an attention budget from the database."""
    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()
        cursor = db.conn.cursor()

        cursor.execute(
            "SELECT * FROM attention_budgets WHERE id = ?", (budget_id,)
        )
        row = cursor.fetchone()
        db.close()

        if not row:
            return None

        # Parse domain allocations from JSON
        alloc_json = row[6]  # domain_allocations column
        alloc_list = json.loads(alloc_json) if alloc_json else []
        allocations = [DomainAllocation(**a) for a in alloc_list]

        return AttentionBudget(
            id=row[0],
            session_id=row[1],
            total_budget=row[2],
            allocated=row[3],
            remaining=row[4],
            strategy=row[5],
            allocations=allocations,
            created_at=row[7],
            updated_at=row[8],
        )
    except Exception as e:
        logger.error(f"Failed to load budget: {e}")
        return None
