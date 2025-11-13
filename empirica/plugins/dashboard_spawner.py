#!/usr/bin/env python3
"""
Dashboard Spawner - AI Orchestration Visibility Plugin

This module allows AIs to spawn tmux dashboards for transparency.
Empirica works fine without it - this just gives users visibility.

AI Usage:
    from empirica.plugins.dashboard_spawner import spawn_dashboard_if_possible

    # AI detects tmux and spawns dashboard automatically
    spawn_dashboard_if_possible()  # Non-blocking, silent if no tmux

Design:
    - Auto-detects tmux environment
    - Spawns dashboard if tmux available
    - Silent failure if no tmux (Empirica still works)
    - Uses libtmux for clean spawning
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Try to import libtmux
try:
    import libtmux
    LIBTMUX_AVAILABLE = True
except ImportError:
    LIBTMUX_AVAILABLE = False
    libtmux = None


class DashboardSpawner:
    """
    Spawns Empirica dashboard for AI orchestration visibility

    Design Philosophy:
    - Non-intrusive: Works silently, fails gracefully
    - AI-friendly: Simple API for AI orchestration
    - Optional: Empirica works fine without it
    """

    def __init__(self):
        self.empirica_root = self._find_empirica_root()
        # Use new CASCADE monitor (minimalist design)
        self.dashboard_script = self.empirica_root / "empirica/dashboard/cascade_monitor.py"

    def _find_empirica_root(self) -> Path:
        """Find Empirica root directory"""
        # Try from current file location
        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / "empirica" / "plugins").exists():
                return parent

        # Fallback to common locations
        possible = [
            Path("/home/yogapad/empirical-ai/empirica"),
            Path.cwd(),
        ]

        for path in possible:
            if path.exists() and (path / "empirica").exists():
                return path

        return Path.cwd()

    def is_tmux_available(self) -> bool:
        """Check if running in tmux"""
        return bool(os.environ.get('TMUX'))

    def is_libtmux_available(self) -> bool:
        """Check if libtmux is available"""
        return LIBTMUX_AVAILABLE

    def get_dashboard_status(self) -> Dict[str, Any]:
        """Get current dashboard status"""
        if not self.is_tmux_available():
            return {
                "status": "not_available",
                "reason": "not_in_tmux",
                "message": "Empirica works fine without tmux - this is just for visibility"
            }

        if not self.is_libtmux_available():
            return {
                "status": "degraded",
                "reason": "libtmux_not_installed",
                "message": "Install libtmux for dashboard: pip install libtmux"
            }

        # Check if dashboard already running
        try:
            server = libtmux.Server()
            sessions = server.sessions

            if not sessions:
                return {"status": "no_session"}

            # Check panes for dashboard process
            for session in sessions:
                for window in session.windows:
                    for pane in window.panes:
                        cmd = pane.get('pane_current_command', '')
                        if 'snapshot_monitor' in cmd or 'python' in cmd:
                            return {
                                "status": "running",
                                "session": session.name,
                                "pane": pane.get('pane_id')
                            }

            return {"status": "not_running"}

        except Exception as e:
            logger.debug(f"Error checking dashboard status: {e}")
            return {"status": "unknown", "error": str(e)}

    def _get_current_session_name(self) -> Optional[str]:
        """Get current tmux session name from environment or display-message"""
        # Try tmux display-message first (most reliable)
        try:
            import subprocess
            result = subprocess.run(
                ['tmux', 'display-message', '-p', '#{session_name}'],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.debug(f"Could not get session name via display-message: {e}")

        # Fallback: parse $TMUX environment variable
        # Format: /tmp/tmux-{uid}/{server},{session_id},{window_index}
        tmux_env = os.environ.get('TMUX')
        if tmux_env:
            try:
                # Try to extract session ID from $TMUX, but this is unreliable
                # So we'll just return None and let libtmux handle it
                pass
            except Exception:
                pass

        return None

    def spawn_dashboard(self, force: bool = False) -> Dict[str, Any]:
        """
        Spawn dashboard in tmux (if available)

        Args:
            force: Force spawn even if dashboard already running

        Returns:
            Dict with spawn status
        """
        # Check if tmux available
        if not self.is_tmux_available():
            return {
                "spawned": False,
                "reason": "not_in_tmux",
                "message": "Not in tmux - Empirica works fine without it"
            }

        # Check if libtmux available
        if not self.is_libtmux_available():
            logger.warning("libtmux not available, dashboard spawning disabled")
            return {
                "spawned": False,
                "reason": "libtmux_not_available",
                "message": "Install libtmux for dashboard: pip install libtmux"
            }

        try:
            # Get current status
            status = self.get_dashboard_status()

            if status.get("status") == "running" and not force:
                return {
                    "spawned": False,
                    "reason": "already_running",
                    "session": status.get("session"),
                    "pane": status.get("pane")
                }

            # Spawn dashboard
            server = libtmux.Server()

            # Get current session name from tmux display-message
            current_session_name = self._get_current_session_name()

            if not current_session_name:
                logger.warning("Could not detect current session name")
                return {"spawned": False, "reason": "no_current_session"}

            # Find the actual current session by name
            session = server.find_where({"session_name": current_session_name})

            if not session:
                logger.warning(f"Session '{current_session_name}' not found")
                return {"spawned": False, "reason": "session_not_found"}

            window = session.active_window

            # Check pane count
            panes = window.panes

            if len(panes) == 1:
                # Single pane - split horizontally
                new_pane = window.split_window(vertical=False, percent=30)

                # Launch dashboard
                launch_cmd = f"cd {self.empirica_root} && python3 {self.dashboard_script}"
                new_pane.send_keys(launch_cmd)

                # Focus back on main pane
                panes[0].select_pane()

                return {
                    "spawned": True,
                    "method": "libtmux",
                    "layout": "split_horizontal",
                    "session": session.name,
                    "pane": new_pane.get('pane_id'),
                    "message": "Dashboard spawned in right pane (30%)"
                }

            elif len(panes) >= 2:
                # Multiple panes - use pane 1
                target_pane = panes[1]

                # Kill existing process
                target_pane.send_keys('C-c')
                import time
                time.sleep(0.5)

                # Launch dashboard
                launch_cmd = f"cd {self.empirica_root} && python3 {self.dashboard_script}"
                target_pane.send_keys(launch_cmd)

                return {
                    "spawned": True,
                    "method": "libtmux",
                    "layout": "existing_pane",
                    "session": session.name,
                    "pane": target_pane.get('pane_id'),
                    "message": "Dashboard spawned in existing pane 1"
                }

        except Exception as e:
            logger.error(f"Failed to spawn dashboard: {e}")
            return {
                "spawned": False,
                "reason": "error",
                "error": str(e)
            }


# Singleton instance
_spawner = None

def get_spawner() -> DashboardSpawner:
    """Get singleton DashboardSpawner instance"""
    global _spawner
    if _spawner is None:
        _spawner = DashboardSpawner()
    return _spawner


# Convenience functions for AI use
def spawn_dashboard_if_possible() -> bool:
    """
    AI-friendly: Spawn dashboard if tmux available, silent otherwise

    Returns:
        True if spawned, False otherwise (not an error!)

    Usage (AI):
        # At start of orchestration, give user visibility
        spawn_dashboard_if_possible()

        # Continue with normal work (works fine either way)
        result = modality_switcher.route(...)
    """
    spawner = get_spawner()
    result = spawner.spawn_dashboard()

    if result.get("spawned"):
        logger.info(f"Dashboard spawned: {result.get('message')}")
        return True
    else:
        logger.debug(f"Dashboard not spawned: {result.get('reason')}")
        return False


def check_dashboard_status() -> Dict[str, Any]:
    """
    Check if dashboard is running

    Returns:
        Status dict
    """
    spawner = get_spawner()
    return spawner.get_dashboard_status()


def spawn_dashboard(force: bool = False) -> Dict[str, Any]:
    """
    Spawn dashboard (with control over force)

    Args:
        force: Force spawn even if already running

    Returns:
        Spawn result dict
    """
    spawner = get_spawner()
    return spawner.spawn_dashboard(force=force)


# Auto-spawn on import (if AI imports this module)
def _auto_spawn_on_import():
    """
    Auto-spawn dashboard when this module is imported by an AI

    Philosophy:
    - If AI imports dashboard_spawner, it wants visibility
    - Spawn silently if possible
    - Don't fail if not possible
    """
    # Only auto-spawn if:
    # 1. In tmux
    # 2. libtmux available
    # 3. Not already running

    spawner = get_spawner()

    if spawner.is_tmux_available() and spawner.is_libtmux_available():
        status = spawner.get_dashboard_status()

        if status.get("status") != "running":
            result = spawner.spawn_dashboard()

            if result.get("spawned"):
                logger.info("✨ Dashboard auto-spawned for AI orchestration visibility")


# Auto-spawn on import (commented out by default - AI can enable)
# _auto_spawn_on_import()


if __name__ == "__main__":
    """Test dashboard spawner"""
    import sys

    logging.basicConfig(level=logging.INFO)

    spawner = DashboardSpawner()

    print("Dashboard Spawner Test")
    print("=" * 60)

    print(f"Empirica root: {spawner.empirica_root}")
    print(f"Dashboard script: {spawner.dashboard_script}")
    print(f"In tmux: {spawner.is_tmux_available()}")
    print(f"libtmux available: {spawner.is_libtmux_available()}")

    print("\nCurrent status:")
    status = spawner.get_dashboard_status()
    for key, value in status.items():
        print(f"  {key}: {value}")

    if len(sys.argv) > 1 and sys.argv[1] == "--spawn":
        print("\nSpawning dashboard...")
        result = spawner.spawn_dashboard()
        for key, value in result.items():
            print(f"  {key}: {value}")
