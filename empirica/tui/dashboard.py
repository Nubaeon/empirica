#!/usr/bin/env python3
"""
Empirica TUI Dashboard - Main Application

Terminal-based dashboard for monitoring AI activity, epistemic state,
and entity-aware artifacts (projects, contacts, engagements).
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
import sqlite3
from datetime import datetime
from pathlib import Path

from empirica.data.session_database import SessionDatabase
from empirica.config.path_resolver import debug_paths


# ---------------------------------------------------------------------------
# Entity artifact query dispatch
# ---------------------------------------------------------------------------

def _get_workspace_db():
    """Get connection to workspace.db (contacts, engagements, lessons)."""
    db_path = Path.home() / '.empirica' / 'workspace' / 'workspace.db'
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _get_project_db():
    """Get connection to current project's sessions.db."""
    try:
        db = SessionDatabase()
        return db
    except Exception:
        return None


def get_entity_artifacts(entity_type, entity_id=None):
    """
    Query epistemic artifacts for any entity type.

    Returns dict with artifact counts and recent items:
    {
        'findings': {'count': N, 'recent': [...]},
        'unknowns': {'count': N, 'recent': [...]},
        'dead_ends': {'count': N, 'recent': [...]},
        'mistakes': {'count': N, 'recent': [...]},
        'goals': {'count': N, 'recent': [...]},
        'sources': {'count': N, 'recent': [...]},
    }
    """
    if entity_type == 'project':
        return _get_project_artifacts(entity_id)
    elif entity_type == 'contact':
        return _get_contact_artifacts(entity_id)
    elif entity_type == 'engagement':
        return _get_engagement_artifacts(entity_id)
    return {}


def _get_project_artifacts(project_id=None):
    """Query artifacts from per-project sessions.db."""
    db = _get_project_db()
    if not db:
        return {}
    try:
        cursor = db.conn.cursor()
        result = {}

        # Findings
        cursor.execute("SELECT COUNT(*) as cnt FROM project_findings")
        count = cursor.fetchone()['cnt']
        cursor.execute("""
            SELECT finding as content, impact, created_timestamp as timestamp
            FROM project_findings ORDER BY created_timestamp DESC LIMIT 3
        """)
        result['findings'] = {'count': count, 'recent': [dict(r) for r in cursor.fetchall()]}

        # Unknowns
        cursor.execute("SELECT COUNT(*) as cnt FROM project_unknowns WHERE is_resolved = 0")
        count = cursor.fetchone()['cnt']
        cursor.execute("""
            SELECT unknown as content, impact, created_timestamp as timestamp
            FROM project_unknowns WHERE is_resolved = 0
            ORDER BY created_timestamp DESC LIMIT 3
        """)
        result['unknowns'] = {'count': count, 'recent': [dict(r) for r in cursor.fetchall()]}

        # Dead-ends
        cursor.execute("SELECT COUNT(*) as cnt FROM project_dead_ends")
        count = cursor.fetchone()['cnt']
        cursor.execute("""
            SELECT approach as content, why_failed, created_timestamp as timestamp
            FROM project_dead_ends ORDER BY created_timestamp DESC LIMIT 3
        """)
        result['dead_ends'] = {'count': count, 'recent': [dict(r) for r in cursor.fetchall()]}

        # Mistakes
        cursor.execute("SELECT COUNT(*) as cnt FROM mistakes_made")
        count = cursor.fetchone()['cnt']
        cursor.execute("""
            SELECT mistake as content, cost_estimate as severity, created_timestamp as timestamp
            FROM mistakes_made ORDER BY created_timestamp DESC LIMIT 3
        """)
        result['mistakes'] = {'count': count, 'recent': [dict(r) for r in cursor.fetchall()]}

        # Goals
        cursor.execute("SELECT COUNT(*) as cnt FROM goals WHERE status = 'in_progress'")
        count = cursor.fetchone()['cnt']
        cursor.execute("""
            SELECT objective as content, status, created_timestamp as timestamp
            FROM goals WHERE status = 'in_progress'
            ORDER BY created_timestamp DESC LIMIT 3
        """)
        result['goals'] = {'count': count, 'recent': [dict(r) for r in cursor.fetchall()]}

        # Sources
        cursor.execute("SELECT COUNT(*) as cnt FROM epistemic_sources")
        count = cursor.fetchone()['cnt']
        cursor.execute("""
            SELECT title as content, epistemic_layer, discovered_at as timestamp
            FROM epistemic_sources ORDER BY discovered_at DESC LIMIT 3
        """)
        result['sources'] = {'count': count, 'recent': [dict(r) for r in cursor.fetchall()]}

        db.close()
        return result
    except Exception:
        db.close()
        return {}


def _get_contact_artifacts(contact_id=None):
    """Query artifacts from workspace.db for contacts."""
    conn = _get_workspace_db()
    if not conn:
        return {}
    try:
        cursor = conn.cursor()
        result = {}

        if contact_id:
            # Specific contact — use contact_memory (unified) + standalone tables
            cursor.execute(
                "SELECT COUNT(*) as cnt FROM contact_memory WHERE contact_id = ? AND memory_type = 'finding'",
                (contact_id,))
            count = cursor.fetchone()['cnt']
            cursor.execute("""
                SELECT content, confidence as impact, created_at as timestamp
                FROM contact_memory WHERE contact_id = ? AND memory_type = 'finding'
                ORDER BY created_at DESC LIMIT 3
            """, (contact_id,))
            result['findings'] = {'count': count, 'recent': [dict(r) for r in cursor.fetchall()]}

            cursor.execute(
                "SELECT COUNT(*) as cnt FROM contact_memory WHERE contact_id = ? AND memory_type = 'unknown' AND is_resolved = 0",
                (contact_id,))
            count = cursor.fetchone()['cnt']
            cursor.execute("""
                SELECT content, confidence as priority, created_at as timestamp
                FROM contact_memory WHERE contact_id = ? AND memory_type = 'unknown' AND is_resolved = 0
                ORDER BY created_at DESC LIMIT 3
            """, (contact_id,))
            result['unknowns'] = {'count': count, 'recent': [dict(r) for r in cursor.fetchall()]}

            cursor.execute(
                "SELECT COUNT(*) as cnt FROM contact_dead_ends WHERE contact_id = ?",
                (contact_id,))
            count = cursor.fetchone()['cnt']
            cursor.execute("""
                SELECT approach as content, why_failed, created_at as timestamp
                FROM contact_dead_ends WHERE contact_id = ?
                ORDER BY created_at DESC LIMIT 3
            """, (contact_id,))
            result['dead_ends'] = {'count': count, 'recent': [dict(r) for r in cursor.fetchall()]}

            cursor.execute(
                "SELECT COUNT(*) as cnt FROM contact_mistakes WHERE contact_id = ?",
                (contact_id,))
            count = cursor.fetchone()['cnt']
            cursor.execute("""
                SELECT what_happened as content, severity, created_at as timestamp
                FROM contact_mistakes WHERE contact_id = ?
                ORDER BY created_at DESC LIMIT 3
            """, (contact_id,))
            result['mistakes'] = {'count': count, 'recent': [dict(r) for r in cursor.fetchall()]}
        else:
            # All contacts aggregate
            for mem_type in ['finding', 'unknown']:
                key = 'findings' if mem_type == 'finding' else 'unknowns'
                where = " AND is_resolved = 0" if mem_type == 'unknown' else ""
                cursor.execute(f"SELECT COUNT(*) as cnt FROM contact_memory WHERE memory_type = ?{where}", (mem_type,))
                count = cursor.fetchone()['cnt']
                cursor.execute(f"""
                    SELECT content, created_at as timestamp
                    FROM contact_memory WHERE memory_type = ?{where}
                    ORDER BY created_at DESC LIMIT 3
                """, (mem_type,))
                result[key] = {'count': count, 'recent': [dict(r) for r in cursor.fetchall()]}

            cursor.execute("SELECT COUNT(*) as cnt FROM contact_dead_ends")
            count = cursor.fetchone()['cnt']
            result['dead_ends'] = {'count': count, 'recent': []}

            cursor.execute("SELECT COUNT(*) as cnt FROM contact_mistakes")
            count = cursor.fetchone()['cnt']
            result['mistakes'] = {'count': count, 'recent': []}

        conn.close()
        return result
    except Exception:
        conn.close()
        return {}


def _get_engagement_artifacts(engagement_id=None):
    """Query artifacts from workspace.db for engagements."""
    conn = _get_workspace_db()
    if not conn:
        return {}
    try:
        cursor = conn.cursor()
        result = {}

        if engagement_id:
            # Tasks as the primary praxic artifact for engagements
            cursor.execute(
                "SELECT COUNT(*) as cnt FROM engagement_tasks WHERE engagement_id = ? AND status != 'completed'",
                (engagement_id,))
            count = cursor.fetchone()['cnt']
            cursor.execute("""
                SELECT title as content, status, created_at as timestamp
                FROM engagement_tasks WHERE engagement_id = ? AND status != 'completed'
                ORDER BY created_at DESC LIMIT 3
            """, (engagement_id,))
            result['goals'] = {'count': count, 'recent': [dict(r) for r in cursor.fetchall()]}

            # Dead-ends via linked contacts
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM contact_dead_ends
                WHERE engagement_id = ?
            """, (engagement_id,))
            count = cursor.fetchone()['cnt']
            cursor.execute("""
                SELECT approach as content, why_failed, created_at as timestamp
                FROM contact_dead_ends WHERE engagement_id = ?
                ORDER BY created_at DESC LIMIT 3
            """, (engagement_id,))
            result['dead_ends'] = {'count': count, 'recent': [dict(r) for r in cursor.fetchall()]}

            # Mistakes via linked contacts
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM contact_mistakes
                WHERE engagement_id = ?
            """, (engagement_id,))
            count = cursor.fetchone()['cnt']
            cursor.execute("""
                SELECT what_happened as content, severity, created_at as timestamp
                FROM contact_mistakes WHERE engagement_id = ?
                ORDER BY created_at DESC LIMIT 3
            """, (engagement_id,))
            result['mistakes'] = {'count': count, 'recent': [dict(r) for r in cursor.fetchall()]}
        else:
            # Aggregate across all engagements
            cursor.execute("SELECT COUNT(*) as cnt FROM engagement_tasks WHERE status != 'completed'")
            count = cursor.fetchone()['cnt']
            result['goals'] = {'count': count, 'recent': []}

        conn.close()
        return result
    except Exception:
        conn.close()
        return {}


class ProjectHeader(Static):
    """Display current project context"""

    def on_mount(self) -> None:
        """Initialize widget on mount and start periodic context refresh."""
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

    def on_mount(self) -> None:
        """Initialize widget on mount and start periodic activity refresh."""
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
                if isinstance(start_time, (int, float)):
                    start_dt = datetime.fromtimestamp(start_time)
                else:
                    start_dt = datetime.fromisoformat(str(start_time))
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
                    raw_rt = reflex_row['timestamp']
                    if isinstance(raw_rt, (int, float)):
                        reflex_time = datetime.fromtimestamp(raw_rt)
                    else:
                        reflex_time = datetime.fromisoformat(str(raw_rt))
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

    def on_mount(self) -> None:
        """Initialize widget on mount and start periodic vector refresh."""
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


class EpistemicArtifactsPanel(Static):
    """Display epistemic artifacts for any entity type (project, contact, engagement)."""

    ARTIFACT_STYLES = {
        'findings': ('green', 'F'),
        'unknowns': ('yellow', '?'),
        'dead_ends': ('red', 'X'),
        'mistakes': ('bright_red', '!'),
        'goals': ('cyan', 'G'),
        'sources': ('blue', 'S'),
    }

    def __init__(self, entity_type='project', entity_id=None, **kwargs):
        super().__init__(**kwargs)
        self.entity_type = entity_type
        self.entity_id = entity_id

    def on_mount(self) -> None:
        self._refresh()
        self.set_interval(2.0, self._refresh)

    def _refresh(self):
        try:
            artifacts = get_entity_artifacts(self.entity_type, self.entity_id)
            if not artifacts:
                entity_label = self.entity_type.title()
                self.update(Panel(
                    f"No artifacts for {entity_label}",
                    title=f"[bold]EPISTEMIC ARTIFACTS ({entity_label.upper()})[/bold]",
                    border_style="dim"))
                return

            # Summary row with counts
            table = Table(show_header=True, box=None, padding=(0, 1))
            table.add_column("Artifact", style="bold", width=12)
            table.add_column("Count", justify="right", width=6)
            table.add_column("Latest", width=55)

            for artifact_type, (style, icon) in self.ARTIFACT_STYLES.items():
                data = artifacts.get(artifact_type)
                if data is None:
                    continue
                count = data['count']
                recent = data.get('recent', [])
                latest_text = ""
                if recent:
                    content = recent[0].get('content', '')
                    if content:
                        latest_text = content[:52] + "..." if len(content) > 52 else content

                count_style = style if count > 0 else "dim"
                table.add_row(
                    Text(f" {icon} {artifact_type.replace('_', ' ').title()}", style=style),
                    Text(str(count), style=count_style),
                    Text(latest_text, style="white" if count > 0 else "dim"),
                )

            entity_label = self.entity_type.upper()
            if self.entity_id:
                entity_label += f" ({self.entity_id[:12]}...)" if len(str(self.entity_id)) > 12 else f" ({self.entity_id})"

            self.update(Panel(table, title=f"[bold]EPISTEMIC ARTIFACTS ({entity_label})[/bold]", border_style="blue"))

        except Exception as e:
            self.update(Panel(f"Error: {e}", title="[bold red]ARTIFACTS ERROR[/bold red]", border_style="red"))


class CommandsLog(Static):
    """Display recent activity log across all entity types."""

    def on_mount(self) -> None:
        self.update_log()
        self.set_interval(2.0, self.update_log)

    def update_log(self):
        try:
            db = SessionDatabase()
            cursor = db.conn.cursor()

            cursor.execute("""
                SELECT 'FINDING' as type, finding as message, created_timestamp as timestamp
                FROM project_findings
                UNION ALL
                SELECT 'UNKNOWN' as type, unknown as message, created_timestamp as timestamp
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
                    raw_ts = row['timestamp']
                    if isinstance(raw_ts, (int, float)):
                        timestamp = datetime.fromtimestamp(raw_ts)
                    else:
                        timestamp = datetime.fromisoformat(str(raw_ts))
                    time_str = timestamp.strftime("%H:%M:%S")
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
    """Empirica TUI Dashboard Application

    Supports entity-aware artifact display for projects, contacts, and engagements.
    """

    CSS = """
    Screen {
        background: $background;
    }

    .container {
        height: auto;
    }

    .entity-label {
        text-style: bold;
        color: $accent;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("p", "entity_project", "Project"),
        ("o", "entity_contact", "Contacts"),
        ("e", "entity_engagement", "Engagements"),
    ]

    def __init__(self, entity_type='project', entity_id=None, **kwargs):
        super().__init__(**kwargs)
        self._entity_type = entity_type
        self._entity_id = entity_id

    def compose(self) -> ComposeResult:
        yield Header()
        yield ProjectHeader()
        yield ActivityPanel()
        yield VectorsPanel()
        yield EpistemicArtifactsPanel(
            entity_type=self._entity_type,
            entity_id=self._entity_id,
        )
        yield CommandsLog()
        yield Footer()

    async def _switch_entity(self, entity_type, entity_id=None):
        """Switch the artifacts panel to a different entity type."""
        old_panel = self.query_one(EpistemicArtifactsPanel)
        new_panel = EpistemicArtifactsPanel(entity_type=entity_type, entity_id=entity_id)
        await old_panel.remove()
        # Mount new panel before CommandsLog
        cmd_log = self.query_one(CommandsLog)
        await self.mount(new_panel, before=cmd_log)

    def action_refresh(self):
        for widget in self.query(Static):
            for method in ('update_context', 'update_activity', 'update_vectors', 'update_log', '_refresh'):
                if hasattr(widget, method):
                    getattr(widget, method)()
                    break

    async def action_entity_project(self):
        await self._switch_entity('project')

    async def action_entity_contact(self):
        await self._switch_entity('contact')

    async def action_entity_engagement(self):
        await self._switch_entity('engagement')


def run_dashboard(entity_type='project', entity_id=None):
    """Entry point for dashboard command.

    Args:
        entity_type: 'project', 'contact', or 'engagement'
        entity_id: Optional specific entity ID to focus on
    """
    app = EmpiricaDashboard(entity_type=entity_type, entity_id=entity_id)
    app.run()


if __name__ == "__main__":
    run_dashboard()
