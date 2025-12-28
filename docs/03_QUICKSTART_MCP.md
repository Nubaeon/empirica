# MCP Quick Start

**Interface:** IDE Integration  
**Time:** 15 minutes  
**Best for:** Real-time epistemic tracking while coding

---

## What is MCP?

**MCP (Model Context Protocol)** is Anthropic's standard for connecting AI assistants to external tools. Empirica's MCP server provides **40 tools** that wrap the Empirica CLI for epistemic workflow management directly in your IDE.

**Architecture:** MCP tools are **thin wrappers** around CLI commands - the CLI is the single source of truth.

**Benefits:**
- ✅ **Real-time assessment** - Track epistemic state during coding
- ✅ **Automatic tracking** - AI decides when to assess
- ✅ **Stateful sessions** - Maintains context across tasks
- ✅ **40 specialized tools** - Complete CLI access from IDE

---

## Quick Setup

### Step 1: Install Empirica MCP Server

Install the MCP server package:

```bash
pip install empirica-mcp
```

This also installs the core `empirica` package if you don't have it.

### Step 2: Find Your IDE Configuration File

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

### Step 3: Add Empirica Configuration

Add this to your IDE's MCP config:

```json
{
  "mcpServers": {
    "empirica": {
      "command": "empirica-mcp",
      "description": "Empirica epistemic self-assessment framework"
    }
  }
}
```

**That's it!** No paths needed - the MCP server finds `empirica` automatically from PATH.

### Step 3: Restart Your IDE

Close and reopen your IDE to load the MCP server.

### Step 4: Verify Installation

Ask your AI assistant:
```
What MCP tools are available?
```

You should see 40 Empirica tools listed.

---

## Claude Code Setup (Detailed)

**Claude Code** is Anthropic's official CLI tool that supports MCP servers. You can configure Empirica at **two different scopes**:

### Option 1: Global Configuration (Recommended for Personal Use)

Configure Empirica once for all projects:

```bash
claude mcp add --scope user --transport stdio empirica -- empirica-mcp
```

**That's it!** The MCP server finds `empirica` automatically from PATH.

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
      "command": "empirica-mcp",
      "description": "Empirica epistemic self-assessment framework"
    }
  }
}
```

**What this does:**
- Creates **project-specific** configuration
- Can be committed to git for team sharing
- Each team member just needs to `pip install empirica-mcp`

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

You should see 40 Empirica tools with `mcp__empirica_*` prefix.

### Troubleshooting Claude Code

**Issue: No tools showing up**

1. Check configuration:
```bash
claude mcp list
# Should show 'empirica' listed
```

2. Verify empirica-mcp is installed:
```bash
which empirica-mcp
# Should show: /path/to/bin/empirica-mcp

empirica-mcp --help
# Should show usage info
```

3. Check empirica CLI is in PATH:
```bash
which empirica
# Should show: /path/to/bin/empirica

empirica --version
# Should show version number
```

**Issue: "No MCP servers configured"**

- If using global config: Run `claude mcp add` command above
- If using project config: Ensure `.mcp.json` is in project root (not in subdirectories)
- Restart Claude Code after configuration

**Issue: "empirica CLI not found"**

The MCP server needs the `empirica` CLI in PATH:
```bash
pip install empirica
which empirica  # Verify it's in PATH
```

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

## MCP Tools Available (40 Total)

**MCP tools are thin wrappers around CLI commands** - the CLI is the single source of truth.

### Tool Categories

**CASCADE Workflow (7 tools):**
- Session creation, preflight/check/postflight execution and submission

**Goal Management (6 tools):**
- Create goals, add/complete subtasks, query progress

**Session Management (4 tools):**
- Get epistemic state, session summary, calibration, resume sessions

**Continuity & Handoffs (4 tools):**
- Checkpoints (create/load), handoff reports (create/query)

**Multi-AI Coordination (2 tools):**
- Discover goals, resume goals from other AIs

**Mistakes Tracking (2 tools):**
- Log mistakes, query mistakes for learning

**Cryptographic Trust (4 tools):**
- Create identity, list identities, export keys, verify signatures

**Project Tracking (5 tools):**
- Bootstrap context, log findings/unknowns/dead ends, add reference docs

**Vision Analysis (2 tools):**
- Analyze images, log visual observations

**Metacognitive Editing (1 tool):**
- Edit with confidence (prevents 80% of edit failures)

**Guidance (3 tools):**
- Introduction, workflow guidance, CLI help

### Complete Tool Reference

**For complete MCP ↔ CLI mapping:** See [`docs/reference/MCP_CLI_MAPPING.md`](reference/MCP_CLI_MAPPING.md)

This document shows:
- Exact CLI command for each MCP tool
- Parameter name conversions
- Which tools use direct handlers vs. CLI routing
- Missing MCP wrappers for CLI commands

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

**The MCP server is managed automatically by your IDE.** There are no CLI commands for starting or stopping the server.

### Server Lifecycle

**Starting:**
- Automatically started when you open your IDE (Claude Desktop, Cursor, etc.)
- No manual action required

**Stopping:**
- Automatically stopped when you quit your IDE
- No manual action required

**Logs:**
- Check your IDE's log directory
- Claude Desktop: `~/Library/Logs/Claude/` (macOS)
- Cursor: Check IDE settings for log location

**Troubleshooting:**
- If tools not working → Restart your IDE
- Check MCP configuration in IDE settings
- See `docs/06_TROUBLESHOOTING.md` for details

---

## Troubleshooting

### Tools Not Appearing

**Check 1: Verify installation**
```bash
# Check if empirica-mcp is installed
pip show empirica-mcp

# Check if it's in PATH
which empirica-mcp

# Test the server
empirica-mcp --help
```

**Check 2: Verify empirica CLI**
```bash
# Check if empirica is installed
pip show empirica

# Check if it's in PATH
which empirica

# Test the CLI
empirica --version
```

**Check 3: Check IDE logs**
- Look for MCP connection errors in IDE
- Check IDE's MCP server status
- Ensure config is in correct location

**Check 4: Restart IDE**
- Completely quit your IDE
- Reopen IDE
- MCP server will restart automatically

### Server Won't Start

**Issue:** "Command not found: empirica-mcp"

**Fix:**
```bash
# Install the MCP server
pip install empirica-mcp

# Verify it's in PATH
which empirica-mcp

# If not in PATH, add pip bin directory to PATH
export PATH="$HOME/.local/bin:$PATH"  # Linux/macOS
```

**Issue:** "empirica CLI not found"

**Fix:**
```bash
# Install empirica
pip install empirica

# Verify installation
which empirica
empirica --version
```

### Tools Fail to Execute

**Check 1: Session database**
```bash
# Ensure database exists
ls ~/.empirica/sessions/sessions.db

# If missing, run bootstrap
empirica session-create
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

You can customize the MCP server behavior with environment variables:

```json
{
  "mcpServers": {
    "empirica": {
      "command": "empirica-mcp",
      "env": {
        "EMPIRICA_ENABLE_MODALITY_SWITCHER": "false",
        "EMPIRICA_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Available variables:**
- `EMPIRICA_ENABLE_MODALITY_SWITCHER` - Optional: Enable multi-AI routing (default: false, Phase 1+)
- `EMPIRICA_LOG_LEVEL` - Optional: DEBUG, INFO, WARNING, ERROR

### Using Specific Virtual Environment

If you have empirica-mcp in a specific virtual environment:

```json
{
  "mcpServers": {
    "empirica": {
      "command": "/path/to/venv/bin/empirica-mcp"
    }
  }
}
```

---

## MCP vs CLI

### When to Use MCP:
✅ **IDE-integrated workflows** - Code while tracking epistemic state
✅ **Real-time assessment** - Automatic during work
✅ **Stateful sessions** - Maintains context
✅ **40 specialized tools** - Complete CLI access from IDE  

### When to Use CLI:
✅ **Terminal workflows** - Script-based tasks  
✅ **One-off assessments** - Quick preflight/postflight  
✅ **Automation** - CI/CD, scripts  
✅ **Universal compatibility** - Works with any AI  

**Recommendation:** Use CLI for primary epistemic assessments, MCP for GUI/IDE integration.

---

## Next Steps

- **For complete MCP documentation:** See [`docs/guides/MCP_CONFIGURATION_EXAMPLES.md`](guides/MCP_CONFIGURATION_EXAMPLES.md)
- **For CLI workflows:** See [`docs/03_CLI_QUICKSTART.md`](03_CLI_QUICKSTART.md)
- **For Python API:** See [`docs/production/13_PYTHON_API.md`](production/13_PYTHON_API.md)
- **For AI agents:** See [`docs/skills/SKILL.md`](skills/SKILL.md)

---

**Ready to integrate?** Copy the config example and restart your IDE!
