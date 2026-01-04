#!/usr/bin/env python3
"""
Empirica PostCompact Hook - Phase-Aware Recovery

After memory compaction, the AI has only a summary - not real knowledge.
This hook detects the CASCADE phase state and routes appropriately:

1. If old session is COMPLETE (has POSTFLIGHT) → New session + PREFLIGHT
2. If old session is INCOMPLETE (mid-work) → CHECK gate on old session

Key insight: Compact can happen at ANY point in the CASCADE cycle.
The recovery action depends on WHERE in the cycle compact occurred.
"""

import json
import sys
import subprocess
import os
from pathlib import Path
from datetime import datetime


def find_project_root() -> Path:
    """
    Find the Empirica project root by searching for .empirica/ directory with valid database.

    Search order:
    1. EMPIRICA_WORKSPACE_ROOT environment variable
    2. Known development paths (prioritized to avoid polluted temp dirs)
    3. Search upward from current directory
    4. Fallback to current directory
    """
    def has_valid_db(path: Path) -> bool:
        """Check if path has valid Empirica database"""
        db_path = path / '.empirica' / 'sessions' / 'sessions.db'
        return db_path.exists() and db_path.stat().st_size > 0

    # 1. Check environment variable
    if workspace_root := os.getenv('EMPIRICA_WORKSPACE_ROOT'):
        workspace_path = Path(workspace_root).expanduser().resolve()
        if has_valid_db(workspace_path):
            return workspace_path

    # 2. Try known development paths FIRST (to avoid polluted temp dirs like /tmp/.empirica)
    known_paths = [
        Path.home() / 'empirical-ai' / 'empirica',
        Path.home() / 'empirica',
        Path('/workspace'),
    ]
    for path in known_paths:
        if has_valid_db(path):
            return path

    # 3. Search upward from current directory (only if has valid DB)
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if has_valid_db(parent):
            return parent
        # Stop at filesystem root
        if parent == parent.parent:
            break

    # 4. Fallback to current directory
    return Path.cwd()


def main():
    hook_input = json.loads(sys.stdin.read())
    session_id = hook_input.get('session_id')

    # CRITICAL: Find and change to project root BEFORE importing empirica
    # This ensures SessionDatabase uses the correct database path
    project_root = find_project_root()
    os.chdir(project_root)

    # Now safe to import empirica (after cwd is set correctly)
    sys.path.insert(0, str(Path.home() / 'empirical-ai' / 'empirica'))

    # Find active Empirica session
    empirica_session = _get_empirica_session()
    if not empirica_session:
        print(json.dumps({"ok": True, "skipped": True, "reason": "No active Empirica session"}))
        sys.exit(0)

    ai_id = os.getenv('EMPIRICA_AI_ID', 'claude-code')

    # CRITICAL: Detect phase state to route recovery correctly
    phase_state = _get_session_phase_state(empirica_session)

    # Step 1: Capture FRESH epistemic state POST-compact (canonical via assess-state)
    # This shows what the AI's epistemic state actually is NOW (after compacting)
    fresh_vectors_post = {}
    try:
        assess_result = subprocess.run(
            ['empirica', 'assess-state', '--session-id', empirica_session, '--output', 'json'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if assess_result.returncode == 0:
            assess_data = json.loads(assess_result.stdout)
            fresh_vectors_post = assess_data.get('state', {}).get('vectors', {})
    except Exception:
        pass  # Non-fatal

    # Load pre-compact snapshot (what the AI thought it knew BEFORE compacting)
    pre_snapshot = _load_pre_snapshot()
    pre_vectors = {}
    pre_reasoning = None

    if pre_snapshot:
        # Use canonical vectors if available, fallback to live_state
        pre_vectors = pre_snapshot.get('vectors_canonical', {}) or \
                      pre_snapshot.get('checkpoint', {}) or \
                      (pre_snapshot.get('live_state') or {}).get('vectors', {})
        pre_reasoning = (pre_snapshot.get('live_state') or {}).get('reasoning')

    # Load DYNAMIC context - only what's relevant for re-grounding
    dynamic_context = _load_dynamic_context(empirica_session, ai_id, pre_snapshot)

    # Route based on phase state:
    # - Session COMPLETE (has POSTFLIGHT) → New session + PREFLIGHT
    # - Session INCOMPLETE (mid-work) → CHECK gate on old session
    if phase_state.get('is_complete'):
        recovery_prompt = _generate_new_session_prompt(
            pre_vectors=pre_vectors,
            dynamic_context=dynamic_context,
            old_session_id=empirica_session,
            ai_id=ai_id
        )
        action_required = "NEW_SESSION_PREFLIGHT"
    else:
        recovery_prompt = _generate_check_prompt(
            pre_vectors=pre_vectors,
            pre_reasoning=pre_reasoning,
            dynamic_context=dynamic_context
        )
        action_required = "CHECK_GATE"

    # Calculate what drift WOULD be if vectors unchanged (to show the problem)
    potential_drift = _calculate_potential_drift(pre_vectors)

    # Build the injection payload using Claude Code's hook format
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": recovery_prompt
        },
        "empirica_session_id": empirica_session,
        "action_required": action_required,
        "phase_state": phase_state,
        "pre_compact_state": {
            "vectors": pre_vectors,
            "reasoning": pre_reasoning,
            "timestamp": pre_snapshot.get('timestamp') if pre_snapshot else None
        },
        "post_compact_state": {
            "vectors_fresh": fresh_vectors_post,  # TIER 2a: Fresh vectors POST-compact
            "captured_via": "assess-state (canonical)"
        },
        "potential_drift_warning": potential_drift
    }

    print(json.dumps(output), file=sys.stdout)

    # User-visible message to stderr
    _print_user_message(pre_vectors, dynamic_context, potential_drift, phase_state, ai_id)

    sys.exit(0)


def _get_empirica_session():
    """Find the active Empirica session"""
    try:
        from empirica.utils.session_resolver import get_latest_session_id
        for ai_pattern in ['claude-code', None]:
            try:
                return get_latest_session_id(ai_id=ai_pattern, active_only=True)
            except ValueError:
                continue
    except Exception:
        pass
    return None


def _get_session_phase_state(session_id: str) -> dict:
    """
    Detect the CASCADE phase state of a session.

    Returns:
        {
            "has_preflight": bool,
            "has_postflight": bool,
            "last_phase": str or None,
            "is_complete": bool  # True if session has POSTFLIGHT
        }
    """
    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Get all phases for this session
        cursor.execute("""
            SELECT phase, timestamp
            FROM reflexes
            WHERE session_id = ?
            ORDER BY timestamp DESC
        """, (session_id,))
        rows = cursor.fetchall()
        db.close()

        if not rows:
            return {
                "has_preflight": False,
                "has_postflight": False,
                "last_phase": None,
                "is_complete": False
            }

        phases = [r[0] for r in rows]
        last_phase = phases[0] if phases else None

        # Session is "complete" if the LAST phase was POSTFLIGHT
        # (not just if it ever had a POSTFLIGHT - could be in cycle 2+)
        is_complete = last_phase == "POSTFLIGHT"

        return {
            "has_preflight": "PREFLIGHT" in phases,
            "has_postflight": "POSTFLIGHT" in phases,
            "last_phase": last_phase,
            "is_complete": is_complete
        }
    except Exception as e:
        return {
            "has_preflight": False,
            "has_postflight": False,
            "last_phase": None,
            "is_complete": False,
            "error": str(e)
        }


def _load_pre_snapshot():
    """Load the most recent pre-compact snapshot"""
    try:
        ref_docs_dir = Path.cwd() / ".empirica" / "ref-docs"
        snapshots = sorted(ref_docs_dir.glob("pre_summary_*.json"), reverse=True)
        if snapshots:
            with open(snapshots[0], 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return None


def _load_memory_context(project_id: str, goals: list) -> dict:
    """
    Load MEMORY context from eidetic (facts) and episodic (narratives) layers.

    This is the cognitive memory that should be surfaced automatically
    based on epistemic state (high uncertainty triggers more retrieval).
    """
    memory_context = {
        "eidetic_facts": [],
        "episodic_narratives": [],
        "memory_available": False
    }

    try:
        from empirica.core.qdrant.vector_store import search_eidetic, search_episodic

        # Query eidetic memory for relevant facts based on active goals
        for goal in goals[:3]:  # Top 3 goals
            objective = goal.get('objective', '')
            if not objective:
                continue

            # Search eidetic facts
            facts = search_eidetic(
                project_id=project_id,
                query=objective,
                min_confidence=0.5,
                limit=3
            )
            for fact in facts:
                if fact not in memory_context["eidetic_facts"]:
                    memory_context["eidetic_facts"].append({
                        "content": fact.get('content', '')[:200],
                        "confidence": fact.get('confidence', 0.5),
                        "domain": fact.get('domain'),
                        "type": fact.get('type', 'fact')
                    })

            # Search episodic narratives
            episodes = search_episodic(
                project_id=project_id,
                query=objective,
                limit=2
            )
            for episode in episodes:
                if episode not in memory_context["episodic_narratives"]:
                    memory_context["episodic_narratives"].append({
                        "narrative": episode.get('narrative', '')[:200],
                        "outcome": episode.get('outcome'),
                        "session_id": episode.get('session_id', '')[:8]
                    })

        memory_context["memory_available"] = bool(
            memory_context["eidetic_facts"] or memory_context["episodic_narratives"]
        )

    except Exception as e:
        memory_context["error"] = str(e)

    return memory_context


def _load_dynamic_context(session_id: str, ai_id: str, pre_snapshot: dict) -> dict:
    """
    Load DYNAMIC context - only what's relevant for re-grounding.

    NOT everything that ever was - just:
    1. Active goals (what was being worked on)
    2. Recent findings from THIS session (last learnings)
    3. Unresolved unknowns (open questions)
    4. Critical dead ends (mistakes to avoid)
    5. Memory context (eidetic facts + episodic narratives)
    """
    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Get the session's project_id
        cursor.execute("SELECT project_id FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        project_id = row[0] if row else None

        context = {
            "active_goals": [],
            "recent_findings": [],
            "open_unknowns": [],
            "critical_dead_ends": [],
            "session_context": {}
        }

        if not project_id:
            db.close()
            return context

        # 1. Active goals (incomplete, high priority)
        cursor.execute("""
            SELECT id, objective, status, scope
            FROM goals
            WHERE project_id = ? AND status IN ('active', 'in_progress', 'blocked')
            ORDER BY created_timestamp DESC LIMIT 3
        """, (project_id,))
        for row in cursor.fetchall():
            context["active_goals"].append({
                "id": row[0],
                "objective": row[1],
                "status": row[2],
                "scope": row[3]
            })

        # 2. Recent findings from THIS session (last session's learnings)
        cursor.execute("""
            SELECT finding, impact, created_timestamp
            FROM project_findings
            WHERE project_id = ? AND impact >= 0.6
            ORDER BY created_timestamp DESC LIMIT 5
        """, (project_id,))
        for row in cursor.fetchall():
            context["recent_findings"].append({
                "finding": row[0],
                "impact": row[1],
                "when": str(row[2])[:19] if row[2] else None
            })

        # 3. Unresolved unknowns (open questions you need to address)
        cursor.execute("""
            SELECT unknown, impact, created_timestamp
            FROM project_unknowns
            WHERE project_id = ? AND is_resolved = 0
            ORDER BY impact DESC, created_timestamp DESC LIMIT 5
        """, (project_id,))
        for row in cursor.fetchall():
            context["open_unknowns"].append({
                "unknown": row[0],
                "impact": row[1]
            })

        # 4. Critical dead ends (mistakes to avoid)
        cursor.execute("""
            SELECT approach, why_failed
            FROM project_dead_ends
            WHERE project_id = ?
            ORDER BY created_timestamp DESC LIMIT 3
        """, (project_id,))
        for row in cursor.fetchall():
            context["critical_dead_ends"].append({
                "approach": row[0],
                "why_failed": row[1]
            })

        # 5. Session context (what was happening)
        context["session_context"] = {
            "session_id": session_id,
            "ai_id": ai_id,
            "project_id": project_id
        }

        db.close()

        # 6. Memory context (eidetic facts + episodic narratives from vector store)
        memory_context = _load_memory_context(project_id, context["active_goals"])
        context["memory_context"] = memory_context

        return context

    except Exception as e:
        return {
            "error": str(e),
            "active_goals": [],
            "recent_findings": [],
            "open_unknowns": [],
            "critical_dead_ends": []
        }


def _generate_new_session_prompt(pre_vectors: dict, dynamic_context: dict, old_session_id: str, ai_id: str) -> str:
    """
    Generate prompt for NEW session + PREFLIGHT when old session was complete.

    This is the correct path when compact happens AFTER POSTFLIGHT - the old
    session is done, we need a fresh start with proper baseline.
    """
    goals_text = _format_goals(dynamic_context)
    findings_text = _format_findings(dynamic_context)
    unknowns_text = _format_unknowns(dynamic_context)
    memory_text = _format_memory_context(dynamic_context)

    pre_know = pre_vectors.get('know', 'N/A')
    pre_unc = pre_vectors.get('uncertainty', 'N/A')

    return f"""
## POST-COMPACT: NEW SESSION REQUIRED

Your context was just compacted. The previous session ({old_session_id[:8]}...) was **COMPLETE**
(had POSTFLIGHT), so you need a NEW session with fresh PREFLIGHT baseline.

**Pre-compact vectors (NOW INVALID):** know={pre_know}, uncertainty={pre_unc}

### Evidence from Database (Ground Truth):

**Active Goals:**
{goals_text}

**Recent Findings (high-impact learnings):**
{findings_text}

**Open Unknowns (unresolved questions):**
{unknowns_text}

### Memory Context (Auto-Retrieved):

{memory_text}

### Step 1: Create New Session

```bash
empirica session-create --ai-id {ai_id} --output json
```

### Step 2: Load Project Context

```bash
empirica project-bootstrap --session-id <NEW_SESSION_ID> --output json
```

### Step 3: Run PREFLIGHT (Baseline)

```bash
empirica preflight-submit - << 'EOF'
{{
  "session_id": "<NEW_SESSION_ID>",
  "task_context": "<what you're working on>",
  "vectors": {{
    "know": <0.0-1.0: What do you ACTUALLY know now?>,
    "uncertainty": <0.0-1.0: How uncertain are you?>,
    "context": <0.0-1.0: How well do you understand current state?>,
    "engagement": <0.0-1.0: How engaged are you with the task?>
  }},
  "reasoning": "Post-compact fresh session: <explain current epistemic state>"
}}
EOF
```

**Key principle:** Be HONEST about reduced knowledge. This is a FRESH START, not a continuation.
"""


def _format_goals(dynamic_context: dict) -> str:
    """Format goals for prompt."""
    if dynamic_context.get("active_goals"):
        return "\n".join([
            f"  - {g['objective']} ({g['status']})"
            for g in dynamic_context["active_goals"]
        ])
    return "  (No active goals)"


def _format_findings(dynamic_context: dict) -> str:
    """Format findings for prompt."""
    if dynamic_context.get("recent_findings"):
        return "\n".join([
            f"  - {f['finding'][:100]}..." if len(f['finding']) > 100 else f"  - {f['finding']}"
            for f in dynamic_context["recent_findings"]
        ])
    return "  (No recent findings)"


def _format_unknowns(dynamic_context: dict) -> str:
    """Format unknowns for prompt."""
    if dynamic_context.get("open_unknowns"):
        return "\n".join([
            f"  - {u['unknown'][:100]}..." if len(u['unknown']) > 100 else f"  - {u['unknown']}"
            for u in dynamic_context["open_unknowns"]
        ])
    return "  (No open unknowns)"


def _format_dead_ends(dynamic_context: dict) -> str:
    """Format dead ends for prompt."""
    if dynamic_context.get("critical_dead_ends"):
        return "\n".join([
            f"  - {d['approach']}: {d['why_failed']}"
            for d in dynamic_context["critical_dead_ends"]
        ])
    return "  (None recorded)"


def _format_memory_context(dynamic_context: dict) -> str:
    """Format eidetic facts and episodic narratives from memory."""
    memory = dynamic_context.get("memory_context", {})

    if not memory.get("memory_available"):
        return "  (No memory context available - Qdrant may not be running)"

    parts = []

    # Format eidetic facts
    facts = memory.get("eidetic_facts", [])
    if facts:
        parts.append("**Relevant Facts (eidetic):**")
        for f in facts[:5]:
            conf = f.get('confidence', 0.5)
            domain = f.get('domain', 'general')
            parts.append(f"  - [{conf:.0%}] {f['content'][:100]}...")

    # Format episodic narratives
    episodes = memory.get("episodic_narratives", [])
    if episodes:
        parts.append("\n**Past Work (episodic):**")
        for e in episodes[:3]:
            session = e.get('session_id', '?')
            outcome = e.get('outcome', 'unknown')
            parts.append(f"  - Session {session}: {e['narrative'][:80]}... ({outcome})")

    return "\n".join(parts) if parts else "  (No relevant memories found)"


def _generate_check_prompt(pre_vectors: dict, pre_reasoning: str, dynamic_context: dict) -> str:
    """
    Generate a CHECK gate prompt for post-compact validation.

    CHECK is correct when session is INCOMPLETE (no POSTFLIGHT yet) -
    we're continuing work and need to validate readiness.
    """
    goals_text = _format_goals(dynamic_context)
    findings_text = _format_findings(dynamic_context)
    unknowns_text = _format_unknowns(dynamic_context)
    dead_ends_text = _format_dead_ends(dynamic_context)
    memory_text = _format_memory_context(dynamic_context)

    pre_know = pre_vectors.get('know', 'N/A')
    pre_unc = pre_vectors.get('uncertainty', 'N/A')

    session_id = dynamic_context.get('session_context', {}).get('session_id', 'unknown')

    prompt = f"""
## POST-COMPACT CHECK GATE

Your context was just compacted. Your previous vectors (know={pre_know}, uncertainty={pre_unc})
are NO LONGER VALID - they reflected knowledge you had in full context.

**You now have only a summary. Run CHECK to validate readiness before proceeding.**

### Evidence from Database (Ground Truth):

**Active Goals:**
{goals_text}

**Recent Findings (high-impact learnings):**
{findings_text}

**Open Unknowns (unresolved questions):**
{unknowns_text}

**Dead Ends (approaches that failed):**
{dead_ends_text}

### Memory Context (Auto-Retrieved):

{memory_text}

### Step 1: Load Context (Recommended)

Before CHECK, recover context via bootstrap and/or semantic search:

```bash
# Load project context (depth scales with uncertainty)
empirica project-bootstrap --session-id {session_id} --output json

# Semantic search for specific topics (if qdrant-client installed)
empirica project-search --query "<your current task>" --output json
```

### Step 2: Run CHECK Gate

After loading context, validate readiness to proceed:

```bash
empirica check-submit - << 'EOF'
{{
  "session_id": "{session_id}",
  "action_description": "<what you intend to do next>",
  "vectors": {{
    "know": <0.0-1.0: What do you ACTUALLY know now?>,
    "uncertainty": <0.0-1.0: How uncertain are you?>,
    "context": <0.0-1.0: How well do you understand current state?>,
    "scope": <0.0-1.0: How broad is the intended action?>
  }},
  "reasoning": "Post-compact assessment: <explain current epistemic state>"
}}
EOF
```

### Step 3: Follow CHECK Decision

CHECK returns one of:
- **"proceed"** → You have sufficient confidence. Continue with work.
- **"investigate"** → Confidence too low. Load more context, read files, then CHECK again.

**Key principle:** Be HONEST about reduced knowledge. Post-compact know should typically be
LOWER than pre-compact. Do NOT proceed until CHECK returns "proceed".
"""
    return prompt


def _calculate_potential_drift(pre_vectors: dict) -> dict:
    """
    Calculate what drift WOULD look like if we naively kept pre-compact vectors.
    This shows why re-assessment is necessary.
    """
    if not pre_vectors:
        return {"warning": "No pre-compact vectors to compare"}

    # Post-compact, honest assessment would typically show:
    # - Lower know (lost detailed context)
    # - Higher uncertainty (less confident)
    # - Similar or lower context (depends on evidence loaded)

    pre_know = pre_vectors.get('know', 0.5)
    pre_unc = pre_vectors.get('uncertainty', 0.5)

    return {
        "pre_compact": {
            "know": pre_know,
            "uncertainty": pre_unc
        },
        "expected_honest_post_compact": {
            "know": max(0.3, pre_know - 0.2),  # Typically drops
            "uncertainty": min(0.8, pre_unc + 0.2)  # Typically rises
        },
        "message": "If your post-compact know equals pre-compact, you may be overestimating"
    }


def _print_user_message(pre_vectors: dict, dynamic_context: dict, potential_drift: dict,
                        phase_state: dict = None, ai_id: str = 'claude-code'):
    """Print user-visible summary to stderr"""
    pre_know = pre_vectors.get('know', 'N/A')
    pre_unc = pre_vectors.get('uncertainty', 'N/A')

    goals_count = len(dynamic_context.get('active_goals', []))
    findings_count = len(dynamic_context.get('recent_findings', []))
    unknowns_count = len(dynamic_context.get('open_unknowns', []))

    is_complete = phase_state.get('is_complete', False) if phase_state else False
    last_phase = phase_state.get('last_phase', 'unknown') if phase_state else 'unknown'

    if is_complete:
        # Session was complete - need new session + PREFLIGHT
        print(f"""
🔄 Empirica: Post-Compact Recovery (Session Complete)

📊 Previous Session State:
   Last Phase: {last_phase} (COMPLETE)
   Pre-compact vectors (NOW INVALID): know={pre_know}, uncertainty={pre_unc}

⚠️  Previous session had POSTFLIGHT - it's COMPLETE.
   You need a NEW session with fresh PREFLIGHT baseline.

📚 Dynamic Context Available:
   Active Goals: {goals_count}
   Recent Findings: {findings_count}
   Open Unknowns: {unknowns_count}

🎯 ACTION REQUIRED:
   1. Create new session: empirica session-create --ai-id {ai_id}
   2. Load context: empirica project-bootstrap --session-id <NEW_ID>
   3. Run PREFLIGHT: empirica preflight-submit (with honest baseline)
""", file=sys.stderr)
    else:
        # Session incomplete - need CHECK to continue
        print(f"""
🔄 Empirica: Post-Compact CHECK Gate (Session Incomplete)

📊 Pre-Compact State (NOW INVALID):
   Last Phase: {last_phase}
   know={pre_know}, uncertainty={pre_unc}

⚠️  These vectors reflected FULL context knowledge.
   You now have only a summary. Session is INCOMPLETE.

📚 Dynamic Context Loaded:
   Active Goals: {goals_count}
   Recent Findings: {findings_count}
   Open Unknowns: {unknowns_count}

🎯 ACTION REQUIRED:
   1. Load context: empirica project-bootstrap --session-id <ID>
   2. Run CHECK: empirica check-submit (with honest assessment)
   3. Follow decision: "proceed" or "investigate"
""", file=sys.stderr)


if __name__ == '__main__':
    main()
