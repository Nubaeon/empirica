"""Natural-language workflow narration for empirica chat (Phase 15).

Per David's conversational-layer surface principle: the Sentinel-
enforced empirica discipline (PREFLIGHT/CHECK/POSTFLIGHT, transactions,
plans, artifact logs, skill invocations, agent launches) happens
under the hood. Chat does NOT expose JSON or raw tool-call output.

This module translates raw empirica events into terse natural-language
one-liners suitable for SystemTurn rendering — "thinking through…",
"ready to act on…", "logged: <finding>", "plan transitioned: …",
"invoking <skill>", "launching <agent>".

This v0 ships the pure translation layer + golden snapshot tests.
The live tail/dedup/threading wiring (Phase 15b) plugs into:
  - translator event tap JSONL (request_started, stream_event, etc)
  - empirica session DB events (reflexes table for transaction phases,
    project_findings/decisions/etc for artifact logs)
"""

from __future__ import annotations

from typing import Any


def _ellipsize(text: str | None, n: int = 40) -> str:
    if not text:
        return ""
    text = " ".join(text.split())  # collapse whitespace
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def _n_preflight(e: dict[str, Any]) -> str:
    ctx = _ellipsize(e.get("task_context"), 50)
    return f"thinking through: {ctx}" if ctx else "thinking through new transaction"


def _n_check(e: dict[str, Any]) -> str | None:
    d = e.get("decision", "")
    if d == "proceed":
        return "ready to act"
    if d == "investigate":
        return "needs more investigation"
    return None


def _n_postflight(e: dict[str, Any]) -> str:
    c = e.get("confidence")
    if isinstance(c, (int, float)):
        return f"wrapped up (confidence {int(c * 100)}%)"
    return "wrapped up transaction"


def _n_artifact(prefix: str, alt: str, *body_keys: str):
    """Factory for artifact_log narrators that share the body-extraction shape."""
    def _fn(e: dict[str, Any]) -> str:
        body = ""
        for k in body_keys:
            v = e.get(k)
            if v:
                body = _ellipsize(v, 60)
                break
        return f"{prefix}: {body}" if body else alt
    return _fn


def _n_skill(e: dict[str, Any]) -> str:
    return f"invoking skill: {e.get('skill') or e.get('name') or 'unknown'}"


def _n_agent(e: dict[str, Any]) -> str:
    agent = e.get("agent") or e.get("subagent_type") or "subagent"
    desc = _ellipsize(e.get("description"), 40)
    return f"launching {agent}" + (f" — {desc}" if desc else "")


def _n_plan(e: dict[str, Any]) -> str:
    return f"plan: {e.get('from') or '?'} → {e.get('to') or '?'}"


# Dispatch table — single source of truth for which kinds we narrate.
_EMPIRICA_NARRATORS = {
    "preflight": _n_preflight,
    "check": _n_check,
    "postflight": _n_postflight,
    "finding_log": _n_artifact("logged finding", "logged finding", "finding", "text"),
    "decision_log": _n_artifact("decided", "logged decision", "choice", "text"),
    "unknown_log": _n_artifact("open question", "logged unknown", "unknown", "text"),
    "mistake_log": _n_artifact("caught a mistake", "logged a mistake", "mistake", "text"),
    "deadend_log": _n_artifact("dead end", "hit a dead end", "approach", "text"),
    "assumption_log": _n_artifact("assuming", "logged assumption", "assumption", "text"),
    "goal_create": _n_artifact("new goal", "opened a goal", "objective"),
    "goal_complete": _n_artifact("goal complete", "closed a goal", "objective"),
    "skill_invoke": _n_skill,
    "agent_launch": _n_agent,
    "plan_transition": _n_plan,
}


def narrate_empirica_event(event: dict[str, Any]) -> str | None:
    """Translate one empirica-side event dict into a chat one-liner.

    Returns verbiage string (no formatting — caller wraps as SystemTurn).
    Returns None when the kind is unknown or the handler decides to mute.
    See `_EMPIRICA_NARRATORS` for recognized kinds.
    """
    handler = _EMPIRICA_NARRATORS.get(event.get("kind", ""))
    if handler is None:
        return None
    return handler(event)


def narrate_translator_event(event: dict[str, Any]) -> str | None:
    """Translate one translator event tap event into a chat one-liner.

    Translator events (per T28 Phase 4 of codex-empirica-translator):
      request_started   — outbound LLM call begins
      stream_event      — SSE chunk received (high-frequency; usually muted)
      request_completed — final response assembled
      request_errored   — upstream/parsing failure

    Most stream_event signals are too noisy to surface — return None.
    request_started/completed/errored translate to terse one-liners.
    """
    kind = event.get("kind") or event.get("type") or ""
    if not kind:
        return None

    if kind == "request_started":
        provider = event.get("provider") or "?"
        model = event.get("model") or "?"
        return f"calling {provider}:{model}"

    if kind == "request_completed":
        ms = event.get("duration_ms")
        chars = event.get("text_chars")
        bits = []
        if isinstance(ms, (int, float)):
            bits.append(f"{int(ms)}ms")
        if isinstance(chars, (int, float)):
            bits.append(f"{int(chars)} chars")
        suffix = f" ({', '.join(bits)})" if bits else ""
        return f"response complete{suffix}"

    if kind == "request_errored":
        stage = event.get("stage") or "?"
        err = _ellipsize(event.get("error") or event.get("message"), 60)
        return f"request error at {stage}" + (f": {err}" if err else "")

    # stream_event and other high-frequency events: silent at chat layer
    return None


def narrate(event: dict[str, Any]) -> str | None:
    """Best-effort dispatch: route by event source/shape.

    If the event has a `source: 'translator'` marker (as written by the
    translator's tap), use the translator narrator. Otherwise treat as
    an empirica-side event. Returns None when no surface is appropriate.
    """
    if event.get("source") == "translator":
        return narrate_translator_event(event)
    # Translator events also identifiable by characteristic keys
    if event.get("kind") in (
        "request_started", "request_completed",
        "request_errored", "stream_event",
    ):
        return narrate_translator_event(event)
    return narrate_empirica_event(event)
