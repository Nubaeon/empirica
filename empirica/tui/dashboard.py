#!/usr/bin/env python3
"""
Empirica TUI Dashboard - Main Application

Terminal-based dashboard for monitoring AI activity in current project.
Shows active context (project, database, git repo) and epistemic state.
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container, VerticalScroll
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
import time
from datetime import datetime, timedelta
from pathlib import Path

from empirica.data.session_database import SessionDatabase
from empirica.config.path_resolver import debug_paths


class ProjectHeader(Static):
    """Display current project context"""

    def on_mount(self):
        self.update_context()
        self.set_interval(5.0, self.update_context)

    def update_context(self):
        """Refresh project context information"""
        paths = debug_paths()

        content = Text()
        content.append("📁 Project: ", style="bold cyan")
        content.append(f"{Path.cwd().name}\n", style="yellow")

        content.append("🗄️  Database: ", style="bold cyan")
        db_path = paths.get('session_db', 'Unknown')
        content.append(f"{db_path}\n", style="green")

        content.append("📂 Git Repo: ", style="bold cyan")
        git_root = paths.get('git_root', 'Not in git repo')
        content.append(f"{git_root}", style="blue")

        self.update(Panel(content, title="[bold]EMPIRICA PROJECT MONITOR[/bold]", border_style="cyan"))


class ActivityPanel(Static):
    """Display current session activity"""

    def on_mount(self):
        self.update_activity()
        self.set_interval(1.0, self.update_activity)

    def update_activity(self):
        """Refresh activity information"""
        try:
            db = SessionDatabase()
            cursor = db.conn.cursor()

            # Get active session (most recent without end_time)
            cursor.execute("""
                SELECT session_id, ai_id, start_time, project_id
                FROM sessions
                WHERE end_time IS NULL
                ORDER BY start_time DESC
                LIMIT 1
            """)

            row = cursor.fetchone()

            if row:
                session_id = row['session_id']
                ai_id = row['ai_id']
                start_time = row['start_time']

                # Calculate session duration
                start_dt = datetime.fromisoformat(start_time)
                duration = datetime.now() - start_dt
                duration_str = str(duration).split('.')[0]  # Remove microseconds

                # Get latest reflex for phase information
                cursor.execute("""
                    SELECT phase, round_num, timestamp
                    FROM reflexes
                    WHERE session_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (session_id,))

                reflex_row = cursor.fetchone()

                content = Text()
                content.append("🆔 Session: ", style="bold cyan")
                content.append(f"{session_id[:8]}... ", style="yellow")
                content.append(f"(AI: {ai_id})\n", style="green")

                content.append("⏱️  Duration: ", style="bold cyan")
                content.append(f"{duration_str}\n", style="white")

                if reflex_row:
                    phase = reflex_row['phase']
                    round_num = reflex_row['round_num']
                    reflex_time = datetime.fromisoformat(reflex_row['timestamp'])
                    time_in_phase = datetime.now() - reflex_time

                    content.append("🎯 Phase: ", style="bold cyan")
                    content.append(f"{phase} ", style="magenta bold")
                    content.append(f"(Round {round_num})\n", style="white")

                    content.append("⏰ Time in Phase: ", style="bold cyan")
                    content.append(f"{str(time_in_phase).split('.')[0]}", style="white")
                else:
                    content.append("🎯 Phase: ", style="bold cyan")
                    content.append("No reflexes yet", style="dim")
            else:
                content = Text("No active session", style="dim italic")

            db.close()

            self.update(Panel(content, title="[bold]CURRENT ACTIVITY[/bold]", border_style="green"))

        except Exception as e:
            self.update(Panel(f"Error: {e}", title="[bold red]ERROR[/bold red]", border_style="red"))


class VectorsPanel(Static):
    """Display epistemic vectors"""

    def on_mount(self):
        self.update_vectors()
        self.set_interval(1.0, self.update_vectors)

    def update_vectors(self):
        """Refresh epistemic vectors"""
        try:
            db = SessionDatabase()
            cursor = db.conn.cursor()

            # Get active session
            cursor.execute("""
                SELECT session_id FROM sessions
                WHERE end_time IS NULL
                ORDER BY start_time DESC
                LIMIT 1
            """)

            session_row = cursor.fetchone()

            if session_row:
                session_id = session_row['session_id']

                # Get latest two reflexes for delta calculation
                cursor.execute("""
                    SELECT engagement, know, context, uncertainty, timestamp
                    FROM reflexes
                    WHERE session_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 2
                """, (session_id,))

                rows = cursor.fetchall()

                if rows:
                    latest = rows[0]
                    previous = rows[1] if len(rows) > 1 else None

                    # Build vector display
                    table = Table(show_header=False, box=None, padding=(0, 1))
                    table.add_column("Vector", style="cyan bold", width=15)
                    table.add_column("Bar", width=20)
                    table.add_column("Value", style="white", width=6)
                    table.add_column("Delta", width=8)

                    vectors = [
                        ("Engagement", latest['engagement']),
                        ("Know", latest['know']),
                        ("Context", latest['context']),
                        ("Uncertainty", latest['uncertainty'])
                    ]

                    for name, value in vectors:
                        # Create progress bar
                        filled = int(value * 10)
                        bar = "█" * filled + "░" * (10 - filled)

                        # Calculate delta
                        if previous:
                            prev_key = name.lower()
                            delta = value - previous[prev_key]
                            delta_str = f"{'⬆' if delta > 0 else '⬇'} {delta:+.2f}" if abs(delta) > 0.01 else ""
                            delta_style = "green" if delta > 0 else "red" if delta < 0 else "dim"
                        else:
                            delta_str = ""
                            delta_style = "dim"

                        table.add_row(
                            name,
                            bar,
                            f"{value:.2f}",
                            Text(delta_str, style=delta_style)
                        )

                    self.update(Panel(table, title="[bold]EPISTEMIC STATE[/bold]", border_style="magenta"))
                else:
                    self.update(Panel("No epistemic data yet", title="[bold]EPISTEMIC STATE[/bold]", border_style="dim"))
            else:
                self.update(Panel("No active session", title="[bold]EPISTEMIC STATE[/bold]", border_style="dim"))

            db.close()

        except Exception as e:
            self.update(Panel(f"Error: {e}", title="[bold red]ERROR[/bold red]", border_style="red"))


class CommandsLog(Static):
    """Display recent activity log"""

    def on_mount(self):
        self.update_log()
        self.set_interval(2.0, self.update_log)

    def update_log(self):
        """Refresh command log from database"""
        try:
            db = SessionDatabase()
            cursor = db.conn.cursor()

            # Get recent findings and unknowns as proxy for activity
            cursor.execute("""
                SELECT 'FINDING' as type, finding as message, timestamp
                FROM project_findings
                UNION ALL
                SELECT 'UNKNOWN' as type, unknown as message, timestamp
                FROM project_unknowns
                WHERE is_resolved = 0
                ORDER BY timestamp DESC
                LIMIT 5
            """)

            rows = cursor.fetchall()

            if rows:
                content = Text()
                for row in rows:
                    event_type = row['type']
                    message = row['message']
                    timestamp = datetime.fromisoformat(row['timestamp'])
                    time_str = timestamp.strftime("%H:%M:%S")

                    # Color based on type
                    type_style = "green" if event_type == "FINDING" else "yellow"

                    content.append(f"{time_str} ", style="dim")
                    content.append(f"[{event_type}] ", style=type_style)
                    content.append(f"{message[:60]}...\n" if len(message) > 60 else f"{message}\n")

                self.update(Panel(content, title="[bold]RECENT ACTIVITY[/bold]", border_style="blue"))
            else:
                self.update(Panel("No recent activity", title="[bold]RECENT ACTIVITY[/bold]", border_style="dim"))

            db.close()

        except Exception as e:
            self.update(Panel(f"Error: {e}", title="[bold red]ERROR[/bold red]", border_style="red"))


class EmpiricaDashboard(App):
    """Empirica TUI Dashboard Application"""

    CSS = """
    Screen {
        background: $background;
    }

    .container {
        height: auto;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("c", "clear", "Clear"),
    ]

    def compose(self) -> ComposeResult:
        """Create dashboard layout"""
        yield Header()
        yield ProjectHeader()
        yield ActivityPanel()
        yield VectorsPanel()
        yield CommandsLog()
        yield Footer()

    def action_refresh(self):
        """Manually refresh all panels"""
        for widget in self.query(Static):
            if hasattr(widget, 'update_context'):
                widget.update_context()
            elif hasattr(widget, 'update_activity'):
                widget.update_activity()
            elif hasattr(widget, 'update_vectors'):
                widget.update_vectors()
            elif hasattr(widget, 'update_log'):
                widget.update_log()

    def action_clear(self):
        """Clear the screen"""
        self.clear()


def run_dashboard():
    """Entry point for dashboard command"""
    app = EmpiricaDashboard()
    app.run()


if __name__ == "__main__":
    run_dashboard()
