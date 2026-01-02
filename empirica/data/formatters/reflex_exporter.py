"""Reflex log exporter for dashboard visualization"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional


def export_to_reflex_logs(
    session_id: str,
    phase: str,
    assessment_data: Dict[str, Any],
    log_dir: str = ".empirica_reflex_logs"
) -> Optional[Path]:
    """
    Export assessment to reflex log format for dashboard visualization

    Args:
        session_id: Session identifier
        phase: CASCADE phase (preflight/check/postflight)
        assessment_data: Assessment data dict with vectors
        log_dir: Directory for reflex logs

    Returns:
        Path to created log file, or None on error
    """
    try:
        vectors = assessment_data.get("vectors", {})

        # Load configuration weights for confidence calculations
        try:
            import yaml

            # Load the confidence weights configuration
            config_path = Path(__file__).parent.parent.parent / "config" / "mco" / "confidence_weights.yaml"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)

                foundation_weights = config.get("foundation_confidence_weights", {
                    'know': 0.4,
                    'do': 0.3,
                    'context': 0.3
                })
            else:
                # Default weights if config file not found
                foundation_weights = {
                    'know': 0.4,
                    'do': 0.3,
                    'context': 0.3
                }
        except Exception:
            # Fallback to original hardcoded values if config loading fails
            foundation_weights = {
                'know': 0.4,
                'do': 0.3,
                'context': 0.3
            }

        # Calculate confidence scores using configurable weights
        foundation_confidence = (
            vectors.get('know', 0.5) * foundation_weights.get('know', 0.4) +
            vectors.get('do', 0.5) * foundation_weights.get('do', 0.3) +
            vectors.get('context', 0.5) * foundation_weights.get('context', 0.3)
        )

        # Load comprehension weights
        try:
            comprehension_weights = config.get("comprehension_confidence_weights", {
                'clarity': 0.3,
                'coherence': 0.3,
                'signal': 0.2,
                'density': 0.2
            }) if 'config' in locals() else {
                'clarity': 0.3,
                'coherence': 0.3,
                'signal': 0.2,
                'density': 0.2
            }
        except:
            comprehension_weights = {
                'clarity': 0.3,
                'coherence': 0.3,
                'signal': 0.2,
                'density': 0.2
            }

        comprehension_confidence = (
            vectors.get('clarity', 0.5) * comprehension_weights.get('clarity', 0.3) +
            vectors.get('coherence', 0.5) * comprehension_weights.get('coherence', 0.3) +
            vectors.get('signal', 0.5) * comprehension_weights.get('signal', 0.2) +
            (1.0 - vectors.get('density', 0.5)) * comprehension_weights.get('density', 0.2)
        )

        # Load execution weights
        try:
            execution_weights = config.get("execution_confidence_weights", {
                'state': 0.25,
                'change': 0.25,
                'completion': 0.25,
                'impact': 0.25
            }) if 'config' in locals() else {
                'state': 0.25,
                'change': 0.25,
                'completion': 0.25,
                'impact': 0.25
            }
        except:
            execution_weights = {
                'state': 0.25,
                'change': 0.25,
                'completion': 0.25,
                'impact': 0.25
            }

        execution_confidence = (
            vectors.get('state', 0.5) * execution_weights.get('state', 0.25) +
            vectors.get('change', 0.5) * execution_weights.get('change', 0.25) +
            vectors.get('completion', 0.5) * execution_weights.get('completion', 0.25) +
            vectors.get('impact', 0.5) * execution_weights.get('impact', 0.25)
        )

        # Load overall weights
        try:
            overall_weights = config.get("overall_confidence_weights", {
                'foundation': 0.35,
                'comprehension': 0.25,
                'execution': 0.25,
                'engagement': 0.15
            }) if 'config' in locals() else {
                'foundation': 0.35,
                'comprehension': 0.25,
                'execution': 0.25,
                'engagement': 0.15
            }
        except:
            overall_weights = {
                'foundation': 0.35,
                'comprehension': 0.25,
                'execution': 0.25,
                'engagement': 0.15
            }

        overall_confidence = (
            foundation_confidence * overall_weights.get('foundation', 0.35) +
            comprehension_confidence * overall_weights.get('comprehension', 0.25) +
            execution_confidence * overall_weights.get('execution', 0.25) +
            vectors.get('engagement', 0.5) * overall_weights.get('engagement', 0.15)
        )

        # Build metaStateVector (current phase = 1.0, others = 0.0)
        meta_state = {
            "preflight": 1.0 if phase == "preflight" else 0.0,
            "think": 0.0,
            "plan": 0.0,
            "investigate": 0.0,
            "check": 1.0 if phase == "check" else 0.0,
            "act": 0.0,
            "postflight": 1.0 if phase == "postflight" else 0.0
        }

        # Create ReflexFrame structure
        frame_data = {
            "frameId": f"{session_id}_{phase}_{assessment_data.get('assessment_id', 'unknown')}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "selfAwareFlag": True,
            "epistemicVector": {
                **vectors,
                "foundation_confidence": foundation_confidence,
                "comprehension_confidence": comprehension_confidence,
                "execution_confidence": execution_confidence,
                "overall_confidence": overall_confidence,
                "engagement_gate_passed": vectors.get('engagement', 0) >= 0.6
            },
            "metaStateVector": meta_state,
            "recommendedAction": determine_action(vectors),
            "criticalFlags": {
                "coherence_critical": vectors.get('coherence', 1.0) < 0.5,
                "density_critical": vectors.get('density', 0.0) > 0.9,
                "change_critical": vectors.get('change', 1.0) < 0.5
            },
            "task": assessment_data.get("task_summary", assessment_data.get("prompt_summary", "Unknown task")),
            "session_id": session_id,
            "cascade_id": assessment_data.get("cascade_id"),
            "phase": phase,
            "full_assessment": assessment_data
        }

        # Write JSON
        log_date = datetime.now(timezone.utc).date()
        agent_dir = Path(log_dir) / session_id / log_date.isoformat()
        agent_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        filename = f"reflex_frame_{timestamp}_{phase}.json"
        log_path = agent_dir / filename

        with open(log_path, 'w') as f:
            json.dump(frame_data, f, indent=2)

        return log_path

    except Exception as e:
        return None


def determine_action(vectors: Dict[str, float]) -> str:
    """
    Determine recommended action based on epistemic vectors

    Args:
        vectors: Dict of epistemic assessment vectors

    Returns:
        Recommended action string (reset/stop/clarify/investigate/proceed)
    """
    if vectors.get('coherence', 1.0) < 0.5 or vectors.get('density', 0.0) > 0.9:
        return "reset"
    if vectors.get('change', 1.0) < 0.5:
        return "stop"
    if vectors.get('engagement', 1.0) < 0.6:
        return "clarify"
    if vectors.get('uncertainty', 0.0) > 0.8:
        return "investigate"
    return "proceed"
