"""empirica tui — portrait Textual cockpit (v1.6.1).

Designed for phone terminals first; tmux split-strip and laptop work too.
Targets ~36 cols × 22 rows minimum, expands gracefully when the terminal
is taller. Reads the same JSON as the CLI (`aggregate_all`); no business
logic duplication.

Vertical layout (single column):
  ┌─ Header   (title + clock)
  │  Summary line   (N inst · ⊕ K notif)
  │  Instance table (one row per live Claude)
  │  Action bar    [P sent] [L loops] [S stop] [N notif]
  │  Statusline    k:.. c:.. conf:..% goals:N — ctx:M%
  │  Open goals    (selected instance, top 5)
  │  Notifications (selected instance, top 5; placeholder for ENP)
  └─ Footer    (key bindings)

Actions (mouse OR keyboard):
  p  toggle Sentinel pause/resume
  l  toggle all loops on/off
  s  stop = remote interrupt (tmux send-keys Escape)
  n  clear all notifications for selected instance
  D  toggle live-only / include-dead view
  r  refresh now
  q  quit
"""

from __future__ import annotations

import textwrap
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Static,
)

from empirica.core.cockpit import (
    LoopRegistry,
    aggregate_all,
    clear_notifications,
    context_usage,
    is_loop_paused,
    notifications_for_project,
    open_goals_list,
    pause_sentinel,
    resume_sentinel,
    set_loop_paused,
    statusline_summary,
    stop_instance,
)

REFRESH_SECONDS = 2.0

# Wrap width for the goals + notifications strips (portrait-friendly).
# Items longer than this wrap onto continuation lines indented under
# the bullet so the visual association is preserved.
_WRAP_WIDTH = 36
# Hard cap per item (David: ~200 chars) to bound widget height per row.
_ITEM_HARD_CAP = 200


class CockpitApp(App):
    """Portrait interactive Empirica cockpit."""

    CSS = """
    Screen { layout: vertical; }

    #summary  { padding: 0 1; height: 1; color: $text-muted; }
    #inst-table { height: auto; min-height: 7; max-height: 12; }

    #action-bar {
        height: 3;
        background: $surface;
        align-horizontal: left;
        padding: 0 1;
    }
    #action-bar Button { margin: 0 1; min-width: 8; }

    #statusline {
        height: 1;
        padding: 0 1;
        color: $primary;
        background: $boost;
    }

    #goals-header   { height: 1; padding: 0 1; color: $text-muted; }
    #goals { height: auto; min-height: 3; max-height: 14; padding: 0 1; }
    #notif-header   { height: 1; padding: 0 1; color: $text-muted; }
    #notif { height: auto; min-height: 1; padding: 0 1; color: $text-muted; }
    #dispatch-banner { height: auto; max-height: 2; padding: 0 1; color: $warning; }
    #dispatch-header { height: 1; padding: 0 1; color: $text-muted; }
    #dispatch { height: auto; min-height: 1; max-height: 7; padding: 0 1; }
    """

    BINDINGS = [
        Binding('q', 'quit', 'Quit'),
        Binding('r', 'refresh_now', 'Refresh'),
        Binding('p', 'toggle_sentinel', 'Sent.'),
        Binding('l', 'toggle_loops', 'Loops'),
        Binding('s', 'stop', 'Stop'),
        Binding('n', 'clear_notifications', 'Notif'),
        Binding('D', 'toggle_dead', 'Show dead'),
    ]

    def __init__(self, include_dead: bool = False) -> None:
        super().__init__()
        self.payload: dict[str, Any] = {'instances': [], 'summary': {}, 'generated_at': ''}
        self.selected_instance_id: str | None = None
        self.include_dead = include_dead

    # ─── lifecycle ────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static('', id='summary')

        table = DataTable(id='inst-table', cursor_type='row', zebra_stripes=True)
        table.add_columns('s', 'name', 'ph', 'S', 'L', 'N')
        yield table

        with Horizontal(id='action-bar'):
            yield Button('P sent', id='btn-sent', variant='warning')
            yield Button('L loops', id='btn-loops', variant='warning')
            yield Button('S stop', id='btn-stop', variant='error')
            yield Button('N notif', id='btn-notif', variant='primary')

        yield Static('', id='statusline')
        yield Static('open goals', id='goals-header')
        yield Static('(none selected)', id='goals')
        yield Static('notifications', id='notif-header')
        yield Static('', id='notif')
        yield Static('', id='dispatch-banner')
        yield Static('notify dispatcher · recent', id='dispatch-header')
        yield Static('', id='dispatch')
        yield Footer()

    def on_mount(self) -> None:
        self.title = 'empirica cockpit'
        self.refresh_payload()
        self.set_interval(REFRESH_SECONDS, self.refresh_payload)

    # ─── data + rendering ─────────────────────────────────────────────────

    def refresh_payload(self) -> None:
        try:
            self.payload = aggregate_all(include_dead=self.include_dead)
        except Exception as e:
            self._log_status(f'refresh failed: {e}')
            return
        self._render_summary()
        self._render_table()
        self._render_selected_widgets()
        self._render_dispatcher()

    def action_toggle_dead(self) -> None:
        self.include_dead = not self.include_dead
        self.refresh_payload()

    def _render_summary(self) -> None:
        s = self.payload.get('summary', {})
        notif_total = s.get('open_notifications', 0)
        ts = self.payload.get('generated_at', '').split('T')[-1].split('+')[0][:5]
        notif_part = f' · ⊕{notif_total}' if notif_total else ''
        text = f"empirica · {s.get('instances', 0)} inst{notif_part} · {ts}"
        self.query_one('#summary', Static).update(text)

    def _render_table(self) -> None:
        table = self.query_one('#inst-table', DataTable)
        previously_selected = self.selected_instance_id
        table.clear()
        rows = self.payload.get('instances', [])
        for inst in rows:
            iid = inst['instance_id']
            stat = self._state_glyph(inst['state'])
            name = (inst.get('label') or iid)[:16]
            phase = self._phase_short(inst.get('phase'), inst.get('asking', False))
            sentinel = '○' if inst['sentinel']['paused'] else '●'
            loops = self._loops_glyph(inst.get('loops') or {})
            notif = self._notif_glyph(inst.get('notifications') or {})
            table.add_row(stat, name, phase, sentinel, loops, notif, key=iid)

        if rows:
            target = previously_selected or rows[0]['instance_id']
            for idx, inst in enumerate(rows):
                if inst['instance_id'] == target:
                    table.move_cursor(row=idx)
                    self.selected_instance_id = target
                    break
            else:
                table.move_cursor(row=0)
                self.selected_instance_id = rows[0]['instance_id']
        else:
            self.selected_instance_id = None

    @staticmethod
    def _state_glyph(state: str) -> str:
        return {
            'active': '🟢', 'idle': '🟡', 'stuck': '🔴',
            'closed': '⊘', 'no-claude': '⊗',
        }.get(state, '?')

    @staticmethod
    def _phase_short(phase: str | None, asking: bool) -> str:
        """Compress phase to ≤4 chars to fit the narrow column."""
        if asking:
            return 'ask⚠'
        if not phase:
            return '—'
        return {
            'noetic': 'noet', 'praxic': 'prax',
            'closed': 'cls', 'no-transaction': '—',
        }.get(phase, phase[:4])

    @staticmethod
    def _loops_glyph(loops: dict[str, Any]) -> str:
        if not loops:
            return '–'
        paused = sum(1 for v in loops.values() if v.get('paused'))
        if paused == 0:
            return '●'
        if paused == len(loops):
            return '○'
        return '◐'

    @staticmethod
    def _notif_glyph(notif: dict[str, Any]) -> str:
        count = int(notif.get('open_count', 0) or 0)
        if count == 0:
            return '·'
        return f'⊕{count}'

    def _selected_instance(self) -> dict[str, Any] | None:
        if not self.selected_instance_id:
            return None
        for inst in self.payload.get('instances', []):
            if inst['instance_id'] == self.selected_instance_id:
                return inst
        return None

    def _render_selected_widgets(self) -> None:
        """Statusline + open-goals + notifications for the selected instance."""
        inst = self._selected_instance()
        statusline_widget = self.query_one('#statusline', Static)
        goals_widget = self.query_one('#goals', Static)
        notif_widget = self.query_one('#notif', Static)

        if inst is None:
            statusline_widget.update('')
            goals_widget.update('(no instance selected)')
            notif_widget.update('')
            return

        statusline_widget.update(self._format_statusline(inst))
        goals_widget.update(self._format_goals(inst))
        notif_widget.update(self._format_notifications(inst))

    def _format_statusline(self, inst: dict[str, Any]) -> str:
        """k:X c:Y conf:Z% goals:N — ctx:M% (omit ctx when not available)."""
        ss = statusline_summary(
            inst['instance_id'],
            label_fallback=inst.get('label'),
            project_path=inst.get('project_path'),
            session_id=inst.get('session_id'),
        )
        parts: list[str] = []
        if ss.know is not None:
            parts.append(f'k:{ss.know:.2f}')
        if ss.context is not None:
            parts.append(f'c:{ss.context:.2f}')
        if ss.confidence is not None:
            parts.append(f'conf:{int(ss.confidence * 100)}%')
        if ss.open_goals is not None:
            parts.append(f'goals:{ss.open_goals}')
        ctx = context_usage(inst['instance_id'])
        line = ' '.join(parts) if parts else '(no vectors)'
        if ctx is not None:
            line = f'{line} — ctx:{ctx}%'
        return line

    def _format_goals(self, inst: dict[str, Any]) -> str:
        # Project-scoped: passes session_id through but it's ignored by
        # the reader (kept for signature compat).
        goals = open_goals_list(
            inst.get('project_path'), inst.get('session_id'), limit=5,
        )
        if not goals:
            return '(none)'
        return '\n'.join(
            _wrap_item(
                ('⏸' if g.status == 'blocked' else '·'),
                g.objective.replace('\n', ' ').strip(),
            )
            for g in goals
        )

    def _format_notifications(self, inst: dict[str, Any]) -> str:
        items = notifications_for_project(inst.get('project_path'), limit=5)
        if not items:
            return '(none for this project)'
        return '\n'.join(_wrap_item('•', n.title) for n in items)

    def _render_dispatcher(self) -> None:
        """Render the notify-dispatcher block: banner, recent emits, backends.

        Reads summary.notify_dispatcher (built by the dispatcher view module).
        Always present in payload — fall through to hidden state when empty
        rather than crashing.
        """
        nd = (self.payload.get('summary', {}) or {}).get('notify_dispatcher') or {}
        banner_widget = self.query_one('#dispatch-banner', Static)
        header_widget = self.query_one('#dispatch-header', Static)
        body_widget = self.query_one('#dispatch', Static)

        banner = nd.get('banner_failure')
        if banner:
            backend = banner.get('resolved_backend') or '?'
            age = self._age_short(banner.get('age_seconds'))
            detail = (banner.get('detail') or '').split('\n', 1)[0][:60]
            banner_widget.update(
                f'[red]⚠ notify backend {backend} failed {age} ago — {detail}[/red]'
            )
        else:
            banner_widget.update('')

        default = nd.get('default_backend') or '?'
        emit_24h = nd.get('emit_count_24h', 0)
        fb_24h = nd.get('fell_back_count_24h', 0)
        backends = nd.get('backends') or []
        backend_glyphs: list[str] = []
        for b in backends:
            glyph = '●' if b.get('configured') else '○'
            name = b.get('name', '?')
            tag = ''
            if name == 'ntfy':
                tag = f' {b.get("auth_method") or "none"}'
            backend_glyphs.append(f'{glyph}{name}{tag}')
        header_widget.update(
            f'notify dispatcher · default:{default} · 24h:{emit_24h} emits, {fb_24h} fb'
        )

        recent = nd.get('recent') or []
        if not recent and not backends:
            body_widget.update('(no activity — set ~/.empirica/notify.yaml)')
            return

        lines: list[str] = []
        if backend_glyphs:
            lines.append('  '.join(backend_glyphs))
        if not recent:
            lines.append('(no recent emits)')
        else:
            for r in recent:
                ts_short = (r.get('ts') or '').split('T')[-1].split('+')[0].split('.')[0][:8]
                source = (r.get('source') or 'manual')[:18].ljust(18)
                arrow = '↻' if r.get('fell_back') else '↗'
                backend = r.get('resolved_backend') or '?'
                topic = r.get('topic') or ''
                dest = f'{backend}/{topic}' if topic else backend
                ok = 'ok' if r.get('ok') else 'FAIL'
                rc = r.get('response_code')
                rc_str = f' ({rc})' if rc else ''
                lines.append(f'{ts_short} {source}{arrow} {dest} {ok}{rc_str}')
        body_widget.update('\n'.join(lines))

    @staticmethod
    def _age_short(seconds: int | None) -> str:
        if seconds is None:
            return '?'
        if seconds < 60:
            return f'{seconds}s'
        if seconds < 3600:
            return f'{seconds // 60}m'
        return f'{seconds // 3600}h'

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key and event.row_key.value:
            self.selected_instance_id = str(event.row_key.value)
            self._render_selected_widgets()

    # ─── actions ──────────────────────────────────────────────────────────

    def action_refresh_now(self) -> None:
        self.refresh_payload()

    def action_toggle_sentinel(self) -> None:
        inst = self._require_selected()
        if inst is None:
            return
        if inst['sentinel']['paused']:
            resume_sentinel(inst['instance_id'])
            self._log_status(f'sentinel resumed: {inst["instance_id"]}')
        else:
            pause_sentinel(inst['instance_id'], reason='via tui')
            self._log_status(f'sentinel paused: {inst["instance_id"]}')
        self.refresh_payload()

    def action_toggle_loops(self) -> None:
        inst = self._require_selected()
        if inst is None:
            return
        loops = inst.get('loops') or {}
        if not loops:
            self._log_status(f'{inst["instance_id"]}: no loops registered')
            return
        any_unpaused = any(not v.get('paused') for v in loops.values())
        target_state = bool(any_unpaused)
        for name in loops:
            set_loop_paused(inst['instance_id'], name, target_state)
        verb = 'paused' if target_state else 'resumed'
        self._log_status(f'{verb} {len(loops)} loop(s) on {inst["instance_id"]}')
        self.refresh_payload()

    def action_stop(self) -> None:
        inst = self._require_selected()
        if inst is None:
            return
        result = stop_instance(inst['instance_id'])
        self._log_status(f'stop {inst["instance_id"]}: {result.detail}')
        self.refresh_payload()

    def action_clear_notifications(self) -> None:
        inst = self._require_selected()
        if inst is None:
            return
        project_path = inst.get('project_path')
        cleared = clear_notifications(inst['instance_id'], project_path=project_path)
        scope = project_path or inst['instance_id']
        if cleared:
            self._log_status(f'cleared {cleared} notif(s) for {scope}')
        else:
            self._log_status(f'no notifications to clear for {scope}')
        self.refresh_payload()

    # ─── button events (mouse / touch) ────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        actions = {
            'btn-sent': self.action_toggle_sentinel,
            'btn-loops': self.action_toggle_loops,
            'btn-stop': self.action_stop,
            'btn-notif': self.action_clear_notifications,
        }
        handler = actions.get(event.button.id or '')
        if handler:
            handler()

    # ─── helpers ──────────────────────────────────────────────────────────

    def _require_selected(self) -> dict[str, Any] | None:
        inst = self._selected_instance()
        if inst is None:
            self._log_status('no instance selected')
        return inst

    def _log_status(self, message: str) -> None:
        """Status messages share the notif widget when nothing else lives there."""
        try:
            notif = self.query_one('#notif', Static)
            notif.update(f'• {message}')
        except Exception:
            pass


def _wrap_item(marker: str, text: str, width: int = _WRAP_WIDTH) -> str:
    """Wrap a single bulleted item to multiple lines.

    First line: '{marker} {first chunk}'.
    Continuation lines: indented under the marker so the bullet stays
    visually associated. Hard cap at _ITEM_HARD_CAP chars (David's ~200).
    """
    if not text:
        return marker
    capped = text[:_ITEM_HARD_CAP]
    if len(text) > _ITEM_HARD_CAP:
        capped += '…'

    indent = ' ' * (len(marker) + 1)
    body_width = max(8, width - len(marker) - 1)
    chunks = textwrap.wrap(
        capped, width=body_width, break_long_words=True, break_on_hyphens=False,
    )
    if not chunks:
        return marker
    first, rest = chunks[0], chunks[1:]
    lines = [f'{marker} {first}']
    for chunk in rest:
        lines.append(f'{indent}{chunk}')
    return '\n'.join(lines)


def run_tui(include_dead: bool = False) -> int:
    """Entry point for `empirica tui`. Returns shell exit code."""
    try:
        LoopRegistry.__name__  # noqa: B018
        is_loop_paused  # noqa: B018
    except Exception:
        pass

    try:
        app = CockpitApp(include_dead=include_dead)
        app.run()
        return 0
    except KeyboardInterrupt:
        return 130
