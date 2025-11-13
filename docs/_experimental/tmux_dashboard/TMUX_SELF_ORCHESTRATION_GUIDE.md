# 🖥️ TMux Self-Orchestration Guide for Claude AIs

## Quick Start for New Claude Sessions

```bash
# 1. Initialize with path management
cd semantic_self_aware_kit/mcp_servers
python3 -c "
from tmux_path_manager import TmuxPathManager, enhance_simple_tmux_manager
from simple_tmux_manager import SimpleTmuxManager

# Enhance with path management
enhance_simple_tmux_manager()

# Initialize with portable paths
path_mgr = TmuxPathManager()
path_mgr.standardize_all_panes()  # Set all panes to workspace root

manager = SimpleTmuxManager()
manager.setup_self_management_layout()
print(f'✅ Portable tmux orchestration ready: {manager.session_name}')
"

# 2. Use MCP interface (now with path awareness)
# empirica-tmux server provides: list_sessions, create_session, setup_workspace, monitor_workspace
```

## Path Portability Solution

**Problem**: Variable paths cause command failures across different workspace setups.

**Solution**: TmuxPathManager provides:
- Auto-detection of workspace root
- Standardized pane paths
- Portable command execution
- Semantic path mapping (cli/monitor/debug/empirica/mcp)

## Semantic Layout Convention

- **cli**: Main interface (rovodev/acli) - pane 0
- **monitor**: System/component monitoring - pane 1  
- **debug**: Testing/validation output - pane 2
- **work**: Active development (optional)
- **log**: Log viewing (optional)

## Action Hooks System

The tmux orchestration uses action hooks for:
- Session persistence across AI instances
- Workspace state restoration
- Component monitoring integration
- Real-time debugging support

## MCP Integration

Available via `empirica-tmux` MCP server:
- `list_sessions`: Get all tmux sessions
- `create_session`: Create semantic workspace
- `setup_workspace`: Configure development layout
- `monitor_workspace`: Real-time status monitoring

## Token Efficiency Pattern

✅ **Efficient**: Read panes directly with `tmux capture-pane -t N -p`
❌ **Wasteful**: Duplicate pane output in main interface

```python
# Read debug output efficiently
debug_output = subprocess.run(['tmux', 'capture-pane', '-t', '2', '-p'], 
                             capture_output=True, text=True).stdout
# Process internally, summarize to interface
```

## Self-Management Workflow

1. **Initialize**: Use SimpleTmuxManager to assess current layout
2. **Setup**: Create missing semantic panes (monitor/debug)
3. **Execute**: Run commands in appropriate panes
4. **Monitor**: Use tmux capture-pane for validation
5. **Report**: Clean interface summaries only

This enables seamless handoff between Claude instances with persistent workspace awareness.