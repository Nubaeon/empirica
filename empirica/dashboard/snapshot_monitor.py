#!/usr/bin/env python3
"""
Terminal Dashboard for Epistemic Snapshot Monitoring

Real-time monitoring of epistemic snapshot memory quality with:
- Session and model information
- Token budget and compression metrics
- Memory reliability visualization
- Snapshot timeline with deltas
- Interactive commands

Usage:
    python3 empirica/dashboard/snapshot_monitor.py [session_id]
    
    Or from Python:
    from empirica.dashboard.snapshot_monitor import launch_dashboard
    launch_dashboard(session_id="current")

Interactive Commands:
    q - Quit dashboard
    r - Refresh display
    f - Show full context (all snapshots)
    e - Export current snapshot to JSON
    h - Show snapshot history
    d - Show detailed metrics
"""

import curses
import time
import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Add empirica to path
empirica_root = Path(__file__).parent.parent.parent
if str(empirica_root) not in sys.path:
    sys.path.insert(0, str(empirica_root))

from empirica.plugins.modality_switcher.snapshot_provider import EpistemicSnapshotProvider
from empirica.plugins.modality_switcher.epistemic_snapshot import EpistemicStateSnapshot
from empirica.auto_tracker import EmpericaTracker


class SnapshotMonitor:
    """Terminal-based snapshot monitoring dashboard"""
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize snapshot monitor
        
        Args:
            session_id: Session to monitor (uses current if None)
        """
        self.provider = EpistemicSnapshotProvider()
        self.session_id = session_id
        self.tracker = None
        self.running = True
        self.show_full = False
        self.show_history = False
        self.show_details = False
        self.last_update = time.time()
        self.update_interval = 2.0  # seconds
        self.message = ""  # Status message to display
        
        # Initialize tracker to get current session
        if self.session_id is None or self.session_id == "current":
            try:
                self.tracker = EmpericaTracker.get_instance()
                self.session_id = self.tracker.session_id
            except Exception as e:
                self.session_id = None
    
    def get_color_for_reliability(self, score: float) -> int:
        """Get curses color pair for reliability score"""
        if score >= 0.90:
            return 1  # Blue - EXCELLENT
        elif score >= 0.80:
            return 2  # Green - GOOD
        elif score >= 0.70:
            return 3  # Yellow - FAIR
        elif score >= 0.60:
            return 4  # Magenta - DEGRADED
        else:
            return 5  # Red - CRITICAL
    
    def get_status_label(self, score: float) -> str:
        """Get status label for reliability score"""
        if score >= 0.90:
            return "EXCELLENT"
        elif score >= 0.80:
            return "GOOD"
        elif score >= 0.70:
            return "FAIR"
        elif score >= 0.60:
            return "DEGRADED"
        else:
            return "CRITICAL"
    
    def format_bar(self, score: float, width: int = 40) -> str:
        """Format a progress bar for a score"""
        filled = int(score * width)
        empty = width - filled
        return "█" * filled + "░" * empty
    
    def draw_header(self, stdscr, snapshot: Optional[EpistemicStateSnapshot]):
        """Draw dashboard header"""
        height, width = stdscr.getmaxyx()
        
        # Title bar
        title = " EMPIRICA SNAPSHOT MEMORY TRACKER "
        stdscr.addstr(0, 0, "┌" + "─" * (width - 2) + "┐")
        stdscr.addstr(1, 0, "│")
        stdscr.addstr(1, (width - len(title)) // 2, title, curses.A_BOLD)
        stdscr.addstr(1, width - 1, "│")
        
        # Session info
        if snapshot:
            session_info = f"Session: {snapshot.session_id[:8]}...    Model: {snapshot.ai_id}"
            phase_info = f"Phase: {snapshot.cascade_phase or 'N/A'}    Memory: {snapshot.transfer_count} transfers"
        else:
            session_info = f"Session: {self.session_id[:8] if self.session_id else 'None'}    Model: Unknown"
            phase_info = "Phase: N/A    Memory: No snapshots"
        
        stdscr.addstr(2, 0, "│ ")
        stdscr.addstr(2, 2, session_info)
        stdscr.addstr(2, width - 1, "│")
        
        stdscr.addstr(3, 0, "│ ")
        stdscr.addstr(3, 2, phase_info)
        stdscr.addstr(3, width - 1, "│")
        
        stdscr.addstr(4, 0, "├" + "─" * (width - 2) + "┤")
    
    def draw_compression_status(self, stdscr, snapshot: Optional[EpistemicStateSnapshot], y_offset: int):
        """Draw compression status section"""
        height, width = stdscr.getmaxyx()
        
        stdscr.addstr(y_offset, 0, "│ CONTEXT COMPRESSION STATUS")
        stdscr.addstr(y_offset, width - 1, "│")
        y_offset += 1
        
        if snapshot:
            # Token budget (simulate from compression ratio)
            original_tokens = snapshot.original_tokens or 10000
            snapshot_tokens = snapshot.snapshot_tokens or 500
            total_budget = 200000
            used_tokens = total_budget - 150000  # Simulated
            usage_pct = (used_tokens / total_budget) * 100
            
            budget_line = f"Token Budget: {used_tokens:,} / {total_budget:,} ({usage_pct:.0f}% used)"
            stdscr.addstr(y_offset, 0, "│ ")
            stdscr.addstr(y_offset, 2, budget_line)
            stdscr.addstr(y_offset, width - 1, "│")
            y_offset += 1
            
            # Budget bar
            budget_bar = self.format_bar(usage_pct / 100, width - 20)
            status = "CRITICAL" if usage_pct > 95 else "GOOD" if usage_pct > 80 else "PLENTY"
            stdscr.addstr(y_offset, 0, "│ ")
            stdscr.addstr(y_offset, 2, budget_bar)
            stdscr.addstr(y_offset, 2 + len(budget_bar) + 1, status)
            stdscr.addstr(y_offset, width - 1, "│")
            y_offset += 1
            
            # Empty line
            stdscr.addstr(y_offset, 0, "│")
            stdscr.addstr(y_offset, width - 1, "│")
            y_offset += 1
            
            # Compression metrics
            compression_pct = snapshot.compression_ratio * 100
            comp_line = f"Compression: {compression_pct:.0f}% ({original_tokens:,} -> {snapshot_tokens:,} tokens)"
            stdscr.addstr(y_offset, 0, "│ ")
            stdscr.addstr(y_offset, 2, comp_line)
            stdscr.addstr(y_offset, width - 1, "│")
            y_offset += 1
            
            # Memory reliability
            reliability = snapshot.estimate_memory_reliability()
            reliability_pct = reliability * 100
            reliability_bar = self.format_bar(reliability, 20)
            reliability_status = self.get_status_label(reliability)
            
            stdscr.addstr(y_offset, 0, "│ ")
            stdscr.addstr(y_offset, 2, f"Reliability: {reliability_bar} {reliability_pct:.0f}% {reliability_status}")
            stdscr.addstr(y_offset, width - 1, "│")
            y_offset += 1
            
            # Fidelity
            fidelity_line = f"Fidelity: {snapshot.fidelity_score:.2f}"
            fidelity_status = "OK" if snapshot.fidelity_score >= 0.90 else "WARN"
            stdscr.addstr(y_offset, 0, "│ ")
            stdscr.addstr(y_offset, 2, f"{fidelity_line} {fidelity_status} (>=0.90 threshold)")
            stdscr.addstr(y_offset, width - 1, "│")
            y_offset += 1
            
            # Information loss
            info_loss_pct = snapshot.information_loss_estimate * 100
            info_loss_status = "OK" if info_loss_pct <= 15 else "WARN"
            stdscr.addstr(y_offset, 0, "│ ")
            stdscr.addstr(y_offset, 2, f"Info Loss: {info_loss_pct:.0f}% (<=15% tolerance) {info_loss_status}")
            stdscr.addstr(y_offset, width - 1, "│")
            y_offset += 1
        else:
            stdscr.addstr(y_offset, 0, "│ ")
            stdscr.addstr(y_offset, 2, "No snapshot data available")
            stdscr.addstr(y_offset, width - 1, "│")
            y_offset += 1
        
        return y_offset
    
    def draw_snapshot_timeline(self, stdscr, snapshots: List[EpistemicStateSnapshot], y_offset: int):
        """Draw snapshot timeline section"""
        height, width = stdscr.getmaxyx()
        
        # Empty line
        stdscr.addstr(y_offset, 0, "│")
        stdscr.addstr(y_offset, width - 1, "│")
        y_offset += 1
        
        # Timeline header
        count = len(snapshots)
        header = f"SNAPSHOT TIMELINE ({count} snapshot{'s' if count != 1 else ''})"
        stdscr.addstr(y_offset, 0, "│ ")
        stdscr.addstr(y_offset, 2, header, curses.A_BOLD)
        stdscr.addstr(y_offset, width - 1, "│")
        y_offset += 1
        
        if not snapshots:
            stdscr.addstr(y_offset, 0, "│ ")
            stdscr.addstr(y_offset, 2, "No snapshots yet")
            stdscr.addstr(y_offset, width - 1, "│")
            y_offset += 1
            return y_offset
        
        # Show snapshots (most recent first)
        max_display = 5 if not self.show_full else 20
        for i, snapshot in enumerate(snapshots[:max_display]):
            timestamp = datetime.fromisoformat(snapshot.timestamp)
            time_str = timestamp.strftime("%H:%M")
            
            # Snapshot header line
            marker = "<- CURRENT" if i == 0 else ""
            phase_display = snapshot.cascade_phase or "UNKNOWN"
            ai_display = snapshot.ai_id or "Unknown"
            
            line1 = f"{time_str} {phase_display} [{ai_display}] {marker}"
            stdscr.addstr(y_offset, 0, "│ ")
            stdscr.addstr(y_offset, 2, line1)
            stdscr.addstr(y_offset, width - 1, "│")
            y_offset += 1
            
            # Vector summary
            vectors = snapshot.vectors
            know = vectors.get('know', 0.0)
            context = vectors.get('context', 0.0)
            uncertainty = vectors.get('uncertainty', 0.0)
            
            line2 = f"      KNOW {know:.2f} | CONTEXT {context:.2f} | UNCERTAINTY {uncertainty:.2f}"
            stdscr.addstr(y_offset, 0, "│ ")
            stdscr.addstr(y_offset, 2, line2)
            stdscr.addstr(y_offset, width - 1, "│")
            y_offset += 1
            
            # Delta information (if available)
            if snapshot.delta:
                deltas = []
                for key, value in snapshot.delta.items():
                    if abs(value) > 0.1:  # Only show significant changes
                        arrow = "UP" if value > 0 else "DOWN"
                        deltas.append(f"D {key.upper()} {value:+.2f} {arrow}")
                
                if deltas:
                    delta_line = "      " + " | ".join(deltas[:3])  # Max 3 deltas
                    stdscr.addstr(y_offset, 0, "│ ")
                    stdscr.addstr(y_offset, 2, delta_line)
                    stdscr.addstr(y_offset, width - 1, "│")
                    y_offset += 1
            
            # Reliability warning
            reliability = snapshot.estimate_memory_reliability()
            if reliability < 0.80:
                warning = f"      WARN: Reliability dropped to {reliability*100:.0f}%"
                stdscr.addstr(y_offset, 0, "│ ")
                stdscr.addstr(y_offset, 2, warning, curses.color_pair(4))
                stdscr.addstr(y_offset, width - 1, "│")
                y_offset += 1
            
            # Check if we're running out of space
            if y_offset >= height - 5:
                break
        
        return y_offset
    
    def draw_commands(self, stdscr, y_offset: int):
        """Draw command bar at bottom"""
        height, width = stdscr.getmaxyx()
        
        # Move to bottom
        y_offset = height - 4
        
        # Show message if any
        if self.message:
            stdscr.addstr(y_offset, 0, "│ ")
            stdscr.addstr(y_offset, 2, self.message[:width-4])
            stdscr.addstr(y_offset, width - 1, "│")
            y_offset += 1
        
        stdscr.addstr(y_offset, 0, "├" + "─ COMMANDS " + "─" * (width - 13) + "┤")
        y_offset += 1
        
        commands = "[Q]uit [R]efresh [F]ull [E]xport [D]etails"
        stdscr.addstr(y_offset, 0, "│ ")
        stdscr.addstr(y_offset, 2, commands)
        stdscr.addstr(y_offset, width - 1, "│")
        y_offset += 1
        
        stdscr.addstr(y_offset, 0, "└" + "─" * (width - 2) + "┘")
    
    def draw_details(self, stdscr, snapshot: Optional[EpistemicStateSnapshot]):
        """Draw detailed metrics view"""
        height, width = stdscr.getmaxyx()
        stdscr.clear()
        
        self.draw_header(stdscr, snapshot)
        
        if not snapshot:
            stdscr.addstr(6, 0, "│ No snapshot data available")
            stdscr.addstr(6, width - 1, "│")
            self.draw_commands(stdscr, 7)
            return
        
        y = 5
        
        # All 13 vectors
        stdscr.addstr(y, 0, "│ EPISTEMIC VECTORS (13 dimensions)")
        stdscr.addstr(y, width - 1, "│")
        y += 1
        
        vectors = snapshot.vectors
        vector_names = [
            ('engagement', 'GATE'),
            ('know', 'FOUNDATION'),
            ('do', 'FOUNDATION'),
            ('context', 'FOUNDATION'),
            ('clarity', 'COMPREHENSION'),
            ('coherence', 'COMPREHENSION'),
            ('signal', 'COMPREHENSION'),
            ('density', 'COMPREHENSION'),
            ('state', 'EXECUTION'),
            ('change', 'EXECUTION'),
            ('completion', 'EXECUTION'),
            ('impact', 'EXECUTION'),
            ('uncertainty', 'META-EPISTEMIC')
        ]
        
        for name, category in vector_names:
            score = vectors.get(name, 0.0)
            bar = self.format_bar(score, 30)
            line = f"  {name.upper():12} {bar} {score:.2f} ({category})"
            stdscr.addstr(y, 0, "│ ")
            stdscr.addstr(y, 2, line)
            stdscr.addstr(y, width - 1, "│")
            y += 1
            
            if y >= height - 5:
                break
        
        self.draw_commands(stdscr, y)
    
    def export_snapshot(self, snapshot: EpistemicStateSnapshot):
        """Export snapshot to JSON file"""
        if not snapshot:
            return None
        
        filename = f"snapshot_{snapshot.snapshot_id[:8]}_{int(time.time())}.json"
        filepath = Path(filename)
        
        with open(filepath, 'w') as f:
            f.write(snapshot.to_json())
        
        return str(filepath.absolute())
    
    def main_loop(self, stdscr):
        """Main curses loop"""
        # Initialize colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)    # EXCELLENT
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)   # GOOD
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # FAIR
        curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # DEGRADED
        curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)     # CRITICAL
        
        # Configure curses
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(1)   # Non-blocking input
        stdscr.timeout(100) # 100ms timeout for getch()
        
        while self.running:
            try:
                # Clear screen
                stdscr.clear()
                
                # Get latest snapshot
                snapshot = None
                snapshots = []
                
                if self.session_id:
                    try:
                        snapshot = self.provider.get_latest_snapshot(self.session_id)
                        snapshots = self.provider.get_snapshot_history(self.session_id, limit=10)
                    except Exception as e:
                        self.message = f"Error loading snapshots: {str(e)[:50]}"
                
                # Draw UI based on mode
                if self.show_details and snapshot:
                    self.draw_details(stdscr, snapshot)
                else:
                    # Normal view
                    self.draw_header(stdscr, snapshot)
                    
                    y_offset = 5
                    y_offset = self.draw_compression_status(stdscr, snapshot, y_offset)
                    y_offset = self.draw_snapshot_timeline(stdscr, snapshots, y_offset)
                    
                    self.draw_commands(stdscr, y_offset)
                
                # Refresh display
                stdscr.refresh()
                
                # Handle input
                key = stdscr.getch()
                
                if key == ord('q') or key == ord('Q'):
                    self.running = False
                elif key == ord('r') or key == ord('R'):
                    self.message = "Refreshed"
                elif key == ord('f') or key == ord('F'):
                    self.show_full = not self.show_full
                    self.message = f"Full view: {'ON' if self.show_full else 'OFF'}"
                elif key == ord('e') or key == ord('E'):
                    if snapshot:
                        filepath = self.export_snapshot(snapshot)
                        self.message = f"Exported to {filepath}"
                    else:
                        self.message = "No snapshot to export"
                elif key == ord('d') or key == ord('D'):
                    self.show_details = not self.show_details
                    self.message = f"Details view: {'ON' if self.show_details else 'OFF'}"
                
                # Auto-refresh every interval
                if time.time() - self.last_update > self.update_interval:
                    self.last_update = time.time()
                
                # Small delay to prevent CPU spinning
                time.sleep(0.05)
                
            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                # Draw error message but keep running
                try:
                    height, width = stdscr.getmaxyx()
                    stdscr.addstr(height-1, 0, f"⚠️  ERROR: {str(e)[:width-12]}", curses.color_pair(3))
                    stdscr.refresh()
                except:
                    pass  # If we can't even draw the error, just continue
                self.message = f"Error: {str(e)[:50]}"
                time.sleep(0.5)  # Brief pause, then continue
                # Don't set self.running = False - keep the dashboard running!


def launch_dashboard(session_id: Optional[str] = None):
    """
    Launch the snapshot monitoring dashboard
    
    Args:
        session_id: Session ID to monitor (uses current session if None)
    """
    monitor = SnapshotMonitor(session_id)
    
    if not monitor.session_id:
        print("❌ No session ID provided and no active session found")
        print("   Start a session first or provide a session_id")
        return
    
    print(f"🖥️  Launching dashboard for session: {monitor.session_id[:8]}...")
    print("   Press 'q' to quit")
    
    try:
        curses.wrapper(monitor.main_loop)
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        import traceback
        traceback.print_exc()
    
    print("✅ Dashboard closed")


if __name__ == "__main__":
    # Command line usage
    session_id = sys.argv[1] if len(sys.argv) > 1 else None
    launch_dashboard(session_id)
