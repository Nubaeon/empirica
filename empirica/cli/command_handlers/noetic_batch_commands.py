"""CLI handler for `empirica noetic-batch`.

Reads a JSON noetic-batch payload from stdin (AI-first pattern) or accepts
flag-form input. Returns merged structured response. See
docs/architecture/NOETIC_BATCH_SPEC.md for the full design.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def handle_noetic_batch_command(args) -> None:
    """Run a noetic batch and emit text or JSON report.

    Exit codes:
        0 — batch ok, all per-op succeeded
        1 — batch ok but ≥1 per-op error
        2 — schema validation failed (input invalid)
    """
    output_format = getattr(args, "output", "json")

    if getattr(args, "schema", False):
        _print_schema(output_format)
        sys.exit(0)

    payload = _resolve_payload(args)
    if payload is None:
        print(json.dumps({"ok": False, "error": "no input provided (use - for stdin or --intent + flags)"}))
        sys.exit(2)

    if getattr(args, "dry_run", False):
        from empirica.core.noetic_batch.schema import NoeticBatchInput
        try:
            parsed = NoeticBatchInput(**payload)
            result = {
                "ok": True,
                "dry_run": True,
                "intent": parsed.intent,
                "schema_version": parsed.schema_version,
                "operation_count": parsed.operation_count(),
            }
            print(json.dumps(result, indent=2))
            sys.exit(0)
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc)}))
            sys.exit(2)

    from empirica.core.noetic_batch import run_batch
    project_root = Path(getattr(args, "project_root", ".") or ".").resolve()

    try:
        result = run_batch(payload, project_root=project_root)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        sys.exit(2)

    error_count = (
        sum(1 for r in result.reads if r.error)
        + sum(1 for g in result.greps if g.error)
        + sum(1 for g in result.globs if g.error)
        + sum(1 for i in result.investigate if i.error)
    )

    if output_format == "json":
        print(result.model_dump_json(indent=2))
    else:
        _print_text_report(result.model_dump())

    sys.exit(0 if error_count == 0 else 1)


def _resolve_payload(args) -> dict | None:
    """Source the JSON payload from stdin (config='-') or build from flags."""
    config = getattr(args, "config", None)
    if config == "-":
        try:
            return json.loads(sys.stdin.read())
        except json.JSONDecodeError as exc:
            print(json.dumps({"ok": False, "error": f"invalid JSON on stdin: {exc}"}))
            sys.exit(2)

    if config and config != "-":
        try:
            return json.loads(Path(config).read_text())
        except (OSError, json.JSONDecodeError) as exc:
            print(json.dumps({"ok": False, "error": f"could not read config file: {exc}"}))
            sys.exit(2)

    intent = getattr(args, "intent", None)
    if not intent:
        return None

    payload: dict[str, Any] = {"intent": intent}
    reads = getattr(args, "read", None) or []
    greps = getattr(args, "grep", None) or []
    globs = getattr(args, "glob", None) or []
    investigates = getattr(args, "investigate", None) or []

    if reads:
        payload["reads"] = [{"path": r} for r in reads]
    if greps:
        payload["greps"] = [_parse_grep_flag(g) for g in greps]
    if globs:
        payload["globs"] = list(globs)
    if investigates:
        payload["investigate"] = [{"query": q} for q in investigates]
    return payload


def _parse_grep_flag(spec: str) -> dict:
    """Parse 'pattern' or 'pattern:glob' or 'pattern:glob:context=N' shorthand."""
    parts = spec.split(":")
    out: dict[str, Any] = {"pattern": parts[0]}
    if len(parts) > 1 and parts[1]:
        out["glob"] = parts[1]
    for extra in parts[2:]:
        if "=" in extra:
            k, v = extra.split("=", 1)
            if k == "context":
                out["context"] = int(v)
            elif k == "case_sensitive":
                out["case_sensitive"] = v.lower() in ("1", "true", "yes")
            elif k == "max_matches":
                out["max_matches"] = int(v)
    return out


def _print_schema(output_format: str) -> None:
    from empirica.core.noetic_batch.schema import NoeticBatchInput
    schema = NoeticBatchInput.model_json_schema()
    if output_format == "json":
        print(json.dumps(schema, indent=2))
    else:
        print("# Noetic Batch — input schema")
        print(f"# Schema version: {schema.get('properties', {}).get('schema_version', {}).get('default', '?')}")
        print(json.dumps(schema, indent=2))


def _print_text_report(report: dict) -> None:
    summary = report.get("summary", {})
    print("=" * 60)
    print(f"NOETIC BATCH  intent: {report.get('intent', '?')}")
    print("=" * 60)
    print(f"  Reads:        {summary.get('total_files_read', 0)}")
    print(f"  Grep matches: {summary.get('total_grep_matches', 0)}")
    print(f"  Globs:        {summary.get('total_globs_resolved', 0)}")
    print(f"  Investigate:  {summary.get('total_investigate_results', 0)}")
    print(f"  Duration:     {summary.get('duration_ms', 0)}ms")
    print(f"  ~Tokens:      {summary.get('approx_tokens', 0)}")
    print()

    for r in report.get("reads", []):
        if r.get("error"):
            print(f"  READ ERROR: {r['path']} — {r['error']}")
        else:
            tag = " (truncated)" if r.get("truncated") else ""
            print(f"  READ: {r['path']}  {r.get('size_bytes', 0)} bytes{tag}")

    for g in report.get("greps", []):
        if g.get("error"):
            print(f"  GREP ERROR: {g['pattern']} — {g['error']}")
        else:
            tag = " (truncated)" if g.get("truncated") else ""
            print(f"  GREP: '{g['pattern']}' in {g['glob']} → {g.get('total_matches', 0)} matches{tag}")

    for g in report.get("globs", []):
        if g.get("error"):
            print(f"  GLOB ERROR: {g['pattern']} — {g['error']}")
        else:
            tag = " (truncated)" if g.get("truncated") else ""
            print(f"  GLOB: {g['pattern']} → {g.get('total_matches', 0)} files{tag}")

    for i in report.get("investigate", []):
        if i.get("error"):
            print(f"  INVESTIGATE ERROR: {i['query']} — {i['error']}")
        else:
            print(f"  INVESTIGATE: '{i['query']}' [{i['scope']}] → {len(i.get('results', []))} results")
