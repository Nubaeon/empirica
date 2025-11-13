# MCP Configuration Examples

**Date:** 2025-11-07  
**Purpose:** IDE/CLI integration configurations for Empirica MCP server  
**Status:** Ready for use

---

## Overview

Empirica provides an MCP (Model Context Protocol) server that exposes 19 tools for epistemic workflow management. This guide shows how to configure various AI assistants and IDEs to use the Empirica MCP server.

---

## Quick Start

### 1. Ensure Empirica is Installed

```bash
cd /path/to/empirica
pip install -e .
```

### 2. Test MCP Server

```bash
# Start server (optional - most IDEs start it automatically)
python3 -m empirica.cli mcp-start

# Check status
python3 -m empirica.cli mcp-status

# List available tools
python3 -m empirica.cli mcp-list-tools
```

### 3. Configure Your IDE

Choose your IDE/tool below and add the configuration.

---

## Configuration Examples

### 1. Rovo Dev (Claude Code MCP)

**File:** `~/.config/rovo-dev/mcp.json` or project-level `mcp_config_rovodev.json`

```json
{
  "mcpServers": {
    "empirica": {
      "command": "python3",
      "args": [
        "/path/to/empirica/mcp_local/empirica_mcp_server.py"
      ],
      "description": "Empirica epistemic workflow and self-assessment framework",
      "env": {
        "PYTHONPATH": "/path/to/empirica",
        "EMPIRICA_ENABLE_MODALITY_SWITCHER": "false"
      },
      "capabilities": [
        "preflight_assessment",
        "postflight_assessment",
        "epistemic_tracking",
        "calibration_validation",
        "session_continuity"
      ]
    }
  }
}
```

**Usage in Rovo Dev:**

The AI can now use Empirica tools:

```
User: "Review the authentication module"

AI: Let me start with a preflight assessment...
    [calls execute_preflight tool]
    
    Based on the assessment:
    - KNOW: 0.6 (moderate domain knowledge)
    - DO: 0.7 (good capability)
    - CONTEXT: 0.5 (adequate information)
    
    I'll proceed with the review...
    
    [performs review]
    
    Now let me do a postflight assessment...
    [calls execute_postflight tool]
    
    Learning analysis:
    - KNOW increased from 0.6 to 0.8 (+0.2)
    - Well calibrated ✓
```

---

### 2. Cursor IDE

**File:** `~/.cursor/mcp.json` or workspace `.cursor/mcp_config.json`

```json
{
  "mcpServers": {
    "empirica": {
      "command": "python3",
      "args": [
        "-m",
        "mcp_local.empirica_mcp_server"
      ],
      "cwd": "/path/to/empirica",
      "env": {
        "PYTHONPATH": "/path/to/empirica"
      },
      "description": "Empirica epistemic self-awareness framework"
    }
  }
}
```

---

### 3. Windsurf IDE

**File:** Windsurf settings > MCP Servers

```json
{
  "empirica": {
    "command": "/usr/bin/python3",
    "args": [
      "/path/to/empirica/mcp_local/empirica_mcp_server.py"
    ],
    "description": "Epistemic workflow management"
  }
}
```

---

### 4. Continue.dev (VS Code Extension)

**File:** `~/.continue/config.json`

```json
{
  "mcpServers": [
    {
      "name": "empirica",
      "command": "python3",
      "args": [
        "/path/to/empirica/mcp_local/empirica_mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/empirica"
      }
    }
  ]
}
```

---

### 5. Claude Desktop App

**File:** `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac)  
**File:** `%APPDATA%\Claude\claude_desktop_config.json` (Windows)  
**File:** `~/.config/Claude/claude_desktop_config.json` (Linux)

```json
{
  "mcpServers": {
    "empirica": {
      "command": "python3",
      "args": [
        "/path/to/empirica/mcp_local/empirica_mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/empirica"
      }
    }
  }
}
```

---

### 6. Zed Editor

**File:** `~/.config/zed/settings.json`

```json
{
  "mcp": {
    "servers": {
      "empirica": {
        "command": "python3",
        "args": [
          "/path/to/empirica/mcp_local/empirica_mcp_server.py"
        ],
        "env": {
          "PYTHONPATH": "/path/to/empirica"
        }
      }
    }
  }
}
```

---

### 7. Generic MCP Client (Python)

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def use_empirica():
    server_params = StdioServerParameters(
        command="python3",
        args=["/path/to/empirica/mcp_local/empirica_mcp_server.py"],
        env={"PYTHONPATH": "/path/to/empirica"}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {len(tools.tools)}")
            
            # Call execute_preflight
            result = await session.call_tool(
                "execute_preflight",
                arguments={
                    "session_id": "test123",
                    "prompt": "Review authentication code"
                }
            )
            print(result)

asyncio.run(use_empirica())
```

---

### 8. Generic MCP Client (TypeScript/JavaScript)

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const transport = new StdioClientTransport({
  command: "python3",
  args: ["/path/to/empirica/mcp_local/empirica_mcp_server.py"],
  env: {
    PYTHONPATH: "/path/to/empirica"
  }
});

const client = new Client({
  name: "empirica-client",
  version: "1.0.0"
}, {
  capabilities: {}
});

await client.connect(transport);

// List tools
const tools = await client.listTools();
console.log(`Available tools: ${tools.tools.length}`);

// Call preflight
const result = await client.callTool({
  name: "execute_preflight",
  arguments: {
    session_id: "test123",
    prompt: "Review authentication code"
  }
});

console.log(result);
```

---

## Configuration Options

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

**Available Variables:**

- `PYTHONPATH` - Required: Path to Empirica installation
- `EMPIRICA_ENABLE_MODALITY_SWITCHER` - Optional: Enable multi-AI routing (default: false)
- `EMPIRICA_LOG_LEVEL` - Optional: Logging level (DEBUG, INFO, WARNING, ERROR)

---

## Available MCP Tools

### Core Workflow (5 tools)

1. **`execute_preflight`** - Preflight epistemic assessment
2. **`submit_preflight_assessment`** - Submit preflight scores
3. **`execute_check`** - Mid-task decision point validation
4. **`execute_postflight`** - Postflight reassessment
5. **`submit_postflight_assessment`** - Submit postflight with calibration

### Session Management (5 tools)

6. **`bootstrap_session`** - Initialize new session
7. **`resume_previous_session`** - Load previous session context
8. **`get_epistemic_state`** - Query current vectors
9. **`get_session_summary`** - Full session history
10. **`get_calibration_report`** - Calibration accuracy stats

### Monitoring (3 tools)

11. **`query_bayesian_beliefs`** - Belief tracking
12. **`check_drift_monitor`** - Behavioral integrity check
13. **`query_goal_orchestrator`** - Task hierarchy

### Guidance (2 tools)

14. **`get_workflow_guidance`** - Workflow step guidance
15. **`cli_help`** - CLI command help

### Optional: Modality Switcher (4 tools) 🔀

16. **`modality_route_query`** - Route to specialist AI
17. **`modality_list_adapters`** - List available AIs
18. **`modality_adapter_health`** - Health check
19. **`modality_decision_assist`** - Routing recommendation

*Note: Modality switcher tools are disabled by default. Enable with `EMPIRICA_ENABLE_MODALITY_SWITCHER=true`*

---

## Example Workflows

### Workflow 1: Basic Preflight→Work→Postflight

```javascript
// AI assistant internal workflow
async function aiTaskWithEpistemicTracking(task) {
  // 1. Preflight
  const sessionId = generateSessionId();
  const preflight = await mcp.callTool("execute_preflight", {
    session_id: sessionId,
    prompt: task
  });
  
  // Parse self-assessment prompt and respond
  const vectors = await selfAssess(preflight.self_assessment_prompt);
  
  await mcp.callTool("submit_preflight_assessment", {
    session_id: sessionId,
    vectors: vectors,
    reasoning: "My assessment reasoning..."
  });
  
  // 2. Work
  const result = await performTask(task);
  
  // 3. Postflight
  const postflight = await mcp.callTool("execute_postflight", {
    session_id: sessionId,
    task_summary: `Completed: ${task}`
  });
  
  const postVectors = await selfAssess(postflight.self_assessment_prompt);
  
  const calibration = await mcp.callTool("submit_postflight_assessment", {
    session_id: sessionId,
    vectors: postVectors,
    changes_noticed: "Increased understanding of..."
  });
  
  return {
    result,
    learning: calibration.epistemic_delta,
    calibrated: calibration.calibration.well_calibrated
  };
}
```

### Workflow 2: Session Continuity

```javascript
async function resumeWork() {
  // Load previous session
  const summary = await mcp.callTool("resume_previous_session", {
    ai_id: "claude",
    resume_mode: "last",
    detail_level: "detailed"
  });
  
  console.log("Previous session summary:");
  console.log(summary.accomplishments);
  console.log(`Learning: ${summary.epistemic_trajectory}`);
  
  // Continue with new task using context
  return await aiTaskWithEpistemicTracking(summary.next_steps[0]);
}
```

---

## Testing Your Configuration

### 1. Test MCP Server Directly

```bash
# Start server manually
python3 /path/to/empirica/mcp_local/empirica_mcp_server.py

# Or use CLI
python3 -m empirica.cli mcp-start
python3 -m empirica.cli mcp-status
python3 -m empirica.cli mcp-list-tools
```

### 2. Test from IDE

In your IDE's AI assistant:

```
User: "Can you list the available MCP tools?"

AI should respond with Empirica tools if configured correctly.
```

### 3. Test Workflow

```
User: "Use Empirica to assess your epistemic state before reviewing auth.py"

AI: [calls execute_preflight]
    Preflight assessment shows:
    - KNOW: 0.6
    - DO: 0.7
    - CONTEXT: 0.5
    
    I'll proceed with the review...
```

---

## Troubleshooting

### Server Won't Start

```bash
# Check Python path
which python3

# Check Empirica installation
python3 -c "import empirica; print(empirica.__file__)"

# Check MCP server directly
python3 /path/to/empirica/mcp_local/empirica_mcp_server.py --help
```

### Tools Not Appearing

1. Check IDE logs for MCP errors
2. Verify `PYTHONPATH` is correct
3. Ensure Empirica is installed: `pip list | grep empirica`
4. Test server manually: `python3 -m empirica.cli mcp-test`

### Tools Fail to Execute

1. Check session database exists: `ls .empirica/sessions/sessions.db`
2. Check permissions on `.empirica/` directory
3. Enable debug logging: `EMPIRICA_LOG_LEVEL=DEBUG`

---

## Production Considerations

### 1. Use Virtual Environment

```json
{
  "command": "/path/to/venv/bin/python3",
  "args": ["/path/to/empirica/mcp_local/empirica_mcp_server.py"]
}
```

### 2. Set Working Directory

```json
{
  "command": "python3",
  "args": ["mcp_local/empirica_mcp_server.py"],
  "cwd": "/path/to/empirica"
}
```

### 3. Enable Logging

```json
{
  "env": {
    "EMPIRICA_LOG_LEVEL": "INFO",
    "EMPIRICA_LOG_FILE": "/path/to/logs/empirica-mcp.log"
  }
}
```

---

## Summary

**Configurations Provided:**
- ✅ Rovo Dev (Claude Code MCP)
- ✅ Cursor IDE
- ✅ Windsurf IDE
- ✅ Continue.dev (VS Code)
- ✅ Claude Desktop App
- ✅ Zed Editor
- ✅ Generic Python MCP Client
- ✅ Generic TypeScript/JavaScript MCP Client

**Tools Available:** 19 (15 core + 4 optional modality switcher)

**Ready to Use:** Copy configuration, update paths, restart IDE

---

**See Also:**
- `docs/guides/setup/MCP_SERVERS_SETUP.md` - Detailed MCP setup guide
- `docs/guides/CLI_WORKFLOW_COMMANDS_COMPLETE.md` - CLI workflow commands
- `docs/guides/MCP_CLI_INTEGRATION_COMPLETE.md` - MCP+CLI integration

**Next:** Try the configuration in your IDE and test with a simple workflow!
