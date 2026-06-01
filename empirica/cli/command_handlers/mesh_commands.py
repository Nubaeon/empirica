"""Unified mesh diagnostic + control surface — `empirica mesh ...`.

Consolidates listener service management, instance health, zombie
detection, and live tail across the two layers of the empirica mesh:

  LOCAL — single-tenant multi-practitioner mesh primitives that work
          on empirica core alone (systemd-user / launchd persistent
          listener service running per ai_id, loop_fires.log writes,
          local loop scheduling).

  CORTEX BRIDGE — the optional proprietary cross-tenant overlay
          (curl subscription to ntfy, proposal_event ingestion,
          inbox poll). Surfaced only when `~/.empirica/credentials.yaml`
          declares a cortex section.

The two layers are reported distinctly so empirica core users see local
health without cortex noise; cortex users see both. Falls out of the
core-vs-proprietary split.

Why this exists: diagnosing a curl-subscription zombie (TCP died,
process still alive, no fires writing) previously required
`systemctl status` + `ps aux | grep curl` + `grep loop_fires.log` +
`cortex_inbox_poll` to triangulate. `empirica mesh status` collapses
that surface to one command.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

from empirica.core.loop_scheduler.persistent_listener import (
    install_listener_for,
    listener_status_for,
    uninstall_listener_for,
)

LOOP_FIRES_LOG = Path.home() / ".empirica" / "loop_fires.log"
CREDENTIALS_YAML = Path.home() / ".empirica" / "credentials.yaml"

# Threshold past which a cortex-bridged instance with no fires is suspected
# zombie. Tuned to be above the normal idle gap between cortex polls.
ZOMBIE_THRESHOLD_SECONDS = 1800  # 30 min


class MeshInstanceState(NamedTuple):
    ai_id: str
    backend: str
    service_installed: bool
    service_active: bool
    listener_process_pid: int | None
    curl_subprocess_pid: int | None
    last_fire_at_utc: datetime | None
    fires_last_hour: int
    cortex_configured: bool
    loops_registered: int
    health_color: str  # green | yellow | red
    health_reason: str


def _load_cortex_credentials() -> dict | None:
    if not CREDENTIALS_YAML.exists():
        return None
    try:
        import yaml
        with CREDENTIALS_YAML.open() as f:
            data = yaml.safe_load(f) or {}
        cortex = data.get("cortex")
        if cortex and cortex.get("api_key"):
            return cortex
    except Exception:
        pass
    return None


def _enumerate_instances() -> list[str]:
    instances: set[str] = set()
    systemd_dir = Path.home() / ".config" / "systemd" / "user"
    if systemd_dir.exists():
        for unit in systemd_dir.glob("empirica-listener-*.service"):
            instances.add(unit.stem.removeprefix("empirica-listener-"))
    launchd_dir = Path.home() / "Library" / "LaunchAgents"
    if launchd_dir.exists():
        for plist in launchd_dir.glob("com.empirica.listener.*.plist"):
            instances.add(plist.stem.removeprefix("com.empirica.listener."))
    return sorted(instances)


def _find_listener_pids(ai_id: str) -> tuple[int | None, int | None]:
    try:
        ps_out = subprocess.run(
            ["ps", "-eo", "pid,args"],
            capture_output=True, text=True, timeout=5,
        ).stdout
    except Exception:
        return None, None
    listener_pid = None
    curl_pid = None
    listen_needle = f"loop listen --instance {ai_id}"
    curl_needle = f"tags={ai_id}"
    for line in ps_out.splitlines()[1:]:
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue
        pid_str, cmd = parts
        try:
            pid = int(pid_str)
        except ValueError:
            continue
        if listen_needle in cmd and "loop listen" in cmd:
            listener_pid = pid
        elif "orchestration-events" in cmd and curl_needle in cmd:
            curl_pid = pid
    return listener_pid, curl_pid


def _last_fire_for(ai_id: str) -> tuple[datetime | None, int]:
    if not LOOP_FIRES_LOG.exists():
        return None, 0
    last_ts: datetime | None = None
    fires_last_hour = 0
    now = datetime.now(tz=timezone.utc)
    cutoff_ts = now.timestamp() - 3600
    needle = f'"instance_id": "{ai_id}"'
    try:
        with LOOP_FIRES_LOG.open() as f:
            for line in f:
                if needle not in line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                ts_str = entry.get("ts")
                if not ts_str:
                    continue
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except Exception:
                    continue
                if last_ts is None or ts > last_ts:
                    last_ts = ts
                if ts.timestamp() >= cutoff_ts:
                    fires_last_hour += 1
    except Exception:
        pass
    return last_ts, fires_last_hour


def _compute_health(s: dict, cortex_configured: bool) -> tuple[str, str]:
    if not s["service_installed"]:
        return "yellow", "service not installed"
    if not s["service_active"]:
        return "red", "service inactive"
    if s["listener_process_pid"] is None:
        return "red", "listener process not found despite active service"
    if not cortex_configured:
        return "green", "local-only (cortex bridge not configured)"
    if s["curl_subprocess_pid"] is None:
        return "red", "curl subscription dead — cortex bridge broken"
    last = s["last_fire_at_utc"]
    if last is None:
        return "yellow", "no fires recorded yet (cold start ok if recent install)"
    idle_seconds = (datetime.now(tz=timezone.utc) - last).total_seconds()
    if idle_seconds > ZOMBIE_THRESHOLD_SECONDS:
        return "red", f"zombie suspected: no fires in {int(idle_seconds // 60)} min"
    return "green", f"last fire {_fmt_age(idle_seconds)} ago"


def _fmt_age(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds // 60)}m"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h"
    return f"{int(seconds // 86400)}d"


def _gather_state(ai_id: str, cortex_configured: bool) -> MeshInstanceState:
    svc = listener_status_for(ai_id)
    listener_pid, curl_pid = _find_listener_pids(ai_id)
    last_fire, fires_last_hour = _last_fire_for(ai_id)
    loops_count = 0
    try:
        from empirica.core.loop_scheduler.systemd import list_active_loops_for_instance
        loops_count = len(list_active_loops_for_instance(ai_id) or [])
    except Exception:
        pass
    s = dict(
        ai_id=ai_id,
        backend=svc.backend,
        service_installed=svc.installed,
        service_active=svc.active,
        listener_process_pid=listener_pid,
        curl_subprocess_pid=curl_pid,
        last_fire_at_utc=last_fire,
        fires_last_hour=fires_last_hour,
        cortex_configured=cortex_configured,
        loops_registered=loops_count,
    )
    color, reason = _compute_health(s, cortex_configured)
    return MeshInstanceState(**s, health_color=color, health_reason=reason)


# ── Verbs ──────────────────────────────────────────────────────────────


def handle_mesh_status_command(args) -> int:
    cortex_configured = _load_cortex_credentials() is not None
    target = getattr(args, "instance", None)
    instances = [target] if target else _enumerate_instances()
    rows = [_gather_state(ai_id, cortex_configured) for ai_id in instances]

    if getattr(args, "output", "human") == "json":
        out = []
        for r in rows:
            d = r._asdict()
            if d["last_fire_at_utc"]:
                d["last_fire_at_utc"] = d["last_fire_at_utc"].isoformat()
            out.append(d)
        print(json.dumps(
            {"ok": True, "cortex_configured": cortex_configured, "instances": out},
            indent=2,
        ))
        return 0

    if not rows:
        print("No mesh instances registered.")
        print("Try: empirica mesh on <ai_id>")
        return 0

    glyph = {"green": "OK ", "yellow": "WARN", "red": "DOWN"}
    header = f"{'ai_id':<20} {'health':<6} {'service':<10} {'curl':<8} {'last fire':<12} {'fires/h':>8}  reason"
    print(header)
    print("-" * len(header))
    for r in rows:
        if r.last_fire_at_utc:
            idle = (datetime.now(tz=timezone.utc) - r.last_fire_at_utc).total_seconds()
            last_str = _fmt_age(idle)
        else:
            last_str = "-"
        svc_str = "active" if r.service_active else ("dead" if r.service_installed else "absent")
        if r.cortex_configured:
            curl_str = "ok" if r.curl_subprocess_pid else "dead"
        else:
            curl_str = "n/a"
        g = glyph.get(r.health_color, "?")
        print(f"{r.ai_id:<20} {g:<6} {svc_str:<10} {curl_str:<8} {last_str:<12} {r.fires_last_hour:>8}  {r.health_reason}")

    if not cortex_configured:
        print()
        print("Cortex bridge not configured -- running local-only.")
        print("Single-tenant multi-practitioner coordination works without cortex.")
        print("For cross-tenant + push-wake + browser triage, see https://getempirica.com")
    return 0


def handle_mesh_diagnose_command(args) -> int:
    ai_id = args.instance
    cortex_configured = _load_cortex_credentials() is not None
    state = _gather_state(ai_id, cortex_configured)

    print(f"=== mesh diagnose: {ai_id} ===")
    print()
    print(f"  Backend:              {state.backend}")
    print(f"  Service installed:    {state.service_installed}")
    print(f"  Service active:       {state.service_active}")
    print(f"  Listener PID:         {state.listener_process_pid or 'NONE'}")
    print(f"  Loops registered:     {state.loops_registered}")
    print(f"  Cortex configured:    {cortex_configured}")
    if cortex_configured:
        print(f"  Curl subscription:    {state.curl_subprocess_pid or 'DEAD (no curl process for tags=' + ai_id + ')'}")
    if state.last_fire_at_utc:
        idle = (datetime.now(tz=timezone.utc) - state.last_fire_at_utc).total_seconds()
        print(f"  Last fire:            {state.last_fire_at_utc.isoformat()}  ({_fmt_age(idle)} ago)")
    else:
        print(f"  Last fire:            NEVER")
    print(f"  Fires in last hour:   {state.fires_last_hour}")
    print()
    print(f"  Health: {state.health_color.upper()} -- {state.health_reason}")
    print()

    if state.health_color == "green":
        print("No action needed.")
        return 0
    if not state.service_installed:
        print(f"Fix: empirica mesh on {ai_id}")
    elif not state.service_active:
        print(f"Fix: empirica mesh restart {ai_id}")
    elif cortex_configured and state.curl_subprocess_pid is None:
        print(f"Fix: empirica mesh restart {ai_id}  (curl subprocess died; restart re-spawns)")
    elif (state.last_fire_at_utc
          and (datetime.now(tz=timezone.utc) - state.last_fire_at_utc).total_seconds() > ZOMBIE_THRESHOLD_SECONDS):
        print("Likely curl-zombie (TCP died silently while process stayed alive).")
        print(f"Fix: empirica mesh restart {ai_id}")
    else:
        print(f"Manual investigation needed.")
        print(f"  journalctl --user -u empirica-listener-{ai_id}.service")
    return 1


def handle_mesh_restart_command(args) -> int:
    ai_id = args.instance
    svc = listener_status_for(ai_id)
    if not svc.installed:
        sys.stderr.write(f"service for '{ai_id}' not installed -- run: empirica mesh on {ai_id}\n")
        return 2

    print(f"Restarting empirica-listener-{ai_id}...")
    if svc.backend == "systemd":
        rc = subprocess.run(
            ["systemctl", "--user", "restart", f"empirica-listener-{ai_id}.service"],
            capture_output=True, text=True,
        )
        if rc.returncode != 0:
            sys.stderr.write(f"systemctl restart failed: {rc.stderr}\n")
            return 1
    elif svc.backend == "launchd":
        rc = subprocess.run(
            ["launchctl", "kickstart", "-k", f"gui/{__import__('os').getuid()}/com.empirica.listener.{ai_id}"],
            capture_output=True, text=True,
        )
        if rc.returncode != 0:
            sys.stderr.write(f"launchctl kickstart failed: {rc.stderr}\n")
            return 1
    else:
        sys.stderr.write(f"backend '{svc.backend}' restart not implemented\n")
        return 1

    time.sleep(2)
    new_state = listener_status_for(ai_id)
    if not new_state.active:
        sys.stderr.write("service did not become active after restart\n")
        return 1
    print(f"OK -- {ai_id} listener service restarted (active).")

    cortex_configured = _load_cortex_credentials() is not None
    if not cortex_configured:
        return 0

    print("Waiting up to 10s for first fire to confirm subscription is live...")
    baseline_last, _ = _last_fire_for(ai_id)
    for _ in range(10):
        time.sleep(1)
        last, _ = _last_fire_for(ai_id)
        if last and last != baseline_last:
            print(f"OK -- fire received at {last.isoformat()}; subscription live.")
            return 0
    print("WARN -- no fire received in 10s. Curl may still be warming or subscription is hung.")
    print(f"       diagnose further: empirica mesh diagnose {ai_id}")
    return 0


def handle_mesh_on_command(args) -> int:
    ai_id = args.instance
    svc = listener_status_for(ai_id)
    if svc.installed and svc.active:
        print(f"OK -- service for '{ai_id}' already installed + active.")
        return 0
    if not svc.installed:
        print(f"Installing listener service for '{ai_id}'...")
        try:
            install_listener_for(ai_id)
        except Exception as e:
            sys.stderr.write(f"install failed: {e}\n")
            return 1
    if svc.backend == "systemd":
        subprocess.run(
            ["systemctl", "--user", "enable", "--now",
             f"empirica-listener-{ai_id}.service"],
            capture_output=True, text=True, check=False,
        )
    new_state = listener_status_for(ai_id)
    if new_state.active:
        print(f"OK -- {ai_id} listener active.")
        return 0
    sys.stderr.write(
        f"failed to activate; check journalctl --user -u empirica-listener-{ai_id}.service\n"
    )
    return 1


def handle_mesh_off_command(args) -> int:
    ai_id = args.instance
    svc = listener_status_for(ai_id)
    if not svc.installed:
        print(f"service for '{ai_id}' not installed; nothing to do")
        return 0
    if svc.backend == "systemd":
        subprocess.run(
            ["systemctl", "--user", "disable", "--now",
             f"empirica-listener-{ai_id}.service"],
            capture_output=True, text=True, check=False,
        )
    if getattr(args, "uninstall", False):
        try:
            uninstall_listener_for(ai_id)
            print(f"OK -- {ai_id} listener uninstalled.")
        except Exception as e:
            sys.stderr.write(f"uninstall failed: {e}\n")
            return 1
    else:
        print(f"OK -- {ai_id} listener stopped (still installed; pass --uninstall to remove).")
    return 0


def handle_mesh_tail_command(args) -> int:
    if not LOOP_FIRES_LOG.exists():
        sys.stderr.write(f"{LOOP_FIRES_LOG} does not exist\n")
        return 1
    target = getattr(args, "instance", None)
    instances = [target] if target else _enumerate_instances()
    if not instances:
        sys.stderr.write("no instances to tail\n")
        return 1
    pattern = re.compile("|".join(re.escape(f'"instance_id": "{i}"') for i in instances))
    sys.stderr.write(
        f"tailing {LOOP_FIRES_LOG} for: {', '.join(instances)} (Ctrl-C to stop)\n"
    )
    proc = subprocess.Popen(
        ["tail", "-F", "-n", "0", str(LOOP_FIRES_LOG)],
        stdout=subprocess.PIPE, text=True,
    )
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            if pattern.search(line):
                sys.stdout.write(line)
                sys.stdout.flush()
    except KeyboardInterrupt:
        pass
    finally:
        proc.terminate()
    return 0


_MESH_DISPATCH = {
    "status": handle_mesh_status_command,
    "diagnose": handle_mesh_diagnose_command,
    "restart": handle_mesh_restart_command,
    "on": handle_mesh_on_command,
    "off": handle_mesh_off_command,
    "tail": handle_mesh_tail_command,
}


def handle_mesh_group_command(args) -> int:
    action = getattr(args, "mesh_action", None)
    if not action:
        sys.stderr.write(
            "usage: empirica mesh <status|diagnose|restart|on|off|tail> [args...]\n"
        )
        return 2
    handler = _MESH_DISPATCH.get(action)
    if handler is None:
        sys.stderr.write(f"error: unknown mesh action: {action}\n")
        return 2
    return handler(args) or 0


__all__ = [
    "handle_mesh_group_command",
    "handle_mesh_status_command",
    "handle_mesh_diagnose_command",
    "handle_mesh_restart_command",
    "handle_mesh_on_command",
    "handle_mesh_off_command",
    "handle_mesh_tail_command",
]
