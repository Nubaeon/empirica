"""
Bayesian Belief Manager

Updates AI priors based on historical performance.
Implements calibration loop: POSTFLIGHT deltas → update beliefs → inform next PREFLIGHT.

The core insight: AI doesn't "want" to lie - hallucination is an epistemic assessment problem.
By tracking actual performance against self-assessed vectors, we calibrate future assessments.

Bayesian Update:
    posterior_mean = (prior_var * observation + obs_var * prior_mean) / (prior_var + obs_var)
    posterior_var = 1 / (1/prior_var + 1/obs_var)

Author: Claude Code
Date: 2025-12-30
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class Belief:
    """A Bayesian belief about a vector."""
    vector_name: str
    mean: float
    variance: float
    evidence_count: int
    prior_mean: float
    prior_variance: float
    last_updated: datetime


class BayesianBeliefManager:
    """
    Manages Bayesian beliefs for epistemic vector calibration.

    Tracks how well AI self-assessments predict actual outcomes,
    updating priors to improve future assessments.
    """

    # Default priors for new vectors (uninformative)
    DEFAULT_PRIOR_MEAN = 0.5
    DEFAULT_PRIOR_VARIANCE = 0.25  # High variance = uncertain

    # Observation variance (how much we trust single observations)
    OBSERVATION_VARIANCE = 0.1

    # Vectors to track
    TRACKED_VECTORS = [
        'engagement', 'know', 'do', 'context',
        'clarity', 'coherence', 'signal', 'density',
        'state', 'change', 'completion', 'impact', 'uncertainty'
    ]

    def __init__(self, db):
        """Initialize with database connection."""
        self.db = db
        self.conn = db.conn

    def get_beliefs(self, ai_id: str) -> Dict[str, Belief]:
        """
        Get current beliefs for an AI.

        Returns beliefs aggregated across all sessions for this AI.
        """
        cursor = self.conn.cursor()

        # Get most recent belief for each vector
        cursor.execute("""
            SELECT bb.vector_name, bb.mean, bb.variance, bb.evidence_count,
                   bb.prior_mean, bb.prior_variance, bb.last_updated
            FROM bayesian_beliefs bb
            JOIN cascades c ON bb.cascade_id = c.cascade_id
            JOIN sessions s ON c.session_id = s.session_id
            WHERE s.ai_id = ?
            ORDER BY bb.last_updated DESC
        """, (ai_id,))

        beliefs = {}
        seen_vectors = set()

        for row in cursor.fetchall():
            vector_name = row[0]
            if vector_name not in seen_vectors:
                beliefs[vector_name] = Belief(
                    vector_name=vector_name,
                    mean=row[1],
                    variance=row[2],
                    evidence_count=row[3],
                    prior_mean=row[4],
                    prior_variance=row[5],
                    last_updated=row[6]
                )
                seen_vectors.add(vector_name)

        # Fill in defaults for missing vectors
        for vector in self.TRACKED_VECTORS:
            if vector not in beliefs:
                beliefs[vector] = Belief(
                    vector_name=vector,
                    mean=self.DEFAULT_PRIOR_MEAN,
                    variance=self.DEFAULT_PRIOR_VARIANCE,
                    evidence_count=0,
                    prior_mean=self.DEFAULT_PRIOR_MEAN,
                    prior_variance=self.DEFAULT_PRIOR_VARIANCE,
                    last_updated=None
                )

        return beliefs

    def get_calibration_adjustments(self, ai_id: str) -> Dict[str, float]:
        """
        Get calibration adjustments for PREFLIGHT based on historical beliefs.

        Returns adjustment factors: positive means AI tends to underestimate,
        negative means AI tends to overestimate.
        """
        beliefs = self.get_beliefs(ai_id)
        adjustments = {}

        for vector, belief in beliefs.items():
            if belief.evidence_count >= 3:  # Need sufficient evidence
                # Compare mean (actual performance) to prior_mean (self-assessment)
                # If mean > prior_mean: AI underestimates (adjustment positive)
                # If mean < prior_mean: AI overestimates (adjustment negative)
                adjustment = belief.mean - belief.prior_mean

                # Weight by confidence (inverse variance)
                confidence = 1.0 / (belief.variance + 0.01)
                confidence = min(confidence, 10.0)  # Cap confidence

                # Scale adjustment by evidence count (more evidence = trust adjustment more)
                evidence_weight = min(belief.evidence_count / 10.0, 1.0)

                adjustments[vector] = adjustment * evidence_weight

        return adjustments

    def update_belief(self, session_id: str, vector_name: str, observation: float,
                      phase: str = "CHECK", round_num: int = 1) -> Optional[Dict]:
        """
        Update belief for a single vector during CHECK phase.

        This is the incremental update interface, used during mid-loop assessments.
        For full PREFLIGHT→POSTFLIGHT comparison, use update_beliefs() instead.

        Args:
            session_id: The session ID
            vector_name: The vector to update (e.g., 'know', 'uncertainty')
            observation: The observed/assessed value
            phase: The CASCADE phase (CHECK, POSTFLIGHT)
            round_num: The round number within the phase

        Returns:
            Dict with belief update details, or None if update failed
        """
        if vector_name not in self.TRACKED_VECTORS:
            return None

        cursor = self.conn.cursor()

        # Get AI ID for this session
        cursor.execute("SELECT ai_id FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        if not row:
            return None
        ai_id = row[0]

        # Get current belief for this vector
        current_beliefs = self.get_beliefs(ai_id)
        belief = current_beliefs.get(vector_name)

        if not belief:
            prior_mean = self.DEFAULT_PRIOR_MEAN
            prior_var = self.DEFAULT_PRIOR_VARIANCE
            evidence_count = 0
        else:
            prior_mean = belief.mean
            prior_var = belief.variance
            evidence_count = belief.evidence_count

        # Bayesian update
        obs_var = self.OBSERVATION_VARIANCE

        posterior_mean = (
            (prior_var * observation + obs_var * prior_mean) /
            (prior_var + obs_var)
        )
        posterior_var = 1.0 / (1.0/prior_var + 1.0/obs_var)
        new_evidence_count = evidence_count + 1

        # Get or create cascade_id for this session
        cursor.execute("""
            SELECT cascade_id FROM cascades
            WHERE session_id = ?
            ORDER BY started_at DESC LIMIT 1
        """, (session_id,))
        cascade_row = cursor.fetchone()
        cascade_id = cascade_row[0] if cascade_row else str(uuid.uuid4())

        # Store the update
        belief_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO bayesian_beliefs (
                belief_id, cascade_id, vector_name,
                mean, variance, evidence_count,
                prior_mean, prior_variance, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            belief_id, cascade_id, vector_name,
            posterior_mean, posterior_var, new_evidence_count,
            observation, self.OBSERVATION_VARIANCE, datetime.now()
        ))

        self.conn.commit()

        return {
            'vector_name': vector_name,
            'phase': phase,
            'round_num': round_num,
            'prior_mean': prior_mean,
            'prior_variance': prior_var,
            'observation': observation,
            'posterior_mean': posterior_mean,
            'posterior_variance': posterior_var,
            'evidence_count': new_evidence_count,
            'calibration_delta': observation - prior_mean
        }

    def update_beliefs(self, cascade_id: str, session_id: str,
                       preflight_vectors: Dict[str, float],
                       postflight_vectors: Dict[str, float]) -> Dict[str, Dict]:
        """
        Update beliefs based on PREFLIGHT → POSTFLIGHT comparison.

        The delta between self-assessment (preflight) and measured outcome (postflight)
        becomes evidence for updating our beliefs about this AI's calibration.

        Args:
            cascade_id: The CASCADE cycle ID
            session_id: The session ID
            preflight_vectors: Self-assessed vectors at session start
            postflight_vectors: Measured vectors at session end

        Returns:
            Dict of updated beliefs with deltas
        """
        cursor = self.conn.cursor()

        # Get AI ID for this session
        cursor.execute("SELECT ai_id FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        if not row:
            return {}
        ai_id = row[0]

        # Get current beliefs
        current_beliefs = self.get_beliefs(ai_id)

        updates = {}

        for vector in self.TRACKED_VECTORS:
            pre_val = preflight_vectors.get(vector)
            post_val = postflight_vectors.get(vector)

            if pre_val is None or post_val is None:
                continue

            # The "observation" is the actual outcome (postflight)
            observation = post_val

            # Get current belief
            belief = current_beliefs.get(vector)
            if not belief:
                prior_mean = self.DEFAULT_PRIOR_MEAN
                prior_var = self.DEFAULT_PRIOR_VARIANCE
                evidence_count = 0
            else:
                prior_mean = belief.mean
                prior_var = belief.variance
                evidence_count = belief.evidence_count

            # Bayesian update
            obs_var = self.OBSERVATION_VARIANCE

            # Posterior mean: weighted average of prior and observation
            posterior_mean = (
                (prior_var * observation + obs_var * prior_mean) /
                (prior_var + obs_var)
            )

            # Posterior variance: decreases with more evidence
            posterior_var = 1.0 / (1.0/prior_var + 1.0/obs_var)

            # Increment evidence count
            new_evidence_count = evidence_count + 1

            # Store the update
            belief_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO bayesian_beliefs (
                    belief_id, cascade_id, vector_name,
                    mean, variance, evidence_count,
                    prior_mean, prior_variance, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                belief_id, cascade_id, vector,
                posterior_mean, posterior_var, new_evidence_count,
                pre_val, self.OBSERVATION_VARIANCE, datetime.now()
            ))

            updates[vector] = {
                'prior_mean': prior_mean,
                'prior_variance': prior_var,
                'observation': observation,
                'posterior_mean': posterior_mean,
                'posterior_variance': posterior_var,
                'evidence_count': new_evidence_count,
                'calibration_delta': observation - pre_val  # How wrong was self-assessment
            }

        self.conn.commit()
        return updates

    def get_calibration_report(self, ai_id: str) -> Dict:
        """
        Generate a calibration report for an AI.

        Shows how well-calibrated the AI's self-assessments are.
        """
        beliefs = self.get_beliefs(ai_id)
        adjustments = self.get_calibration_adjustments(ai_id)

        report = {
            'ai_id': ai_id,
            'total_evidence': sum(b.evidence_count for b in beliefs.values()),
            'vectors': {},
            'calibration_summary': {
                'overestimates': [],
                'underestimates': [],
                'well_calibrated': []
            }
        }

        for vector, belief in beliefs.items():
            adjustment = adjustments.get(vector, 0)

            vector_report = {
                'mean': belief.mean,
                'variance': belief.variance,
                'evidence_count': belief.evidence_count,
                'adjustment': adjustment,
                'confidence': 1.0 / (belief.variance + 0.01) if belief.variance else 0
            }
            report['vectors'][vector] = vector_report

            # Categorize calibration
            if belief.evidence_count >= 3:
                if adjustment < -0.1:
                    report['calibration_summary']['overestimates'].append(vector)
                elif adjustment > 0.1:
                    report['calibration_summary']['underestimates'].append(vector)
                else:
                    report['calibration_summary']['well_calibrated'].append(vector)

        return report


def apply_calibration_to_vectors(vectors: Dict[str, float],
                                  adjustments: Dict[str, float]) -> Dict[str, float]:
    """
    Apply calibration adjustments to self-assessed vectors.

    Used during PREFLIGHT to correct for known biases.
    """
    calibrated = {}

    for vector, value in vectors.items():
        adjustment = adjustments.get(vector, 0)
        # Apply adjustment, clamping to [0, 1]
        calibrated[vector] = max(0.0, min(1.0, value + adjustment))

    return calibrated
