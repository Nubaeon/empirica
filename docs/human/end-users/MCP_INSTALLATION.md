# Empirica MCP Server - Installation & Setup Guide

**Last Updated:** December 2025  
**MCP Spec Version:** 2025-11-25

---

## Why Use the Empirica CLI Instead?

**Before we dive into MCP setup**, consider using the Empirica CLI directly:

### CLI vs MCP Comparison

| Feature | Empirica CLI | Empirica MCP Server |
|---------|-------------|---------------------|
| **Setup** | `pip install empirica` | Install package + configure client |
| **Usage** | Direct commands | Via MCP client wrapper |
| **AI-First JSON** | ✅ Native stdin support | ⚠️ Depends on client |
| **Performance** | 🚀 Direct execution | 🐌 Client → MCP → CLI |
| **Debugging** | ✅ Direct output | ⚠️ Client-dependent |
| **Portability** | ✅ Works everywhere | ⚠️ Client-specific |

**Empirica CLI Example:**
```bash
# Direct, fast, works everywhere
echo '{"ai_id": "myai"}' | empirica session-create -
```

**MCP Server Example:**
```
You: "Create session with ID myai"
AI: *calls MCP server* → *MCP calls CLI* → *returns result*
```

**Recommendation:** Use CLI directly unless you specifically need MCP integration (e.g., Claude Desktop workflow).

---

## When to Use MCP

Use Empirica MCP server if:
- ✅ You're using Claude Desktop and want GUI integration
- ✅ Your IDE/editor only supports MCP (not direct CLI)
- ✅ You want context sharing across tools in same environment
- ❌ For most AI coding workflows → **Use CLI directly**

---

## Installation

### Option 1: PyPI Package (Recommended)

```bash
# Core Empirica
pip install empirica

# MCP Server
pip install empirica-mcp
```

### Option 2: Docker Container

```bash
docker pull empirica/mcp:latest
docker run -p 3000:3000 empirica/mcp
```

---

## Client Setup

### 1. Claude Desktop (Official, Anthropic)

**Platform:** macOS, Windows  
**MCP Support:** ✅ Native, Stable  
**Best For:** Claude API users, GUI workflow

**Setup:**

```bash
# macOS
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Windows
notepad %APPDATA%\Claude\claude_desktop_config.json
```

**Configuration:**
```json
{
  "mcpServers": {
    "empirica": {
      "command": "empirica-mcp"
    }
  }
}
```

**Restart Claude Desktop**, then test:
```
You: "Use empirica to create a session"
Claude: *uses MCP server automatically*
```

---

### 2. Cline (VSCode Extension)

**Platform:** VSCode  
**MCP Support:** ✅ Stable (as of Dec 2025)  
**Best For:** VSCode AI coding workflows

**Setup:**

1. Install Cline extension from VSCode marketplace
2. Open VSCode Settings → Extensions → Cline
3. Find "MCP Servers" section
4. Add server configuration:

```json
{
  "mcpServers": {
    "empirica": {
      "command": "empirica-mcp",
      "env": {
        "EMPIRICA_DATA_DIR": "${workspaceFolder}/.empirica"
      }
    }
  }
}
```

**Usage:**
```
Cline: "I need to track epistemic state"
You: "@empirica create session"
```

**Documentation:** https://docs.cline.bot/mcp/mcp-overview

---

### 3. Roo-Cline (VSCode Fork)

**Platform:** VSCode  
**MCP Support:** ✅ Enhanced (multiple servers)  
**Best For:** Advanced VSCode workflows

**Setup:**

Same as Cline, but with enhanced features:

```json
{
  "mcpServers": {
    "empirica": {
      "command": "empirica-mcp",
      "args": ["--workspace", "${workspaceFolder}"],
      "autoStart": true
    }
  }
}
```

**Documentation:** https://docs.roocode.com/features/mcp/using-mcp-in-roo

---

### 4. VSCode Native (GitHub Copilot)

**Platform:** VSCode  
**MCP Support:** ✅ Built-in (2025)  
**Best For:** GitHub Copilot users

**Setup:**

1. VSCode 1.95+ with GitHub Copilot
2. Settings → GitHub Copilot → MCP Servers
3. Add configuration:

```json
{
  "github.copilot.mcpServers": {
    "empirica": {
      "command": "empirica-mcp"
    }
  }
}
```

**Documentation:** https://code.visualstudio.com/docs/copilot/customization/mcp-servers

---

### 5. Continue.dev (VSCode/JetBrains)

**Platform:** VSCode, JetBrains IDEs  
**MCP Support:** ⚠️ Beta (Dec 2025)  
**Best For:** Local AI models (Ollama, LM Studio)

**Setup:**

Edit `~/.continue/config.json`:

```json
{
  "mcpServers": [
    {
      "name": "empirica",
      "command": "empirica-mcp"
    }
  ]
}
```

**Note:** MCP support still stabilizing. Consider using CLI directly with Continue.dev.

---

### 6. Cursor IDE

**Platform:** Standalone IDE  
**MCP Support:** ⚠️ Coming Soon (Q1 2025)  
**Best For:** Cursor-specific workflows

**Setup:** Not yet available. Use Empirica CLI directly:

```bash
# In Cursor terminal
empirica session-create --ai-id cursor-ai
```

---

### 7. Local AI + MCP Bridges

**For:** Ollama, LM Studio, local models  
**MCP Support:** Via third-party bridges

**Ollama + MCP:**
```bash
# Install MCP bridge
npm install -g @modelcontextprotocol/server-ollama

# Configure to call empirica-mcp
# (Setup varies by bridge)
```

**Better Approach:** Use Empirica CLI directly with your local AI's API:

```python
# Python script for local AI
import subprocess
import json

def call_empirica(command):
    result = subprocess.run(
        ["empirica"] + command,
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

# Your AI calls this directly
```

---

## Testing Your Setup

Once configured, test with:

```
# Via MCP client
You: "Create an empirica session with ID test-ai"

# Expected: AI calls empirica-mcp → returns session info
```

**Debugging:**

```bash
# Test MCP server directly
empirica-mcp

# Should output MCP protocol messages
# Press Ctrl+C to stop

# Test CLI directly (comparison)
empirica session-create --ai-id test --output json
```

---

## Available MCP Tools

The Empirica MCP server exposes **all CLI commands** as MCP tools:

### Core Workflow
- `session_create` - Create new session
- `preflight_submit` - PREFLIGHT assessment
- `check` - CHECK gate
- `postflight_submit` - POSTFLIGHT assessment

### Goals & Tasks
- `goals_create` - Create goals
- `goals_add_subtask` - Add subtasks
- `goals_complete_subtask` - Mark complete
- `goals_list` - List goals

### Findings & Learning
- `finding_log` - Log findings
- `unknown_log` - Log unknowns
- `deadend_log` - Log dead ends
- `mistake_log` - Log mistakes

### Project & Session
- `project_bootstrap` - Load project context
- `session_snapshot` - Get session state
- `session_list` - List sessions

**Total:** 60+ MCP tools available

---

## MCP vs CLI: Performance

**Benchmark (Session Creation):**

| Method | Latency | Steps |
|--------|---------|-------|
| **CLI Direct** | 50ms | 1 step |
| **MCP Server** | 150-300ms | 3 steps (client → MCP → CLI) |

**Recommendation:** For performance-critical workflows, use CLI directly.

---

## Troubleshooting

### MCP Server Not Found

```bash
# Verify installation
which empirica-mcp

# If not found, reinstall
pip install --force-reinstall empirica-mcp
```

### Permission Denied

```bash
# macOS/Linux: Make executable
chmod +x $(which empirica-mcp)

# Windows: Run as administrator
```

### Client Can't Connect

```bash
# Check MCP server runs standalone
empirica-mcp
# Should show MCP protocol messages

# Check client logs
# Claude Desktop: ~/Library/Logs/Claude/
# Cline: VSCode Output → Cline
```

### Wrong Session/Project

MCP server uses:
- **Project:** Auto-detected from git remote
- **Session:** Creates new each time
- **Data:** `.empirica/` in workspace directory

**To use specific session:**
```json
{
  "command": "empirica-mcp",
  "env": {
    "EMPIRICA_SESSION_ID": "your-session-id"
  }
}
```

---

## Advanced: Custom MCP Configuration

### Per-Project Configuration

**VSCode (.vscode/settings.json):**
```json
{
  "mcpServers": {
    "empirica": {
      "command": "empirica-mcp",
      "env": {
        "EMPIRICA_DATA_DIR": "${workspaceFolder}/.empirica",
        "EMPIRICA_SESSION_DB": "${workspaceFolder}/.empirica/sessions/sessions.db"
      }
    }
  }
}
```

### Multiple Profiles

```json
{
  "mcpServers": {
    "empirica-dev": {
      "command": "empirica-mcp",
      "env": {"EMPIRICA_PROFILE": "development"}
    },
    "empirica-prod": {
      "command": "empirica-mcp",
      "env": {"EMPIRICA_PROFILE": "production"}
    }
  }
}
```

---

## Docker Deployment

**For team/shared MCP server:**

```bash
# Run as service
docker run -d \
  --name empirica-mcp \
  -p 3000:3000 \
  -v $(pwd)/.empirica:/root/.empirica \
  empirica/mcp:latest

# Client connects to http://localhost:3000
```

**Client Configuration:**
```json
{
  "mcpServers": {
    "empirica": {
      "url": "http://localhost:3000"
    }
  }
}
```

---

## When CLI is Better

**Use Empirica CLI directly when:**

✅ Writing scripts/automation  
✅ CI/CD pipelines  
✅ Performance matters  
✅ Debugging issues  
✅ Working in terminal  
✅ AI agent has direct shell access  

**CLI Example (AI agent script):**
```bash
#!/bin/bash
SESSION=$(echo '{"ai_id":"agent"}' | empirica session-create - | jq -r '.session_id')
echo "Session: $SESSION"

# PREFLIGHT
cat preflight.json | empirica preflight-submit -

# Work...

# POSTFLIGHT
cat postflight.json | empirica postflight-submit -
```

**This is faster, simpler, and more reliable than MCP!**

---

## Further Reading

- [Empirica CLI Reference](../reference/CLI_COMMANDS_COMPLETE.md)
- [CASCADE Workflow](CASCADE_WORKFLOW.md)
- [First-Time Setup](FIRST_TIME_SETUP.md)
- [MCP Specification](https://modelcontextprotocol.io/specification/2025-11-25)

---

**Honest recommendation:** Unless you're specifically using Claude Desktop or an IDE that requires MCP, **use the Empirica CLI directly**. It's faster, simpler, and more powerful. MCP is great for GUI integration, but the CLI is built for AI agents. 🚀

---

## Additional IDE Support

### 8. Antigravity (Google)

**Platform:** VSCode (Google's web-focused fork)  
**MCP Support:** ✅ Stable  
**Best For:** Web development, Google Cloud workflows

**Setup:**

Antigravity uses standard VSCode MCP configuration:

```json
{
  "mcpServers": {
    "empirica": {
      "command": "empirica-mcp",
      "env": {
        "EMPIRICA_DATA_DIR": "${workspaceFolder}/.empirica"
      }
    }
  }
}
```

**Documentation:** https://cloud.google.com/code/docs/vscode/mcp

---

### 9. Cursor IDE (Updated)

**Platform:** Standalone IDE  
**MCP Support:** ⚠️ Limited (December 2025)  
**Best For:** Cursor-specific AI workflows

**Status Update:** Cursor has experimental MCP support. Configuration:

```json
{
  "mcp": {
    "servers": {
      "empirica": {
        "command": "empirica-mcp"
      }
    }
  }
}
```

**Note:** MCP support still maturing. For production, use Empirica CLI directly:

```bash
# In Cursor terminal
empirica session-create --ai-id cursor-ai --output json
```

---

### 10. Windsurf IDE

**Platform:** Standalone IDE (Codeium)  
**MCP Support:** ✅ Stable  
**Best For:** Codeium AI workflows

**Setup:**

Windsurf Settings → AI → MCP Servers:

```json
{
  "mcpServers": {
    "empirica": {
      "command": "empirica-mcp",
      "autoStart": true
    }
  }
}
```

**Documentation:** https://codeium.com/windsurf/docs/mcp

---

## Summary: Which IDE for What?

| IDE/Tool | MCP Support | Best Use Case | Recommendation |
|----------|-------------|---------------|----------------|
| **Claude Desktop** | ✅ Native | Claude API users | Use MCP |
| **Cline (VSCode)** | ✅ Stable | AI coding in VSCode | Use MCP |
| **Roo-Cline** | ✅ Enhanced | Advanced VSCode | Use MCP |
| **Antigravity** | ✅ Stable | Google Cloud dev | Use MCP |
| **Windsurf** | ✅ Stable | Codeium workflows | Use MCP |
| **Cursor** | ⚠️ Limited | Cursor AI | **Use CLI** |
| **Continue.dev** | ⚠️ Beta | Local AI models | **Use CLI** |
| **Terminal (Aider, etc.)** | N/A | Terminal workflows | **Use CLI** |

**Rule of thumb:**
- **GUI IDE with stable MCP** → Use MCP server
- **Terminal or unstable MCP** → Use CLI directly

