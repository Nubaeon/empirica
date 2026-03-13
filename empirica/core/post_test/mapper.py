"""
Evidence-to-Vector Mapper

Maps objective evidence items to estimated vector values.
Only produces estimates for vectors with sufficient evidence.
Uses weighted aggregation when multiple evidence items support the same vector.

Calibration scoring uses domain-aware category weights (Tier 1) from
confidence_weights.yaml. Per-vector weights (Tier 2) can be passed in
from project.yaml for per-project, per-phase dynamic weighting.

Ungroundable vectors (no objective signal): engagement.
Coherence and density are now grounded via code quality metrics (ruff, radon).
These keep self-referential calibration.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from .collector import EvidenceBundle, EvidenceItem, EvidenceQuality

logger = logging.getLogger(__name__)


QUALITY_WEIGHTS = {
    EvidenceQuality.OBJECTIVE: 1.0,
    EvidenceQuality.SEMI_OBJECTIVE: 0.7,
    EvidenceQuality.INFERRED: 0.4,
}

# Vectors with no objective signal. Code quality metrics (ruff, radon) now
# provide grounding for coherence and density, leaving only engagement.
UNGROUNDABLE_VECTORS = {"engagement"}

# Evidence source relevance by work type.
# Keys = work_type, values = dict of evidence_source → relevance multiplier.
# Missing sources default to 1.0 (neutral). Values < 1.0 down-weight irrelevant evidence.
# Values > 1.0 up-weight primary evidence for that work type.
WORK_TYPE_RELEVANCE: Dict[str, Dict[str, float]] = {
    "code": {},  # default weights — code is the baseline
    "infra": {
        "git_metrics": 0.3, "test_results": 0.3, "code_quality": 0.3,
        "goal_completion": 1.2, "artifact_counts": 1.0,
    },
    "research": {
        "git_metrics": 0.2, "test_results": 0.2, "code_quality": 0.2,
        "artifact_counts": 1.5, "goal_completion": 1.0,
    },
    "release": {
        "git_metrics": 0.5, "code_quality": 0.3,
        "goal_completion": 1.3, "test_results": 1.2,
    },
    "debug": {
        "git_metrics": 0.4, "test_results": 1.4,
        "artifact_counts": 1.3, "code_quality": 0.5,
    },
    "config": {
        "git_metrics": 0.4, "test_results": 0.5, "code_quality": 0.4,
        "goal_completion": 1.2,
    },
    "docs": {
        "test_results": 0.2, "code_quality": 0.3,
        "git_metrics": 0.8, "goal_completion": 1.2,
    },
    "data": {
        "git_metrics": 0.4, "code_quality": 0.3,
        "test_results": 0.8, "goal_completion": 1.2,
    },
    "comms": {
        "git_metrics": 0.1, "test_results": 0.1, "code_quality": 0.1,
        "goal_completion": 1.5, "artifact_counts": 1.0,
    },
    "design": {
        "git_metrics": 0.2, "test_results": 0.2, "code_quality": 0.2,
        "artifact_counts": 1.4, "goal_completion": 1.2,
    },
    "audit": {
        "git_metrics": 0.1, "test_results": 0.3,
        "artifact_counts": 1.5, "goal_completion": 1.2, "code_quality": 0.5,
    },
}


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
    phase: str = "combined"  # "noetic", "praxic", or "combined"


def _load_domain_weights(domain: str = "default") -> Dict[str, Any]:
    """Load domain category weights and vector-category map from confidence_weights.yaml.

    Args:
        domain: Domain name (software, consulting, research, operations, default)

    Returns:
        Dict with 'category_weights' and 'vector_category_map'
    """
    config_path = Path(__file__).parent.parent.parent / "config" / "mco" / "confidence_weights.yaml"
    defaults = {
        "category_weights": {"foundation": 0.35, "comprehension": 0.25, "execution": 0.25, "engagement": 0.15},
        "vector_category_map": {
            "know": "foundation", "do": "foundation", "context": "foundation",
            "clarity": "comprehension", "coherence": "comprehension",
            "signal": "comprehension", "density": "comprehension",
            "state": "execution", "change": "execution",
            "completion": "execution", "impact": "execution",
            "engagement": "engagement",
            "uncertainty": "engagement",
        },
    }
    if not config_path.exists():
        return defaults

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

        domain_weights = config.get("domain_category_weights", {})
        category_weights = domain_weights.get(domain, domain_weights.get("default", defaults["category_weights"]))
        vector_map = config.get("vector_category_map", defaults["vector_category_map"])
        return {"category_weights": category_weights, "vector_category_map": vector_map}
    except Exception as e:
        logger.warning(f"Failed to load domain weights: {e}")
        return defaults


def _compute_weighted_calibration(
    calibration_gaps: Dict[str, float],
    domain: str = "default",
    per_vector_weights: Optional[Dict[str, float]] = None,
) -> float:
    """Compute category-weighted calibration score.

    Tier 1: Domain category weights determine how much each category contributes.
    Tier 2: Per-vector weights (optional) scale individual vector gaps within categories.

    Args:
        calibration_gaps: Dict of vector_name → gap (self - grounded)
        domain: Domain for Tier 1 category weights
        per_vector_weights: Optional Tier 2 per-vector weights (from project.yaml)

    Returns:
        Weighted calibration score (lower = better calibrated)
    """
    if not calibration_gaps:
        return 0.0

    config = _load_domain_weights(domain)
    category_weights = config["category_weights"]
    vector_map = config["vector_category_map"]

    # Group gaps by category
    category_gaps: Dict[str, List[Tuple[str, float]]] = {}
    for vector_name, gap in calibration_gaps.items():
        category = vector_map.get(vector_name, "foundation")
        if category not in category_gaps:
            category_gaps[category] = []

        # Apply per-vector weight (Tier 2) if provided
        vector_weight = 1.0
        if per_vector_weights:
            vector_weight = per_vector_weights.get(vector_name, 1.0)

        category_gaps[category].append((vector_name, abs(gap) * vector_weight))

    # Weighted mean: category weight * mean abs gap within category
    total_score = 0.0
    total_weight = 0.0
    for category, gaps in category_gaps.items():
        cat_weight = category_weights.get(category, 0.25)
        cat_mean = sum(g for _, g in gaps) / len(gaps)
        total_score += cat_weight * cat_mean
        total_weight += cat_weight

    # Normalize by actual weight used (not all categories may have grounded vectors)
    if total_weight > 0:
        return total_score / total_weight
    return 0.0


class EvidenceMapper:
    """Maps evidence bundles to grounded vector estimates."""

    def map_evidence(
        self,
        bundle: EvidenceBundle,
        self_assessed_vectors: Dict[str, float],
        phase: str = "combined",
        domain: str = "default",
        per_vector_weights: Optional[Dict[str, float]] = None,
        work_type: Optional[str] = None,
    ) -> GroundedAssessment:
        """Map evidence to grounded vector estimates and compare to self-assessment."""
        # Work-type relevance profile (scales evidence weights by source relevance)
        relevance = WORK_TYPE_RELEVANCE.get(work_type, {}) if work_type else {}

        # Group evidence by supported vector
        vector_evidence: Dict[str, List[Tuple[EvidenceItem, float]]] = {}
        for item in bundle.items:
            quality_weight = QUALITY_WEIGHTS.get(item.quality, 0.5)
            # Apply work-type relevance scaling to evidence source
            source_relevance = relevance.get(item.source, 1.0)
            weight = quality_weight * source_relevance
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

        # Overall calibration score — domain-weighted (Tier 1 + optional Tier 2)
        overall_score = _compute_weighted_calibration(
            calibration_gaps, domain=domain, per_vector_weights=per_vector_weights,
        )

        return GroundedAssessment(
            session_id=bundle.session_id,
            self_assessed=self_assessed_vectors,
            grounded=grounded,
            calibration_gaps=calibration_gaps,
            grounded_coverage=bundle.coverage,
            overall_calibration_score=round(overall_score, 4),
            phase=phase,
        )
