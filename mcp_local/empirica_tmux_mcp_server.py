#!/usr/bin/env python3
"""
🧠🖥️ Empirica TMux MCP Server
Self-orchestration addon for workspace management and tmux integration

Plugins Integration:
- debug_runner_panel: Debug process management
- epistemic_panel: Epistemic uncertainty visualization  
- helper_panel: AI assistance interface
- service_status_monitor: System monitoring

TMux Dashboard Features:
- Session persistence and restoration
- Workspace semantic memory
- Component monitoring
- Action hooks integration
"""

import asyncio
import json
import sys
import subprocess
import time
from typing import Any, Dict, List, Optional
from pathlib import Path

# Add semantic_self_aware_kit to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from mcp import server, types
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
except ImportError:
    print("Warning: MCP library not available, creating mock interface")
    
    class MockServer:
        def list_tools(self): return []
        def call_tool(self, name, args): return {"error": "MCP not available"}
    
    def stdio_server(): return MockServer()

# Import Empirica plugins
try:
    from plugins.debug_runner_panel import DebugRunnerPanel
    from plugins.epistemic_panel import EpistemicPanel  
    from plugins.helper_panel import HelperPanel
    from plugins.service_status_monitor import ServiceStatusMonitor
except ImportError as e:
    print(f"Warning: Plugin import failed: {e}")
    DebugRunnerPanel = None
    EpistemicPanel = None
    HelperPanel = None
    ServiceStatusMonitor = None

class EmpiricaTmuxServer:
    """Empirica TMux MCP Server for self-orchestration"""
    
    def __init__(self):
        self.debug_panel = None
        self.epistemic_panel = None
        self.helper_panel = None
        self.status_monitor = None
        
        # Initialize plugins
        self._initialize_plugins()
        
    def _initialize_plugins(self):
        """Initialize Empirica plugins with error handling"""
        try:
            if DebugRunnerPanel:
                self.debug_panel = DebugRunnerPanel()
                print("✅ Debug Runner Panel initialized")
        except Exception as e:
            print(f"⚠️ Debug panel init failed: {e}")
            
        try:
            if EpistemicPanel:
                self.epistemic_panel = EpistemicPanel()
                print("✅ Epistemic Panel initialized")
        except Exception as e:
            print(f"⚠️ Epistemic panel init failed: {e}")
            
        try:
            if HelperPanel:
                self.helper_panel = HelperPanel()
                print("✅ Helper Panel initialized")
        except Exception as e:
            print(f"⚠️ Helper panel init failed: {e}")
            
        try:
            if ServiceStatusMonitor:
                self.status_monitor = ServiceStatusMonitor()
                print("✅ Service Status Monitor initialized")
        except Exception as e:
            print(f"⚠️ Status monitor init failed: {e}")

    def get_tool_groups(self) -> Dict[str, List[str]]:
        """Return available TMux tool groups"""
        return {
            "session_management": [
                "list_sessions",
                "create_session",
                "restore_session",
                "save_session_state"
            ],
            "workspace_orchestration": [
                "setup_workspace",
                "monitor_workspace",
                "orchestrate_panels"
            ],
            "dashboard_management": [
                "launch_snapshot_dashboard",
                "check_dashboard_status",
                "spawn_dashboard_if_possible"
            ],
            "debug_management": [
                "start_debug_session",
                "monitor_debug_process",
                "debug_panel_status"
            ],
            "epistemic_monitoring": [
                "show_epistemic_state",
                "uncertainty_visualization",
                "cognitive_dashboard"
            ],
            "service_monitoring": [
                "check_service_status",
                "monitor_system_health",
                "service_dashboard"
            ]
        }

    # Session Management Tools
    async def list_sessions(self, session_name: str = None, **options) -> Dict[str, Any]:
        """List all tmux sessions"""
        try:
            result = subprocess.run(['tmux', 'list-sessions', '-F', '#{session_name}:#{session_windows}:#{session_created}'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                sessions = []
                for line in result.stdout.strip().splitlines():
                    if line:
                        name, windows, created = line.split(':')
                        sessions.append({
                            "name": name,
                            "windows": int(windows),
                            "created": created
                        })
                return {
                    "sessions": sessions,
                    "total": len(sessions),
                    "tool_group": "session_management"
                }
            else:
                return {"error": "No tmux sessions found or tmux not running"}
        except Exception as e:
            return {"error": f"Failed to list sessions: {e}"}

    async def create_session(self, name: str, workspace_type: str = "development") -> Dict[str, Any]:
        """Create new tmux session with workspace setup"""
        try:
            # Create session
            subprocess.run(['tmux', 'new-session', '-d', '-s', name], check=True)
            
            # Setup workspace based on type
            if workspace_type == "development":
                subprocess.run(['tmux', 'new-window', '-t', name, '-n', 'code'], check=True)
                subprocess.run(['tmux', 'new-window', '-t', name, '-n', 'debug'], check=True)
                subprocess.run(['tmux', 'new-window', '-t', name, '-n', 'monitor'], check=True)
            
            return {
                "session_created": name,
                "workspace_type": workspace_type,
                "windows_setup": "complete",
                "tool_group": "session_management"
            }
        except Exception as e:
            return {"error": f"Failed to create session: {e}"}

    # Workspace Orchestration Tools
    async def setup_workspace(self, session_name: str, layout: str = "empirica_default") -> Dict[str, Any]:
        """Setup complete Empirica workspace"""
        try:
            # Setup semantic workspace with panels
            commands = [
                f"tmux send-keys -t {session_name}:code 'cd semantic_self_aware_kit' Enter",
                f"tmux send-keys -t {session_name}:debug 'python3 -m semantic_self_aware_kit.empirica_cli' Enter", 
                f"tmux send-keys -t {session_name}:monitor 'python3 -m semantic_self_aware_kit.plugins.service_status_monitor' Enter"
            ]
            
            for cmd in commands:
                subprocess.run(cmd, shell=True, check=True)
            
            return {
                "workspace_setup": "complete",
                "layout": layout,
                "session": session_name,
                "tool_group": "workspace_orchestration"
            }
        except Exception as e:
            return {"error": f"Workspace setup failed: {e}"}

    # Dashboard Management Tools
    async def launch_snapshot_dashboard(self, force: bool = False) -> Dict[str, Any]:
        """Launch Empirica snapshot dashboard in tmux (if available)"""
        try:
            from empirica.plugins.dashboard_spawner import spawn_dashboard

            result = spawn_dashboard(force=force)

            if result.get("spawned"):
                return {
                    "status": "success",
                    "message": result.get("message", "Dashboard launched"),
                    "session": result.get("session"),
                    "pane": result.get("pane"),
                    "layout": result.get("layout"),
                    "tool_group": "dashboard_management"
                }
            else:
                return {
                    "status": "not_spawned",
                    "reason": result.get("reason"),
                    "message": result.get("message", "Dashboard not spawned"),
                    "tool_group": "dashboard_management"
                }
        except Exception as e:
            return {"error": f"Failed to launch dashboard: {e}", "tool_group": "dashboard_management"}

    async def check_dashboard_status(self) -> Dict[str, Any]:
        """Check if dashboard is currently running"""
        try:
            from empirica.plugins.dashboard_spawner import check_dashboard_status

            status = check_dashboard_status()
            return {
                **status,
                "tool_group": "dashboard_management"
            }
        except Exception as e:
            return {"error": f"Failed to check dashboard status: {e}", "tool_group": "dashboard_management"}

    async def spawn_dashboard_if_possible(self) -> Dict[str, Any]:
        """Attempt to spawn dashboard (silent if not possible)"""
        try:
            from empirica.plugins.dashboard_spawner import spawn_dashboard_if_possible

            spawned = spawn_dashboard_if_possible()

            if spawned:
                return {
                    "status": "success",
                    "message": "Dashboard spawned successfully",
                    "spawned": True,
                    "tool_group": "dashboard_management"
                }
            else:
                return {
                    "status": "not_spawned",
                    "message": "Dashboard not spawned (tmux not available or already running)",
                    "spawned": False,
                    "tool_group": "dashboard_management"
                }
        except Exception as e:
            return {"error": f"Failed to spawn dashboard: {e}", "tool_group": "dashboard_management"}

    # Debug Management Tools
    async def start_debug_session(self, target: str, session_name: str = "debug") -> Dict[str, Any]:
        """Start debug session with runner panel"""
        if not self.debug_panel:
            return {"error": "Debug panel not available"}
            
        try:
            debug_info = self.debug_panel.start_debug_session(target)
            
            # Setup tmux debug window
            subprocess.run(['tmux', 'new-window', '-t', session_name, '-n', f'debug-{target}'], check=True)
            subprocess.run(['tmux', 'send-keys', '-t', f'{session_name}:debug-{target}', 
                          f'python3 -c "from plugins.debug_runner_panel import DebugRunnerPanel; DebugRunnerPanel().monitor_debug(\'{target}\')"', 'Enter'], 
                          check=True)
            
            return {
                "debug_session": debug_info,
                "tmux_window": f"debug-{target}",
                "tool_group": "debug_management"
            }
        except Exception as e:
            return {"error": f"Debug session failed: {e}"}

    # Epistemic Monitoring Tools
    async def show_epistemic_state(self, context: str = "") -> Dict[str, Any]:
        """Show current epistemic uncertainty state"""
        if not self.epistemic_panel:
            return {"error": "Epistemic panel not available"}
            
        try:
            epistemic_state = self.epistemic_panel.get_current_state(context)
            return {
                "epistemic_state": epistemic_state,
                "visualization": "panel_active",
                "tool_group": "epistemic_monitoring"
            }
        except Exception as e:
            return {"error": f"Epistemic state failed: {e}"}

    # Action Hook API Endpoints
    async def update_12d_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Update 12D epistemic monitor via action hooks"""
        try:
            from empirica_action_hooks import log_12d_state
            log_12d_state(state)
            return {
                "status": "success",
                "message": "12D state updated via action hooks",
                "timestamp": time.time(),
                "tool_group": "action_hooks"
            }
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Failed to update 12D state: {e}",
                "tool_group": "action_hooks"
            }
    
    async def update_cascade_phase(self, phase: str, goal: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Update metacognitive cascade phase"""
        try:
            from empirica_action_hooks import log_cascade_phase
            log_cascade_phase(phase, goal, context or {})
            return {
                "status": "success",
                "message": f"Cascade updated to {phase} phase",
                "phase": phase,
                "goal": goal,
                "timestamp": time.time(),
                "tool_group": "action_hooks"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to update cascade: {e}",
                "tool_group": "action_hooks"
            }
    
    async def update_chain_of_thought(self, thought: str, phase: str = "ACT", goal: str = None) -> Dict[str, Any]:
        """Add reasoning step to chain of thought"""
        try:
            from empirica_action_hooks import log_thought
            log_thought(thought, phase, goal)
            return {
                "status": "success",
                "message": "Chain of thought updated",
                "thought": thought[:50] + "..." if len(thought) > 50 else thought,
                "phase": phase,
                "timestamp": time.time(),
                "tool_group": "action_hooks"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to update chain of thought: {e}",
                "tool_group": "action_hooks"
            }
    
    async def trigger_component_usage(self, component_name: str, usage_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Log component usage event for dashboard updates"""
        try:
            from empirica_action_hooks import log_thought, log_cascade_phase
            
            # Log component usage
            thought = f"Using {component_name}"
            if usage_context:
                thought += f" - {usage_context.get('description', '')}"
            
            log_thought(thought, "ACT", usage_context.get('goal', f'Running {component_name}'))
            
            # If usage context contains cascade info, update that too
            if usage_context and 'cascade_phase' in usage_context:
                log_cascade_phase(
                    usage_context['cascade_phase'], 
                    usage_context.get('goal', 'Component Usage'),
                    usage_context
                )
            
            return {
                "status": "success",
                "message": f"Component usage logged: {component_name}",
                "component": component_name,
                "timestamp": time.time(),
                "tool_group": "action_hooks"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to log component usage: {e}",
                "tool_group": "action_hooks"
            }

    async def orchestrate_panels(self, session_name: str = None, target_window: str = None) -> Dict[str, Any]:
        """Intelligently orchestrate tmux panels - detect existing layout and enhance minimally"""
        try:
            # Auto-detect current session if not provided
            if not session_name:
                result = subprocess.run(['tmux', 'display-message', '-p', '#{session_name}'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    session_name = result.stdout.strip()
                else:
                    return {"error": "No active tmux session found"}
            
            # Get current window info
            if not target_window:
                target_window = f"{session_name}:0"  # Default to first window
            
            # Check current pane layout
            pane_info = subprocess.run(['tmux', 'list-panes', '-t', target_window, '-F', '#{pane_id}:#{pane_width}:#{pane_height}'], 
                                     capture_output=True, text=True)
            
            if pane_info.returncode != 0:
                return {"error": f"Could not access window {target_window}"}
            
            panes = pane_info.stdout.strip().split('\n')
            pane_count = len([p for p in panes if p])
            
            layout_action = "none"
            
            if pane_count == 1:
                # Single pane - split vertically (main left, monitoring right)
                subprocess.run(['tmux', 'split-window', '-t', target_window, '-h', '-p', '25'], check=True)
                # Split right pane horizontally for upper/lower
                subprocess.run(['tmux', 'split-window', '-t', f'{target_window}.1', '-v'], check=True)
                # Split lower-right again to create small cascade status pane
                subprocess.run(['tmux', 'split-window', '-t', f'{target_window}.2', '-v', '-p', '25'], check=True)
                layout_action = "created_4_pane_layout"
                
            elif pane_count == 2:
                # Two panes - split right pane horizontally
                subprocess.run(['tmux', 'split-window', '-t', f'{target_window}.1', '-v'], check=True)
                # Split lower-right again for cascade status
                subprocess.run(['tmux', 'split-window', '-t', f'{target_window}.2', '-v', '-p', '25'], check=True)
                layout_action = "enhanced_to_4_pane_layout"
                
            elif pane_count >= 4:
                # Already has 4+ panes - leave existing layout alone
                layout_action = "preserved_existing_layout"
            elif pane_count == 3:
                # Has 3 panes - add one more small cascade status pane
                subprocess.run(['tmux', 'split-window', '-t', f'{target_window}.2', '-v', '-p', '25'], check=True)
                layout_action = "added_cascade_status_pane"
            
            # Start monitoring panels in appropriate panes
            if layout_action != "preserved_existing_layout":
                # Start chain of thought monitor in upper-right pane (pane 1)
                subprocess.run(['tmux', 'send-keys', '-t', f'{target_window}.1',
                              'python3 -m semantic_self_aware_kit.semantic_self_aware_kit.plugins.cot_monitor',
                              'Enter'], check=True)
                
                # Start cascade status in middle-right pane (pane 3)
                subprocess.run(['tmux', 'send-keys', '-t', f'{target_window}.3',
                              'python3 -m semantic_self_aware_kit.semantic_self_aware_kit.plugins.cascade_status_monitor',
                              'Enter'], check=True)
                
                # Start epistemic humility monitor in lower-right pane (pane 2)
                subprocess.run(['tmux', 'send-keys', '-t', f'{target_window}.2',
                              'python3 -m semantic_self_aware_kit.semantic_self_aware_kit.plugins.epistemic_monitor',
                              'Enter'], check=True)
            
            return {
                "orchestration": "complete",
                "layout_action": layout_action,
                "panes_detected": pane_count,
                "session": session_name,
                "window": target_window,
                "decision_flow_pane": f"{target_window}.1" if layout_action != "preserved_existing_layout" else "not_modified",
                "epistemic_log_pane": f"{target_window}.2" if layout_action != "preserved_existing_layout" else "not_modified",
                "tool_group": "workspace_orchestration"
            }
            
        except Exception as e:
            return {"error": f"Panel orchestration failed: {e}"}

    # Service Monitoring Tools
    async def check_service_status(self, session_name: str = None, **options) -> Dict[str, Any]:
        """Check status of all Empirica services"""
        if not self.status_monitor:
            return {"error": "Status monitor not available"}
            
        try:
            status = self.status_monitor.get_service_status()
            return {
                "service_status": status,
                "monitoring": "active",
                "tool_group": "service_monitoring"
            }
        except Exception as e:
            return {"error": f"Service status check failed: {e}"}

# MCP Server Setup
async def setup_mcp_server():
    """Setup MCP server with Empirica TMux capabilities"""
    
    server = Server("empirica-tmux")
    empirica_tmux = EmpiricaTmuxServer()
    
    @server.list_tools()
    async def list_tools() -> List[types.Tool]:
        """List all available Empirica TMux tools"""
        tools = []
        tool_groups = empirica_tmux.get_tool_groups()
        
        for group_name, tool_names in tool_groups.items():
            for tool_name in tool_names:
                tools.append(types.Tool(
                    name=tool_name,
                    description=f"Empirica TMux {group_name} tool: {tool_name}",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "session_name": {"type": "string", "description": "TMux session name"},
                            "options": {"type": "object", "description": "Additional options"}
                        }
                    }
                ))
        
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle tool calls"""
        
        # Route to appropriate method
        if hasattr(empirica_tmux, name):
            method = getattr(empirica_tmux, name)
            if asyncio.iscoroutinefunction(method):
                result = await method(**arguments)
            else:
                result = method(**arguments)
        else:
            result = {"error": f"Tool {name} not found"}
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    return server

async def main():
    """Main entry point"""
    print("🧠🖥️ Starting Empirica TMux MCP Server...")
    
    # Initialize server
    server = await setup_mcp_server()
    
    # Start stdio server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n✅ Empirica TMux MCP Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)