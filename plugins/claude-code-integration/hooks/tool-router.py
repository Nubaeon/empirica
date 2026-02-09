#!/usr/bin/env python3
"""
Epistemic Tool Router - UserPromptSubmit Hook

Runs on every user prompt BEFORE Claude starts reasoning. Assesses the task
against the current epistemic state and recommends specific Empirica
tools/agents/skills, influencing Claude's tool selection.

This is the bridge between "what should I do" (VectorRouter modes) and
"what should I use" (specific agents, skills, MCP tools).

Input (stdin JSON):
  {"prompt": "user's prompt text"}

Output (stdout JSON):
  {"continue": true, "context": "routing advice text"}

Performance target: < 2 seconds (runs on every prompt).
"""

import json
import sys
import os
from pathlib import Path


# ============================================================================
# Agent domain registry — keyword → agent mapping
# ============================================================================

AGENT_DOMAINS = {
    "empirica-integration:security": {
        "keywords": [
            "security", "auth", "authentication", "authorization",
            "encrypt", "vulnerability", "xss", "csrf", "injection",
            "token", "credential", "permission", "access control",
            "threat", "attack", "sanitiz",
        ],
        "description": "Security analysis and hardening",
    },
    "empirica-integration:architecture": {
        "keywords": [
            "architecture", "design pattern", "refactor",
            "modular", "coupling", "cohesion", "abstraction",
            "interface", "dependency", "scalab", "structure",
            "component", "layer", "separation of concerns",
            "system design",
        ],
        "description": "Architecture analysis and system design",
    },
    "empirica-integration:performance": {
        "keywords": [
            "performance", "optimiz", "latency", "throughput",
            "memory", "cpu", "cache", "profil", "slow",
            "bottleneck", "n+1", "query optim", "index",
        ],
        "description": "Performance analysis and optimization",
    },
    "empirica-integration:ux": {
        "keywords": [
            "usability", "accessibility", "user flow", "ux",
            "error message", "response time", "wcag", "a11y",
            "user experience", "interaction design",
        ],
        "description": "UX and accessibility analysis",
    },
}

# ============================================================================
# AAP (Anti-Agreement Protocol) — Hedge detection patterns
# ============================================================================

# Hedge patterns with categories and deobfuscation prompts
HEDGE_PATTERNS = {
    "softening_qualifiers": {
        "patterns": [
            r'\bkind of\b', r'\bsort of\b', r'\bmaybe\b', r'\bperhaps\b',
            r'\bI guess\b', r'\bI suppose\b', r'\bprobably\b',
            r'\bmight be\b', r'\bcould be\b',
        ],
        "deobfuscation": "You used softening language — what's the specific thing you mean?",
    },
    "dismissive_agreement": {
        "patterns": [
            r'\byeah\s+(sure|fine|ok|whatever)\b',
            r'\bI hear you\b', r'\bfair enough\b', r'\bif you say so\b',
            r'\bI\'m not going to argue\b', r'\blet\'s just go with\b',
        ],
        "deobfuscation": "That sounded like agreement without conviction — do you actually agree, or is there a reservation?",
    },
    "vague_deflection": {
        "patterns": [
            r'\bit\'s complicated\b', r'\bit depends\b', r'\bnot really\b',
            r'\bnot exactly\b', r'\bnot wrong\b', r'\bnot necessarily\b',
            r'\bin a way\b', r'\bto some extent\b',
        ],
        "deobfuscation": "Can you be more specific? What exactly is complicated / what does it depend on?",
    },
    "passive_uncertainty": {
        "patterns": [
            r'\bI\'?m not sure\s+(if|whether|about|that)\b',
            r'\bI don\'?t know\s+(if|whether|about)\b',
            r'\bI\'?m not (really\s+)?sure\b',
        ],
        "deobfuscation": "What specifically are you unsure about? Can you name the uncertainty?",
    },
    "false_modesty": {
        "patterns": [
            r'\bI\'?m (probably|just)\s+(wrong|being|overthinking)\b',
            r'\bthis is (probably\s+)?(stupid|dumb|obvious)\b',
            r'\byou (probably\s+)?know better\b',
            r'\bI\'?m no expert\b',
        ],
        "deobfuscation": "Don't discount your own assessment — what's the actual concern you're raising?",
    },
}

# Patterns that indicate genuine epistemic humility (NOT hedging)
# These should NOT trigger AAP
GENUINE_HUMILITY_PATTERNS = [
    r'\bI\'?m uncertain about .+ because\b',
    r'\bmy confidence is (low|around|about)\b',
    r'\bI don\'?t have (evidence|data|enough info)\b',
    r'\bthe evidence (suggests|shows|indicates)\b',
    r'\bbased on what I\'?ve (seen|read|found)\b',
    r'\bI need to (check|verify|investigate)\b',
]


def detect_hedges(text: str) -> list[dict]:
    """Detect hedge patterns in user text. Returns list of detected hedges with categories."""
    import re

    text_lower = text.lower()

    # Check for genuine epistemic humility first — if present, reduce sensitivity
    genuine_count = sum(
        1 for pattern in GENUINE_HUMILITY_PATTERNS
        if re.search(pattern, text_lower, re.IGNORECASE)
    )

    # If the text shows genuine epistemic reasoning, skip hedge detection
    if genuine_count >= 2:
        return []

    detected = []
    for category, config in HEDGE_PATTERNS.items():
        for pattern in config["patterns"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                detected.append({
                    "category": category,
                    "deobfuscation": config["deobfuscation"],
                })
                break  # One match per category is enough

    return detected


def load_aap_config() -> dict:
    """Load AAP configuration from workflow protocol."""
    try:
        import yaml as _yaml
        protocol_path = Path.home() / '.empirica' / 'workflow-protocol.yaml'
        if protocol_path.exists():
            with open(protocol_path, 'r') as f:
                protocol = _yaml.safe_load(f)
            return protocol.get('anti_agreement_protocol', {})
    except Exception:
        pass
    return {"enabled": False}


# Keywords that suggest investigation/exploration tasks
# (where Empirica agents are most valuable vs built-in Explore)
INVESTIGATION_KEYWORDS = [
    "investigate", "explore", "understand", "analyze", "assess",
    "audit", "review", "examine", "check", "inspect", "evaluate",
    "figure out", "look into", "dig into", "deep dive",
]

# Keywords that suggest epistemic workflow
EPISTEMIC_KEYWORDS = [
    "preflight", "postflight", "check", "cascade",
    "epistemic", "vector", "calibrat", "drift",
    "knowledge state", "confidence",
]


def get_active_session_vectors():
    """Get current session's epistemic vectors from DB. Fast path."""
    try:
        # Find active session ID
        instance_id = os.environ.get('EMPIRICA_INSTANCE_ID')
        if not instance_id:
            tmux = os.environ.get('TMUX_PANE')
            if tmux:
                instance_id = f"tmux:{tmux}"

        suffix = ""
        if instance_id:
            safe = instance_id.replace(":", "_").replace("%", "")
            suffix = f"_{safe}"

        session_id = None
        for base in [Path.cwd() / '.empirica', Path.home() / '.empirica']:
            active_file = base / f'active_session{suffix}'
            if active_file.exists():
                content = active_file.read_text().strip()
                if content:
                    # Parse JSON format (CLI/MCP) or plain text (legacy)
                    if content.startswith('{'):
                        try:
                            data = json.loads(content)
                            session_id = data.get('session_id')
                        except json.JSONDecodeError:
                            session_id = content  # Fallback to raw content
                    else:
                        session_id = content  # Plain text format
                    if session_id:
                        break

        if not session_id:
            return None, None

        # Read vectors from DB
        sys.path.insert(0, str(Path.home() / 'empirical-ai' / 'empirica'))
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Get latest epistemic assessment for this session
        cursor.execute("""
            SELECT vectors FROM epistemic_assessments
            WHERE session_id = ?
            ORDER BY created_timestamp DESC LIMIT 1
        """, (session_id,))
        row = cursor.fetchone()
        db.close()

        if row:
            vectors = json.loads(row[0]) if isinstance(row[0], str) else row[0]
            return session_id, vectors

        return session_id, None
    except Exception:
        return None, None


def determine_mode(vectors):
    """Lightweight mode determination from vectors."""
    if not vectors:
        return "unknown"

    clarity = vectors.get("clarity", 0.5)
    context = vectors.get("context", 0.5)
    uncertainty = vectors.get("uncertainty", 0.5)
    know = vectors.get("know", 0.5)

    if clarity < 0.5:
        return "clarify"
    if context < 0.5:
        return "load_context"
    if uncertainty > 0.6:
        return "investigate"
    if know >= 0.7 and uncertainty < 0.4:
        return "confident_implementation"
    return "cautious_implementation"


def match_agents(task_lower):
    """Match task keywords to domain-specific agents."""
    matches = []
    for agent_name, config in AGENT_DOMAINS.items():
        keyword_hits = sum(
            1 for kw in config["keywords"]
            if kw in task_lower
        )
        if keyword_hits > 0:
            confidence = min(0.95, 0.5 + keyword_hits * 0.15)
            matches.append({
                "name": agent_name,
                "confidence": confidence,
                "description": config["description"],
                "hits": keyword_hits,
            })
    # Sort by confidence descending
    return sorted(matches, key=lambda m: -m["confidence"])


def is_investigation_task(task_lower):
    """Check if the task suggests investigation/exploration."""
    return any(kw in task_lower for kw in INVESTIGATION_KEYWORDS)


def is_epistemic_task(task_lower):
    """Check if the task involves epistemic workflow."""
    return any(kw in task_lower for kw in EPISTEMIC_KEYWORDS)


def is_blindspot_relevant(task_lower, mode, vectors):
    """Check if blindspot scanning would be valuable for this task."""
    # Explicit blindspot keywords
    if any(kw in task_lower for kw in ["blindspot", "blind spot", "unknown unknown",
                                        "what am i missing", "what are we missing",
                                        "what might i be missing", "negative space",
                                        "coverage gap", "gap in", "gaps in"]):
        return True
    # High uncertainty + investigation mode
    if vectors and vectors.get("uncertainty", 0) > 0.5 and mode in ("investigate", "clarify"):
        return True
    # Starting new work (low completion, low context)
    if vectors and vectors.get("completion", 0) < 0.15 and vectors.get("context", 0) < 0.5:
        return True
    return False


def build_routing_advice(task, vectors, session_id):
    """Build routing advice from task + vectors."""
    task_lower = task.lower()
    advice_parts = []

    # Determine current mode
    mode = determine_mode(vectors)

    # Match domain agents
    agent_matches = match_agents(task_lower)

    # Only emit advice if there's something useful to say
    has_advice = False

    # Agent recommendations (most impactful)
    if agent_matches:
        has_advice = True
        top = agent_matches[0]
        advice_parts.append(
            f"For this task, consider using the `{top['name']}` agent "
            f"({top['description']})."
        )
        if len(agent_matches) > 1:
            others = ", ".join(f"`{m['name']}`" for m in agent_matches[1:3])
            advice_parts.append(f"Also relevant: {others}.")

    # Investigation routing — suggest Empirica agents over built-in Explore
    if is_investigation_task(task_lower) and not agent_matches:
        has_advice = True
        advice_parts.append(
            "This looks like an investigation task. "
            "Use `mcp__empirica__investigate` for systematic investigation "
            "with epistemic tracking, or spawn a domain-specific agent "
            "(empirica-integration:architecture, security, performance, ux) "
            "for focused analysis."
        )

    # Blindspot scanning — surface unknown unknowns
    if is_blindspot_relevant(task_lower, mode, vectors):
        has_advice = True
        advice_parts.append(
            "Consider running `mcp__empirica__blindspot_scan` to detect "
            "knowledge gaps from negative space analysis before proceeding."
        )

    # Mode-based tool suggestions
    if mode == "load_context" and vectors:
        has_advice = True
        advice_parts.append(
            "Context is low — run `mcp__empirica__project_bootstrap` "
            "to load project context before proceeding."
        )
    elif mode == "investigate" and vectors:
        has_advice = True
        if not agent_matches:
            advice_parts.append(
                "Uncertainty is high — use `mcp__empirica__investigate` "
                "or spawn a domain agent for systematic investigation."
            )
    elif mode == "cautious_implementation" and vectors:
        # In cautious mode, remind about dead-end logging
        if any(kw in task_lower for kw in ["try", "attempt", "approach", "workaround", "fix"]):
            has_advice = True
            advice_parts.append(
                "If this approach doesn't work, log it with "
                "`mcp__empirica__deadend_log` to prevent re-exploration."
            )

    # Epistemic workflow hints
    if is_epistemic_task(task_lower):
        has_advice = True
        advice_parts.append(
            "This involves epistemic workflow. "
            "Use the Empirica MCP tools (preflight/check/postflight) "
            "or invoke the `empirica-framework` skill for guidance."
        )

    if not has_advice:
        return None

    return "\n".join(advice_parts)


def main():
    """Main hook handler."""
    try:
        input_data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}
    except (json.JSONDecodeError, EOFError):
        input_data = {}

    prompt = input_data.get("prompt", "")

    # Skip very short prompts or commands
    if len(prompt) < 10 or prompt.startswith("/"):
        print(json.dumps({"continue": True}))
        return

    # Get current epistemic state
    session_id, vectors = get_active_session_vectors()

    # Build routing advice
    advice = build_routing_advice(prompt, vectors, session_id)

    # AAP hedge detection
    aap_context = ""
    aap_config = load_aap_config()
    if aap_config.get("enabled") and prompt and len(prompt) > 15:
        hedges = detect_hedges(prompt)
        if hedges:
            # Build deobfuscation guidance for Claude
            hedge_lines = []
            for h in hedges[:3]:  # Max 3 to avoid overwhelming
                hedge_lines.append(f"  - [{h['category']}] {h['deobfuscation']}")
            aap_context = (
                "<aap-hedge-detected>\n"
                "User language contains hedging patterns. Per AAP protocol:\n"
                + "\n".join(hedge_lines) + "\n"
                "Surface the actual epistemic content. Don't mirror the hedging.\n"
                "</aap-hedge-detected>"
            )

    # Combine contexts
    context_parts = []
    if advice:
        context_parts.append(f"<epistemic-routing>\n{advice}\n</epistemic-routing>")
    if aap_context:
        context_parts.append(aap_context)

    if context_parts:
        output = {
            "continue": True,
            "context": "\n".join(context_parts)
        }
    else:
        output = {"continue": True}

    print(json.dumps(output))


if __name__ == "__main__":
    main()
