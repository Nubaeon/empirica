#!/usr/bin/env python3
"""
SubagentStop Hook: Roll up epistemic findings from sub-agent to parent session.

Triggered by Claude Code SubagentStop event. Reads the agent's transcript,
extracts findings/unknowns/dead-ends, and logs them to the parent session.

Input (stdin JSON from Claude Code):
  - agent_name: str - The agent identifier
  - agent_type: str - The agent type
  - agent_transcript_path: str - Path to the agent's transcript file
  - session_id: str - Claude Code's internal session ID

Output (stdout JSON):
  - continue: true
  - message: str - Status message with rollup summary

Side effects:
  - Ends child Empirica session
  - Logs findings from transcript to parent session
  - Updates subagent session file status to "completed"
"""

import json
import sys
import glob
from pathlib import Path
from datetime import datetime


def find_subagent_session(agent_name: str) -> dict:
    """Find the most recent active subagent session for this agent."""
    subagent_dir = Path.cwd() / '.empirica' / 'subagent_sessions'
    if not subagent_dir.exists():
        return {}

    safe_name = agent_name.replace(":", "_").replace("/", "_")
    # Find most recent active session file for this agent
    pattern = str(subagent_dir / f"{safe_name}_*.json")
    files = sorted(glob.glob(pattern), reverse=True)

    for f in files:
        try:
            data = json.loads(Path(f).read_text())
            if data.get("status") == "active":
                data["_file_path"] = f
                return data
        except (json.JSONDecodeError, OSError):
            continue

    return {}


def mark_session_completed(session_file: str, summary: dict):
    """Mark subagent session as completed with rollup summary."""
    try:
        data = json.loads(Path(session_file).read_text())
        data["status"] = "completed"
        data["completed_at"] = datetime.now().isoformat()
        data["rollup_summary"] = summary
        Path(session_file).write_text(json.dumps(data, indent=2))
    except (json.JSONDecodeError, OSError):
        pass


def extract_findings_from_transcript(transcript_path: str) -> dict:
    """Extract epistemic artifacts from agent transcript.

    Looks for patterns indicating discoveries, uncertainties, and failures.
    Returns structured findings for rollup to parent session.
    """
    findings = []
    unknowns = []
    dead_ends = []

    if not transcript_path or not Path(transcript_path).exists():
        return {"findings": findings, "unknowns": unknowns, "dead_ends": dead_ends}

    try:
        content = Path(transcript_path).read_text()

        # Try to parse as JSONL (Claude Code transcript format)
        for line in content.strip().split('\n'):
            try:
                entry = json.loads(line)
                msg = entry.get("message", {})
                role = msg.get("role", "")
                text_content = ""

                # Extract text from message content
                if isinstance(msg.get("content"), str):
                    text_content = msg["content"]
                elif isinstance(msg.get("content"), list):
                    for block in msg["content"]:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text_content += block.get("text", "") + "\n"

                if role == "assistant" and text_content:
                    # Look for finding-like patterns
                    for pattern_start in ["Found:", "Discovered:", "Key insight:", "Result:"]:
                        if pattern_start in text_content:
                            # Extract the sentence containing the pattern
                            for sentence in text_content.split('.'):
                                if pattern_start.rstrip(':') in sentence:
                                    finding = sentence.strip()
                                    if len(finding) > 10:
                                        findings.append(finding[:200])
                                    break

                    # Look for unknown-like patterns
                    for pattern_start in ["Unknown:", "Unclear:", "Need to investigate:", "TODO:"]:
                        if pattern_start in text_content:
                            for sentence in text_content.split('.'):
                                if pattern_start.rstrip(':') in sentence:
                                    unknown = sentence.strip()
                                    if len(unknown) > 10:
                                        unknowns.append(unknown[:200])
                                    break

            except json.JSONDecodeError:
                continue

    except (OSError, UnicodeDecodeError):
        pass

    return {
        "findings": findings[:5],  # Cap at 5 per type
        "unknowns": unknowns[:5],
        "dead_ends": dead_ends[:3]
    }


def rollup_to_parent(parent_session_id: str, agent_name: str, extracted: dict):
    """Log extracted findings/unknowns to parent session."""
    logged = {"findings": 0, "unknowns": 0, "dead_ends": 0}

    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()

        # Resolve project_id from parent session
        parent = db.sessions.get_session(parent_session_id)
        project_id = parent.get("project_id", "") if parent else ""

        for finding in extracted.get("findings", []):
            try:
                db.log_finding(
                    project_id=project_id,
                    session_id=parent_session_id,
                    finding=f"[{agent_name}] {finding}",
                    impact=0.5
                )
                logged["findings"] += 1
            except Exception:
                pass

        for unknown in extracted.get("unknowns", []):
            try:
                db.log_unknown(
                    project_id=project_id,
                    session_id=parent_session_id,
                    unknown=f"[{agent_name}] {unknown}"
                )
                logged["unknowns"] += 1
            except Exception:
                pass

        for dead_end in extracted.get("dead_ends", []):
            try:
                db.log_dead_end(
                    project_id=project_id,
                    session_id=parent_session_id,
                    approach=f"[{agent_name}] {dead_end.get('approach', 'unknown')}",
                    why_failed=dead_end.get('why_failed', 'unknown')
                )
                logged["dead_ends"] += 1
            except Exception:
                pass

        # End the child session
        subagent_data = find_subagent_session(agent_name)
        if subagent_data:
            child_session_id = subagent_data.get("child_session_id")
            if child_session_id:
                try:
                    db.end_session(child_session_id)
                except Exception:
                    pass

        db.close()
    except ImportError:
        pass

    return logged


def main():
    try:
        input_data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}
    except (json.JSONDecodeError, EOFError):
        input_data = {}

    agent_name = input_data.get("agent_name", input_data.get("agent_type", "unknown-agent"))
    transcript_path = input_data.get("agent_transcript_path", "")

    # Find the subagent session
    subagent_data = find_subagent_session(agent_name)

    if not subagent_data:
        result = {
            "continue": True,
            "message": f"SubagentStop: No active session found for '{agent_name}'. Skipping rollup."
        }
        print(json.dumps(result))
        return

    parent_session_id = subagent_data.get("parent_session_id")
    child_session_id = subagent_data.get("child_session_id")

    # Extract findings from transcript
    extracted = extract_findings_from_transcript(transcript_path)
    total_extracted = sum(len(v) for v in extracted.values())

    # Roll up to parent session
    logged = {"findings": 0, "unknowns": 0, "dead_ends": 0}
    if parent_session_id and total_extracted > 0:
        logged = rollup_to_parent(parent_session_id, agent_name, extracted)

    # Mark session completed
    if subagent_data.get("_file_path"):
        mark_session_completed(subagent_data["_file_path"], {
            "extracted": total_extracted,
            "logged": logged,
            "transcript_path": transcript_path
        })

    total_logged = sum(logged.values())
    result = {
        "continue": True,
        "message": f"SubagentStop: Agent '{agent_name}' completed. "
                   f"Extracted {total_extracted} artifacts, rolled up {total_logged} to parent {parent_session_id[:8] if parent_session_id else 'none'}."
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
