#!/usr/bin/env python3
"""
Dashboard Command Handler - Launch TUI Dashboard
"""

import sys
from ..cli_utils import handle_cli_error


def handle_dashboard_command(args):
    """Handle dashboard command - launch TUI"""
    try:
        from empirica.tui.dashboard import run_dashboard

        # Check if textual is installed
        try:
            import textual
        except ImportError:
            print("❌ Error: textual library not installed")
            print("\nInstall with: pip install textual")
            sys.exit(1)

        # Launch dashboard
        run_dashboard()

    except KeyboardInterrupt:
        print("\n👋 Dashboard closed")
    except Exception as e:
        handle_cli_error(e, "Dashboard", getattr(args, 'verbose', False))
        sys.exit(1)
