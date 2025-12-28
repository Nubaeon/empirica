#!/usr/bin/env python3
"""
Epistemic Artifact Deprecation System

Implements N-step recursive loading with time decay, impact weighting,
and relevance scoring to prevent bootstrap bloat at scale.

Key insight: Not all findings are equally relevant. Recent high-impact
findings should be prioritized, while old low-impact findings fade.
"""

import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class FindingsDeprecationEngine:
    """Calculate relevance scores and filter findings by depth."""
    
    # Deprecation constants
    TIME_DECAY_HALF_LIFE = 30  # days - half-life for time decay
    COMPLETION_PENALTY = 0.3   # completed goals reduced by 30%
    DELTA_BOOST_FACTOR = 0.2   # execution state delta boost
    
    # Tier thresholds
    TIER_THRESHOLDS = {
        "minimal": 0.80,    # Only high relevance (Tier 0)
        "moderate": 0.60,   # Recent context (Tiers 0-1)
        "full": 0.40,       # Extended history (Tiers 0-2)
        "complete": 0.0     # All findings (Tiers 0-3+)
    }
    
    @staticmethod
    def calculate_time_decay(created_timestamp) -> float:
        """
        Calculate time decay factor using exponential decay.
        
        Half-life: 30 days
        At 30 days: score = 0.5
        At 60 days: score = 0.25
        At 90 days: score = 0.125
        
        Args:
            created_timestamp: Unix timestamp (float or string) of finding creation
            
        Returns:
            Float 0.0-1.0, where 1.0 = just created, 0.0 = very old
        """
        # Handle string timestamps
        if isinstance(created_timestamp, str):
            try:
                created_timestamp = float(created_timestamp)
            except (ValueError, TypeError):
                # If can't parse, assume recent (score = 0.5)
                return 0.5
        
        now = datetime.now().timestamp()
        age_seconds = now - created_timestamp
        age_days = age_seconds / 86400
        
        # Exponential decay: e^(-age / half_life)
        decay = math.exp(-age_days / FindingsDeprecationEngine.TIME_DECAY_HALF_LIFE)
        return max(0.0, min(1.0, decay))
    
    @staticmethod
    def calculate_completion_factor(goal_completion: Optional[float]) -> float:
        """
        Calculate completion penalty factor.
        
        Completed goals (completion=1.0) reduce by 30%
        In-progress goals (completion=0.0) full weight
        
        Args:
            goal_completion: Goal completion percentage 0.0-1.0 or None
            
        Returns:
            Multiplication factor 0.7-1.0
        """
        if goal_completion is None:
            return 1.0
        
        # 1.0 - (completion * 0.3)
        # completion=0: factor=1.0
        # completion=1: factor=0.7
        return max(0.7, 1.0 - (goal_completion * FindingsDeprecationEngine.COMPLETION_PENALTY))
    
    @staticmethod
    def calculate_relevance_score(
        finding: Dict,
        current_task: Optional[str] = None,
        execution_state_delta: float = 0.0,
        goal_completion: Optional[float] = None
    ) -> float:
        """
        Calculate 0.0-1.0 relevance score for a finding.
        
        Factors:
        - 40% time decay (newer = higher)
        - 30% impact weight * completion factor
        - 20% execution state delta (learning boost)
        - 10% task semantic similarity (future enhancement)
        
        Args:
            finding: Finding dict with 'created_timestamp', 'impact'
            current_task: Optional current task description
            execution_state_delta: State improvement in current session
            goal_completion: Goal completion percentage if applicable
            
        Returns:
            Float 0.0-1.0 relevance score
        """
        # Component 1: Time decay (40%)
        created_ts = finding.get('created_timestamp')
        if not created_ts:
            time_score = 0.5
        else:
            time_score = FindingsDeprecationEngine.calculate_time_decay(created_ts)
        
        # Component 2: Impact weight * completion factor (30%)
        impact = finding.get('impact')
        if impact is None:
            impact = 0.5  # Default for NULL values
        
        completion_factor = FindingsDeprecationEngine.calculate_completion_factor(goal_completion)
        impact_score = impact * completion_factor
        
        # Component 3: Execution state delta (20%)
        # Boost relevance if there's significant learning happening
        delta_score = 1.0 + (execution_state_delta * FindingsDeprecationEngine.DELTA_BOOST_FACTOR)
        delta_score = max(0.8, min(1.2, delta_score))  # Clamp 0.8-1.2
        
        # Component 4: Task semantic match (10%)
        # TODO: Implement semantic similarity when task_description provided
        task_match = 0.5  # Default neutral
        
        # Weighted combination
        relevance = (
            0.40 * time_score +
            0.30 * impact_score +
            0.20 * delta_score +
            0.10 * task_match
        )
        
        return max(0.0, min(1.0, relevance))
    
    @staticmethod
    def filter_by_depth(
        findings: List[Dict],
        depth: str = "auto",
        relevance_scores: Optional[List[float]] = None,
        uncertainty: float = 0.5
    ) -> List[Dict]:
        """
        Filter findings by depth tier and relevance threshold.
        
        Depth options:
        - "minimal": Only high-relevance (threshold 0.80)
        - "moderate": Recent context (threshold 0.60)
        - "full": Extended history (threshold 0.40)
        - "complete": All findings (threshold 0.0)
        - "auto": Based on uncertainty
            * uncertainty > 0.5: "full" (need context)
            * 0.3 < uncertainty <= 0.5: "moderate"
            * uncertainty <= 0.3: "minimal" (confident, focused)
        
        Args:
            findings: List of finding dicts
            depth: Depth level string
            relevance_scores: Pre-calculated scores (else calculate)
            uncertainty: Current epistemic uncertainty 0.0-1.0
            
        Returns:
            Filtered list of findings
        """
        if not findings:
            return []
        
        # Calculate scores if not provided
        if relevance_scores is None:
            relevance_scores = [
                FindingsDeprecationEngine.calculate_relevance_score(f)
                for f in findings
            ]
        
        # Determine actual depth
        if depth == "auto":
            if uncertainty > 0.5:
                depth = "full"
            elif uncertainty > 0.3:
                depth = "moderate"
            else:
                depth = "minimal"
        
        # Get threshold
        threshold = FindingsDeprecationEngine.TIER_THRESHOLDS.get(depth, 0.0)
        
        # Filter by threshold
        filtered = [
            finding for finding, score in zip(findings, relevance_scores)
            if score >= threshold
        ]
        
        logger.info(
            f"Filtered findings: {len(filtered)}/{len(findings)} "
            f"(depth={depth}, threshold={threshold:.2f})"
        )
        
        return filtered
    
    @staticmethod
    def get_findings_summary(
        findings: List[Dict],
        relevance_scores: Optional[List[float]] = None
    ) -> Dict:
        """
        Generate summary statistics about findings relevance distribution.
        
        Returns:
            Dict with count, avg_relevance, tier_distribution
        """
        if not findings:
            return {
                "total": 0,
                "loaded": 0,
                "avg_relevance": 0.0,
                "tier_distribution": {}
            }
        
        if relevance_scores is None:
            relevance_scores = [
                FindingsDeprecationEngine.calculate_relevance_score(f)
                for f in findings
            ]
        
        # Count by tier
        tiers = {
            "Tier 0 (high)": sum(1 for s in relevance_scores if s >= 0.80),
            "Tier 1 (medium)": sum(1 for s in relevance_scores if 0.60 <= s < 0.80),
            "Tier 2 (low)": sum(1 for s in relevance_scores if 0.40 <= s < 0.60),
            "Tier 3+ (archive)": sum(1 for s in relevance_scores if s < 0.40),
        }
        
        return {
            "total": len(findings),
            "loaded": len(findings),
            "avg_relevance": sum(relevance_scores) / len(relevance_scores),
            "tier_distribution": tiers
        }


def calculate_vector_based_impact(session_id: str, db_connection) -> float:
    """
    Calculate impact based on PREFLIGHT→POSTFLIGHT deltas.
    
    Reflects actual learning in the session:
    - High state delta (execution improvement) = high impact
    - High completion delta = high impact
    - Low deltas = lower impact
    
    Formula: impact = 0.3 + (0.5 * state_delta) + (0.2 * completion_delta)
    Range: 0.3 (no learning) to 1.0 (max learning)
    
    Args:
        session_id: Session identifier
        db_connection: Database connection
        
    Returns:
        Float 0.3-1.0 impact score, or None if no PREFLIGHT/POSTFLIGHT
    """
    cursor = db_connection.cursor()
    
    # Get PREFLIGHT and POSTFLIGHT states
    cursor.execute("""
        SELECT 
            MAX(CASE WHEN phase='PREFLIGHT' THEN state END) as preflight_state,
            MAX(CASE WHEN phase='POSTFLIGHT' THEN state END) as postflight_state,
            MAX(CASE WHEN phase='PREFLIGHT' THEN completion END) as preflight_completion,
            MAX(CASE WHEN phase='POSTFLIGHT' THEN completion END) as postflight_completion
        FROM reflexes
        WHERE session_id = ? AND phase IN ('PREFLIGHT', 'POSTFLIGHT')
    """, (session_id,))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    pf_state, post_state, pf_completion, post_completion = row
    
    # Check if we have both PREFLIGHT and POSTFLIGHT
    if pf_state is None or post_state is None:
        return None
    
    # Calculate deltas
    state_delta = max(0.0, post_state - pf_state)  # Can't be negative
    
    # Handle completion - use POSTFLIGHT if available, else PREFLIGHT
    completion_delta = 0.0
    if post_completion is not None and pf_completion is not None:
        completion_delta = max(0.0, post_completion - pf_completion)
    elif post_completion is not None:
        completion_delta = max(0.0, post_completion - 0.2)  # Assume 0.2 starting
    
    # Calculate impact: 0.3 (baseline) + learning deltas
    impact = 0.3 + (0.5 * state_delta) + (0.2 * completion_delta)
    
    # Clamp to 0.3-1.0
    impact = max(0.3, min(1.0, impact))
    
    logger.debug(
        f"Vector-based impact for session {session_id[:8]}: "
        f"state_delta={state_delta:.2f}, completion_delta={completion_delta:.2f}, "
        f"impact={impact:.2f}"
    )
    
    return impact


def backfill_null_impact_values_hybrid(
    db_connection,
    project_id: str,
    use_vectors: bool = True
) -> Dict[str, int]:
    """
    Backfill NULL impact values using hybrid strategy.
    
    Strategy:
    1. For findings WITH session_id: use vector-based scoring (PREFLIGHT→POSTFLIGHT deltas)
    2. For findings WITHOUT session_id: use heuristic (0.5 default)
    3. Apply age decay adjustment to all
    
    Args:
        db_connection: Database connection
        project_id: Project ID to backfill
        use_vectors: If True, use vector-based scoring where possible
        
    Returns:
        Dict with counts: {"vector_based": N, "heuristic": N, "total": N}
    """
    cursor = db_connection.cursor()
    
    # Step 1: Get all NULL impact findings with session info
    cursor.execute("""
        SELECT id, session_id, created_timestamp
        FROM project_findings
        WHERE project_id = ? AND impact IS NULL
        ORDER BY created_timestamp DESC
    """, (project_id,))
    
    findings = cursor.fetchall()
    
    vector_based_count = 0
    heuristic_count = 0
    
    logger.info(f"Backfilling {len(findings)} NULL impact values...")
    
    for finding_id, session_id, created_ts in findings:
        impact = None
        
        # Try vector-based scoring if session_id available
        if use_vectors and session_id:
            impact = calculate_vector_based_impact(session_id, db_connection)
            if impact is not None:
                vector_based_count += 1
                logger.debug(f"  Finding {finding_id[:8]}: vector-based impact={impact:.2f}")
            else:
                # Fall back to heuristic
                impact = 0.5
                heuristic_count += 1
                logger.debug(f"  Finding {finding_id[:8]}: heuristic (no session deltas)")
        else:
            # Use heuristic
            impact = 0.5
            heuristic_count += 1
        
        # Update the finding
        cursor.execute("""
            UPDATE project_findings
            SET impact = ?
            WHERE id = ?
        """, (impact, finding_id))
    
    db_connection.commit()
    
    total = vector_based_count + heuristic_count
    logger.info(
        f"Backfill complete: {vector_based_count} vector-based, "
        f"{heuristic_count} heuristic, total {total}"
    )
    
    return {
        "vector_based": vector_based_count,
        "heuristic": heuristic_count,
        "total": total
    }
