"""Empirica CLI invocation helpers for chat artifact actions (Phase 4).

Slash commands in chat (/finding, /decision, /unknown) call these to
create real Empirica artifacts via the existing CLI. The returned
artifact_id flows into the rendered ArtifactCard so its action buttons
can later resolve/discuss/pin against the real artifact.

Subprocess pattern (same as cockpit_commands uses for privileged tools):
cheaper to maintain than direct module imports — no internal API churn
risk, no Python import-graph entanglement with the rest of empirica.

Phase 4 supports: finding, decision, unknown. Phase 4b adds: mistake,
dead_end, assumption, source. Goals + transactions remain CLI-only for v1.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any


class ActionError(RuntimeError):
    """Empirica CLI returned non-zero or unparseable JSON."""


def _run_cli(args: list[str], timeout: float = 10.0) -> dict[str, Any]:
    """Invoke `empirica <args>` with --output json appended, return parsed dict."""
    cmd = ["empirica", *args, "--output", "json"]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired as e:
        raise ActionError(f"empirica CLI timeout: {' '.join(cmd[:3])}") from e
    except FileNotFoundError as e:
        raise ActionError("empirica CLI not on PATH") from e

    if result.returncode != 0:
        raise ActionError(
            f"empirica CLI exit {result.returncode}: {result.stderr.strip() or result.stdout.strip()}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise ActionError(f"empirica CLI returned non-JSON: {result.stdout[:200]}") from e


def log_finding(text: str, impact: float = 0.5, subject: str | None = None) -> dict[str, Any]:
    """Create a finding artifact. Returns the parsed JSON response."""
    args = ["finding-log", "--finding", text, "--impact", str(impact)]
    if subject:
        args.extend(["--subject", subject])
    return _run_cli(args)


def log_decision(
    choice: str, rationale: str = "", reversibility: str = "exploratory"
) -> dict[str, Any]:
    """Create a decision artifact. Returns the parsed JSON response."""
    args = ["decision-log", "--choice", choice, "--reversibility", reversibility]
    if rationale:
        args.extend(["--rationale", rationale])
    return _run_cli(args)


def log_unknown(text: str, subject: str | None = None) -> dict[str, Any]:
    """Create an unknown artifact. Returns the parsed JSON response."""
    args = ["unknown-log", "--unknown", text]
    if subject:
        args.extend(["--subject", subject])
    return _run_cli(args)


def extract_artifact_id(response: dict[str, Any]) -> str | None:
    """Best-effort: pull the new artifact UUID from the CLI's JSON response.

    Different artifact loggers return slightly different JSON shapes — try
    common keys: id, finding_id, decision_id, unknown_id, artifact_id.
    """
    for key in ("id", "finding_id", "decision_id", "unknown_id",
                 "artifact_id", "uuid"):
        v = response.get(key)
        if isinstance(v, str) and v:
            return v
    # Some loggers nest the result one level
    for nested_key in ("finding", "decision", "unknown", "artifact", "result"):
        nested = response.get(nested_key)
        if isinstance(nested, dict):
            sub = extract_artifact_id(nested)
            if sub:
                return sub
    return None
