"""
Empirica Doctor - Desktop + general health check.

Sibling to `diagnose` (which is Claude Code-centric). `doctor` checks the
state of an Empirica install regardless of frontend — empirica-mcp install,
.empirica/ folder, git remote, Cortex reachability, sync state.

Designed to be callable from Claude Desktop via the empirica-mcp `doctor`
tool, returning structured JSON the AI can interpret without shell access.

Output modes:
  --output json     (default) — machine-readable
  --output human    colored text with fix hints

Exit codes:
  0 — all checks passed
  1 — one or more FAIL checks
  2 — one or more WARN checks (no FAIL)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

PASS = "PASS"  # noqa: S105
FAIL = "FAIL"
WARN = "WARN"


@dataclass
class Check:
    name: str
    status: str
    detail: str = ""
    hint: str = ""
    data: dict[str, Any] = field(default_factory=dict)


def _which(cmd: str) -> str | None:
    return shutil.which(cmd)


def _run(args: list[str], timeout: float = 5.0) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        return -1, "", str(e)


def check_python() -> Check:
    v = sys.version_info
    if v >= (3, 10):
        return Check("Python version", PASS, f"{v.major}.{v.minor}.{v.micro}")
    return Check("Python version", FAIL, f"{v.major}.{v.minor}.{v.micro}",
                 "Empirica requires Python 3.10+")


def check_empirica_cli() -> Check:
    path = _which("empirica")
    if not path:
        return Check("empirica CLI on PATH", FAIL, "",
                     "pip install --user empirica  (then restart shell)")
    rc, out, _ = _run(["empirica", "--version"])
    version = out if rc == 0 else "unknown"
    return Check("empirica CLI on PATH", PASS, f"{path} ({version})",
                 data={"path": path, "version": version})


def check_empirica_mcp() -> Check:
    path = _which("empirica-mcp")
    if not path:
        return Check("empirica-mcp on PATH", FAIL, "",
                     "pip install --user empirica-mcp  (then restart Claude Desktop)",
                     data={"path": None})
    return Check("empirica-mcp on PATH", PASS, path, data={"path": path})


def check_empirica_folder(cwd: Path | None = None) -> Check:
    cwd = cwd or Path.cwd()
    folder = cwd / ".empirica"
    if not folder.exists():
        return Check(".empirica/ folder", WARN, f"not present at {cwd}",
                     "Run `empirica project-create` in a project directory")
    subdirs = [d.name for d in folder.iterdir() if d.is_dir()]
    return Check(".empirica/ folder", PASS, f"{folder} ({len(subdirs)} subdirs)",
                 data={"path": str(folder), "subdirs": subdirs})


def check_git_remote(cwd: Path | None = None) -> Check:
    cwd = cwd or Path.cwd()
    if not (cwd / ".git").exists():
        return Check("git repo", WARN, "not a git repo",
                     "git init && git remote add origin <url>")
    rc, out, _ = _run(["git", "-C", str(cwd), "remote", "-v"])
    if rc != 0 or not out:
        return Check("git remote", WARN, "no remote configured",
                     "git remote add origin <url>  — sync_push needs a remote")
    remotes = [line.split()[0] for line in out.splitlines() if line]
    return Check("git remote", PASS, f"{len(set(remotes))} configured",
                 data={"remotes": list(set(remotes))})


def check_sync_state(cwd: Path | None = None) -> Check:
    cwd = cwd or Path.cwd()
    if not (cwd / ".git").exists():
        return Check("sync state", WARN, "not a git repo")
    rc, out, _ = _run(["git", "-C", str(cwd), "status", "--porcelain"])
    if rc != 0:
        return Check("sync state", WARN, "git status failed")
    pending = len([line for line in out.splitlines() if line.strip()])
    if pending > 0:
        return Check("sync state", WARN, f"{pending} uncommitted changes",
                     "Call empirica sync-push to propagate to Cortex",
                     data={"pending_changes": pending})
    return Check("sync state", PASS, "clean", data={"pending_changes": 0})


def check_cortex_reachability() -> Check:
    cortex_url = os.environ.get("CORTEX_URL", "https://cortex.getempirica.com")
    health_url = f"{cortex_url.rstrip('/')}/cortex/health"
    try:
        import urllib.request
        with urllib.request.urlopen(health_url, timeout=5) as resp:
            ok = resp.status == 200
            return Check("Cortex reachability", PASS if ok else WARN,
                         f"{health_url} → {resp.status}",
                         data={"url": cortex_url, "status": resp.status})
    except Exception as e:
        return Check("Cortex reachability", WARN, f"{health_url} unreachable: {e}",
                     "Check network or CORTEX_URL env var",
                     data={"url": cortex_url, "error": str(e)})


def run_all_checks(cwd: Path | None = None) -> list[Check]:
    return [
        check_python(),
        check_empirica_cli(),
        check_empirica_mcp(),
        check_empirica_folder(cwd),
        check_git_remote(cwd),
        check_sync_state(cwd),
        check_cortex_reachability(),
    ]


def _format_human(checks: list[Check]) -> str:
    icons = {PASS: "\033[32m✓\033[0m", FAIL: "\033[31m✗\033[0m", WARN: "\033[33m⚠\033[0m"}
    lines = ["", "\033[1mEmpirica Doctor\033[0m", "=" * 40]
    for c in checks:
        icon = icons.get(c.status, "?")
        lines.append(f"{icon} {c.name}: {c.detail}")
        if c.hint and c.status != PASS:
            lines.append(f"    \033[90m→ {c.hint}\033[0m")
    fails = sum(1 for c in checks if c.status == FAIL)
    warns = sum(1 for c in checks if c.status == WARN)
    summary = f"\n{len(checks)} checks: {len(checks) - fails - warns} pass, {warns} warn, {fails} fail"
    lines.append(summary)
    return "\n".join(lines)


def handle_doctor_command(args: Any) -> int:
    cwd = Path.cwd()
    checks = run_all_checks(cwd)
    fails = sum(1 for c in checks if c.status == FAIL)
    warns = sum(1 for c in checks if c.status == WARN)
    output_format = getattr(args, "output", "json")
    if output_format == "human":
        print(_format_human(checks))
    else:
        payload = {
            "ok": fails == 0,
            "summary": {"total": len(checks), "pass": len(checks) - fails - warns,
                        "warn": warns, "fail": fails},
            "checks": [asdict(c) for c in checks],
            "cwd": str(cwd),
        }
        print(json.dumps(payload, indent=2))
    if fails:
        return 1
    if warns:
        return 2
    return 0
