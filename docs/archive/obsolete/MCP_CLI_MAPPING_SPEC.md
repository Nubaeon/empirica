# MCP → CLI Mapping Specification

## 🎯 Architecture Decision

**Rewrite MCP server from scratch as a thin CLI wrapper (~500 lines)**

All stateful operations route through CLI for:
- Single source of truth
- No async bugs
- Easy testing
- Battle-tested code

## 📋 MCP Tool → CLI Command Mapping

### Category 1: Stateless (Handle Directly in MCP - No CLI Call)

**Keep these in MCP server as simple string returns:**

| MCP Tool | Implementation | Lines |
|----------|---------------|-------|
| `get_empirica_introduction` | Return static markdown | ~50 |
| `get_workflow_guidance` | Return guidance dict | ~30 |
| `cli_help` | Return help text | ~20 |

**Total:** ~100 lines of static content

---

### Category 2: Route to CLI (All Stateful Operations)

#### **Workflow Tools** (CASCADE)

| MCP Tool | CLI Command | Status | Priority |
|----------|-------------|--------|----------|
| `bootstrap_session` | `empirica bootstrap --ai-id=X --level=N --output json` | ✅ EXISTS | P0 |
| `execute_preflight` | `empirica preflight --session-id=X --prompt="..." --output json` | ⚠️ PARTIAL | P0 |
| `submit_preflight_assessment` | `empirica preflight-submit --session-id=X --vectors='{}' --output json` | ❌ MISSING | P0 |
| `execute_check` | `empirica check --session-id=X --findings='[]' --unknowns='[]' --output json` | ❌ MISSING | P0 |
| `submit_check_assessment` | `empirica check-submit --session-id=X --vectors='{}' --decision=X --output json` | ❌ MISSING | P0 |
| `execute_postflight` | `empirica postflight --session-id=X --summary="..." --output json` | ⚠️ PARTIAL | P0 |
| `submit_postflight_assessment` | `empirica postflight-submit --session-id=X --vectors='{}' --output json` | ❌ MISSING | P0 |

#### **Session Management**

| MCP Tool | CLI Command | Status | Priority |
|----------|-------------|--------|----------|
| `get_epistemic_state` | `empirica sessions-show <session-id> --output json` | ✅ EXISTS | P1 |
| `get_session_summary` | `empirica sessions-show <session-id> --verbose --output json` | ✅ EXISTS | P1 |
| `get_calibration_report` | `empirica calibration --session-id=X --output json` | ⚠️ EXISTS (no --output) | P1 |
| `resume_previous_session` | `empirica sessions-resume --ai-id=X --count=N --output json` | ❌ MISSING | P1 |

#### **Checkpoint Tools**

| MCP Tool | CLI Command | Status | Priority |
|----------|-------------|--------|----------|
| `create_git_checkpoint` | `empirica checkpoint-create --session-id=X --phase=Y --output json` | ✅ EXISTS | P0 |
| `load_git_checkpoint` | `empirica checkpoint-load <session-id> --output json` | ⚠️ EXISTS (no --output) | P0 |
| `get_vector_diff` | `empirica checkpoint-diff <id1> <id2> --output json` | ⚠️ EXISTS (no --output) | P2 |

#### **Goal/Task Management** (New Architecture)

| MCP Tool | CLI Command | Status | Priority |
|----------|-------------|--------|----------|
| `create_goal` | `empirica goals-create --session-id=X --objective="..." --scope=X --output json` | ❌ MISSING | P0 |
| `add_subtask` | `empirica goals-add-subtask --goal-id=X --description="..." --output json` | ❌ MISSING | P0 |
| `complete_subtask` | `empirica goals-complete-subtask --task-id=X --evidence="..." --output json` | ❌ MISSING | P0 |
| `get_goal_progress` | `empirica goals-progress --goal-id=X --output json` | ❌ MISSING | P0 |
| `list_goals` | `empirica goals-list --session-id=X --output json` | ❌ MISSING | P0 |
| `query_goal_orchestrator` | `empirica goals-query --session-id=X --output json` | ❌ MISSING | P1 |
| `generate_goals` | `empirica goals-generate --session-id=X --context="..." --output json` | ❌ MISSING | P1 |

#### **Monitoring/Analysis**

| MCP Tool | CLI Command | Status | Priority |
|----------|-------------|--------|----------|
| `query_bayesian_beliefs` | `empirica monitor --component=bayesian --session-id=X --output json` | ⚠️ EXISTS (remap) | P2 |
| `check_drift_monitor` | `empirica monitor --component=drift --session-id=X --output json` | ⚠️ EXISTS (remap) | P2 |

#### **Handoff Reports** (Phase 1.6)

| MCP Tool | CLI Command | Status | Priority |
|----------|-------------|--------|----------|
| `generate_handoff_report` | `empirica handoff-generate --session-id=X --output json` | ❌ MISSING | P1 |
| `query_handoff_reports` | `empirica handoff-query --ai-id=X --limit=N --output json` | ❌ MISSING | P1 |

#### **Token Efficiency** (Phase 1.5)

| MCP Tool | CLI Command | Status | Priority |
|----------|-------------|--------|----------|
| `measure_token_efficiency` | `empirica efficiency-report --session-id=X --output json` | ⚠️ EXISTS (remap) | P2 |
| `generate_efficiency_report` | `empirica efficiency-report --session-id=X --detailed --output json` | ⚠️ EXISTS (remap) | P2 |

#### **Multi-Agent Coordination**

| MCP Tool | CLI Command | Status | Priority |
|----------|-------------|--------|----------|
| `query_git_progress` | `empirica goals-git-query --goal-ids="..." --output json` | ❌ MISSING | P2 |
| `get_team_progress` | `empirica goals-team-progress --goal-ids="..." --output json` | ❌ MISSING | P2 |
| `get_unified_timeline` | `empirica timeline --session-id=X --output json` | ❌ MISSING | P2 |
| `create_cascade` | `empirica cascade-create --session-id=X --task="..." --output json` | ❌ MISSING | P2 |

#### **Modality Switcher** (Optional - Disabled by Default)

| MCP Tool | CLI Command | Status | Priority |
|----------|-------------|--------|----------|
| `query_ai` | `empirica query-ai --adapter=X --query="..." --output json` | ❌ MISSING | P3 |
| `modality_route_query` | (Same as query_ai) | ❌ MISSING | P3 |
| `modality_list_adapters` | `empirica modality-adapters --output json` | ❌ MISSING | P3 |
| `modality_adapter_health` | `empirica modality-health --adapter=X --output json` | ❌ MISSING | P3 |
| `modality_decision_assist` | `empirica modality-decide --query="..." --output json` | ❌ MISSING | P3 |

---

## 📊 Status Summary

| Status | Count | Tools |
|--------|-------|-------|
| ✅ EXISTS (ready) | 5 | bootstrap, checkpoint-create, sessions-show, sessions-export, sessions-list |
| ⚠️ PARTIAL (needs --output json) | 5 | preflight, postflight, calibration, checkpoint-load, checkpoint-diff |
| ❌ MISSING (needs CLI command) | 27 | All submit-* tools, goals-*, handoff-*, timeline, cascade |
| 📝 STATELESS (MCP only) | 3 | introduction, guidance, cli_help |

**Total:** 40 tools (37 MCP + 3 stateless)

---

## 🚀 Implementation Plan

### Phase 1: High-Priority CLI Commands (P0) - **Mini-agent Task**

**Create these 10 CLI commands with --output json:**

1. `empirica preflight-submit` - Submit PREFLIGHT assessment
2. `empirica check` - Execute CHECK phase
3. `empirica check-submit` - Submit CHECK assessment
4. `empirica postflight-submit` - Submit POSTFLIGHT assessment
5. `empirica goals-create` - Create new goal
6. `empirica goals-add-subtask` - Add subtask to goal
7. `empirica goals-complete-subtask` - Mark subtask complete
8. `empirica goals-progress` - Get goal progress
9. `empirica goals-list` - List goals
10. `empirica sessions-resume` - Resume previous session

**Estimated effort:** 4-6 hours (Mini-agent)

**Pattern for each command:**
```python
def handle_X_command(args):
    """Handle X command"""
    # 1. Parse arguments
    # 2. Call Python API
    # 3. Format output based on args.output

    if args.output == 'json':
        print(json.dumps(result, indent=2))
    else:
        # Human-readable format
        print(f"✅ {result}")
```

### Phase 2: Add --output json to Existing Commands - **Mini-agent Task**

**Modify these 5 commands to support --output json:**

1. `empirica preflight` (currently exists, add --output json)
2. `empirica postflight` (currently exists, add --output json)
3. `empirica calibration` (currently exists, add --output json)
4. `empirica checkpoint-load` (currently exists, add --output json)
5. `empirica checkpoint-diff` (currently exists, add --output json)

**Estimated effort:** 1-2 hours (Mini-agent)

**Pattern:**
```python
# Add to argparser
parser.add_argument('--output', choices=['text', 'json'], default='text')

# In handler
if args.output == 'json':
    print(json.dumps({...}, indent=2))
else:
    # Existing human-readable output
```

### Phase 3: Rewrite MCP Server - **Claude Code Task (Me)**

**Create new `empirica_mcp_server_v2.py` (~500 lines):**

```python
#!/usr/bin/env python3
"""
Empirica MCP Server v2 - Thin CLI Wrapper
Routes all stateful operations through CLI for reliability and simplicity
"""

import asyncio
import subprocess
import json
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("empirica")

# Empirica CLI path
EMPIRICA_CLI = "empirica"
EMPIRICA_ROOT = Path(__file__).parent.parent

# --- Tool Definitions ---

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List all available tools"""
    return [
        # Stateless tools (handled directly)
        types.Tool(
            name="get_empirica_introduction",
            description="Get comprehensive Empirica introduction",
            inputSchema={"type": "object", "properties": {}}
        ),
        # ... more tool definitions

        # Stateful tools (route to CLI)
        types.Tool(
            name="bootstrap_session",
            description="Bootstrap new Empirica session",
            inputSchema={
                "type": "object",
                "properties": {
                    "ai_id": {"type": "string"},
                    "session_type": {"type": "string"},
                    "bootstrap_level": {"type": "integer"}
                },
                "required": ["ai_id"]
            }
        ),
        # ... more tool definitions (one per CLI command)
    ]

# --- Tool Handlers ---

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Route tool calls to CLI or handle directly"""

    # Category 1: Stateless (handle directly)
    if name == "get_empirica_introduction":
        return handle_introduction()
    elif name == "get_workflow_guidance":
        return handle_guidance(arguments)
    elif name == "cli_help":
        return handle_help()

    # Category 2: Route to CLI
    else:
        return await route_to_cli(name, arguments)

# --- Helper Functions ---

async def route_to_cli(tool_name: str, arguments: dict) -> list[types.TextContent]:
    """Route MCP tool call to Empirica CLI"""

    # Map tool name to CLI command
    cmd = build_cli_command(tool_name, arguments)

    # Execute CLI command
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=EMPIRICA_ROOT
    )

    if result.returncode == 0:
        # CLI returned JSON (--output json)
        return [types.TextContent(type="text", text=result.stdout)]
    else:
        # CLI returned error
        return [types.TextContent(type="text", text=json.dumps({
            "ok": False,
            "error": result.stderr,
            "command": " ".join(cmd),
            "suggestion": "Check CLI command syntax with: empirica --help"
        }, indent=2))]

def build_cli_command(tool_name: str, arguments: dict) -> list[str]:
    """Build CLI command from MCP tool call"""

    # Tool name → CLI command mapping
    tool_map = {
        "bootstrap_session": ["bootstrap"],
        "execute_preflight": ["preflight"],
        "submit_preflight_assessment": ["preflight-submit"],
        "execute_check": ["check"],
        "submit_check_assessment": ["check-submit"],
        # ... etc
    }

    cmd = [EMPIRICA_CLI] + tool_map.get(tool_name, [tool_name])

    # Map arguments to CLI flags
    for key, value in arguments.items():
        if value is not None:
            if isinstance(value, bool):
                if value:
                    cmd.append(f"--{key.replace('_', '-')}")
            elif isinstance(value, dict) or isinstance(value, list):
                cmd.extend([f"--{key.replace('_', '-')}", json.dumps(value)])
            else:
                cmd.extend([f"--{key.replace('_', '-')}", str(value)])

    # Always request JSON output
    cmd.extend(["--output", "json"])

    return cmd

# --- Stateless Handlers ---

def handle_introduction() -> list[types.TextContent]:
    """Return Empirica introduction"""
    intro = """
# Empirica Framework
...
"""
    return [types.TextContent(type="text", text=intro)]

# ... more stateless handlers

# --- Server Main ---

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

**Estimated effort:** 4-6 hours (Me - holistic architecture)

### Phase 4: Testing - **Both**

**Test with diagnostic script:**
```bash
python3 debug_mcp_communication.py
```

**Expected results:**
- ✅ All 37 tools listed
- ✅ bootstrap_session works
- ✅ All workflow tools work
- ✅ All goal tools work
- ✅ No async errors

**Estimated effort:** 1-2 hours

---

## 🎯 Task Distribution

### Claude Code (Me) - Holistic Architecture
1. Design MCP server v2 architecture
2. Write MCP server v2 (~500 lines)
3. Create tool → CLI mapping logic
4. Handle stateless tools (introduction, guidance)
5. Test integration
6. Update documentation

**Estimated: 6-8 hours**

### Mini-agent - CLI Implementation Details
1. Create 10 new CLI commands (P0 priority)
2. Add --output json to 5 existing commands
3. Test each CLI command individually
4. Update CLI help text
5. Create CLI command tests

**Estimated: 6-8 hours**

---

## 📝 Next Steps

1. **Commit this mapping spec**
2. **Create Mini-agent goal** for CLI commands
3. **Start MCP server v2** architecture
4. **Parallel work** - I do MCP, Mini-agent does CLI
5. **Integration test** when both complete

Ready to proceed?
