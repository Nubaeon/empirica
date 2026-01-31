"""
Evidence-to-Vector Mapper

Maps objective evidence items to estimated vector values.
Only produces estimates for vectors with sufficient evidence.
Uses weighted aggregation when multiple evidence items support the same vector.

Ungroundable vectors (no objective signal): engagement, coherence, density.
These keep self-referential calibration.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .collector import EvidenceBundle, EvidenceItem, EvidenceQuality

logger = logging.getLogger(__name__)


QUALITY_WEIGHTS = {
    EvidenceQuality.OBJECTIVE: 1.0,
    EvidenceQuality.SEMI_OBJECTIVE: 0.7,
    EvidenceQuality.INFERRED: 0.4,
}

UNGROUNDABLE_VECTORS = {"engagement", "coherence", "density"}


@dataclass
class GroundedVectorEstimate:
    """An objectively grounded estimate for a single vector."""
    vector_name: str
    estimated_value: float
    confidence: float
    evidence_count: int
    primary_source: str
    is_grounded: bool = True


@dataclass
class GroundedAssessment:
    """Complete grounded assessment alongside self-assessment."""
    session_id: str
    self_assessed: Dict[str, float]
    grounded: Dict[str, GroundedVectorEstimate]
    calibration_gaps: Dict[str, float]
    grounded_coverage: float
    overall_calibration_score: float


class EvidenceMapper:
    """Maps evidence bundles to grounded vector estimates."""

    def map_evidence(
        self,
        bundle: EvidenceBundle,
        self_assessed_vectors: Dict[str, float],
    ) -> GroundedAssessment:
        """Map evidence to grounded vector estimates and compare to self-assessment."""
        # Group evidence by supported vector
        vector_evidence: Dict[str, List[Tuple[EvidenceItem, float]]] = {}
        for item in bundle.items:
            weight = QUALITY_WEIGHTS.get(item.quality, 0.5)
            for vector in item.supports_vectors:
                if vector not in vector_evidence:
                    vector_evidence[vector] = []
                vector_evidence[vector].append((item, weight))

        # Compute grounded estimates via weighted average
        grounded = {}
        for vector_name, evidence_list in vector_evidence.items():
            if vector_name in UNGROUNDABLE_VECTORS:
                continue

            total_weight = sum(w for _, w in evidence_list)
            if total_weight == 0:
                continue

            weighted_value = sum(
                item.value * w for item, w in evidence_list
            ) / total_weight
            primary_source = max(evidence_list, key=lambda x: x[1])[0].source

            grounded[vector_name] = GroundedVectorEstimate(
                vector_name=vector_name,
                estimated_value=max(0.0, min(1.0, weighted_value)),
                confidence=min(1.0, total_weight / len(evidence_list)),
                evidence_count=len(evidence_list),
                primary_source=primary_source,
            )

        # Compute calibration gaps (self - grounded)
        # Positive = AI overestimates, Negative = AI underestimates
        calibration_gaps = {}
        for vector_name, estimate in grounded.items():
            self_val = self_assessed_vectors.get(vector_name, 0.5)
            calibration_gaps[vector_name] = round(
                self_val - estimate.estimated_value, 4
            )

        # Overall calibration score (mean absolute gap)
        if calibration_gaps:
            overall_score = sum(
                abs(g) for g in calibration_gaps.values()
            ) / len(calibration_gaps)
        else:
            overall_score = 0.0

        return GroundedAssessment(
            session_id=bundle.session_id,
            self_assessed=self_assessed_vectors,
            grounded=grounded,
            calibration_gaps=calibration_gaps,
            grounded_coverage=bundle.coverage,
            overall_calibration_score=round(overall_score, 4),
        )
