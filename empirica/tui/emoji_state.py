"""
Emoji State Engine (v0.6.0)

Computes functional emotive states from epistemic vectors per entity type.
These states represent the AI's relationship to an entity — not feelings,
but measured confidence rendered as an immediately readable visual.

States are entity-relative: a project's "confident" maps from different
vectors than a contact's "confident".

Used by: dashboard TUI, statusline, future mobile pixel renderer.

Pixel rendering: The emoji_state string maps to a 20x20 grid (100x100px
with 5x5 "pixels") that animates through transaction phases.
"""

from typing import Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# Functional emotive states
# ---------------------------------------------------------------------------

# Each state has: (name, description, pixel_char, color)
STATES = {
    'confident':    ('Confident',    'High knowledge, low uncertainty',      '😎', 'green'),
    'thinking':     ('Thinking',     'Active investigation, moderate know',  '🤔', 'cyan'),
    'uncertain':    ('Uncertain',    'Low knowledge, high uncertainty',      '😰', 'yellow'),
    'learning':     ('Learning',     'Knowledge rising, uncertainty falling','😃', 'blue'),
    'worried':      ('Worried',      'Knowledge dropping or high risk',     '😟', 'red'),
    'accomplished': ('Accomplished', 'High completion, high confidence',    '🏆', 'bright_green'),
    'focused':      ('Focused',      'Deep in praxic action',              '🎯', 'magenta'),
    'lost':         ('Lost',         'Very low context and knowledge',      '😵', 'bright_red'),
    'idle':         ('Idle',         'No active work or measurement',       '💤', 'dim'),
}

# ---------------------------------------------------------------------------
# Pixel art for each state (20x20 grid, rendered with 5x5 actual pixels)
# Using block characters: █ = filled, ░ = empty, ▓ = mid
# Each face is an 8-line representation for terminal display
# ---------------------------------------------------------------------------

PIXEL_FACES = {
    'confident': [
        "  ░██████░  ",
        " ██░░░░░░██ ",
        " ██▓██░██▓█ ",
        " ██░░░░░░██ ",
        " ██░░░░░░██ ",
        " ██░███████ ",
        " ██░░░░░░██ ",
        "  ░██████░  ",
    ],
    'thinking': [
        "  ░██████░  ",
        " ██░░░░░░██ ",
        " ██░██░██░█ ",
        " ██░░░░░░██ ",
        " ██░░░░░░██ ",
        " ██░░███░██ ",
        " ██░░░░░░██ ",
        "  ░██████░  ",
    ],
    'uncertain': [
        "  ░██████░  ",
        " ██░░░░░░██ ",
        " ██░██░██░█ ",
        " ██░░░░░░██ ",
        " ██░░░░░░██ ",
        " ██░░░░░░██ ",
        " ██░████░██ ",
        "  ░██████░  ",
    ],
    'learning': [
        "  ░██████░  ",
        " ██░░░░░░██ ",
        " ██▓██░██▓█ ",
        " ██░░░░░░██ ",
        " ██░░░░░░██ ",
        " ██░░██░░██ ",
        " ██░███████ ",
        "  ░██████░  ",
    ],
    'worried': [
        "  ░██████░  ",
        " ██░░░░░░██ ",
        " █▓░██░██░▓ ",
        " ██░░░░░░██ ",
        " ██░░░░░░██ ",
        " ██░░██░░██ ",
        " ██░██░░██░ ",
        "  ░██████░  ",
    ],
    'accomplished': [
        "  ░██████░  ",
        " ██░░░░░░██ ",
        " ██▓██░██▓█ ",
        " ██░▓░░▓░██ ",
        " ██░░░░░░██ ",
        " █▓░░░░░░▓█ ",
        " ██░███████ ",
        "  ░██████░  ",
    ],
    'focused': [
        "  ░██████░  ",
        " ██░░░░░░██ ",
        " ██░██░██░█ ",
        " ██░██░██░█ ",
        " ██░░░░░░██ ",
        " ██░░██░░██ ",
        " ██░░░░░░██ ",
        "  ░██████░  ",
    ],
    'lost': [
        "  ░██████░  ",
        " ██░░░░░░██ ",
        " ██░▓▓░▓▓█░ ",
        " ██░░░░░░██ ",
        " ██░░██░░██ ",
        " ██░██░░██░ ",
        " ██░░░░░░██ ",
        "  ░██████░  ",
    ],
    'idle': [
        "  ░██████░  ",
        " ██░░░░░░██ ",
        " ██░░░░░░██ ",
        " ██░██░██░█ ",
        " ██░░░░░░██ ",
        " ██░░██░░██ ",
        " ██░░░░░░██ ",
        "  ░██████░  ",
    ],
}


def compute_emoji_state(
    entity_type: str,
    vectors: Dict[str, float],
    phase: Optional[str] = None,
) -> Tuple[str, Dict]:
    """
    Compute functional emotive state from epistemic vectors.

    Args:
        entity_type: 'project', 'contact', or 'engagement'
        vectors: Dict of vector name → value (0.0-1.0)
        phase: Optional current transaction phase ('noetic', 'praxic')

    Returns:
        (state_name, detail_dict) where detail_dict has vectors_used and reason
    """
    if entity_type == 'project':
        return _compute_project_state(vectors, phase)
    elif entity_type == 'contact':
        return _compute_contact_state(vectors)
    elif entity_type == 'engagement':
        return _compute_engagement_state(vectors)
    return ('idle', {'vectors_used': [], 'reason': 'Unknown entity type'})


def _compute_project_state(vectors: Dict[str, float], phase: Optional[str] = None) -> Tuple[str, Dict]:
    """Project state from know, uncertainty, completion, do."""
    know = vectors.get('know', 0.0)
    uncertainty = vectors.get('uncertainty', 0.5)
    completion = vectors.get('completion', 0.0)
    do_val = vectors.get('do', 0.0)
    context = vectors.get('context', 0.0)

    used = ['know', 'uncertainty', 'completion', 'do', 'context']

    # High completion + high know = accomplished
    if completion >= 0.8 and know >= 0.7:
        return ('accomplished', {'vectors_used': used, 'reason': f'completion={completion:.2f}, know={know:.2f}'})

    # Very low context and knowledge = lost
    if know <= 0.25 and context <= 0.3:
        return ('lost', {'vectors_used': used, 'reason': f'know={know:.2f}, context={context:.2f}'})

    # Active praxic phase with good confidence = focused
    if phase == 'praxic' and know >= 0.6 and do_val >= 0.4:
        return ('focused', {'vectors_used': used, 'reason': f'praxic phase, know={know:.2f}, do={do_val:.2f}'})

    # High know + low uncertainty = confident
    if know >= 0.7 and uncertainty <= 0.3:
        return ('confident', {'vectors_used': used, 'reason': f'know={know:.2f}, uncertainty={uncertainty:.2f}'})

    # Knowledge rising (implied by do > know) = learning
    if do_val > know and uncertainty < 0.5:
        return ('learning', {'vectors_used': used, 'reason': f'do={do_val:.2f} > know={know:.2f}'})

    # High uncertainty = uncertain
    if uncertainty >= 0.5:
        if know <= 0.4:
            return ('worried', {'vectors_used': used, 'reason': f'uncertainty={uncertainty:.2f}, know={know:.2f}'})
        return ('uncertain', {'vectors_used': used, 'reason': f'uncertainty={uncertainty:.2f}'})

    # Default: thinking (active investigation)
    return ('thinking', {'vectors_used': used, 'reason': 'Active investigation'})


def _compute_contact_state(vectors: Dict[str, float]) -> Tuple[str, Dict]:
    """Contact state from relationship_health, knowledge_depth, sentiment_trend."""
    health = vectors.get('relationship_health', 0.5)
    depth = vectors.get('knowledge_depth', 0.0)
    # sentiment_trend is text but we can map it
    sentiment_val = vectors.get('sentiment_value', 0.5)  # pre-mapped to 0-1

    used = ['relationship_health', 'knowledge_depth', 'sentiment_value']

    if health >= 0.8 and depth >= 0.7:
        return ('confident', {'vectors_used': used, 'reason': f'health={health:.2f}, depth={depth:.2f}'})

    if health <= 0.3:
        return ('worried', {'vectors_used': used, 'reason': f'health={health:.2f}'})

    if depth <= 0.2:
        return ('uncertain', {'vectors_used': used, 'reason': f'depth={depth:.2f}'})

    if sentiment_val >= 0.7:
        return ('learning', {'vectors_used': used, 'reason': f'sentiment positive ({sentiment_val:.2f})'})

    return ('thinking', {'vectors_used': used, 'reason': 'Moderate engagement'})


def _compute_engagement_state(vectors: Dict[str, float]) -> Tuple[str, Dict]:
    """Engagement state from task completion and outcome trajectory."""
    task_completion = vectors.get('task_completion', 0.0)
    outcome_confidence = vectors.get('outcome_confidence', 0.5)

    used = ['task_completion', 'outcome_confidence']

    if task_completion >= 0.8 and outcome_confidence >= 0.7:
        return ('accomplished', {'vectors_used': used, 'reason': f'tasks={task_completion:.2f}, outcome={outcome_confidence:.2f}'})

    if outcome_confidence <= 0.3:
        return ('worried', {'vectors_used': used, 'reason': f'outcome_confidence={outcome_confidence:.2f}'})

    if task_completion >= 0.5:
        return ('focused', {'vectors_used': used, 'reason': f'tasks={task_completion:.2f}'})

    return ('thinking', {'vectors_used': used, 'reason': 'In progress'})


def get_emoji_char(state: str) -> str:
    """Get the emoji character for a state."""
    return STATES.get(state, STATES['idle'])[2]


def get_emoji_color(state: str) -> str:
    """Get the rich color for a state."""
    return STATES.get(state, STATES['idle'])[3]


def get_pixel_face(state: str) -> list:
    """Get the pixel art face lines for a state."""
    return PIXEL_FACES.get(state, PIXEL_FACES['idle'])


def render_pixel_face(state: str, color: Optional[str] = None) -> str:
    """Render a pixel face as a colored string for terminal display."""
    face_lines = get_pixel_face(state)
    if color is None:
        color = get_emoji_color(state)
    return '\n'.join(face_lines)
