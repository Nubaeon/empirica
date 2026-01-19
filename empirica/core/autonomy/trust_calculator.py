"""
Domain-Specific Trust Calculator

Calculates earned trust/authority levels for AI agents based on:
1. Calibration accuracy (from Bayesian beliefs)
2. Suggestion outcomes (accepted boost, rejected penalty)
3. Recent mistakes (per-domain penalties)

Trust levels gate what actions an AI can take autonomously:
- Low trust: Human approval required for all changes
- Medium trust: Human approval for significant changes only
- High trust: AI can make tactical decisions autonomously
- Very high trust: AI can make strategic decisions with async review

Usage:
    from empirica.core.autonomy.trust_calculator import TrustCalculator

    calculator = TrustCalculator(session_id)
    trust = calculator.get_domain_trust("architecture")
    # Returns: {"level": "medium", "score": 0.65, "factors": {...}}
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TrustLevel(Enum):
    """Trust levels for graduated autonomy"""
    NONE = "none"           # No trust established
    LOW = "low"             # 0.0 - 0.4: Human approval for all changes
    MEDIUM = "medium"       # 0.4 - 0.6: Human approval for significant changes
    HIGH = "high"           # 0.6 - 0.8: Autonomous tactical decisions
    VERY_HIGH = "very_high" # 0.8 - 1.0: Autonomous strategic decisions


@dataclass
class DomainTrust:
    """Trust assessment for a specific domain"""
    domain: str
    score: float  # 0.0 - 1.0
    level: TrustLevel
    factors: Dict[str, float]
    suggestions_accepted: int
    suggestions_rejected: int
    recent_mistakes: int
    calibration_accuracy: float


class TrustCalculator:
    """
    Calculate domain-specific trust based on historical performance.

    Trust formula:
        trust = (
            base_calibration_accuracy * 0.4 +
            suggestion_success_rate * 0.4 +
            mistake_penalty * 0.2
        )

    Where:
        - base_calibration_accuracy: From Bayesian beliefs (vector-specific)
        - suggestion_success_rate: accepted / (accepted + rejected)
        - mistake_penalty: 1.0 - (recent_mistakes * 0.1), floor 0.0
    """

    # Trust level thresholds
    THRESHOLDS = {
        TrustLevel.NONE: 0.0,
        TrustLevel.LOW: 0.0,
        TrustLevel.MEDIUM: 0.4,
        TrustLevel.HIGH: 0.6,
        TrustLevel.VERY_HIGH: 0.8,
    }

    # Weights for trust calculation
    WEIGHTS = {
        "calibration": 0.4,
        "suggestions": 0.4,
        "mistakes": 0.2,
    }

    # Minimum observations for trust calculation
    MIN_OBSERVATIONS = 3

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize trust calculator.

        Args:
            project_id: Optional project ID for scoping trust calculation
        """
        self.project_id = project_id
        self._db = None

    def _get_db(self):
        """Lazy load database connection"""
        if self._db is None:
            from empirica.data.session_database import SessionDatabase
            self._db = SessionDatabase()
        return self._db

    def get_domain_trust(self, domain: str) -> DomainTrust:
        """
        Calculate trust score for a specific domain.

        Args:
            domain: Domain to calculate trust for (e.g., "architecture", "testing")

        Returns:
            DomainTrust with score, level, and breakdown
        """
        db = self._get_db()
        cursor = db.conn.cursor()

        # Get suggestion stats for domain
        cursor.execute("""
            SELECT
                COUNT(*) FILTER (WHERE review_outcome = 'accepted') as accepted,
                COUNT(*) FILTER (WHERE review_outcome = 'rejected') as rejected,
                COUNT(*) as total
            FROM suggestions
            WHERE domain = ?
            AND (project_id = ? OR ? IS NULL)
        """, (domain, self.project_id, self.project_id))

        row = cursor.fetchone()
        if row:
            accepted = row['accepted'] or 0
            rejected = row['rejected'] or 0
            total = row['total'] or 0
        else:
            accepted, rejected, total = 0, 0, 0

        # Get recent mistakes for domain
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM mistakes_made
            WHERE root_cause_vector LIKE ?
            AND created_timestamp > ?
            AND (project_id = ? OR ? IS NULL)
        """, (f"%{domain}%", self._get_recent_cutoff(), self.project_id, self.project_id))

        mistakes_row = cursor.fetchone()
        recent_mistakes = mistakes_row['count'] if mistakes_row else 0

        # Get calibration accuracy (use overall if no domain-specific)
        calibration_accuracy = self._get_calibration_accuracy(domain)

        # Calculate trust score
        factors = {}

        # Calibration factor (0.0 - 1.0, higher is better)
        factors["calibration"] = calibration_accuracy

        # Suggestion success rate (0.0 - 1.0)
        if accepted + rejected >= self.MIN_OBSERVATIONS:
            factors["suggestions"] = accepted / (accepted + rejected)
        else:
            # Not enough data - use neutral value
            factors["suggestions"] = 0.5

        # Mistake penalty (0.0 - 1.0, higher is better = fewer mistakes)
        factors["mistakes"] = max(0.0, 1.0 - (recent_mistakes * 0.1))

        # Calculate weighted score
        score = (
            factors["calibration"] * self.WEIGHTS["calibration"] +
            factors["suggestions"] * self.WEIGHTS["suggestions"] +
            factors["mistakes"] * self.WEIGHTS["mistakes"]
        )

        # Determine trust level
        level = self._score_to_level(score)

        return DomainTrust(
            domain=domain,
            score=score,
            level=level,
            factors=factors,
            suggestions_accepted=accepted,
            suggestions_rejected=rejected,
            recent_mistakes=recent_mistakes,
            calibration_accuracy=calibration_accuracy
        )

    def get_all_domain_trust(self) -> Dict[str, DomainTrust]:
        """
        Get trust scores for all domains with data.

        Returns:
            Dict mapping domain names to DomainTrust objects
        """
        db = self._get_db()
        cursor = db.conn.cursor()

        # Get all unique domains
        cursor.execute("""
            SELECT DISTINCT domain
            FROM suggestions
            WHERE domain IS NOT NULL
            AND (project_id = ? OR ? IS NULL)
        """, (self.project_id, self.project_id))

        domains = [row['domain'] for row in cursor.fetchall()]

        # Calculate trust for each domain
        result = {}
        for domain in domains:
            result[domain] = self.get_domain_trust(domain)

        # Add overall trust
        result["_overall"] = self._calculate_overall_trust(result)

        return result

    def _calculate_overall_trust(self, domain_trusts: Dict[str, DomainTrust]) -> DomainTrust:
        """Calculate overall trust across all domains"""
        if not domain_trusts:
            return DomainTrust(
                domain="_overall",
                score=0.5,  # Neutral baseline
                level=TrustLevel.MEDIUM,
                factors={"calibration": 0.5, "suggestions": 0.5, "mistakes": 1.0},
                suggestions_accepted=0,
                suggestions_rejected=0,
                recent_mistakes=0,
                calibration_accuracy=0.5
            )

        # Average across domains
        total_score = sum(t.score for t in domain_trusts.values())
        avg_score = total_score / len(domain_trusts)

        total_accepted = sum(t.suggestions_accepted for t in domain_trusts.values())
        total_rejected = sum(t.suggestions_rejected for t in domain_trusts.values())
        total_mistakes = sum(t.recent_mistakes for t in domain_trusts.values())

        return DomainTrust(
            domain="_overall",
            score=avg_score,
            level=self._score_to_level(avg_score),
            factors={
                "calibration": sum(t.factors.get("calibration", 0.5) for t in domain_trusts.values()) / len(domain_trusts),
                "suggestions": sum(t.factors.get("suggestions", 0.5) for t in domain_trusts.values()) / len(domain_trusts),
                "mistakes": sum(t.factors.get("mistakes", 1.0) for t in domain_trusts.values()) / len(domain_trusts),
            },
            suggestions_accepted=total_accepted,
            suggestions_rejected=total_rejected,
            recent_mistakes=total_mistakes,
            calibration_accuracy=sum(t.calibration_accuracy for t in domain_trusts.values()) / len(domain_trusts)
        )

    def _get_calibration_accuracy(self, domain: str) -> float:
        """
        Get calibration accuracy for a domain.

        Uses Bayesian beliefs if available, otherwise returns neutral 0.5.
        """
        try:
            # Map domain to relevant vectors
            domain_vectors = {
                "architecture": ["coherence", "context", "clarity"],
                "testing": ["completion", "do", "state"],
                "performance": ["change", "impact", "signal"],
                "security": ["uncertainty", "know", "context"],
                "documentation": ["clarity", "density", "coherence"],
            }

            vectors = domain_vectors.get(domain, ["know", "uncertainty", "context"])

            # Load calibration from breadcrumbs
            import yaml
            from pathlib import Path

            breadcrumbs_path = Path(".breadcrumbs.yaml")
            if not breadcrumbs_path.exists():
                return 0.5

            with open(breadcrumbs_path) as f:
                data = yaml.safe_load(f)

            calibration = data.get("calibration", {})
            corrections = calibration.get("bias_corrections", {})

            # Calculate accuracy from bias corrections
            # Lower absolute bias = better calibration
            total_bias = 0.0
            count = 0
            for vector in vectors:
                if vector in corrections:
                    # Parse correction value (e.g., "+0.10" or "-0.05")
                    correction_str = str(corrections[vector])
                    correction = float(correction_str.replace("+", ""))
                    total_bias += abs(correction)
                    count += 1

            if count == 0:
                return 0.5

            avg_bias = total_bias / count
            # Convert bias to accuracy (lower bias = higher accuracy)
            # Max expected bias is ~0.7, so we scale accordingly
            accuracy = max(0.0, 1.0 - (avg_bias / 0.7))

            return accuracy

        except Exception as e:
            logger.warning(f"Could not calculate calibration accuracy: {e}")
            return 0.5

    def _score_to_level(self, score: float) -> TrustLevel:
        """Convert numeric score to trust level"""
        if score >= 0.8:
            return TrustLevel.VERY_HIGH
        elif score >= 0.6:
            return TrustLevel.HIGH
        elif score >= 0.4:
            return TrustLevel.MEDIUM
        elif score > 0.0:
            return TrustLevel.LOW
        else:
            return TrustLevel.NONE

    def _get_recent_cutoff(self) -> float:
        """Get timestamp cutoff for 'recent' (7 days)"""
        import time
        return time.time() - (7 * 24 * 60 * 60)

    def close(self):
        """Close database connection"""
        if self._db:
            self._db.close()
            self._db = None
