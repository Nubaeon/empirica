"""
Drift Detection Module - Monitors epistemic drift via temporal self-validation

Uses Git checkpoints to compare current state to historical baselines.
Detects memory corruption, context loss, and scope drift.

Pattern detection:
- TRUE_DRIFT: KNOW + CLARITY + CONTEXT all dropping (memory loss)
- LEARNING: KNOW down but CLARITY up (discovering complexity - healthy)
- SCOPE_DRIFT: KNOW down with scope expansion signals

Calibration is handled separately by BayesianBeliefManager in bayesian_beliefs.py
"""

from .mirror_drift_monitor import MirrorDriftMonitor, DriftReport

__all__ = ["MirrorDriftMonitor", "DriftReport"]
