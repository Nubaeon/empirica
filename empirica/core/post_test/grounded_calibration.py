"""
Grounded Calibration Manager

Parallel Bayesian track that uses objective evidence as observations
instead of self-assessed POSTFLIGHT vectors.

Mirrors BayesianBeliefManager but with:
- Lower observation variance (0.05 vs 0.1) — higher trust in objective evidence
- Evidence from PostTestCollector/EvidenceMapper instead of self-assessment
- Tracks divergence between self-referential and grounded tracks
- Stores in grounded_beliefs table (parallel to bayesian_beliefs)

The key insight: the existing calibration measures learning (PREFLIGHT→POSTFLIGHT delta),
not calibration accuracy. This track measures how well POSTFLIGHT self-assessment
matches what actually happened (objective evidence).
"""

import json
import logging
import uuid
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Optional

from .collector import PostTestCollector, EvidenceBundle
from .mapper import (
    EvidenceMapper,
    GroundedAssessment,
    UNGROUNDABLE_VECTORS,
)

logger = logging.getLogger(__name__)


@dataclass
class GroundedBelief:
    """A Bayesian belief grounded in objective evidence."""
    vector_name: str
    mean: float
    variance: float
    evidence_count: int
    last_observation: float
    last_observation_source: str
    self_referential_mean: Optional[float]
    divergence: Optional[float]
    last_updated: float


class GroundedCalibrationManager:
    """
    Manages grounded calibration beliefs using objective evidence.

    Parallel to BayesianBeliefManager, but observations come from
    deterministic sources (test results, git metrics, artifact counts)
    instead of self-assessment.
    """

    DEFAULT_PRIOR_MEAN = 0.5
    DEFAULT_PRIOR_VARIANCE = 0.25

    # Lower than self-referential (0.1) — we trust objective evidence more
    OBSERVATION_VARIANCE = 0.05

    TRACKED_VECTORS = [
        'engagement', 'know', 'do', 'context',
        'clarity', 'coherence', 'signal', 'density',
        'state', 'change', 'completion', 'impact', 'uncertainty'
    ]

    def __init__(self, db):
        self.db = db
        self.conn = db.conn

    def get_grounded_beliefs(self, ai_id: str) -> Dict[str, GroundedBelief]:
        """Get current grounded beliefs for an AI, most recent per vector."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT vector_name, mean, variance, evidence_count,
                   last_observation, last_observation_source,
                   self_referential_mean, divergence, last_updated
            FROM grounded_beliefs
            WHERE ai_id = ?
            ORDER BY last_updated DESC
        """, (ai_id,))

        beliefs = {}
        seen = set()

        for row in cursor.fetchall():
            vector_name = row[0]
            if vector_name not in seen:
                beliefs[vector_name] = GroundedBelief(
                    vector_name=vector_name,
                    mean=row[1],
                    variance=row[2],
                    evidence_count=row[3],
                    last_observation=row[4],
                    last_observation_source=row[5],
                    self_referential_mean=row[6],
                    divergence=row[7],
                    last_updated=row[8],
                )
                seen.add(vector_name)

        # Fill defaults for missing groundable vectors
        for vector in self.TRACKED_VECTORS:
            if vector not in beliefs and vector not in UNGROUNDABLE_VECTORS:
                beliefs[vector] = GroundedBelief(
                    vector_name=vector,
                    mean=self.DEFAULT_PRIOR_MEAN,
                    variance=self.DEFAULT_PRIOR_VARIANCE,
                    evidence_count=0,
                    last_observation=0.0,
                    last_observation_source="none",
                    self_referential_mean=None,
                    divergence=None,
                    last_updated=0.0,
                )

        return beliefs

    def update_grounded_beliefs(
        self,
        session_id: str,
        assessment: GroundedAssessment,
        phase: str = "combined",
    ) -> Dict[str, Dict]:
        """
        Update grounded beliefs from a GroundedAssessment.

        For each grounded vector estimate, performs a Bayesian update using
        the objective evidence value as the observation.

        Returns dict of vector → update details.
        """
        cursor = self.conn.cursor()

        # Get AI ID
        cursor.execute(
            "SELECT ai_id FROM sessions WHERE session_id = ?",
            (session_id,),
        )
        row = cursor.fetchone()
        if not row:
            return {}
        ai_id = row[0]

        current_beliefs = self.get_grounded_beliefs(ai_id)
        updates = {}

        for vector_name, estimate in assessment.grounded.items():
            if vector_name in UNGROUNDABLE_VECTORS:
                continue

            belief = current_beliefs.get(vector_name)
            if belief:
                prior_mean = belief.mean
                prior_var = belief.variance
                evidence_count = belief.evidence_count
            else:
                prior_mean = self.DEFAULT_PRIOR_MEAN
                prior_var = self.DEFAULT_PRIOR_VARIANCE
                evidence_count = 0

            # Scale observation variance by evidence confidence
            # High-confidence evidence gets lower variance (more trusted)
            obs_var = self.OBSERVATION_VARIANCE / max(estimate.confidence, 0.1)

            # Bayesian update
            posterior_mean = (
                (prior_var * estimate.estimated_value + obs_var * prior_mean)
                / (prior_var + obs_var)
            )
            posterior_var = 1.0 / (1.0 / prior_var + 1.0 / obs_var)
            new_evidence_count = evidence_count + estimate.evidence_count

            # Self-referential comparison
            self_val = assessment.self_assessed.get(vector_name)
            divergence = None
            if self_val is not None:
                divergence = round(self_val - posterior_mean, 4)

            # Store
            belief_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO grounded_beliefs (
                    belief_id, session_id, ai_id, vector_name,
                    mean, variance, evidence_count,
                    last_observation, last_observation_source,
                    self_referential_mean, divergence, last_updated,
                    phase
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                belief_id, session_id, ai_id, vector_name,
                posterior_mean, posterior_var, new_evidence_count,
                estimate.estimated_value, estimate.primary_source,
                self_val, divergence,
                datetime.now().timestamp(),
                phase,
            ))

            updates[vector_name] = {
                'prior_mean': prior_mean,
                'prior_variance': prior_var,
                'observation': estimate.estimated_value,
                'observation_source': estimate.primary_source,
                'posterior_mean': posterior_mean,
                'posterior_variance': posterior_var,
                'evidence_count': new_evidence_count,
                'self_assessed': self_val,
                'divergence': divergence,
            }

        self.conn.commit()
        return updates

    def store_evidence(
        self,
        bundle: EvidenceBundle,
    ) -> int:
        """Store raw evidence items for audit trail."""
        cursor = self.conn.cursor()
        stored = 0

        for item in bundle.items:
            evidence_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO verification_evidence (
                    evidence_id, session_id, source, metric_name,
                    raw_value, normalized_value, quality,
                    supports_vectors, collected_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                evidence_id,
                bundle.session_id,
                item.source,
                item.metric_name,
                json.dumps(item.raw_value),
                item.value,
                item.quality.value,
                json.dumps(item.supports_vectors),
                bundle.collection_timestamp,
                json.dumps(item.metadata) if item.metadata else None,
            ))
            stored += 1

        self.conn.commit()
        return stored

    def store_verification(
        self,
        session_id: str,
        assessment: GroundedAssessment,
        bundle: EvidenceBundle,
        domain: Optional[str] = None,
        goal_id: Optional[str] = None,
        phase: str = "combined",
    ) -> str:
        """Store a complete grounded verification record."""
        cursor = self.conn.cursor()

        # Get AI ID
        cursor.execute(
            "SELECT ai_id FROM sessions WHERE session_id = ?",
            (session_id,),
        )
        row = cursor.fetchone()
        ai_id = row[0] if row else "unknown"

        # Serialize grounded estimates
        grounded_data = {}
        for name, est in assessment.grounded.items():
            grounded_data[name] = {
                'value': est.estimated_value,
                'confidence': est.confidence,
                'evidence_count': est.evidence_count,
                'source': est.primary_source,
            }

        verification_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO grounded_verifications (
                verification_id, session_id, ai_id,
                self_assessed_vectors, grounded_vectors, calibration_gaps,
                grounded_coverage, overall_calibration_score,
                evidence_count, sources_available, sources_failed,
                domain, goal_id, phase
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            verification_id,
            session_id,
            ai_id,
            json.dumps(assessment.self_assessed),
            json.dumps(grounded_data),
            json.dumps(assessment.calibration_gaps),
            assessment.grounded_coverage,
            assessment.overall_calibration_score,
            len(bundle.items),
            json.dumps(bundle.sources_available),
            json.dumps(bundle.sources_failed),
            domain,
            goal_id,
            phase,
        ))

        self.conn.commit()
        return verification_id

    def get_calibration_divergence(self, ai_id: str) -> Dict[str, Dict]:
        """
        Compare self-referential and grounded calibration tracks.

        Returns per-vector comparison showing where the two tracks disagree.
        """
        from ..bayesian_beliefs import BayesianBeliefManager

        self_ref_manager = BayesianBeliefManager(self.db)
        self_ref_beliefs = self_ref_manager.get_beliefs(ai_id)
        grounded_beliefs = self.get_grounded_beliefs(ai_id)

        divergence = {}
        for vector in self.TRACKED_VECTORS:
            if vector in UNGROUNDABLE_VECTORS:
                continue

            self_ref = self_ref_beliefs.get(vector)
            grounded = grounded_beliefs.get(vector)

            if self_ref and grounded and grounded.evidence_count > 0:
                divergence[vector] = {
                    'self_referential_mean': self_ref.mean,
                    'grounded_mean': grounded.mean,
                    'gap': round(self_ref.mean - grounded.mean, 4),
                    'self_ref_evidence': self_ref.evidence_count,
                    'grounded_evidence': grounded.evidence_count,
                    'grounded_variance': grounded.variance,
                }

        return divergence

    def get_grounded_adjustments(self, ai_id: str) -> Dict[str, float]:
        """
        Get calibration adjustments based on grounded evidence.

        Like BayesianBeliefManager.get_calibration_adjustments() but
        grounded in objective evidence.
        """
        beliefs = self.get_grounded_beliefs(ai_id)
        adjustments = {}

        from ..bayesian_beliefs import BayesianBeliefManager
        max_correction = BayesianBeliefManager.MAX_CORRECTION_MAGNITUDE

        for vector, belief in beliefs.items():
            if belief.evidence_count >= 3:
                adjustment = belief.mean - self.DEFAULT_PRIOR_MEAN
                evidence_weight = min(belief.evidence_count / 10.0, 1.0)
                raw = round(adjustment * evidence_weight, 4)
                # Cap correction magnitude (same limit as self-referential track)
                capped = max(-max_correction, min(max_correction, raw))
                adjustments[vector] = capped

        return adjustments

    def export_grounded_calibration(
        self,
        ai_id: str,
        git_root: Optional[str] = None,
    ) -> bool:
        """
        Export grounded calibration to .breadcrumbs.yaml as a new section.

        Does NOT replace the existing `calibration:` section — adds a
        parallel `grounded_calibration:` section for comparison.
        """
        import os
        import subprocess

        if not git_root:
            try:
                result = subprocess.run(
                    ['git', 'rev-parse', '--show-toplevel'],
                    capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0:
                    git_root = result.stdout.strip()
                else:
                    return False
            except Exception:
                return False

        breadcrumbs_path = os.path.join(git_root, '.breadcrumbs.yaml')

        beliefs = self.get_grounded_beliefs(ai_id)
        adjustments = self.get_grounded_adjustments(ai_id)
        divergence = self.get_calibration_divergence(ai_id)

        if not beliefs:
            return False

        total_evidence = sum(b.evidence_count for b in beliefs.values())
        if total_evidence == 0:
            return False

        # Compute grounded coverage (fraction of vectors with evidence)
        grounded_count = sum(
            1 for b in beliefs.values()
            if b.evidence_count > 0
        )
        coverage = grounded_count / len(
            [v for v in self.TRACKED_VECTORS if v not in UNGROUNDABLE_VECTORS]
        )

        # Build YAML
        timestamp = datetime.now().isoformat()
        lines = [
            "\n# Grounded calibration (auto-updated by Empirica post-test verification)\n",
            "grounded_calibration:\n",
            f'  last_updated: "{timestamp}"\n',
            f"  ai_id: {ai_id}\n",
            f"  observations: {total_evidence}\n",
            f"  grounded_coverage: {coverage:.2f}\n",
        ]

        # Divergence section (grounded vs self-referential)
        if divergence:
            lines.append("  divergence:\n")
            sorted_div = sorted(
                divergence.items(),
                key=lambda x: abs(x[1]['gap']),
                reverse=True,
            )
            for vector, data in sorted_div:
                sign = '+' if data['gap'] >= 0 else ''
                lines.append(f"    {vector}: {sign}{data['gap']:.2f}\n")

        # Ungrounded vectors
        lines.append(
            f"  ungrounded: [{', '.join(sorted(UNGROUNDABLE_VECTORS))}]\n"
        )

        # Grounded bias corrections
        if adjustments:
            lines.append("  grounded_bias_corrections:\n")
            sorted_adj = sorted(
                adjustments.items(),
                key=lambda x: abs(x[1]),
                reverse=True,
            )
            for vector, adj in sorted_adj:
                sign = '+' if adj >= 0 else ''
                lines.append(f"    {vector}: {sign}{adj:.2f}\n")

        yaml_block = ''.join(lines)

        # Read existing file, find/replace grounded_calibration section
        try:
            existing_lines = []
            if os.path.exists(breadcrumbs_path):
                with open(breadcrumbs_path, 'r') as f:
                    existing_lines = f.readlines()

            section_start = -1
            section_end = -1
            in_section = False

            for i, line in enumerate(existing_lines):
                if '# Grounded calibration' in line and section_start == -1:
                    section_start = i
                elif line.strip().startswith('grounded_calibration:'):
                    if section_start == -1:
                        section_start = i
                    in_section = True
                elif in_section and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                    section_end = i
                    break

            if in_section and section_end == -1:
                section_end = len(existing_lines)

            if section_start >= 0:
                new_lines = (
                    existing_lines[:section_start]
                    + [yaml_block]
                    + existing_lines[section_end:]
                )
            elif existing_lines:
                new_lines = existing_lines + [yaml_block]
            else:
                new_lines = [yaml_block]

            with open(breadcrumbs_path, 'w') as f:
                f.writelines(new_lines)

            return True
        except Exception as e:
            logger.debug(f"Failed to export grounded calibration: {e}")
            return False


def _run_single_phase_verification(
    session_id: str,
    vectors: Dict[str, float],
    db,
    phase: str,
    project_id: Optional[str] = None,
    domain: Optional[str] = None,
    goal_id: Optional[str] = None,
    check_timestamp: Optional[float] = None,
) -> Optional[Dict]:
    """Run grounded verification for a single phase (noetic, praxic, or combined)."""
    collector = PostTestCollector(
        session_id=session_id,
        project_id=project_id,
        db=db,
        phase=phase,
        check_timestamp=check_timestamp,
    )
    bundle = collector.collect_all()

    if not bundle.items:
        logger.debug(f"No {phase} evidence collected, skipping")
        return None

    mapper = EvidenceMapper()
    assessment = mapper.map_evidence(bundle, vectors, phase=phase)

    manager = GroundedCalibrationManager(db)
    updates = manager.update_grounded_beliefs(session_id, assessment, phase=phase)

    manager.store_evidence(bundle)
    verification_id = manager.store_verification(
        session_id, assessment, bundle,
        domain=domain, goal_id=goal_id, phase=phase,
    )

    from .trajectory_tracker import TrajectoryTracker
    tracker = TrajectoryTracker(db)
    tracker.record_trajectory_point(
        session_id, assessment,
        domain=domain, goal_id=goal_id, phase=phase,
    )

    return {
        'verification_id': verification_id,
        'phase': phase,
        'evidence_count': len(bundle.items),
        'sources': bundle.sources_available,
        'sources_failed': bundle.sources_failed,
        'grounded_coverage': round(assessment.grounded_coverage, 2),
        'calibration_score': assessment.overall_calibration_score,
        'gaps': assessment.calibration_gaps,
        'updates': {
            v: {
                'observation': u['observation'],
                'self_assessed': u['self_assessed'],
                'divergence': u['divergence'],
            }
            for v, u in updates.items()
        },
    }


def run_grounded_verification(
    session_id: str,
    postflight_vectors: Dict[str, float],
    db,
    project_id: Optional[str] = None,
    domain: Optional[str] = None,
    goal_id: Optional[str] = None,
    phase_boundary: Optional[Dict] = None,
) -> Optional[Dict]:
    """
    Full grounded verification pipeline.

    Called after POSTFLIGHT: collect → map → update → store → trajectory → export.

    Phase-aware when phase_boundary is provided (from detect_phase_boundary()):
    - Splits into noetic (PREFLIGHT→CHECK) and praxic (CHECK→POSTFLIGHT) passes
    - Each phase gets independent evidence collection and calibration
    - Falls back to combined when no CHECK boundary exists

    Returns verification summary dict, or None on failure.
    """
    try:
        results = {}

        if phase_boundary and phase_boundary.get("has_check"):
            check_ts = phase_boundary.get("proceed_check_timestamp")
            noetic_only = phase_boundary.get("noetic_only", False)

            # Noetic vectors: delta from PREFLIGHT to CHECK
            preflight_vectors = phase_boundary.get("preflight_vectors") or {}
            check_vectors = phase_boundary.get("proceed_check_vectors") or {}

            # Noetic self-assessment = CHECK vectors (what AI claimed at CHECK)
            noetic_self = {}
            for k, v in check_vectors.items():
                if v is not None:
                    noetic_self[k] = v

            if noetic_self:
                noetic_result = _run_single_phase_verification(
                    session_id, noetic_self, db,
                    phase="noetic",
                    project_id=project_id,
                    domain=domain, goal_id=goal_id,
                    check_timestamp=check_ts,
                )
                if noetic_result:
                    results["noetic"] = noetic_result

            # Praxic: only if not noetic-only (had a proceed CHECK)
            if not noetic_only:
                praxic_result = _run_single_phase_verification(
                    session_id, postflight_vectors, db,
                    phase="praxic",
                    project_id=project_id,
                    domain=domain, goal_id=goal_id,
                    check_timestamp=check_ts,
                )
                if praxic_result:
                    results["praxic"] = praxic_result
        else:
            # No phase boundary — combined mode (backward-compatible)
            combined_result = _run_single_phase_verification(
                session_id, postflight_vectors, db,
                phase="combined",
                project_id=project_id,
                domain=domain, goal_id=goal_id,
            )
            if combined_result:
                results["combined"] = combined_result

        if not results:
            return None

        # Export to .breadcrumbs.yaml
        manager = GroundedCalibrationManager(db)
        cursor = db.conn.cursor()
        cursor.execute(
            "SELECT ai_id FROM sessions WHERE session_id = ?",
            (session_id,),
        )
        row = cursor.fetchone()
        if row:
            manager.export_grounded_calibration(row[0])

        # Build unified summary
        all_gaps = {}
        all_updates = {}
        total_evidence = 0
        all_sources = []
        all_failed = []
        verification_ids = []

        for phase_name, phase_result in results.items():
            total_evidence += phase_result['evidence_count']
            all_sources.extend(phase_result['sources'])
            all_failed.extend(phase_result['sources_failed'])
            verification_ids.append(phase_result['verification_id'])
            for v, gap in phase_result['gaps'].items():
                all_gaps[f"{phase_name}:{v}"] = gap
            for v, u in phase_result['updates'].items():
                all_updates[f"{phase_name}:{v}"] = u

        return {
            'verification_ids': verification_ids,
            'phase_aware': phase_boundary is not None and phase_boundary.get("has_check", False),
            'phases': results,
            'evidence_count': total_evidence,
            'sources': list(set(all_sources)),
            'sources_failed': list(set(all_failed)),
            'gaps': all_gaps,
            'updates': all_updates,
        }

    except Exception as e:
        logger.warning(f"Grounded verification failed (non-fatal): {e}")
        return None
