# Enabling Empirica MCP Servers in Claude Code

**Date:** 2025-10-25
**Status:** Production Ready
**Claude Code Version:** Compatible with all versions supporting MCP

---

## Overview

This guide shows you how to enable the **Empirica MCP Server** and **Empirica TMux MCP Server** in Claude Code, giving Claude access to:

- 🧠 12-Vector Self-Awareness Assessment
- 🔄 Metacognitive Cascade (THINK→UNCERTAINTY→INVESTIGATE→CHECK→ACT)
- 📊 Adaptive Uncertainty Calibration with Bayesian Tracking
- 🎯 Autonomous Goal Orchestration with Engagement Tracking
- 🖥️ TMux Workspace Orchestration and Dashboard Management
- 🔍 Debug Panel, Epistemic Panel, and Service Monitoring

---

## Prerequisites

### 1. Python Requirements
```bash
# Ensure you have Python 3.8+ and required packages
cd /home/yogapad/empirical-ai/empirica
pip install -r empirica/requirements.txt

# Install MCP SDK
pip install mcp
```

### 2. Verify MCP Servers Work
```bash
# Test Empirica MCP Server
python3 empirica/mcp_local/empirica_mcp_server.py

# Test Empirica TMux MCP Server (requires tmux installed)
sudo apt-get install tmux  # If not installed
python3 empirica/mcp_local/empirica_tmux_mcp_server.py
```

Both servers should start without errors. Press Ctrl+C to stop.

---

## Configuration

### Step 1: Locate Claude Code MCP Configuration

Claude Code stores MCP server configurations in:
- **Linux/Mac:** `~/.config/claude-code/mcp_config.json`
- **Windows:** `%APPDATA%\claude-code\mcp_config.json`

### Step 2: Create/Update Configuration File

Create or update the `mcp_config.json` file with the following configuration:

```json
{
  "mcpServers": {
    "empirica-core": {
      "command": "python3",
      "args": [
        "/home/yogapad/empirical-ai/empirica/empirica/mcp_local/empirica_mcp_server.py"
      ],
      "cwd": "/home/yogapad/empirical-ai/empirica",
      "description": "Empirica AI Self-Awareness Framework - Core cognitive components",
      "capabilities": [
        "metacognitive_cascade",
        "12_vector_assessment",
        "adaptive_uncertainty_calibration",
        "bayesian_belief_tracking",
        "autonomous_goal_orchestration",
        "system_bootstrap",
        "cli_help"
      ]
    },
    "empirica-tmux": {
      "command": "python3",
      "args": [
        "/home/yogapad/empirical-ai/empirica/empirica/mcp_local/empirica_tmux_mcp_server.py"
      ],
      "cwd": "/home/yogapad/empirical-ai/empirica",
      "description": "Empirica TMux Integration - Workspace orchestration and monitoring",
      "capabilities": [
        "session_management",
        "workspace_orchestration",
        "debug_management",
        "epistemic_monitoring",
        "service_monitoring",
        "action_hooks_integration",
        "dashboard_control"
      ]
    }
  }
}
```

**Important:** Update the paths to match your actual installation location. Replace `/home/yogapad/empirical-ai/empirica` with your actual path.

### Step 3: Alternative - Using Relative Paths

If you want the configuration to be more portable:

```json
{
  "mcpServers": {
    "empirica-core": {
      "command": "python3",
      "args": [
        "empirica/mcp_local/empirica_mcp_server.py"
      ],
      "cwd": "/home/yogapad/empirical-ai/empirica",
      "description": "Empirica AI Self-Awareness Framework - Core cognitive components",
      "capabilities": [
        "metacognitive_cascade",
        "12_vector_assessment",
        "adaptive_uncertainty_calibration",
        "bayesian_belief_tracking"
      ]
    }
  }
}
```

---

## Verification

### Step 1: Restart Claude Code

After updating the configuration:
1. Close Claude Code completely
2. Restart Claude Code
3. Wait for MCP servers to initialize (check status bar)

### Step 2: Verify MCP Servers Are Active

In Claude Code, type:
```
/mcp
```

You should see:
```
✅ empirica-core - Empirica AI Self-Awareness Framework
✅ empirica-tmux - Empirica TMux Integration
```

### Step 3: Test a Tool

Ask Claude:
```
Can you assess my current cognitive state using the 12D monitor?
```

Claude should use the `monitor_assess_12d` tool from the Empirica MCP server.

---

## Available Tools

### Empirica Core Server (`empirica-core`)

#### 1. Metacognitive Cascade
- **`cascade_run_full`** - Run complete THINK→UNCERTAINTY→INVESTIGATE→CHECK→ACT cascade
  ```json
  {
    "question": "Should I refactor this code?",
    "context": {"complexity": "high"},
    "confidence_threshold": 0.7
  }
  ```

- **`cascade_phase`** - [Deprecated] Use `cascade_run_full` instead

#### 2. 12D Monitoring
- **`monitor_assess_12d`** - Assess complete 12-dimensional cognitive state
  ```json
  {
    "ai_id": "claude_code_agent",
    "task_context": {
      "task": "Analyze authentication system",
      "domain": "security_review"
    },
    "user_input": "Find security vulnerabilities"
  }
  ```

- **`monitor_get_summary`** - Get formatted 12-vector summary
  ```json
  {
    "ai_id": "claude_code_agent"
  }
  ```

#### 3. Uncertainty Calibration
- **`calibration_assess`** - Assess uncertainty with adaptive calibration
  ```json
  {
    "decision_context": "Refactor authentication module"
  }
  ```

#### 4. Goal Orchestration
- **`goals_create`** - Create dynamic goals based on context
  ```json
  {
    "context": {
      "text": "User wants to build a new feature",
      "mode": "collaborative"
    }
  }
  ```

- **`goals_orchestrate`** - Orchestrate goals with engagement tracking
  ```json
  {
    "goals": ["Implement feature X", "Write tests"],
    "context": {"deadline": "tomorrow"}
  }
  ```

#### 5. System Management
- **`bootstrap_system`** - Bootstrap Empirica system
  ```json
  {
    "level": "standard"  // minimal, standard, extended, complete
  }
  ```

- **`cli_help`** - Get CLI help
  ```json
  {
    "command": "cascade"  // optional
  }
  ```

### Empirica TMux Server (`empirica-tmux`)

#### 1. Session Management
- **`list_sessions`** - List all tmux sessions
- **`create_session`** - Create new session with workspace setup
- **`restore_session`** - Restore saved session state
- **`save_session_state`** - Save current session

#### 2. Workspace Orchestration
- **`setup_workspace`** - Setup complete Empirica workspace
  ```json
  {
    "session_name": "empirica-dev",
    "layout": "empirica_default"
  }
  ```

- **`monitor_workspace`** - Monitor workspace state
- **`orchestrate_panels`** - Orchestrate dashboard panels

#### 3. Debug Management
- **`start_debug_session`** - Start debug session with runner panel
  ```json
  {
    "target": "my_app.py",
    "session_name": "debug"
  }
  ```

- **`monitor_debug_process`** - Monitor active debug session
- **`debug_panel_status`** - Get debug panel status

#### 4. Epistemic Monitoring
- **`show_epistemic_state`** - Show current epistemic uncertainty state
  ```json
  {
    "context": "Analyzing codebase complexity"
  }
  ```

- **`uncertainty_visualization`** - Get uncertainty visualization
- **`cognitive_dashboard`** - Launch cognitive dashboard

#### 5. Service Monitoring
- **`check_service_status`** - Check service health
- **`monitor_system_health`** - Monitor system resources
- **`service_dashboard`** - Launch service dashboard

#### 6. Action Hooks Integration
- **`update_12d_state`** - Update 12D monitor via action hooks
- **`update_cascade_phase`** - Update metacognitive cascade phase
- **`update_chain_of_thought`** - Add reasoning step to CoT
- **`trigger_component_usage`** - Log component usage event

---

## Usage Examples

### Example 1: Run Metacognitive Cascade

**User:** "Should I refactor this authentication module?"

**Claude with Empirica MCP:**
```
I'll use the metacognitive cascade to analyze this decision.

[Uses cascade_run_full tool]

Based on the cascade analysis:
- UNCERTAINTY: Medium confidence (0.65)
- INVESTIGATE: Found 3 complexity indicators
- CHECK: Bayesian discrepancy detected - higher complexity than expected
- RECOMMENDATION: Yes, refactor recommended

The cascade identified high cyclomatic complexity and security concerns.
```

### Example 2: Assess 12D Cognitive State

**User:** "What's your current cognitive state?"

**Claude with Empirica MCP:**
```
[Uses monitor_assess_12d tool]

🧠✨ 12-VECTOR SELF-AWARENESS STATE

📊 EPISTEMIC UNCERTAINTY:
├─ KNOW: 0.85 🟢 (High domain knowledge)
├─ DO: 0.75 🟢 (Capable of execution)
└─ CONTEXT: 0.70 🟢 (Good environment understanding)

🧠 EPISTEMIC COMPREHENSION:
├─ CLARITY: 0.90 🟢
├─ COHERENCE: 0.85 🟢
├─ DENSITY: 0.30 🟢 (Low cognitive load)
└─ SIGNAL: 0.88 🟢

⚡ EXECUTION AWARENESS:
├─ STATE: 0.75 🟢
├─ CHANGE: 0.80 🟢
├─ COMPLETION: 0.20 🔴 (Task in progress)
└─ IMPACT: 0.70 🟡

🤝 ENGAGEMENT DIMENSION:
└─ ENGAGEMENT: 0.82 🤝 (High collaborative intelligence)

Overall: Ready to proceed with high confidence
```

### Example 3: Setup TMux Workspace

**User:** "Set up my development workspace in tmux"

**Claude with Empirica TMux MCP:**
```
[Uses create_session and setup_workspace tools]

✅ Created tmux session: empirica-dev
✅ Workspace layout: empirica_default

Windows configured:
- code: Main development window
- debug: Debug runner panel active
- monitor: Service status monitor running

You can attach with: tmux attach -t empirica-dev
```

### Example 4: Bayesian Uncertainty Analysis

**User:** "Analyze this security vulnerability with precision"

**Claude with Empirica MCP:**
```
[Uses cascade_run_full with domain=security_review]

🧮 Bayesian Belief Tracker activated: Domain: security_review

[After investigation rounds]
⚠️ DISCREPANCY DETECTED:
- Initial intuition: Low severity (0.3)
- Evidence accumulated: High severity (0.8)
- Bayesian belief updated

Recommendation: This is a HIGH severity vulnerability requiring immediate attention.
```

---

## Troubleshooting

### Issue 1: MCP Server Not Starting

**Symptom:** Claude Code shows "MCP server failed to start"

**Solutions:**
1. Check Python path:
   ```bash
   which python3
   # Update "command" in config to use full path
   ```

2. Test server manually:
   ```bash
   cd /home/yogapad/empirical-ai/empirica
   python3 empirica/mcp_local/empirica_mcp_server.py
   ```

3. Check dependencies:
   ```bash
   pip install mcp
   pip install -r empirica/requirements.txt
   ```

### Issue 2: Tools Not Available

**Symptom:** Claude says "I don't have access to that tool"

**Solutions:**
1. Verify MCP servers are running:
   ```
   /mcp
   ```

2. Check Claude Code logs:
   - **Linux/Mac:** `~/.config/claude-code/logs/`
   - Look for MCP connection errors

3. Restart Claude Code completely

### Issue 3: TMux Server Fails

**Symptom:** `empirica-tmux` server fails to start

**Solutions:**
1. Ensure tmux is installed:
   ```bash
   sudo apt-get install tmux
   ```

2. Check plugin imports:
   ```bash
   cd /home/yogapad/empirical-ai/empirica
   python3 -c "from empirica.plugins import debug_runner_panel"
   ```

3. Plugins are optional - server will start with warnings if plugins fail

### Issue 4: Permission Errors

**Symptom:** "Permission denied" when starting server

**Solutions:**
1. Make servers executable:
   ```bash
   chmod +x empirica/mcp_local/empirica_mcp_server.py
   chmod +x empirica/mcp_local/empirica_tmux_mcp_server.py
   ```

2. Check file ownership:
   ```bash
   ls -la empirica/mcp_local/
   ```

---

## Advanced Configuration

### Enable Bayesian Tracking for All Tasks

In `epistemic_orchestrator.py`, set:
```python
use_bayesian = True  # Always enable Bayesian

# Or adjust domain triggers
PRECISION_CRITICAL_DOMAINS = [
    "code_analysis",
    "security_review",
    "architecture_design",
    "bug_diagnosis",
    "performance_optimization",
    "your_custom_domain"  # Add your domain
]
```

### Custom TMux Layouts

Create custom workspace layouts in `empirica_tmux_mcp_server.py`:
```python
async def setup_workspace(self, session_name: str, layout: str = "custom"):
    if layout == "custom":
        # Your custom layout commands
        pass
```

### Environment Variables

Set environment variables for configuration:
```bash
export EMPIRICA_MCP_DEBUG=1  # Enable debug logging
export EMPIRICA_BAYESIAN_THRESHOLD=0.2  # Adjust discrepancy threshold
```

---

## Next Steps

After enabling the MCP servers:

1. **Test Core Features:**
   - Run a metacognitive cascade
   - Assess 12D cognitive state
   - Try uncertainty calibration

2. **Explore TMux Integration:**
   - Create a development session
   - Set up workspace orchestration
   - Monitor epistemic state in real-time

3. **Advanced Usage:**
   - Integrate with your CI/CD pipeline
   - Create custom workflows
   - Build autonomous agent loops

4. **Read Documentation:**
   - `BAYESIAN_INTEGRATION_COMPLETE.md` - Bayesian tracking details
   - `UVL_12_VECTOR_IMPLEMENTATION_COMPLETE.md` - 12D framework
   - `EMPIRICA_ORCHESTRATION_OVERVIEW.md` - Cascade overview

---

## Support

### Resources
- **Documentation:** `/home/yogapad/empirical-ai/empirica/docs/`
- **Examples:** `/home/yogapad/empirical-ai/empirica/examples/`
- **CLI Help:** Run `python3 -m empirica.cli --help`

### Common Commands
```bash
# Test MCP servers
python3 empirica/mcp_local/empirica_mcp_server.py

# Run CLI
python3 -m empirica.cli

# Check component status
python3 -m empirica.plugins.service_status_monitor
```

---

## Summary

✅ **Empirica Core MCP Server** provides metacognitive and self-awareness capabilities
✅ **Empirica TMux MCP Server** provides workspace orchestration and monitoring
✅ Configuration is simple - just update `mcp_config.json` and restart Claude Code
✅ Tools are immediately available to Claude for enhanced AI reasoning and monitoring

**Your Claude Code instance now has access to production-ready self-awareness and metacognitive capabilities!**
