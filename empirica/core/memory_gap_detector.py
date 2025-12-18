#!/usr/bin/env python3
"""
Memory Gap Detector - Detect and enforce awareness of context gaps

Detects when AI claims knowledge without evidence from breadcrumbs.
Configurable enforcement: inform (show only), warn (recommend), strict (adjust vectors), block (prevent).

Philosophy:
- Always detect gaps (transparency)
- User controls enforcement (agency)
- Different policies per category (flexibility)
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Import policy loader (lazy import to avoid circular dependencies)
_policy_loader = None


def get_policy_loader():
    """Lazy load policy loader to avoid circular imports"""
    global _policy_loader
    if _policy_loader is None:
        try:
            from empirica.config.memory_gap_policy_loader import get_policy_loader as _get_loader
            _policy_loader = _get_loader()
        except ImportError:
            logger.warning("Could not import memory_gap_policy_loader, using defaults")
            _policy_loader = None
    return _policy_loader


@dataclass
class MemoryGap:
    """A detected gap between claimed and realistic knowledge."""
    gap_id: str
    gap_type: str  # 'unreferenced_findings' | 'unincorporated_unknowns' | 'file_unawareness' | 'confabulation' | 'compaction'
    content: str
    severity: str  # 'low' | 'medium' | 'high' | 'critical'
    gap_score: float  # 0.0-1.0
    evidence: Dict[str, Any]
    affects_vector: Optional[str] = None  # Which vector this impacts
    realistic_value: Optional[float] = None  # What the vector should be
    resolution_action: str = ""  # How to fix


@dataclass
class MemoryGapReport:
    """Complete memory gap analysis."""
    detected: bool
    gaps: List[MemoryGap]
    overall_gap: float  # Overall gap score
    expected_know: float  # Realistic knowledge estimate
    claimed_know: float  # What AI claimed
    enforcement: Dict[str, Any]  # Enforcement decisions per gap
    actions: List[str]  # Recommended actions


class MemoryGapDetector:
    """
    Detect memory gaps with configurable enforcement.

    Modes:
    - inform: Show gaps, no penalty (default)
    - warn: Show gaps + recommendations
    - strict: Show gaps + adjust vectors to realistic
    - block: Show gaps + prevent proceeding until resolved
    """

    def __init__(self, policy: Optional[Dict[str, Any]] = None):
        """
        Initialize detector with policy.

        Args:
            policy: Enforcement policy configuration (optional)
                If not provided, loads from memory_gap_policy_loader
                {
                    'enforcement': 'inform|warn|strict|block',
                    'scope': {
                        'findings': 'inform|warn|strict|block',
                        'unknowns': 'inform|warn|strict|block',
                        'file_changes': 'inform|warn|strict|block',
                        'compaction': 'inform|warn|strict|block',
                        'confabulation': 'inform|warn|strict|block'
                    },
                    'thresholds': {
                        'findings': 10,  # Flag if >10 unread
                        'unknowns': 5,
                        'file_changes': 0,
                        'compaction': 0.4,
                        'confabulation': 0.3
                    }
                }
        """
        if policy is None:
            # Try to load from policy loader
            loader = get_policy_loader()
            if loader:
                try:
                    policy = loader.get_policy()
                    logger.info(f"Loaded memory gap policy: enforcement={policy.get('enforcement', 'inform')}")
                except Exception as e:
                    logger.warning(f"Failed to load policy from loader: {e}")
                    policy = None

        # Fallback to default if still None
        self.policy = policy or {
            'enforcement': 'inform',
            'scope': {},
            'thresholds': {}
        }

    def detect_gaps(
        self,
        current_vectors: Dict[str, float],
        breadcrumbs: Dict[str, Any],
        session_context: Dict[str, Any]
    ) -> MemoryGapReport:
        """
        Detect all memory gaps between claimed and realistic knowledge.

        Args:
            current_vectors: Current epistemic vector values
            breadcrumbs: Project breadcrumbs from project-bootstrap
            session_context: Current session state

        Returns:
            MemoryGapReport with detected gaps and enforcement decisions
        """
        gaps = []

        # Gap type 1: Unreferenced findings
        findings_gap = self._check_findings(
            breadcrumbs.get('findings', []),
            session_context
        )
        if findings_gap:
            gaps.append(findings_gap)

        # Gap type 2: Unincorporated unknowns
        unknowns_gap = self._check_unknowns(
            breadcrumbs.get('unknowns', []),
            session_context
        )
        if unknowns_gap:
            gaps.append(unknowns_gap)

        # Gap type 3: File change unawareness
        # Handle recent_artifacts being either dict or list
        recent_artifacts = breadcrumbs.get('recent_artifacts', [])
        files_changed = []
        if isinstance(recent_artifacts, dict):
            files_changed = recent_artifacts.get('files_changed', [])
        elif isinstance(recent_artifacts, list):
            files_changed = recent_artifacts  # Assume list is file changes

        files_gap = self._check_file_awareness(files_changed, session_context)
        if files_gap:
            gaps.append(files_gap)

        # Gap type 4: Compaction impact
        compaction_gap = self._check_compaction(
            session_context.get('compaction_events', []),
            current_vectors
        )
        if compaction_gap:
            gaps.append(compaction_gap)

        # Calculate expected vs claimed knowledge
        expected = self._calculate_expected_knowledge(breadcrumbs, session_context)
        claimed = current_vectors.get('know', 0.5)

        overall_gap = max(claimed - expected['expected_know'], 0.0)

        # Gap type 5: Overall confabulation (claiming too much)
        if overall_gap > 0.2:
            confab_gap = MemoryGap(
                gap_id=f"confabulation_{session_context.get('session_id', 'unknown')}",
                gap_type='confabulation',
                content=f"Claimed KNOW={claimed:.2f} but realistic estimate is {expected['expected_know']:.2f}",
                severity='high' if overall_gap > 0.3 else 'medium',
                gap_score=overall_gap,
                evidence={
                    'claimed': claimed,
                    'realistic': expected['expected_know'],
                    'calculation_signals': expected.get('signals', {})
                },
                affects_vector='know',
                realistic_value=expected['expected_know'],
                resolution_action="Load breadcrumbs and re-assess knowledge"
            )
            gaps.append(confab_gap)

        # Determine enforcement per gap
        enforcement = self._determine_enforcement(gaps)

        # Suggest actions
        actions = self._suggest_actions(gaps, enforcement)

        return MemoryGapReport(
            detected=len(gaps) > 0,
            gaps=gaps,
            overall_gap=overall_gap,
            expected_know=expected['expected_know'],
            claimed_know=claimed,
            enforcement=enforcement,
            actions=actions
        )

    def _check_findings(
        self,
        findings: List[Dict],
        session_context: Dict
    ) -> Optional[MemoryGap]:
        """Check if findings are unreferenced."""
        if not findings:
            return None

        threshold = self.policy.get('thresholds', {}).get('findings', 10)

        # Count unreferenced findings
        unreferenced = []
        for finding in findings:
            # Handle both dict and string findings
            finding_id = finding.get('id', '') if isinstance(finding, dict) else ''
            if not self._referenced_in_session(finding_id, session_context):
                unreferenced.append(finding)

        if len(unreferenced) <= threshold:
            return None

        # Calculate impact on KNOW vector
        finding_weight = 0.05  # Each finding contributes ~0.05 to KNOW
        know_impact = len(unreferenced) * finding_weight

        # Extract finding text (handle both dict and string)
        def get_finding_text(f):
            if isinstance(f, dict):
                return f.get('finding', str(f))[:100]
            return str(f)[:100]

        return MemoryGap(
            gap_id=f"unreferenced_findings_{len(unreferenced)}",
            gap_type='unreferenced_findings',
            content=f"{len(unreferenced)} findings from previous sessions not referenced",
            severity='high' if len(unreferenced) > 20 else 'medium',
            gap_score=min(know_impact, 0.5),
            evidence={
                'total_findings': len(findings),
                'unreferenced_count': len(unreferenced),
                'sample_findings': [get_finding_text(f) for f in unreferenced[:3]]
            },
            affects_vector='know',
            realistic_value=None,  # Calculated during enforcement
            resolution_action="Review findings: empirica project-bootstrap"
        )

    def _check_unknowns(
        self,
        unknowns: List[Dict],
        session_context: Dict
    ) -> Optional[MemoryGap]:
        """Check if resolved unknowns are unincorporated."""
        if not unknowns:
            return None

        threshold = self.policy.get('thresholds', {}).get('unknowns', 5)

        # Find resolved but unincorporated unknowns
        resolved_unincorporated = []
        for unknown in unknowns:
            # Handle both dict and string unknowns
            if isinstance(unknown, dict):
                if unknown.get('status') == 'resolved':
                    if not self._incorporated_in_session(unknown, session_context):
                        resolved_unincorporated.append(unknown)
            else:
                # String unknowns - assume unresolved
                resolved_unincorporated.append(unknown)

        if len(resolved_unincorporated) <= threshold:
            return None

        clarity_impact = len(resolved_unincorporated) * 0.03

        # Extract unknown text (handle both dict and string)
        def get_unknown_text(u):
            if isinstance(u, dict):
                return u.get('unknown', str(u))[:100]
            return str(u)[:100]

        return MemoryGap(
            gap_id=f"unincorporated_unknowns_{len(resolved_unincorporated)}",
            gap_type='unincorporated_unknowns',
            content=f"{len(resolved_unincorporated)} resolved unknowns not incorporated",
            severity='medium',
            gap_score=min(clarity_impact, 0.3),
            evidence={
                'total_unknowns': len(unknowns),
                'resolved_count': len([u for u in unknowns if isinstance(u, dict) and u.get('status') == 'resolved']),
                'unincorporated_count': len(resolved_unincorporated),
                'sample_unknowns': [get_unknown_text(u) for u in resolved_unincorporated[:3]]
            },
            affects_vector='clarity',
            realistic_value=None,
            resolution_action="Review resolved unknowns in breadcrumbs"
        )

    def _check_file_awareness(
        self,
        file_changes: List[str],
        session_context: Dict
    ) -> Optional[MemoryGap]:
        """Check if file changes are acknowledged."""
        if not file_changes:
            return None

        threshold = self.policy.get('thresholds', {}).get('file_changes', 0)

        # Check which files weren't mentioned
        unacknowledged = []
        for file_path in file_changes:
            if not self._mentioned_in_session(file_path, session_context):
                unacknowledged.append(file_path)

        if len(unacknowledged) <= threshold:
            return None

        context_impact = min(len(unacknowledged) * 0.02, 0.3)

        return MemoryGap(
            gap_id=f"file_unawareness_{len(unacknowledged)}",
            gap_type='file_changes',
            content=f"{len(unacknowledged)} file changes not acknowledged",
            severity='low' if len(unacknowledged) < 5 else 'medium',
            gap_score=context_impact,
            evidence={
                'total_changes': len(file_changes),
                'unacknowledged_count': len(unacknowledged),
                'sample_files': unacknowledged[:5]
            },
            affects_vector='context',
            realistic_value=None,
            resolution_action="Review file changes: git diff"
        )

    def _check_compaction(
        self,
        compaction_events: List[Dict],
        current_vectors: Dict[str, float]
    ) -> Optional[MemoryGap]:
        """Check impact of memory compaction."""
        if not compaction_events:
            return None

        threshold = self.policy.get('thresholds', {}).get('compaction', 0.4)

        # Calculate total detail loss
        total_loss = sum(e.get('detail_loss_estimate', 0) for e in compaction_events)

        if total_loss <= threshold:
            return None

        return MemoryGap(
            gap_id=f"compaction_loss_{total_loss:.2f}",
            gap_type='compaction',
            content=f"Memory compacted {total_loss*100:.0f}% - detail loss occurred",
            severity='critical' if total_loss > 0.6 else 'high',
            gap_score=total_loss,
            evidence={
                'compaction_count': len(compaction_events),
                'total_detail_loss': total_loss,
                'recent_event': compaction_events[-1] if compaction_events else None
            },
            affects_vector='clarity',
            realistic_value=current_vectors.get('clarity', 0.5) * (1 - total_loss * 0.5),
            resolution_action="Create checkpoint before further compaction"
        )

    def _calculate_expected_knowledge(
        self,
        breadcrumbs: Dict[str, Any],
        session_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate realistic knowledge baseline from breadcrumbs.

        Uses multiple signals:
        1. Historical baseline (last session)
        2. Artifact count (findings, unknowns)
        3. Git freshness (file changes)
        4. Reference tracking (are breadcrumbs actually used?)
        5. Breadcrumb loading (did AI load context?)
        """
        signals = {}

        # Signal 1: Historical baseline
        last_know = breadcrumbs.get('last_session_vectors', {}).get('know', 0.5)
        signals['historical'] = last_know * 0.95  # Slight decay expected

        # Signal 2: Artifact-based estimation
        findings_count = len(breadcrumbs.get('findings', []))
        unknowns = breadcrumbs.get('unknowns', [])
        unknowns_resolved = len([u for u in unknowns if u.get('status') == 'resolved'])
        unknowns_unresolved = len([u for u in unknowns if u.get('status') == 'active'])

        artifact_score = (
            0.05 * findings_count +
            0.03 * unknowns_resolved +
            -0.02 * unknowns_unresolved
        )
        signals['artifacts'] = min(0.5 + artifact_score, 1.0)

        # Signal 3: Git freshness
        # Handle recent_artifacts being either dict or list
        recent_artifacts = breadcrumbs.get('recent_artifacts', [])
        if isinstance(recent_artifacts, dict):
            files_changed = len(recent_artifacts.get('files_changed', []))
        elif isinstance(recent_artifacts, list):
            files_changed = len(recent_artifacts)
        else:
            files_changed = 0

        context_penalty = min(0.1 * (files_changed / 10), 0.3)
        signals['git_freshness'] = max(last_know - context_penalty, 0.2)

        # Signal 4: Reference tracking
        finding_refs = session_context.get('finding_references', 0)
        reference_ratio = finding_refs / max(findings_count, 1)
        signals['reference_coverage'] = reference_ratio

        # Signal 5: Breadcrumb loading penalty
        breadcrumbs_loaded = session_context.get('breadcrumbs_loaded', False)
        if not breadcrumbs_loaded:
            signals['loading_penalty'] = -0.3
        else:
            signals['loading_penalty'] = 0.0

        # Weighted combination
        expected_know = (
            0.3 * signals['historical'] +
            0.2 * signals['artifacts'] +
            0.2 * signals['git_freshness'] +
            0.3 * signals['reference_coverage']
        ) + signals['loading_penalty']

        expected_know = max(0.1, min(expected_know, 1.0))

        return {
            'expected_know': expected_know,
            'signals': signals,
            'confidence': self._calculate_signal_confidence(signals)
        }

    def _calculate_signal_confidence(self, signals: Dict) -> float:
        """Calculate confidence in expected knowledge estimate."""
        # Higher confidence if more signals available
        available_signals = sum(1 for k, v in signals.items()
                               if k != 'loading_penalty' and v > 0)
        return min(available_signals / 4.0, 1.0)

    def _determine_enforcement(self, gaps: List[MemoryGap]) -> Dict[str, Any]:
        """
        Determine enforcement level per gap based on policy.
        """
        enforcement = {}

        for gap in gaps:
            gap_type = gap.gap_type

            # Get specific policy for this gap type, or use default
            scope_policy = self.policy.get('scope', {})
            level = scope_policy.get(gap_type, self.policy.get('enforcement', 'inform'))

            enforcement[gap_type] = {
                'level': level,
                'should_adjust_vectors': level == 'strict',
                'should_block': level == 'block',
                'should_warn': level in ['warn', 'strict', 'block'],
                'gap_id': gap.gap_id
            }

        return enforcement

    def _suggest_actions(
        self,
        gaps: List[MemoryGap],
        enforcement: Dict[str, Any]
    ) -> List[str]:
        """Suggest actions to resolve gaps."""
        actions = []

        for gap in gaps:
            enf = enforcement.get(gap.gap_type, {})
            level = enf.get('level', 'inform')

            if level in ['block', 'strict']:
                actions.append(f"[REQUIRED] {gap.resolution_action}")
            elif level == 'warn':
                actions.append(f"[RECOMMENDED] {gap.resolution_action}")
            else:  # inform
                actions.append(f"[OPTIONAL] {gap.resolution_action}")

        return actions

    def apply_enforcement(
        self,
        gap_report: MemoryGapReport,
        vectors: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Apply enforcement policy to vectors and responses.

        Returns:
            {
                'ok': bool,
                'vectors': dict (possibly adjusted),
                'warnings': list,
                'corrections': dict,
                'required_actions': list
            }
        """
        result = {
            'ok': True,
            'vectors': vectors.copy(),
            'warnings': [],
            'corrections': {},
            'required_actions': []
        }

        for gap in gap_report.gaps:
            enforcement = gap_report.enforcement.get(gap.gap_type, {})

            # Block level: prevent proceeding
            if enforcement.get('should_block'):
                result['ok'] = False
                result['safe_to_proceed'] = False
                result['required_actions'].append(gap.resolution_action)
                logger.warning(f"Memory gap blocking: {gap.content}")

            # Strict level: adjust vectors to realistic
            elif enforcement.get('should_adjust_vectors'):
                if gap.affects_vector and gap.realistic_value is not None:
                    vector_name = gap.affects_vector
                    claimed = vectors.get(vector_name, 0.5)
                    realistic = gap.realistic_value

                    result['vectors'][vector_name] = realistic
                    result['corrections'][vector_name] = {
                        'claimed': claimed,
                        'adjusted': realistic,
                        'reason': gap.content,
                        'gap_score': gap.gap_score
                    }
                    logger.info(f"Vector adjusted: {vector_name} {claimed:.2f} → {realistic:.2f}")

                elif gap.gap_type == 'confabulation':
                    # Overall confabulation: adjust KNOW to realistic
                    result['vectors']['know'] = gap.realistic_value
                    result['corrections']['know'] = {
                        'claimed': gap_report.claimed_know,
                        'adjusted': gap_report.expected_know,
                        'reason': 'Confabulation detected',
                        'gap_score': gap_report.overall_gap
                    }

            # Warn level: add warnings
            elif enforcement.get('should_warn'):
                result['warnings'].append({
                    'type': gap.gap_type,
                    'severity': gap.severity,
                    'message': gap.content,
                    'gap_score': gap.gap_score,
                    'recommendation': gap.resolution_action
                })

        return result

    # Helper methods for checking references/incorporation

    def _referenced_in_session(self, finding_id: str, session_context: Dict) -> bool:
        """Check if finding was referenced in current session."""
        # TODO: Implement actual reference tracking
        # For now, check if finding_id appears in session reasoning
        referenced_ids = session_context.get('referenced_finding_ids', [])
        return finding_id in referenced_ids

    def _incorporated_in_session(self, unknown: Dict, session_context: Dict) -> bool:
        """Check if resolved unknown was incorporated."""
        # TODO: Implement actual incorporation tracking
        # For now, check if unknown content appears in session
        incorporated_ids = session_context.get('incorporated_unknown_ids', [])
        return unknown.get('id') in incorporated_ids

    def _mentioned_in_session(self, file_path: str, session_context: Dict) -> bool:
        """Check if file was mentioned in session."""
        # TODO: Implement actual mention tracking
        # For now, check if file appears in session messages
        mentioned_files = session_context.get('mentioned_files', [])
        return file_path in mentioned_files
