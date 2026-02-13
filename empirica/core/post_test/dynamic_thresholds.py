"""
Dynamic Thresholds — Earned Autonomy from Calibration History

Computes phase-aware CHECK gate thresholds based on demonstrated
calibration accuracy. Well-calibrated AI gets looser gates (more autonomy).
Regression in calibration automatically tightens gates.

Self-correcting properties:
- Overconfidence → high divergence → tighter gates → forced investigation
- Underconfidence → low divergence → gates stay conservative (no harm)
- Domain regression → domain-specific tightening
- Phase-specific → noetic and praxic competence are independent axes
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Safety floors — no amount of calibration accuracy removes all gates
SAFETY_FLOORS = {
    "ready_know_threshold": 0.55,
    "ready_uncertainty_threshold": 0.50,
}

# Base thresholds (static defaults from workflow-protocol / cascade_styles)
BASE_THRESHOLDS = {
    "ready_know_threshold": 0.70,
    "ready_uncertainty_threshold": 0.35,
}


def compute_dynamic_thresholds(
    ai_id: str,
    db,
    base_thresholds: Optional[Dict] = None,
    min_transactions: int = 5,
    lookback: int = 20,
    autonomy_factor: float = 0.15,
) -> Dict:
    """Compute phase-aware dynamic thresholds from calibration trajectory.

    Args:
        ai_id: AI identifier (e.g., "claude-code")
        db: Database connection
        base_thresholds: Override base thresholds (default: 0.70 know, 0.35 uncertainty)
        min_transactions: Minimum transactions before enabling dynamic thresholds
        lookback: Number of recent trajectory points to analyze
        autonomy_factor: Maximum threshold reduction (0.15 = 15% looser at perfect calibration)

    Returns:
        {
            "noetic": {
                "ready_know_threshold": float,
                "ready_uncertainty_threshold": float,
                "calibration_accuracy": float,
                "transactions_analyzed": int,
            },
            "praxic": { ... same ... },
            "source": "dynamic" | "static",
            "reason": str,
        }
    """
    base = base_thresholds or BASE_THRESHOLDS.copy()
    static_result = {
        "noetic": {
            "ready_know_threshold": base.get("ready_know_threshold", 0.70),
            "ready_uncertainty_threshold": base.get("ready_uncertainty_threshold", 0.35),
            "calibration_accuracy": None,
            "transactions_analyzed": 0,
        },
        "praxic": {
            "ready_know_threshold": base.get("ready_know_threshold", 0.70),
            "ready_uncertainty_threshold": base.get("ready_uncertainty_threshold", 0.35),
            "calibration_accuracy": None,
            "transactions_analyzed": 0,
        },
        "source": "static",
        "reason": "insufficient data",
    }

    try:
        cursor = db.conn.cursor()

        result = {"source": "dynamic", "reason": "calibration history"}

        for phase in ["noetic", "praxic"]:
            # Get recent trajectory points for this phase
            cursor.execute("""
                SELECT ABS(gap) as abs_gap
                FROM calibration_trajectory
                WHERE ai_id = ? AND phase = ? AND gap IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT ?
            """, (ai_id, phase, lookback))

            rows = cursor.fetchall()

            if len(rows) < min_transactions:
                # Not enough data for this phase — use static
                result[phase] = static_result[phase].copy()
                result[phase]["transactions_analyzed"] = len(rows)
                continue

            # Compute mean absolute divergence
            mean_divergence = sum(r[0] for r in rows) / len(rows)
            calibration_accuracy = max(0.0, min(1.0, 1.0 - mean_divergence))

            # Compute adjusted thresholds
            # Better calibration → lower know threshold (easier to proceed)
            # Better calibration → higher uncertainty tolerance (more exploration allowed)
            know_base = base.get("ready_know_threshold", 0.70)
            uncertainty_base = base.get("ready_uncertainty_threshold", 0.35)

            know_adjusted = know_base - (calibration_accuracy * autonomy_factor)
            uncertainty_adjusted = uncertainty_base + (calibration_accuracy * autonomy_factor)

            # Clamp to safety floors
            know_adjusted = max(SAFETY_FLOORS["ready_know_threshold"], know_adjusted)
            uncertainty_adjusted = min(SAFETY_FLOORS["ready_uncertainty_threshold"], uncertainty_adjusted)

            result[phase] = {
                "ready_know_threshold": round(know_adjusted, 3),
                "ready_uncertainty_threshold": round(uncertainty_adjusted, 3),
                "calibration_accuracy": round(calibration_accuracy, 3),
                "transactions_analyzed": len(rows),
            }

        # If both phases are still static, mark overall as static
        noetic_static = result.get("noetic", {}).get("calibration_accuracy") is None
        praxic_static = result.get("praxic", {}).get("calibration_accuracy") is None
        if noetic_static and praxic_static:
            return static_result

        return result

    except Exception as e:
        logger.debug(f"Dynamic threshold computation failed (non-fatal): {e}")
        return static_result
