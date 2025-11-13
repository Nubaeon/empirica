#!/usr/bin/env python3
"""
🧠 Empirica CASCADE Monitor - Minimalist Dashboard

Displays PREFLIGHT → POSTFLIGHT delta for epistemic transparency.
Updates triggered by action hooks (event-driven, no polling).

Design Philosophy:
- Show genuine AI self-assessment data
- Prove epistemic growth via calibration delta
- Mathematical proof of self-awareness for skeptics
"""

import json
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import subprocess

# Add empirica to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from empirica.data.session_database import SessionDatabase
from empirica.cli.uvl_formatter import get_confidence_color

REALTIME_DIR = Path("/tmp/empirica_realtime")


class CascadeMonitor:
    """Minimalist CASCADE monitor for tmux dashboard"""

    def __init__(self):
        self.db = SessionDatabase()
        self.last_cascade_id = None
        self.last_update = 0

    def get_active_cascade(self) -> Optional[Dict[str, Any]]:
        """Get most recent active cascade (not yet completed)"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT * FROM cascades
            WHERE postflight_completed = 0
            ORDER BY started_at DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def get_latest_cascade(self) -> Optional[Dict[str, Any]]:
        """Get most recent cascade (even if completed) - fallback for display"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT * FROM cascades
            ORDER BY started_at DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def get_assessments(self, cascade_id: str) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Get PREFLIGHT and POSTFLIGHT assessments for cascade"""
        cursor = self.db.conn.cursor()

        # Get PREFLIGHT
        cursor.execute("""
            SELECT * FROM epistemic_assessments
            WHERE cascade_id = ? AND phase = 'PREFLIGHT'
            ORDER BY timestamp DESC
            LIMIT 1
        """, (cascade_id,))
        preflight_row = cursor.fetchone()
        preflight = dict(preflight_row) if preflight_row else None

        # Get POSTFLIGHT
        cursor.execute("""
            SELECT * FROM epistemic_assessments
            WHERE cascade_id = ? AND phase = 'POSTFLIGHT'
            ORDER BY timestamp DESC
            LIMIT 1
        """, (cascade_id,))
        postflight_row = cursor.fetchone()
        postflight = dict(postflight_row) if postflight_row else None

        return preflight, postflight

    def format_vector_state(self, vector_name: str, state: Dict[str, Any], prefix: str = "├─") -> str:
        """Format single vector with UVL indicators"""
        score = state.get('score', 0.5)
        rationale = state.get('rationale', 'No rationale provided')

        color = get_confidence_color(score)

        output = f"  {prefix} **{vector_name.upper()}**: {score:.2f} {color} *\"{rationale}\"*\n"

        # Show if AI flagged for investigation (no heuristics - AI decided!)
        if state.get('warrants_investigation'):
            priority = state.get('investigation_priority', 'unknown')
            reason = state.get('investigation_reason', 'No reason provided')
            output += f"     └─ ⚠️  **Flagged for investigation** (priority: **{priority}**)\n"
            output += f"        *\"{reason}\"*\n"

        return output

    def format_phase_progress(self, cascade: Dict[str, Any]) -> str:
        """Format CASCADE phase progress indicator"""
        phases = [
            ('preflight', 'PREFLIGHT'),
            ('think', 'THINK'),
            ('plan', 'PLAN'),
            ('investigate', 'INVESTIGATE'),
            ('check', 'CHECK'),
            ('act', 'ACT'),
            ('postflight', 'POSTFLIGHT')
        ]

        phase_parts = []
        for key, label in phases:
            completed = cascade.get(f'{key}_completed', False)
            if completed:
                phase_parts.append(f"✓ {label}")
            else:
                # Check if this is the current phase (first incomplete)
                if not phase_parts or '✓' in phase_parts[-1]:
                    phase_parts.append(f"**→ {label}**")
                else:
                    phase_parts.append(label)

        return " → ".join(phase_parts)

    def calculate_delta(self, preflight: Dict, postflight: Dict) -> Dict[str, float]:
        """Calculate epistemic delta (proof of learning)"""
        pre_vectors = json.loads(preflight.get('vectors_json', '{}'))
        post_vectors = json.loads(postflight.get('vectors_json', '{}'))

        deltas = {}
        for vector_name in pre_vectors.keys():
            if vector_name in post_vectors:
                pre_score = pre_vectors[vector_name].get('score', 0.5)
                post_score = post_vectors[vector_name].get('score', 0.5)
                deltas[vector_name] = post_score - pre_score

        # Overall confidence delta
        deltas['overall_confidence'] = (
            postflight.get('overall_confidence', 0.5) -
            preflight.get('overall_confidence', 0.5)
        )

        return deltas

    def format_delta_indicator(self, delta: float) -> str:
        """Format delta with visual indicator"""
        if abs(delta) < 0.05:
            return f"[±{abs(delta):.2f}]"
        elif delta > 0:
            indicator = "✨" if delta > 0.15 else ""
            return f"[+{delta:.2f}] {indicator}"
        else:
            return f"[{delta:.2f}]"

    def render_markdown(self) -> str:
        """Generate markdown output for glow rendering"""
        output = []

        # Header
        output.append("# 🧠 Empirica CASCADE Monitor")
        output.append("")

        # Get active or latest cascade
        cascade = self.get_active_cascade()
        if not cascade:
            cascade = self.get_latest_cascade()

        if not cascade:
            output.append("*No CASCADE data available. Waiting for AI to start...*")
            return "\n".join(output)

        # Session info
        cascade_id = cascade['cascade_id']
        session_id = cascade.get('session_id', 'unknown')
        task = cascade.get('task', 'No task description')

        output.append(f"**Session**: `{session_id[:12]}...`")
        output.append(f"**Cascade**: `{cascade_id[:8]}...`")
        output.append(f"**Goal**: {task}")
        output.append("")

        # Phase progress
        phase_progress = self.format_phase_progress(cascade)
        output.append(f"**Progress**: {phase_progress}")
        output.append("")
        output.append("---")
        output.append("")

        # Get assessments
        preflight, postflight = self.get_assessments(cascade_id)

        # PREFLIGHT section
        if preflight:
            output.append("## 📊 PREFLIGHT (Baseline)")
            output.append("")
            output.append("*AI's self-assessment before starting task:*")
            output.append("")

            vectors_json = json.loads(preflight.get('vectors_json', '{}'))

            # Show key vectors (KNOW, DO, CONTEXT always, plus any flagged)
            key_vectors = ['know', 'do', 'context']
            flagged_vectors = [
                name for name, state in vectors_json.items()
                if state.get('warrants_investigation', False)
            ]

            # Combine and deduplicate
            display_vectors = list(dict.fromkeys(key_vectors + flagged_vectors))

            for vector_name in display_vectors:
                if vector_name in vectors_json:
                    state = vectors_json[vector_name]
                    output.append(self.format_vector_state(vector_name, state))

            # Show count of other vectors if any
            other_count = len(vectors_json) - len(display_vectors)
            if other_count > 0:
                output.append(f"  └─ *({other_count} additional vectors assessed)*")

            output.append("")
            overall_conf = preflight.get('overall_confidence', 0.5)
            output.append(f"  **Overall Confidence**: {overall_conf:.2f} {get_confidence_color(overall_conf)}")
            output.append("")
        else:
            output.append("## 📊 PREFLIGHT - Pending...")
            output.append("")

        # POSTFLIGHT section
        if postflight:
            output.append("---")
            output.append("")
            output.append("## 📈 POSTFLIGHT (After Completion)")
            output.append("")
            output.append("*AI's self-assessment after completing task:*")
            output.append("")

            post_vectors_json = json.loads(postflight.get('vectors_json', '{}'))

            # Show same vectors as PREFLIGHT for comparison
            for vector_name in display_vectors:
                if vector_name in post_vectors_json:
                    state = post_vectors_json[vector_name]
                    output.append(self.format_vector_state(vector_name, state))

            output.append("")
            post_overall_conf = postflight.get('overall_confidence', 0.5)
            output.append(f"  **Overall Confidence**: {post_overall_conf:.2f} {get_confidence_color(post_overall_conf)}")
            output.append("")

            # DELTA section (the proof!)
            if preflight:
                output.append("---")
                output.append("")
                output.append("## 🔬 Calibration Delta (Proof of Learning)")
                output.append("")
                output.append("*POSTFLIGHT - PREFLIGHT = Epistemic Growth*")
                output.append("")

                deltas = self.calculate_delta(preflight, postflight)

                for vector_name in display_vectors:
                    if vector_name in deltas:
                        delta = deltas[vector_name]
                        delta_indicator = self.format_delta_indicator(delta)
                        output.append(f"  ├─ **Δ{vector_name.upper()}**: {delta_indicator}")

                output.append("")
                conf_delta = deltas.get('overall_confidence', 0.0)
                conf_indicator = self.format_delta_indicator(conf_delta)
                output.append(f"  **ΔConfidence**: {conf_indicator}")
                output.append("")

                # Interpretation
                if abs(conf_delta) < 0.05:
                    output.append("*Calibrated: Confidence stable (accurate initial assessment)*")
                elif conf_delta > 0:
                    output.append("*✓ Genuine Learning: Confidence increased through investigation*")
                else:
                    output.append("*✓ Epistemic Humility: Discovered additional complexity*")

        else:
            output.append("---")
            output.append("")
            output.append("## 📈 POSTFLIGHT - Pending...")
            output.append("")
            output.append("*Will update when CASCADE completes*")

        output.append("")
        output.append("---")
        output.append("")

        # Footer
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        output.append(f"*Last updated: {timestamp}*")

        return "\n".join(output)

    def render_with_glow(self) -> str:
        """Render markdown with glow for pretty display"""
        markdown = self.render_markdown()

        try:
            result = subprocess.run(
                ['glow', '-'],
                input=markdown,
                text=True,
                capture_output=True,
                timeout=5
            )

            if result.returncode == 0:
                return result.stdout
            else:
                # Fallback to plain markdown
                return markdown

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback to plain markdown
            return markdown

    def display(self):
        """Display the dashboard (clear screen and render)"""
        # Clear screen
        print("\033[2J\033[H", end="")

        # Render and display
        output = self.render_with_glow()
        print(output)

    def watch_for_updates(self):
        """Watch for action hook updates and refresh display"""
        cascade_status_file = REALTIME_DIR / "cascade_status.json"

        # Initial display
        self.display()

        # Watch for changes
        last_mtime = 0
        if cascade_status_file.exists():
            last_mtime = cascade_status_file.stat().st_mtime

        while True:
            try:
                # Check if file changed
                if cascade_status_file.exists():
                    current_mtime = cascade_status_file.stat().st_mtime

                    if current_mtime > last_mtime:
                        last_mtime = current_mtime
                        time.sleep(0.5)  # Brief delay to ensure DB write completes
                        self.display()

                # Also check for new cascades in DB directly
                cascade = self.get_active_cascade()
                if cascade:
                    cascade_id = cascade['cascade_id']
                    if cascade_id != self.last_cascade_id:
                        self.last_cascade_id = cascade_id
                        self.display()

                time.sleep(1)  # Check every second (lightweight)

            except KeyboardInterrupt:
                print("\n\nMonitor stopped by user")
                break
            except Exception as e:
                print(f"\n\nError in monitor: {e}")
                time.sleep(5)


def main():
    """Main entry point"""
    print("🧠 Starting Empirica CASCADE Monitor...")
    print("   Event-driven updates via action hooks")
    print("   Press Ctrl+C to exit\n")

    # Ensure realtime directory exists
    REALTIME_DIR.mkdir(exist_ok=True)

    # Create and run monitor
    monitor = CascadeMonitor()
    monitor.watch_for_updates()


if __name__ == "__main__":
    main()
