#!/usr/bin/env python3
"""
Empirica Statusline - Multi-AI Architecture

Displays Empirica session state per AI agent using MCO (Meta-Agent Configuration Object).
Each AI queries only its own epistemic state, determined by:
  1. EMPIRICA_AI_ID environment variable (if set)
  2. System prompt AI_ID declaration (fallback)

Supports 4 display modes: minimal, balanced, learning-focused, full

Configuration:
  Set EMPIRICA_STATUS_MODE environment variable:
  - minimal: Just session status, goal progress, phase
  - balanced: Adds warnings and key learning deltas (DEFAULT)
  - learning: Focus on epistemic vector changes and drift
  - full: Everything (identity, vectors, deltas, scope, checkpoints)

Usage:
  python statusline_empirica.py                    # Uses EMPIRICA_AI_ID or default
  EMPIRICA_AI_ID=claude-code python statusline_empirica.py    # Show Claude Code's state
  EMPIRICA_AI_ID=claude-sonnet python statusline_empirica.py  # Show Sonnet's state
  EMPIRICA_AI_ID=qwen-code python statusline_empirica.py      # Show Qwen's state

Author: Claude Code (Multi-AI Version)
Date: 2025-12-04
Version: 2.0.0 (MCO-Based Multi-AI)
"""

import os
import sys
import json
from pathlib import Path

# Add empirica to path
EMPIRICA_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(EMPIRICA_ROOT))

from empirica.config.path_resolver import get_session_db_path, get_empirica_root
from empirica.data.session_database import SessionDatabase

# Import drift monitor
try:
    from empirica.core.drift.mirror_drift_monitor import MirrorDriftMonitor
    DRIFT_AVAILABLE = True
except ImportError:
    DRIFT_AVAILABLE = False


# ANSI color codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'

    # Status colors
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    GRAY = '\033[90m'

    # Bright variants
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_CYAN = '\033[96m'


def get_my_ai_id() -> str:
    """
    Determine which AI is running this statusline.

    Priority:
    1. EMPIRICA_AI_ID environment variable (explicit override)
    2. Fallback to 'claude-code' (legacy compatibility)
    3. Return 'unknown' if all else fails

    MCO Configuration Note:
    Each AI should declare AI_ID in their system prompt (Section I).
    This function checks environment first for flexibility.
    """
    ai_id = os.getenv('EMPIRICA_AI_ID', '').strip()
    if ai_id:
        return ai_id

    # Fallback: try 'claude-code' (legacy)
    return 'claude-code'


def get_latest_active_session(db: SessionDatabase, ai_id: str = None) -> dict:
    """
    Get the active session for a specific AI agent.

    Args:
        db: SessionDatabase instance
        ai_id: AI identifier (defaults to current AI)

    Returns:
        Session dict with session_id, ai_id, start_time, or None

    MCO Integration:
    Each AI queries only its own sessions (filtered by ai_id).
    This ensures per-AI epistemic state tracking.
    """
    if not ai_id:
        ai_id = get_my_ai_id()

    cursor = db.conn.cursor()

    # Query active sessions for THIS AI specifically
    # (not all AIs, not hardcoded claude-code priority)
    cursor.execute("""
        SELECT session_id, ai_id, start_time
        FROM sessions
        WHERE end_time IS NULL
        AND ai_id = ?
        ORDER BY start_time DESC
        LIMIT 1
    """, (ai_id,))
    row = cursor.fetchone()
    if row:
        return dict(row)

    # No active session found for this AI
    return None


def get_session_goals(db: SessionDatabase, session_id: str) -> list:
    """Get goals for a session (placeholder - goals are in git notes)."""
    # TODO: Query git notes for goals
    # For now, return empty list
    return []


def get_latest_vectors(db: SessionDatabase, session_id: str) -> dict:
    """
    Get the most recent epistemic vectors for a session.

    MCO Integration: Filters by session_id to ensure per-AI epistemic state tracking.
    """
    cursor = db.conn.cursor()

    # Query uses timestamp column from reflexes table schema
    # The reflexes table stores phase, vectors, and assessment timestamp
    cursor.execute("""
        SELECT phase, engagement, know, do, context,
               clarity, coherence, signal, density,
               state, change, completion, impact, uncertainty
        FROM reflexes
        WHERE session_id = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (session_id,))
    row = cursor.fetchone()
    if row:
        return {
            'type': row[0],
            'vectors': {
                'engagement': row[1],
                'know': row[2],
                'do': row[3],
                'context': row[4],
                'clarity': row[5],
                'coherence': row[6],
                'signal': row[7],
                'density': row[8],
                'state': row[9],
                'change': row[10],
                'completion': row[11],
                'impact': row[12],
                'uncertainty': row[13]
            }
        }
    return None


def calculate_deltas(db: SessionDatabase, session_id: str) -> dict:
    """
    Calculate epistemic deltas from PREFLIGHT to latest assessment.

    MCO Integration: Calculates per-session learning progression.
    """
    cursor = db.conn.cursor()

    # Get PREFLIGHT vectors (earliest PREFLIGHT assessment)
    cursor.execute("""
        SELECT engagement, know, do, context,
               clarity, coherence, signal, density,
               state, change, completion, impact, uncertainty
        FROM reflexes
        WHERE session_id = ? AND phase = 'PREFLIGHT'
        ORDER BY timestamp ASC
        LIMIT 1
    """, (session_id,))
    preflight_row = cursor.fetchone()

    # Get latest vectors (most recent assessment, any phase)
    cursor.execute("""
        SELECT engagement, know, do, context,
               clarity, coherence, signal, density,
               state, change, completion, impact, uncertainty
        FROM reflexes
        WHERE session_id = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (session_id,))
    latest_row = cursor.fetchone()

    if not preflight_row or not latest_row:
        return {}

    vector_names = ['engagement', 'know', 'do', 'context', 'clarity', 'coherence',
                     'signal', 'density', 'state', 'change', 'completion', 'impact', 'uncertainty']

    deltas = {}
    for i, name in enumerate(vector_names):
        delta = latest_row[i] - preflight_row[i]
        if abs(delta) > 0.1:  # Only significant changes
            deltas[name] = delta

    return deltas


def get_drift_status(db: SessionDatabase, session_id: str, current_vectors: dict) -> dict:
    """Get drift monitoring status."""
    if not DRIFT_AVAILABLE or not current_vectors:
        return None

    try:
        # Create simple assessment object
        from types import SimpleNamespace
        assessment = SimpleNamespace(vectors=current_vectors)

        # Initialize drift monitor
        monitor = MirrorDriftMonitor(drift_threshold=0.2, lookback_window=5)

        # Detect drift
        report = monitor.detect_drift(assessment, session_id)

        if report.drift_detected:
            return {
                'severity': report.severity,
                'action': report.recommended_action,
                'drifted_vectors': report.drifted_vectors,
                'checkpoints_analyzed': report.checkpoints_analyzed
            }
    except Exception as e:
        # Fail gracefully
        pass

    return None


def calculate_progress_velocity(db: SessionDatabase, session_id: str) -> dict:
    """
    Calculate progress velocity (tasks/hour) with trend analysis.

    Returns:
        {
            'velocity': float,            # Tasks per hour
            'trend': str,                 # 'accelerating', 'steady', 'slowing', 'insufficient_data'
            'quality': str,               # 'with_evidence', 'rushing', 'unknown'
            'recent_completions': int,    # Number of completions analyzed
            'time_span_hours': float      # Time span of analysis window
        }
    """
    try:
        cursor = db.conn.cursor()

        # Query all completed subtasks for this session (across all goals)
        cursor.execute("""
            SELECT s.completed_timestamp, s.completion_evidence
            FROM subtasks s
            JOIN goals g ON s.goal_id = g.id
            WHERE g.session_id = ?
            AND s.status = 'completed'
            AND s.completed_timestamp IS NOT NULL
            ORDER BY s.completed_timestamp DESC
            LIMIT 20
        """, (session_id,))

        rows = cursor.fetchall()

        if len(rows) < 2:
            # Insufficient data for velocity calculation
            return {
                'velocity': 0.0,
                'trend': 'insufficient_data',
                'quality': 'unknown',
                'recent_completions': len(rows),
                'time_span_hours': 0.0
            }

        # Get timestamps and evidence
        timestamps = [row[0] for row in rows]
        has_evidence = [bool(row[1]) for row in rows]

        # Calculate velocity for recent window (last 10 completions)
        recent_window = min(10, len(timestamps))
        recent_timestamps = timestamps[:recent_window]

        if len(recent_timestamps) < 2:
            return {
                'velocity': 0.0,
                'trend': 'insufficient_data',
                'quality': 'unknown',
                'recent_completions': len(rows),
                'time_span_hours': 0.0
            }

        # Time span (in hours)
        time_span_seconds = recent_timestamps[0] - recent_timestamps[-1]
        time_span_hours = time_span_seconds / 3600.0

        # Velocity = tasks / hour
        # Handle edge case: if span is very small (< 10 seconds), don't compute velocity
        if time_span_seconds < 10:
            # Tasks completed too fast - not meaningful velocity
            return {
                'velocity': 0.0,
                'trend': 'insufficient_data',
                'quality': 'unknown',
                'recent_completions': len(rows),
                'time_span_hours': time_span_hours
            }

        if time_span_hours > 0:
            velocity = (len(recent_timestamps) - 1) / time_span_hours
        else:
            velocity = 0.0

        # Trend analysis: compare first half vs second half of window
        if len(recent_timestamps) >= 6:
            mid = len(recent_timestamps) // 2
            first_half = recent_timestamps[:mid]
            second_half = recent_timestamps[mid:]

            # Calculate velocity for each half
            first_span = (first_half[0] - first_half[-1]) / 3600.0
            second_span = (second_half[0] - second_half[-1]) / 3600.0

            if first_span > 0 and second_span > 0:
                first_velocity = (len(first_half) - 1) / first_span
                second_velocity = (len(second_half) - 1) / second_span

                # Compare velocities (20% threshold for trend detection)
                if first_velocity > second_velocity * 1.2:
                    trend = 'accelerating'
                elif second_velocity > first_velocity * 1.2:
                    trend = 'slowing'
                else:
                    trend = 'steady'
            else:
                trend = 'steady'
        else:
            trend = 'steady'

        # Quality check: Are completions backed by evidence?
        recent_evidence = has_evidence[:recent_window]
        evidence_ratio = sum(recent_evidence) / len(recent_evidence) if recent_evidence else 0

        if velocity > 2.0 and evidence_ratio < 0.5:
            quality = 'rushing'  # High velocity but low evidence
        elif evidence_ratio > 0.6:
            quality = 'with_evidence'  # Good quality
        else:
            quality = 'unknown'

        return {
            'velocity': velocity,
            'trend': trend,
            'quality': quality,
            'recent_completions': len(rows),
            'time_span_hours': time_span_hours,
            'evidence_ratio': evidence_ratio
        }

    except Exception as e:
        # Fail gracefully
        return {
            'velocity': 0.0,
            'trend': 'error',
            'quality': 'unknown',
            'recent_completions': 0,
            'time_span_hours': 0.0
        }


def calculate_cognitive_load(db: SessionDatabase, session_id: str, current_vectors: dict, ai_id: str = None) -> dict:
    """
    Calculate cognitive load based on DENSITY trajectory and feedback loop config.

    Uses actual DENSITY epistemic vector measurement via feedback_loops.yaml config,
    NOT heuristics. Falls back to sensible defaults if config unavailable.

    Args:
        db: SessionDatabase instance
        session_id: Session identifier
        current_vectors: Current epistemic vectors dict
        ai_id: AI agent identifier (used to load agent-specific thresholds)

    Returns:
        {
            'load_level': str,           # 'sustainable', 'high', 'overwhelmed'
            'density': float,            # Current density value
            'density_trend': str,        # 'increasing', 'stable', 'decreasing'
            'time_since_checkpoint': float,  # Hours since last checkpoint
            'checkpoint_recommended': bool,  # Should checkpoint soon?
            'ai_id': str,                # Agent this assessment is for
            'config_source': str         # 'feedback_loops' or 'defaults'
        }
    """
    try:
        # Try to load feedback loops config for agent-specific thresholds
        try:
            from empirica.cli.command_handlers.decision_utils import evaluate_cognitive_load as evaluate_load_from_config
            load_assessment = evaluate_load_from_config(
                current_vectors.get('density', 0.5) if current_vectors else 0.5,
                ai_id=ai_id
            )
            config_source = 'feedback_loops'
            load_level = load_assessment['level']
            checkpoint_recommended = load_assessment['checkpoint_recommended']
        except Exception as e:
            # Fallback: use defaults if config loading fails
            config_source = 'defaults'
            current_density = current_vectors.get('density', 0.5) if current_vectors else 0.5

            # Default thresholds (from feedback_loops.yaml global defaults)
            if current_density > 0.9:
                load_level = 'overwhelmed'
                checkpoint_recommended = True
            elif current_density > 0.75:
                load_level = 'high'
                checkpoint_recommended = True
            elif current_density > 0.6:
                load_level = 'sustainable'
                checkpoint_recommended = False
            else:
                load_level = 'sustainable'
                checkpoint_recommended = False

        cursor = db.conn.cursor()

        # Get recent DENSITY values to detect trend
        cursor.execute("""
            SELECT density, timestamp
            FROM reflexes
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT 5
        """, (session_id,))

        rows = cursor.fetchall()

        if not rows:
            return {
                'load_level': 'unknown',
                'density': 0.0,
                'density_trend': 'unknown',
                'time_since_checkpoint': 0.0,
                'checkpoint_recommended': False,
                'ai_id': ai_id,
                'config_source': config_source
            }

        # Current density (use provided vectors or latest from DB)
        current_density = current_vectors.get('density', rows[0][0]) if current_vectors else rows[0][0]

        # Density trend analysis (3-point trajectory)
        if len(rows) >= 3:
            recent_densities = [row[0] for row in rows[:3]]
            if recent_densities[0] > recent_densities[-1] * 1.2:
                density_trend = 'increasing'
            elif recent_densities[-1] > recent_densities[0] * 1.2:
                density_trend = 'decreasing'
            else:
                density_trend = 'stable'
        else:
            density_trend = 'stable'

        # Time since last checkpoint (uses latest assessment time as proxy)
        import time
        latest_assessment_time = rows[0][1]
        time_since_checkpoint = (time.time() - latest_assessment_time) / 3600.0  # hours

        return {
            'load_level': load_level,
            'density': current_density,
            'density_trend': density_trend,
            'time_since_checkpoint': time_since_checkpoint,
            'checkpoint_recommended': checkpoint_recommended,
            'ai_id': ai_id,
            'config_source': config_source
        }

    except Exception as e:
        return {
            'load_level': 'error',
            'density': 0.0,
            'density_trend': 'unknown',
            'time_since_checkpoint': 0.0,
            'checkpoint_recommended': False,
            'ai_id': ai_id,
            'config_source': 'error'
        }


def calculate_scope_stability(db: SessionDatabase, session_id: str) -> dict:
    """
    Calculate scope stability by monitoring breadth changes over time.

    Returns:
        {
            'stability': str,          # 'focused', 'expanding', 'creeping', 'runaway'
            'breadth_current': float,  # Current scope breadth
            'breadth_change': float,   # Change from initial breadth
            'goal_count': int,         # Number of goals
            'new_goals_added': int     # Goals added after initial
        }
    """
    try:
        cursor = db.conn.cursor()

        # Get all goals for this session ordered by creation time
        cursor.execute("""
            SELECT goal_data
            FROM goals
            WHERE session_id = ?
            ORDER BY created_timestamp ASC
        """, (session_id,))

        rows = cursor.fetchall()

        if not rows:
            return {
                'stability': 'unknown',
                'breadth_current': 0.0,
                'breadth_change': 0.0,
                'goal_count': 0,
                'new_goals_added': 0
            }

        import json
        goals = [json.loads(row[0]) for row in rows]

        # Get breadth values from scope
        breadths = []
        for goal in goals:
            scope = goal.get('scope', {})
            breadth = scope.get('breadth', 0.5)
            breadths.append(breadth)

        if not breadths:
            return {
                'stability': 'unknown',
                'breadth_current': 0.0,
                'breadth_change': 0.0,
                'goal_count': 0,
                'new_goals_added': 0
            }

        # Current and initial breadth
        initial_breadth = breadths[0]
        current_breadth = breadths[-1]
        breadth_change = current_breadth - initial_breadth

        goal_count = len(goals)
        new_goals_added = max(0, goal_count - 1)

        # Determine stability
        if goal_count == 1:
            # Single goal - check if breadth is expanding within the goal
            if current_breadth <= 0.4:
                stability = 'focused'
            else:
                stability = 'expanding'
        elif new_goals_added > 0:
            # Multiple goals - deliberate expansion
            if breadth_change > 0.2:
                stability = 'expanding'  # Deliberate, documented expansion
            else:
                stability = 'focused'  # Multiple focused goals
        else:
            # Single goal with changing breadth = scope creep
            if breadth_change > 0.3:
                stability = 'runaway'  # Severe creep
            elif breadth_change > 0.15:
                stability = 'creeping'  # Gradual creep
            else:
                stability = 'focused'

        return {
            'stability': stability,
            'breadth_current': current_breadth,
            'breadth_change': breadth_change,
            'goal_count': goal_count,
            'new_goals_added': new_goals_added
        }

    except Exception as e:
        return {
            'stability': 'error',
            'breadth_current': 0.0,
            'breadth_change': 0.0,
            'goal_count': 0,
            'new_goals_added': 0
        }


def classify_drift_pattern(drift_status: dict, vectors: dict, deltas: dict) -> tuple:
    """
    Classify drift pattern using multi-vector analysis.

    Returns: (warning_type, value, severity, context)
    """
    if not drift_status:
        return None

    drifted = drift_status.get('drifted_vectors', [])
    if not drifted:
        return None

    worst = max(drifted, key=lambda x: x.get('drop', 0))
    drop_amount = worst.get('drop', 0)
    vector_name = worst.get('vector', 'UNKNOWN')

    # Multi-vector pattern analysis
    clarity_delta = deltas.get('clarity', 0)
    context_delta = deltas.get('context', 0)
    know_delta = deltas.get('know', 0)

    # Pattern 1: TRUE DRIFT (memory loss)
    # KNOW↓ + CLARITY↓ + CONTEXT↓ = all declining together
    if vector_name == 'know' and clarity_delta < -0.1 and context_delta < -0.1:
        return ('TRUE_DRIFT', drop_amount, 'critical', 'memory_loss')

    # Pattern 2: LEARNING ABOUT IGNORANCE (healthy!)
    # KNOW↓ but CLARITY↑ = discovering complexity
    if vector_name == 'know' and clarity_delta > 0.1:
        return ('LEARNING', drop_amount, 'info', 'discovering_complexity')

    # Pattern 3: SCOPE CREEP (warning)
    # KNOW↓ + CONTEXT↓ but not critical
    if vector_name == 'know' and context_delta < -0.1:
        return ('SCOPE_DRIFT', drop_amount, 'warning', 'expanding_scope')

    # Pattern 4: CONTEXT LOSS (drift)
    # CONTEXT↓ or CLARITY↓ significantly
    if vector_name in ['context', 'clarity'] and drop_amount > 0.3:
        return ('TRUE_DRIFT', drop_amount, 'critical', 'context_loss')

    # Default: Generic drift
    return ('DRIFT', drop_amount, 'high', 'unknown_pattern')


def detect_warnings(vectors: dict, drift_status: dict = None, deltas: dict = None, cognitive_load: dict = None, scope_stability: dict = None) -> list:
    """Detect warning conditions from epistemic vectors, drift patterns, cognitive load, and scope stability."""
    warnings = []

    # Drift warnings with pattern classification (HIGHEST PRIORITY)
    if drift_status and deltas:
        drift_pattern = classify_drift_pattern(drift_status, vectors, deltas)
        if drift_pattern:
            warning_type, value, severity, context = drift_pattern
            warnings.append((warning_type, value, severity, context))

    # Cognitive load warnings (SECOND PRIORITY - can prevent drift!)
    if cognitive_load and not warnings:  # Only show if no drift warnings
        load_level = cognitive_load.get('load_level')
        if load_level == 'overwhelmed':
            density = cognitive_load.get('density', 0)
            warnings.append(('OVERWHELMED', density, 'critical', 'checkpoint_now'))
        elif load_level == 'high' and cognitive_load.get('checkpoint_recommended'):
            density = cognitive_load.get('density', 0)
            warnings.append(('HIGH_LOAD', density, 'high', 'checkpoint_soon'))

    # Scope stability warnings (THIRD PRIORITY)
    if scope_stability and not warnings:
        stability = scope_stability.get('stability')
        if stability == 'runaway':
            breadth = scope_stability.get('breadth_current', 0)
            warnings.append(('SCOPE_RUNAWAY', breadth, 'critical', 'refocus_needed'))
        elif stability == 'creeping':
            breadth = scope_stability.get('breadth_current', 0)
            warnings.append(('SCOPE_CREEP', breadth, 'high', 'consider_preflight'))

    # Vector warnings (only if no other warnings, to avoid clutter)
    if not warnings:
        if vectors.get('uncertainty', 0) > 0.7:
            warnings.append(('UNCERTAINTY', vectors['uncertainty'], 'high', 'investigate_needed'))

        if vectors.get('clarity', 1.0) < 0.4:
            warnings.append(('CLARITY', vectors['clarity'], 'low', 'requirements_unclear'))

        if vectors.get('know', 1.0) < 0.3:
            warnings.append(('KNOW', vectors['know'], 'low', 'domain_gap'))

    return warnings


def format_minimal(session: dict, goals: list, vectors: dict) -> str:
    """Minimal mode: status, progress, phase."""
    parts = [
        f"{Colors.GREEN}[empirica]{Colors.RESET}",
    ]

    if goals:
        parts.append(f"goal:{len([g for g in goals if g.get('completed')])}/{len(goals)}")

    if vectors:
        phase = vectors.get('type', 'UNKNOWN')
        parts.append(f"{Colors.BLUE}{phase}{Colors.RESET}")

    return " ".join(parts)


def format_balanced(session: dict, goals: list, vectors: dict, deltas: dict, warnings: list, drift_status: dict = None, velocity_data: dict = None) -> str:
    """Balanced mode: status, progress, phase, warnings, velocity, key delta."""
    parts = [
        f"{Colors.GREEN}[empirica]{Colors.RESET}",
    ]

    if goals:
        completed = len([g for g in goals if g.get('completed')])
        total = len(goals)
        parts.append(f"{completed}/{total}")

    if vectors:
        phase = vectors.get('type', 'UNKNOWN')
        parts.append(f"{Colors.BLUE}{phase}{Colors.RESET}")

    # Show warnings with pattern context (HIGHEST PRIORITY)
    if warnings:
        warning = warnings[0]  # Show first warning only
        if len(warning) == 4:  # New format with context
            name, value, severity, context = warning
        else:  # Old format (backwards compat)
            name, value, severity = warning
            context = None

        # Pattern-aware display
        if name == 'TRUE_DRIFT':
            parts.append(f"{Colors.RED}🔴 DRIFT:{value:.2f} [CHECK BREADCRUMBS!]{Colors.RESET}")
        elif name == 'LEARNING':
            parts.append(f"{Colors.BRIGHT_GREEN}✓ LEARNING:{value:.2f} [COMPLEXITY]{Colors.RESET}")
        elif name == 'SCOPE_DRIFT':
            parts.append(f"{Colors.YELLOW}⚠ SCOPE:{value:.2f} [CONSIDER PREFLIGHT]{Colors.RESET}")
        elif name == 'DRIFT':
            color = Colors.RED if severity == 'critical' else Colors.YELLOW
            parts.append(f"{color}🔴 DRIFT:{value:.2f} [INVESTIGATE]{Colors.RESET}")
        elif name == 'OVERWHELMED':
            parts.append(f"{Colors.RED}🔴 LOAD:{value:.2f} [CHECKPOINT NOW!]{Colors.RESET}")
        elif name == 'HIGH_LOAD':
            parts.append(f"{Colors.YELLOW}⚠️ LOAD:{value:.2f} [CHECKPOINT?]{Colors.RESET}")
        elif name == 'SCOPE_RUNAWAY':
            parts.append(f"{Colors.RED}🔴 SCOPE:{value:.2f} [REFOCUS!]{Colors.RESET}")
        elif name == 'SCOPE_CREEP':
            parts.append(f"{Colors.YELLOW}⚠️ SCOPE:{value:.2f} [PREFLIGHT?]{Colors.RESET}")
        else:
            color = Colors.RED if severity == 'critical' else Colors.YELLOW
            parts.append(f"{color}⚠ {name}:{value:.2f}{Colors.RESET}")

    # Show progress velocity (if no critical warnings)
    elif velocity_data and velocity_data['recent_completions'] >= 2:
        velocity = velocity_data['velocity']
        trend = velocity_data['trend']
        quality = velocity_data['quality']

        if trend == 'accelerating':
            parts.append(f"{Colors.BRIGHT_GREEN}↗️ VEL:{velocity:.1f}/hr{Colors.RESET}")
        elif trend == 'slowing':
            parts.append(f"{Colors.YELLOW}↘️ VEL:{velocity:.1f}/hr [STUCK?]{Colors.RESET}")
        elif quality == 'rushing':
            parts.append(f"{Colors.YELLOW}⚡ VEL:{velocity:.1f}/hr [NO EVIDENCE?]{Colors.RESET}")
        else:
            parts.append(f"→ VEL:{velocity:.1f}/hr")

    # Show top learning delta (skip if LEARNING pattern already shown)
    if deltas and (not warnings or warnings[0][0] != 'LEARNING'):
        top_delta = max(deltas.items(), key=lambda x: abs(x[1]))
        key, value = top_delta
        arrow = '↑' if value > 0 else '↓'
        color = Colors.BRIGHT_GREEN if value > 0 else Colors.GRAY
        parts.append(f"{color}{key.upper()}{arrow}{abs(value):.2f}{Colors.RESET}")

    return " │ ".join(parts)


def format_learning(session: dict, goals: list, vectors: dict, deltas: dict, warnings: list, drift_status: dict = None, velocity_data: dict = None) -> str:
    """Learning-focused mode: deltas, drift, and velocity."""
    parts = [
        f"{Colors.CYAN}[empirica]{Colors.RESET}",
    ]

    if vectors:
        phase = vectors.get('type', 'UNKNOWN')
        parts.append(f"{phase}")

    # Show drift first (critical for learning mode!)
    if drift_status:
        severity = drift_status.get('severity', 'none')
        if severity in ['critical', 'high', 'medium']:
            drifted = drift_status.get('drifted_vectors', [])
            if drifted:
                worst = max(drifted, key=lambda x: x.get('drop', 0))
                drop = worst.get('drop', 0)
                vector_name = worst.get('vector', 'UNKNOWN')
                color = Colors.RED if severity == 'critical' else Colors.YELLOW
                parts.append(f"{color}🔴DRIFT:{vector_name}↓{drop:.2f}{Colors.RESET}")

    # Show velocity (learning indicator)
    if velocity_data and velocity_data['recent_completions'] >= 2:
        velocity = velocity_data['velocity']
        trend = velocity_data['trend']
        if trend == 'accelerating':
            parts.append(f"{Colors.BRIGHT_GREEN}↗️{velocity:.1f}/hr{Colors.RESET}")
        elif trend == 'slowing':
            parts.append(f"{Colors.YELLOW}↘️{velocity:.1f}/hr{Colors.RESET}")
        else:
            parts.append(f"→{velocity:.1f}/hr")

    # Show all significant deltas
    if deltas:
        delta_strs = []
        for key, value in sorted(deltas.items(), key=lambda x: abs(x[1]), reverse=True)[:3]:
            arrow = '↑' if value > 0 else '↓'
            color = Colors.BRIGHT_GREEN if value > 0 else Colors.GRAY
            delta_strs.append(f"{color}{key.upper()[0]}{arrow}{abs(value):.2f}{Colors.RESET}")
        parts.append(" ".join(delta_strs))

    if goals:
        parts.append(f"goal:{len([g for g in goals if g.get('completed')])}/{len(goals)}")

    return " │ ".join(parts)


def format_full(session: dict, goals: list, vectors: dict, deltas: dict, warnings: list, velocity_data: dict = None) -> str:
    """Full visibility mode: everything."""
    parts = [
        f"{Colors.BRIGHT_CYAN}[empirica:{session['ai_id']}@{session['session_id'][:4]}]{Colors.RESET}",
    ]

    if goals:
        completed = len([g for g in goals if g.get('completed')])
        total = len(goals)
        parts.append(f"{completed}/{total}")

    if vectors:
        phase = vectors.get('type', 'UNKNOWN')
        parts.append(f"{Colors.BLUE}{phase}{Colors.RESET}")

        # Show key vectors with colors
        u = vectors.get('vectors', {}).get('uncertainty', 0)
        c = vectors.get('vectors', {}).get('clarity', 0)
        k = vectors.get('vectors', {}).get('know', 0)

        u_color = Colors.RED if u > 0.7 else Colors.YELLOW if u > 0.5 else Colors.GREEN
        c_color = Colors.RED if c < 0.4 else Colors.YELLOW if c < 0.6 else Colors.GREEN
        k_color = Colors.RED if k < 0.3 else Colors.YELLOW if k < 0.5 else Colors.GREEN

        parts.append(f"{u_color}U:{u:.2f}{Colors.RESET} {c_color}C:{c:.2f}{Colors.RESET} {k_color}K:{k:.2f}{Colors.RESET}")

    # Show velocity
    if velocity_data and velocity_data['recent_completions'] >= 2:
        velocity = velocity_data['velocity']
        trend = velocity_data['trend']
        quality = velocity_data['quality']

        trend_symbol = '↗️' if trend == 'accelerating' else '↘️' if trend == 'slowing' else '→'
        quality_indicator = '⚡' if quality == 'rushing' else '✓' if quality == 'with_evidence' else ''
        parts.append(f"{trend_symbol}{velocity:.1f}/hr{quality_indicator}")

    # Show deltas
    if deltas:
        delta_strs = []
        for key, value in sorted(deltas.items(), key=lambda x: abs(x[1]), reverse=True)[:2]:
            arrow = '↑' if value > 0 else '↓'
            delta_strs.append(f"{key.upper()[0]}{arrow}{abs(value):.2f}")
        parts.append(f"{Colors.CYAN}{' '.join(delta_strs)}{Colors.RESET}")

    # TODO: Add scope, checkpoint count
    # parts.append(f"scope[{scope['breadth']:.1f},{scope['duration']:.1f},{scope['coordination']:.1f}]")
    # parts.append(f"cp:{checkpoint_count}")

    return " │ ".join(parts)


def main():
    """Main statusline generation (MCO-Based Multi-AI)."""
    try:
        # Get mode from environment
        mode = os.getenv('EMPIRICA_STATUS_MODE', 'balanced').lower()

        # Determine which AI this is (MCO Configuration)
        ai_id = get_my_ai_id()

        # Get database
        db = SessionDatabase()

        # Get latest active session for THIS AI (not all AIs, not hardcoded)
        session = get_latest_active_session(db, ai_id=ai_id)

        if not session:
            # No active session for this AI
            print(f"{Colors.GRAY}[empirica:{ai_id}:inactive]{Colors.RESET}")
            return

        session_id = session['session_id']

        # Gather data
        goals = get_session_goals(db, session_id)
        vectors_data = get_latest_vectors(db, session_id)
        deltas = calculate_deltas(db, session_id)

        vectors = vectors_data.get('vectors', {}) if vectors_data else {}

        # Check for drift (CRITICAL for detecting context loss!)
        drift_status = get_drift_status(db, session_id, vectors)

        # Calculate progress velocity (Tier 1 metacognitive signal)
        velocity_data = calculate_progress_velocity(db, session_id)

        # Calculate cognitive load (Tier 1 metacognitive signal)
        # Pass ai_id for agent-specific feedback loop thresholds
        cognitive_load = calculate_cognitive_load(db, session_id, vectors, ai_id=ai_id)

        # Calculate scope stability (Tier 1 metacognitive signal)
        scope_stability = calculate_scope_stability(db, session_id)

        # Detect warnings with pattern analysis (all Tier 1 signals)
        warnings = detect_warnings(vectors, drift_status, deltas, cognitive_load, scope_stability)

        # Format based on mode
        if mode == 'minimal':
            output = format_minimal(session, goals, vectors_data)
        elif mode == 'learning':
            output = format_learning(session, goals, vectors_data, deltas, warnings, drift_status, velocity_data)
        elif mode == 'full':
            output = format_full(session, goals, vectors_data, deltas, warnings, velocity_data)
        else:  # balanced (default)
            output = format_balanced(session, goals, vectors_data, deltas, warnings, drift_status, velocity_data)

        print(output)

    except Exception as e:
        # Fail gracefully - don't break statusline
        print(f"{Colors.GRAY}[empirica:error]{Colors.RESET}")
        # Log error to file for debugging
        with open(get_empirica_root() / 'statusline.log', 'a') as f:
            f.write(f"ERROR: {e}\n")


if __name__ == '__main__':
    main()
