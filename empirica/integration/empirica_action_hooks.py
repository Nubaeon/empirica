#!/usr/bin/env python3
"""
🔗 Empirica Action Hooks
Automatically feeds tmux panels via JSON when components are used

Feeds:
- /tmp/empirica_realtime/12d_vectors.json - Full 12D epistemic monitor
- /tmp/empirica_realtime/cascade_status.json - All 5 cascade phases with goal
- /tmp/empirica_realtime/chain_of_thought.json - User-facing reasoning steps
- /tmp/empirica_realtime/statusline_*.json - Per-AI statusline cache (audit trail)

Triggers statusline display when CASCADE phases change, enabling real-time
audit trail during action replay and live task execution.
"""

import json
import time
from pathlib import Path
from functools import wraps
from typing import Any, Dict, Callable
import os

# Ensure realtime directory exists
REALTIME_DIR = Path("/tmp/empirica_realtime")
REALTIME_DIR.mkdir(exist_ok=True)

class EmpiricaActionHooks:
    """Action hooks that feed tmux panels in real-time"""
    
    @staticmethod
    def update_12d_monitor(state: Dict[str, Any]):
        """Update 12D epistemic monitor JSON feed"""
        try:
            # Extract full 12D state with flexible key handling
            def get_nested_value(data, path, fallback=0.5):
                """Get nested dict value with multiple key variations"""
                if not isinstance(data, dict):
                    return fallback
                for section, key in [path]:
                    section_data = data.get(section, {})
                    if not isinstance(section_data, dict):
                        return fallback
                    # Try both uppercase and lowercase keys
                    return section_data.get(key.upper(), section_data.get(key.lower(), fallback))
            
            # Handle both uppercase and lowercase input keys
            unc = state.get("epistemic_uncertainty", {})
            comp = state.get("epistemic_comprehension", {})
            exec_aw = state.get("execution_awareness", {})
            engage = state.get("engagement", {})
            
            twelve_d_data = {
                "timestamp": time.time(),
                "epistemic_uncertainty": {
                    "KNOW": unc.get("KNOW", unc.get("know", 0.5)),
                    "DO": unc.get("DO", unc.get("do", 0.5)),
                    "CONTEXT": unc.get("CONTEXT", unc.get("context", 0.5))
                },
                "epistemic_comprehension": {
                    "CLARITY": comp.get("CLARITY", comp.get("clarity", 0.5)),
                    "COHERENCE": comp.get("COHERENCE", comp.get("coherence", 0.5)),
                    "DENSITY": comp.get("DENSITY", comp.get("density", 0.5)),
                    "SIGNAL": comp.get("SIGNAL", comp.get("signal", 0.5))
                },
                "execution_awareness": {
                    "STATE": exec_aw.get("STATE", exec_aw.get("state", 0.5)),
                    "CHANGE": exec_aw.get("CHANGE", exec_aw.get("change", 0.5)),
                    "COMPLETION": exec_aw.get("COMPLETION", exec_aw.get("completion", 0.5)),
                    "IMPACT": exec_aw.get("IMPACT", exec_aw.get("impact", 0.5))
                },
                "engagement": {
                    "ENGAGEMENT": engage.get("ENGAGEMENT", engage.get("engagement", 0.5))
                },
                "overall_confidence": state.get("overall_confidence", 0.5),
                "ai_id": state.get("ai_id", "empirica_agent")
            }
            
            output_file = REALTIME_DIR / "12d_vectors.json"
            with open(output_file, 'w') as f:
                json.dump(twelve_d_data, f, indent=2)
            
            # Trigger immediate pane update
            trigger_pane_update('12d')
                
        except Exception as e:
            print(f"Warning: Could not update 12D monitor feed: {e}")
    
    @staticmethod
    def update_cascade_status(phase: str, goal: str, context: Dict[str, Any]):
        """Update metacognitive cascade status with all 5 phases"""
        try:
            cascade_data = {
                "timestamp": time.time(),
                "current_goal": goal,
                "current_phase": phase,
                "phases": {
                    "THINK": {
                        "status": "complete" if phase != "THINK" else "active",
                        "description": context.get("think_description", "Analyzing the task and requirements"),
                        "active": phase == "THINK"
                    },
                    "INVESTIGATE": {
                        "status": "complete" if phase not in ["THINK", "INVESTIGATE"] else "active" if phase == "INVESTIGATE" else "pending",
                        "description": context.get("investigate_description", "Gathering information and examining components"),
                        "active": phase == "INVESTIGATE"
                    },
                    "UNCERTAINTY": {
                        "status": "active" if phase == "UNCERTAINTY" else "pending" if phase in ["THINK", "INVESTIGATE"] else "complete",
                        "description": context.get("uncertainty_description", "Checking epistemic humility and calibrating confidence"),
                        "active": phase == "UNCERTAINTY"
                    },
                    "CHECK": {
                        "status": "active" if phase == "CHECK" else "pending" if phase in ["THINK", "INVESTIGATE", "UNCERTAINTY"] else "complete",
                        "description": "Verifying understanding and approach",
                        "active": phase == "CHECK"
                    },
                    "ACT": {
                        "status": "active" if phase == "ACT" else "pending",
                        "description": "Executing with confidence",
                        "active": phase == "ACT"
                    }
                },
                "context": context
            }
            
            output_file = REALTIME_DIR / "cascade_status.json"
            with open(output_file, 'w') as f:
                json.dump(cascade_data, f, indent=2)
            
            # Trigger immediate pane update
            trigger_pane_update('cascade')
                
        except Exception as e:
            print(f"Warning: Could not update cascade status feed: {e}")
    
    @staticmethod
    def update_chain_of_thought(thought: str, phase: str, goal: str = None):
        """Update chain of thought with user-facing reasoning step"""
        try:
            # Read existing chain
            output_file = REALTIME_DIR / "chain_of_thought.json"
            if output_file.exists():
                with open(output_file, 'r') as f:
                    chain_data = json.load(f)
            else:
                chain_data = {"thoughts": [], "current_goal": None}

            # Add new thought
            new_thought = {
                "timestamp": time.time(),
                "phase": phase,
                "thought": thought,
                "goal": goal or chain_data.get("current_goal", "Processing")
            }

            # Keep last 10 thoughts
            chain_data["thoughts"] = chain_data.get("thoughts", [])[-9:] + [new_thought]
            chain_data["current_goal"] = goal or chain_data.get("current_goal")
            chain_data["current_phase"] = phase
            chain_data["last_updated"] = time.time()

            with open(output_file, 'w') as f:
                json.dump(chain_data, f, indent=2)

            # Trigger immediate pane update
            trigger_pane_update('thought')

        except Exception as e:
            print(f"Warning: Could not update chain of thought feed: {e}")

    @staticmethod
    def update_snapshot_status(snapshot: Dict[str, Any]):
        """Update snapshot monitor JSON feed"""
        try:
            snapshot_data = {
                "timestamp": time.time(),
                "snapshot_id": snapshot.get("snapshot_id"),
                "session_id": snapshot.get("session_id"),
                "ai_id": snapshot.get("ai_id"),
                "cascade_phase": snapshot.get("cascade_phase"),
                "vectors": snapshot.get("vectors", {}),
                "delta": snapshot.get("delta", {}),
                "compression": {
                    "original_tokens": snapshot.get("original_context_tokens", 0),
                    "snapshot_tokens": snapshot.get("snapshot_tokens", 0),
                    "ratio": snapshot.get("compression_ratio", 0.0),
                    "fidelity": snapshot.get("fidelity_score", 1.0),
                    "information_loss": snapshot.get("information_loss_estimate", 0.0)
                },
                "transfer": {
                    "count": snapshot.get("transfer_count", 0),
                    "reliability": snapshot.get("reliability", 1.0),
                    "should_refresh": snapshot.get("should_refresh", False),
                    "refresh_reason": snapshot.get("refresh_reason")
                },
                "created_at": snapshot.get("created_at", "")
            }

            output_file = REALTIME_DIR / "snapshot_status.json"
            with open(output_file, 'w') as f:
                json.dump(snapshot_data, f, indent=2)

            # Trigger immediate pane update
            trigger_pane_update('snapshot')

        except Exception as e:
            print(f"Warning: Could not update snapshot monitor feed: {e}")

    @staticmethod
    def update_statusline_cache(session_id: str, ai_id: str, phase: str, vectors: Dict[str, float] = None):
        """Update statusline cache for fast rendering during action replay.

        This allows statusline to be triggered/refreshed automatically when
        CASCADE phases change, providing real-time audit trail.
        """
        try:
            statusline_data = {
                "timestamp": time.time(),
                "session_id": session_id,
                "ai_id": ai_id,
                "phase": phase,
                "vectors": vectors or {},
                "display_mode": os.getenv('EMPIRICA_STATUS_MODE', 'balanced')
            }

            output_file = REALTIME_DIR / f"statusline_{ai_id}.json"
            with open(output_file, 'w') as f:
                json.dump(statusline_data, f, indent=2)

            # Trigger statusline pane update
            trigger_pane_update('statusline')

        except Exception as e:
            print(f"Warning: Could not update statusline cache: {e}")

def track_component_usage(component_name: str):
    """Decorator to track when Empirica components are used"""
    def decorator(func: Callable) -> Callable:
        """Wrap function with component usage tracking."""
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Execute function with usage tracking."""
            # Track component usage
            hooks = EmpiricaActionHooks()
            
            # Log usage
            hooks.update_chain_of_thought(
                f"Using {component_name}",
                "ACT",
                goal=kwargs.get("goal", f"Running {component_name}")
            )
            
            # Execute function
            result = func(*args, **kwargs)
            
            # If result contains 12D state, update monitor
            if isinstance(result, dict):
                if "epistemic_uncertainty" in result or "epistemic_comprehension" in result:
                    hooks.update_12d_monitor(result)
            
            return result
        return wrapper
    return decorator

def track_cascade_phase(phase: str, goal: str = None):
    """Decorator to track metacognitive cascade phases"""
    def decorator(func: Callable) -> Callable:
        """Wrap function with cascade phase tracking."""
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Execute function with phase tracking."""
            hooks = EmpiricaActionHooks()
            
            # Update cascade status
            actual_goal = goal or kwargs.get("goal", "Processing task")
            hooks.update_cascade_status(phase, actual_goal, kwargs)
            
            # Add to chain of thought
            phase_descriptions = {
                "THINK": "Thinking about the problem and approach",
                "INVESTIGATE": "Investigating components and gathering information",
                "UNCERTAINTY": "Assessing uncertainty and confidence levels",
                "CHECK": "Checking understanding and verifying approach",
                "ACT": "Taking action with validated confidence"
            }
            hooks.update_chain_of_thought(
                phase_descriptions.get(phase, f"Phase: {phase}"),
                phase,
                actual_goal
            )
            
            # Execute function
            result = func(*args, **kwargs)
            
            return result
        return wrapper
    return decorator

# Convenience functions for direct usage
def log_cascade_phase(phase: str, goal: str, context: Dict[str, Any] = None):
    """Directly log a cascade phase"""
    hooks = EmpiricaActionHooks()
    hooks.update_cascade_status(phase, goal, context or {})

def log_12d_state(state: Dict[str, Any]):
    """Directly log 12D monitor state"""
    hooks = EmpiricaActionHooks()
    hooks.update_12d_monitor(state)

def log_thought(thought: str, phase: str = "ACT", goal: str = None):
    """Directly log a thought to chain"""
    hooks = EmpiricaActionHooks()
    hooks.update_chain_of_thought(thought, phase, goal)

def log_statusline(session_id: str, ai_id: str, phase: str, vectors: Dict[str, float] = None):
    """Directly update statusline cache for audit trail.

    Use this after CASCADE phase transitions to trigger statusline updates
    during action replay.
    """
    hooks = EmpiricaActionHooks()
    hooks.update_statusline_cache(session_id, ai_id, phase, vectors)

# Auto-initialize tmux dashboard when action hooks are imported
def initialize_tmux_dashboard():
    """Initialize tmux dashboard for real-time monitoring"""
    try:
        from tmux_dashboard_manager import TMuxDashboardManager
        manager = TMuxDashboardManager()
        
        # Only create if session doesn't exist
        if not manager.session_exists():
            print("🖥️ Initializing TMux dashboard...")
            if manager.create_session() and manager.create_dashboard_window():
                manager.start_dashboard_monitoring()
                print("   ✅ TMux dashboard ready for real-time monitoring")
                return True
        else:
            print("   ✅ TMux dashboard session already active")
            return True
    except Exception as e:
        print(f"   ⚠️ TMux dashboard initialization failed: {e}")
        return False

# Initialize on import
if __name__ == "__main__":
    print("🔗 Empirica Action Hooks initialized")
    print(f"   📁 Realtime directory: {REALTIME_DIR}")
    print(f"   📊 12D monitor feed: {REALTIME_DIR / '12d_vectors.json'}")
    print(f"   🔄 Cascade status feed: {REALTIME_DIR / 'cascade_status.json'}")
    print(f"   💭 Chain of thought feed: {REALTIME_DIR / 'chain_of_thought.json'}")
    
    # Test tmux dashboard integration
    print("\n🖥️ Testing TMux Dashboard Integration:")
    initialize_tmux_dashboard()

# Trigger-based pane updates (no polling)
def trigger_pane_update(pane_name: str):
    """Trigger immediate tmux pane update after JSON file change"""
    try:
        import subprocess

        pane_map = {
            '12d': 'empirica:dashboard.0',
            'cascade': 'empirica:dashboard.1',
            'thought': 'empirica:dashboard.2',
            'snapshot': 'empirica:dashboard.1',  # Upper-right pane for snapshot dashboard
            'statusline': 'empirica:statusline'  # Dedicated statusline pane for audit trail
        }

        pane = pane_map.get(pane_name)
        if not pane:
            return

        # Send refresh command to pane (Ctrl+L to refresh current display)
        subprocess.run(['tmux', 'send-keys', '-t', pane, 'C-l'], check=False)

    except Exception as e:
        pass  # Silent fail if tmux not available

