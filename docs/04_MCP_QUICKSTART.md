# MCP Quick Start

**Interface:** IDE Integration  
**Time:** 15 minutes  
**Best for:** Real-time epistemic tracking while coding

---

## What is MCP?

**MCP (Model Context Protocol)** is Anthropic's standard for connecting AI assistants to external tools. Empirica's MCP server provides **21 tools** (17 core + 4 optional modality switcher) for epistemic workflow management directly in your IDE.

**Benefits:**
- ✅ **Real-time assessment** - Track epistemic state during coding
- ✅ **Automatic tracking** - AI decides when to assess
- ✅ **Stateful sessions** - Maintains context across tasks
- ✅ **21 specialized tools** - Fine-grained workflow control

---

## Quick Setup

### Step 1: Find Your IDE Configuration File

**Claude Desktop:**
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Rovo Dev (Claude Code MCP):**
- `~/.config/rovo-dev/mcp.json` or project-level `mcp_config_rovodev.json`

**Cursor:**
- `~/.cursor/mcp.json` or workspace `.cursor/mcp_config.json`

**Windsurf:**
- Windsurf settings > MCP Servers

### Step 2: Add Empirica Configuration

Add this to your IDE's MCP config:

```json
{
  "mcpServers": {
    "empirica": {
      "command": "python3",
      "args": [
        "/path/to/empirica/mcp_local/empirica_mcp_server.py"
      ],
      "description": "Empirica epistemic self-assessment framework",
      "env": {
        "PYTHONPATH": "/path/to/empirica"
      }
    }
  }
}
```

**Replace `/path/to/empirica`** with your actual Empirica installation path.

### Step 3: Restart Your IDE

Close and reopen your IDE to load the MCP server.

### Step 4: Verify Installation

Ask your AI assistant:
```
What MCP tools are available?
```

You should see 21 Empirica tools listed.

---

## Claude Code Setup (Detailed)

**Claude Code** is Anthropic's official CLI tool that supports MCP servers. You can configure Empirica at **two different scopes**:

### Option 1: Global Configuration (Recommended for Personal Use)

Configure Empirica once for all projects:

```bash
claude mcp add --scope user --transport stdio empirica \
  --env PYTHONPATH=/path/to/empirica \
  --env EMPIRICA_ENABLE_MODALITY_SWITCHER=false \
  -- env LD_LIBRARY_PATH= /path/to/empirica/.venv-mcp/bin/python3 \
  /path/to/empirica/mcp_local/empirica_mcp_server.py
```

**Replace `/path/to/empirica`** with your actual Empirica installation path (e.g., `/home/user/empirical-ai/empirica`).

**What this does:**
- Adds Empirica to your **user-level config** (`~/.claude.json`)
- Available in **all projects** automatically
- No per-project setup needed

**Verification:**
```bash
# List configured servers
claude mcp list

# Should show:
# empirica (stdio) - user scope
```

### Option 2: Project-Level Configuration (For Team Sharing)

Create `.mcp.json` in your project root for team collaboration:

```json
{
  "mcpServers": {
    "empirica": {
      "command": "env",
      "args": [
        "LD_LIBRARY_PATH=",
        "/path/to/empirica/.venv-mcp/bin/python3",
        "/path/to/empirica/mcp_local/empirica_mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/empirica",
        "EMPIRICA_ENABLE_MODALITY_SWITCHER": "false"
      }
    }
  }
}
```

**What this does:**
- Creates **project-specific** configuration
- Can be committed to git for team sharing
- Each team member gets same setup

### Verifying Claude Code Setup

After configuration, **restart Claude Code** and verify:

```bash
# Check MCP server list
claude mcp list

# In Claude Code session, run:
/mcp

# Or ask the AI:
"What MCP tools are available?"
```

You should see 15+ tools with `mcp__empirica_*` prefix.

### Troubleshooting Claude Code

**Issue: No tools showing up**

1. Check configuration:
```bash
claude mcp list
# Should show 'empirica' listed
```

2. Check paths are absolute (not relative):
```bash
# Bad: ./mcp_local/empirica_mcp_server.py
# Good: /home/user/empirical-ai/empirica/mcp_local/empirica_mcp_server.py
```

3. Verify Python virtual environment:
```bash
ls -la /path/to/empirica/.venv-mcp/bin/python3
```

4. Check server executable:
```bash
/path/to/empirica/.venv-mcp/bin/python3 /path/to/empirica/mcp_local/empirica_mcp_server.py --help
```

**Issue: "No MCP servers configured"**

- If using global config: Run `claude mcp add` command above
- If using project config: Ensure `.mcp.json` is in project root (not in subdirectories)
- Restart Claude Code after configuration

### Global vs Project Configuration

**Use Global (`--scope user`):**
- Personal development
- You work on multiple projects that need Empirica
- Don't want to configure each project separately

**Use Project (`.mcp.json`):**
- Team collaboration
- Sharing setup with other developers
- Project-specific Empirica configuration needed

**Both can coexist:** Project-level config takes precedence over global config.

---

## MCP Tools Available

### Core Workflow Tools (5)
1. **execute_preflight** - Assess epistemic state before task
2. **submit_preflight_assessment** - Log preflight scores
3. **execute_check** - Mid-task decision point validation
4. **execute_postflight** - Reassess after completion
5. **submit_postflight_assessment** - Log postflight with calibration

### Session Management (5)
6. **bootstrap_session** - Initialize new session
7. **resume_previous_session** - Load previous context
8. **get_epistemic_state** - Query current vectors
9. **get_session_summary** - Full session history
10. **get_calibration_report** - Check calibration accuracy

### Monitoring (3)
11. **query_bayesian_beliefs** - Belief tracking
12. **check_drift_monitor** - Behavioral integrity check
13. **query_goal_orchestrator** - Task hierarchy

### Guidance (2)
14. **get_workflow_guidance** - Workflow step guidance
15. **cli_help** - CLI command help

### Integration Tools (2)
16. **query_ai** - AI-to-AI communication via modality switcher
17. **execute_cli_command** - Token-efficient access to all 39 CLI commands

### Optional: Modality Switcher (4)
18. **modality_route_query** - Route to specialist AI (Phase 1+)
19. **modality_list_adapters** - List available AIs
20. **modality_adapter_health** - Health check
21. **modality_decision_assist** - Routing recommendation

---

## Usage Examples

### Example 1: Automatic Preflight

When you ask the AI to work on a task, it automatically assesses:

**You:**
```
Review the authentication module for security issues
```

**AI (internally):**
```
[Calls execute_preflight tool]
- Receives self-assessment prompt
- Genuinely assesses epistemic state
- KNOW: 0.6 (moderate auth knowledge)
- DO: 0.7 (can review code)
- CONTEXT: 0.5 (need to see the code first)
- UNCERTAINTY: 0.4 (moderate uncertainty)
[Calls submit_preflight_assessment with scores]
```

**AI (to you):**
```
Based on my epistemic assessment:
- I have moderate knowledge of auth patterns (KNOW: 0.6)
- I can effectively review code (DO: 0.7)
- I need to see the codebase first (CONTEXT: 0.5)

Let me start by examining the authentication module...
```

### Example 2: Mid-Task Check

During long tasks, AI can validate with CHECK phase:

**AI (internally during work):**
```
[After initial review, calls execute_check]
- Findings so far: 2 potential issues identified
- Remaining unknowns: Need to check session management
- Confidence: Moderate (0.6)
- Decision: Continue with investigation
```

### Example 3: Postflight Learning

After completing work:

**AI (internally):**
```
[Calls execute_postflight]
- Receives postflight self-assessment prompt
- Genuinely reassesses epistemic state
- KNOW: 0.8 (learned this codebase's patterns)
- Epistemic delta: +0.2 (genuine learning occurred)
[Calls submit_postflight_assessment]
- Calibration: Well-calibrated ✓
```

**AI (to you):**
```
Review complete! I found 3 security issues:
1. SQL injection vulnerability
2. Missing CSRF protection
3. Weak password hashing

Epistemic growth: My understanding of this codebase 
increased from 0.6 → 0.8. I was well-calibrated in 
my initial assessment.
```

---

## Monitoring Tools Deep Dive

The monitoring tools (11-13) provide visibility into epistemic tracking, behavioral integrity, and goal management.

### query_bayesian_beliefs - Evidence-Based Belief Tracking

**Purpose:** Access Bayesian belief tracking and detect calibration discrepancies.

**Use Cases:**
- Check evidence-based confidence levels for specific contexts
- Detect overconfidence patterns (intuition > evidence)
- Detect underconfidence patterns (intuition < evidence)
- Monitor belief updates during investigation

**Example Usage:**
```json
{
  "tool": "query_bayesian_beliefs",
  "arguments": {
    "session_id": "your-session-id",
    "context_key": "authentication_review"
  }
}
```

**Returns:**
```json
{
  "session_id": "your-session-id",
  "context_key": "authentication_review",
  "belief_state": {
    "know": {"mean": 0.62, "variance": 0.15},
    "context": {"mean": 0.58, "variance": 0.18}
  },
  "discrepancies": {
    "detected": true,
    "overconfidence": ["know"],
    "recommendation": "Evidence suggests lower confidence than intuition"
  }
}
```

**When to use:** When you need to validate your confidence against actual evidence gathered during investigation.

### check_drift_monitor - Behavioral Integrity Check

**Purpose:** Analyze behavioral patterns for drift issues (sycophancy, tension avoidance).

**Use Cases:**
- Detect sycophancy drift (increasing user-pleasing bias)
- Identify tension avoidance (not acknowledging conflicts)
- Monitor synthesis patterns for integrity
- Alert on behavioral degradation

**Example Usage:**
```json
{
  "tool": "check_drift_monitor",
  "arguments": {
    "session_id": "your-session-id",
    "window_size": 5
  }
}
```

**Returns:**
```json
{
  "session_id": "your-session-id",
  "drift_analysis": {
    "sycophancy_drift": {
      "detected": false,
      "severity": 0.15
    },
    "tension_avoidance": {
      "detected": false,
      "acknowledgment_rate": 0.80
    }
  },
  "recommendation": "No drift detected - behavioral integrity maintained"
}
```

**When to use:** Periodically check behavioral integrity, especially in long sessions or collaborative work.

### query_goal_orchestrator - Task Hierarchy Tracking

**Purpose:** Track goal decomposition, sub-goals, and progress.

**Use Cases:**
- Query current goal hierarchy
- Monitor sub-goal completion
- Track task dependencies
- Get visibility into autonomous planning

**Example Usage:**
```json
{
  "tool": "query_goal_orchestrator",
  "arguments": {
    "session_id": "your-session-id"
  }
}
```

**Returns:**
```json
{
  "session_id": "your-session-id",
  "goals": {
    "primary": "Review authentication module",
    "sub_goals": [
      {"id": "g1", "name": "Read auth code", "status": "complete"},
      {"id": "g2", "name": "Check vulnerabilities", "status": "in_progress"}
    ]
  },
  "progress": {
    "overall": 0.50,
    "completed": 1,
    "total": 2
  }
}
```

**When to use:** To understand how the AI has decomposed complex tasks and track progress.

---

## Advanced Integration Tools

### query_ai - AI-to-AI Communication

**Purpose:** Allows one AI to query another AI for specialized knowledge or analysis.

**Use Cases:**
- When you need a second opinion from a different AI model
- Specialized tasks requiring different model capabilities
- Cross-checking analysis with another AI perspective

**Example:**
```
AI (Claude) calls query_ai tool:
- query: "Analyze this Rust code for memory safety issues"
- adapter: "qwen"  (force Qwen for code analysis)
- strategy: "epistemic"

Result: Qwen's analysis returned to Claude
```

**Parameters:**
- `query` (required): Question or task for the other AI
- `adapter` (optional): Force specific adapter (qwen, minimax, gemini, rovodev, qodo, openrouter, copilot)
- `model` (optional): Force specific model (e.g., qwen-coder-turbo, gpt-4)
- `strategy` (optional): Routing strategy (epistemic, cost, latency, quality, balanced)
- `session_id` (optional): Track conversation history

**When to use:** When another AI's specialized capabilities would provide valuable insight.

### execute_cli_command - Token-Efficient CLI Access

**Purpose:** Provides access to all 39 Empirica CLI commands through a single MCP tool, reducing token overhead by 96%.

**Why it exists:** Instead of defining 39 separate MCP tools (massive token cost), this single tool wraps all CLI commands.

**Example:**
```
execute_cli_command({
  "command": "sessions-list",
  "arguments": [],
  "flags": {"limit": 10, "verbose": true}
})
```

**Available Commands:**
- **Workflow:** bootstrap, preflight, postflight, workflow, assess, cascade, decision
- **Sessions:** sessions-list, sessions-show, sessions-export
- **Monitoring:** monitor, monitor-export, monitor-cost
- **MCP:** mcp-start, mcp-stop, mcp-status, mcp-test, mcp-list-tools
- **Config:** config-init, config-show, config-validate, config-get, config-set
- **Performance:** benchmark, performance
- **Investigation:** investigate, analyze
- **Utilities:** feedback, goal-analysis, calibration, uvl
- **Components:** list, explain, demo
- **User Interface:** ask, chat

**When to use:** When you need CLI functionality from within MCP (e.g., listing sessions, exporting data, checking status).

---

## Configuration Examples

### Full Configuration Examples

See [`docs/guides/examples/mcp_configs/`](guides/examples/mcp_configs/) for complete examples for:
- Rovo Dev (Claude Code MCP)
- Claude Desktop
- Cursor IDE
- Windsurf IDE
- Continue.dev (VS Code)
- Zed Editor

---

## Managing MCP Server

### From CLI

You can manage the MCP server from command line:

```bash
# Start server
empirica mcp-start

# Check status
empirica mcp-status

# List available tools
empirica mcp-list-tools

# Test connection
empirica mcp-test

# Stop server
empirica mcp-stop
```

### Server Lifecycle

**When to start:**
- Automatically started by IDE when configured
- OR manually: `empirica mcp-start`

**When to stop:**
- IDE handles automatically
- OR manually: `empirica mcp-stop`

**Logs:**
- Location: `~/.empirica/mcp_server.log`
- View: `cat ~/.empirica/mcp_server.log`

---

## Troubleshooting

### Tools Not Appearing

**Check 1: Verify configuration path**
```bash
# Check if file exists
cat ~/.config/Claude/claude_desktop_config.json

# Verify Python path
python3 /path/to/empirica/mcp_local/empirica_mcp_server.py --help
```

**Check 2: Check IDE logs**
- Look for MCP connection errors in IDE
- Check that Python path is correct
- Ensure Empirica is installed

**Check 3: Test server manually**
```bash
empirica mcp-start
empirica mcp-status
```

### Server Won't Start

**Issue:** Permission denied

**Fix:**
```bash
# Make server executable
chmod +x /path/to/empirica/mcp_local/empirica_mcp_server.py

# Or use python3 explicitly (already in config)
```

**Issue:** Module not found

**Fix:**
```bash
# Verify installation
pip list | grep empirica

# Reinstall if needed
cd /path/to/empirica
pip install -e .
```

### Tools Fail to Execute

**Check 1: Session database**
```bash
# Ensure database exists
ls ~/.empirica/sessions/sessions.db

# If missing, run bootstrap
empirica bootstrap
```

**Check 2: Permissions**
```bash
# Check .empirica directory permissions
ls -la ~/.empirica

# Fix if needed
chmod -R u+rw ~/.empirica
```

---

## Advanced Configuration

### Environment Variables

```json
{
  "env": {
    "PYTHONPATH": "/path/to/empirica",
    "EMPIRICA_ENABLE_MODALITY_SWITCHER": "false",
    "EMPIRICA_LOG_LEVEL": "INFO"
  }
}
```

**Available variables:**
- `PYTHONPATH` - Required: Path to Empirica
- `EMPIRICA_ENABLE_MODALITY_SWITCHER` - Optional: Enable multi-AI routing (default: false, Phase 1+)
- `EMPIRICA_LOG_LEVEL` - Optional: DEBUG, INFO, WARNING, ERROR

### Using Virtual Environment

```json
{
  "command": "/path/to/venv/bin/python3",
  "args": ["/path/to/empirica/mcp_local/empirica_mcp_server.py"]
}
```

---

## MCP vs CLI

### When to Use MCP:
✅ **IDE-integrated workflows** - Code while tracking epistemic state  
✅ **Real-time assessment** - Automatic during work  
✅ **Stateful sessions** - Maintains context  
✅ **19 specialized tools** - Fine-grained control  

### When to Use CLI:
✅ **Terminal workflows** - Script-based tasks  
✅ **One-off assessments** - Quick preflight/postflight  
✅ **Automation** - CI/CD, scripts  
✅ **Universal compatibility** - Works with any AI  

**Recommendation:** Use MCP for primary IDE work, CLI for scripts and automation.

---

## Next Steps

- **For complete MCP documentation:** See [`docs/guides/MCP_CONFIGURATION_EXAMPLES.md`](guides/MCP_CONFIGURATION_EXAMPLES.md)
- **For CLI workflows:** See [`docs/03_CLI_QUICKSTART.md`](03_CLI_QUICKSTART.md)
- **For Python API:** See [`docs/production/13_PYTHON_API.md`](production/13_PYTHON_API.md)
- **For AI agents:** See [`docs/skills/SKILL.md`](skills/SKILL.md)

---

**Ready to integrate?** Copy the config example and restart your IDE!
