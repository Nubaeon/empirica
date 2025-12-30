#!/usr/bin/env python3
"""
Empirica PostCompact Hook - Ground Truth Re-Assessment

After memory compaction, the AI has only a summary - not real knowledge.
This hook injects DYNAMIC context and triggers a PREFLIGHT re-assessment
to establish genuine epistemic ground truth.

Key insight: The AI's pre-compact vectors are meaningless post-compact.
The AI must RE-ASSESS what it actually knows given the evidence.
"""

import json
import sys
import subprocess
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path.home() / 'empirical-ai' / 'empirica'))


def main():
    hook_input = json.loads(sys.stdin.read())
    session_id = hook_input.get('session_id')

    # Find active Empirica session
    empirica_session = _get_empirica_session()
    if not empirica_session:
        print(json.dumps({"ok": True, "skipped": True, "reason": "No active Empirica session"}))
        sys.exit(0)

    ai_id = os.getenv('EMPIRICA_AI_ID', 'claude-code')

    # Load pre-compact snapshot (what the AI thought it knew)
    pre_snapshot = _load_pre_snapshot()
    pre_vectors = {}
    pre_reasoning = None
    pre_goals = []

    if pre_snapshot:
        pre_vectors = pre_snapshot.get('checkpoint', {}) or \
                      (pre_snapshot.get('live_state') or {}).get('vectors', {})
        pre_reasoning = (pre_snapshot.get('live_state') or {}).get('reasoning')
        # Extract goal context if available
        summary = pre_snapshot.get('breadcrumbs_summary', {})

    # Load DYNAMIC context - only what's relevant for re-grounding
    dynamic_context = _load_dynamic_context(empirica_session, ai_id, pre_snapshot)

    # Generate the PREFLIGHT re-assessment prompt
    preflight_prompt = _generate_preflight_prompt(
        pre_vectors=pre_vectors,
        pre_reasoning=pre_reasoning,
        dynamic_context=dynamic_context
    )

    # Calculate what drift WOULD be if vectors unchanged (to show the problem)
    potential_drift = _calculate_potential_drift(pre_vectors)

    # Build the injection payload
    output = {
        "ok": True,
        "empirica_session_id": empirica_session,
        "action_required": "PREFLIGHT_REASSESS",
        "pre_compact_state": {
            "vectors": pre_vectors,
            "reasoning": pre_reasoning,
            "timestamp": pre_snapshot.get('timestamp') if pre_snapshot else None
        },
        "dynamic_context": dynamic_context,
        "preflight_prompt": preflight_prompt,
        "potential_drift_warning": potential_drift,
        "inject_context": True,
        "message": "Post-compact: Ground truth re-assessment required"
    }

    print(json.dumps(output), file=sys.stdout)

    # User-visible message
    _print_user_message(pre_vectors, dynamic_context, potential_drift)

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


def _load_dynamic_context(session_id: str, ai_id: str, pre_snapshot: dict) -> dict:
    """
    Load DYNAMIC context - only what's relevant for re-grounding.

    NOT everything that ever was - just:
    1. Active goals (what was being worked on)
    2. Recent findings from THIS session (last learnings)
    3. Unresolved unknowns (open questions)
    4. Critical dead ends (mistakes to avoid)
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
        return context

    except Exception as e:
        return {
            "error": str(e),
            "active_goals": [],
            "recent_findings": [],
            "open_unknowns": [],
            "critical_dead_ends": []
        }


def _generate_preflight_prompt(pre_vectors: dict, pre_reasoning: str, dynamic_context: dict) -> str:
    """
    Generate a PREFLIGHT prompt that triggers genuine re-assessment.

    This is the key innovation: instead of just loading data, we prompt
    the AI to actively re-assess what it knows given the evidence.
    """
    goals_text = ""
    if dynamic_context.get("active_goals"):
        goals_text = "\n".join([
            f"  - {g['objective']} ({g['status']})"
            for g in dynamic_context["active_goals"]
        ])
    else:
        goals_text = "  (No active goals)"

    findings_text = ""
    if dynamic_context.get("recent_findings"):
        findings_text = "\n".join([
            f"  - {f['finding'][:100]}..." if len(f['finding']) > 100 else f"  - {f['finding']}"
            for f in dynamic_context["recent_findings"]
        ])
    else:
        findings_text = "  (No recent findings)"

    unknowns_text = ""
    if dynamic_context.get("open_unknowns"):
        unknowns_text = "\n".join([
            f"  - {u['unknown'][:100]}..." if len(u['unknown']) > 100 else f"  - {u['unknown']}"
            for u in dynamic_context["open_unknowns"]
        ])
    else:
        unknowns_text = "  (No open unknowns)"

    dead_ends_text = ""
    if dynamic_context.get("critical_dead_ends"):
        dead_ends_text = "\n".join([
            f"  - {d['approach']}: {d['why_failed']}"
            for d in dynamic_context["critical_dead_ends"]
        ])
    else:
        dead_ends_text = "  (None recorded)"

    pre_know = pre_vectors.get('know', 'N/A')
    pre_unc = pre_vectors.get('uncertainty', 'N/A')

    prompt = f"""
## POST-COMPACT GROUND TRUTH RE-ASSESSMENT

Your context was just compacted. Your previous vectors (know={pre_know}, uncertainty={pre_unc})
are NO LONGER VALID - they reflected knowledge you had in full context.

**You now have only a summary. You must RE-ASSESS what you actually know.**

### Evidence from Database (Ground Truth):

**Active Goals:**
{goals_text}

**Recent Findings (high-impact learnings):**
{findings_text}

**Open Unknowns (unresolved questions):**
{unknowns_text}

**Dead Ends (approaches that failed):**
{dead_ends_text}

### Required Action: Run PREFLIGHT

Assess your ACTUAL epistemic state given ONLY what you can see above:

```bash
empirica preflight-submit - << 'EOF'
{{
  "session_id": "{dynamic_context.get('session_context', {}).get('session_id', 'unknown')}",
  "vectors": {{
    "know": <0.0-1.0: What do you ACTUALLY know from the evidence above?>,
    "uncertainty": <0.0-1.0: How uncertain are you given limited context?>,
    "context": <0.0-1.0: How well do you understand the current state?>,
    "completion": <0.0-1.0: How complete is your understanding?>
  }},
  "reasoning": "Post-compact re-assessment: <explain what you know and don't know>"
}}
EOF
```

**Key principle:** Be HONEST about reduced knowledge. Post-compact know should typically be
LOWER than pre-compact because you've lost detailed context. Uncertainty should be HIGHER.
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


def _print_user_message(pre_vectors: dict, dynamic_context: dict, potential_drift: dict):
    """Print user-visible summary to stderr"""
    pre_know = pre_vectors.get('know', 'N/A')
    pre_unc = pre_vectors.get('uncertainty', 'N/A')

    goals_count = len(dynamic_context.get('active_goals', []))
    findings_count = len(dynamic_context.get('recent_findings', []))
    unknowns_count = len(dynamic_context.get('open_unknowns', []))

    print(f"""
🔄 Empirica: Post-Compact Ground Truth

📊 Pre-Compact State (NOW INVALID):
   know={pre_know}, uncertainty={pre_unc}

⚠️  These vectors reflected FULL context knowledge.
   You now have only a summary - RE-ASSESS required.

📚 Dynamic Context Loaded:
   Active Goals: {goals_count}
   Recent Findings: {findings_count}
   Open Unknowns: {unknowns_count}

🎯 ACTION REQUIRED: Run PREFLIGHT
   Assess what you ACTUALLY know from the evidence above.
   Be honest - post-compact know is typically LOWER.
""", file=sys.stderr)


if __name__ == '__main__':
    main()
