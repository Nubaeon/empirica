# MCP Configuration - Package-Based Setup (v1.0.2+)

**Updated:** 2025-12-18
**Replaces:** Local file-based MCP server configuration

## Overview

Starting with v1.0.2, the Empirica MCP server is distributed as a **standalone Python package** (`empirica-mcp`) that works across all repositories and installations.

**Note:** The CLI is the primary interface for epistemic assessments. MCP tools provide GUI/IDE integration that maps directly to CLI commands.

### ✅ What Changed

| Old (v1.0.1) | New (v1.0.2+) |
|--------------|---------------|
| Points to local file: `mcp_local/empirica_mcp_server.py` | Uses installed command: `empirica-mcp` |
| Hardcoded paths: `.venv-mcp/bin/empirica` | Uses PATH: `shutil.which("empirica")` |
| Only works in empirica repo | Works in ANY repository |
| Requires `cwd` to empirica repo | Works from current directory |

### 🐛 Bug Fixed

**Problem:** Old MCP server hardcoded paths like:
```python
EMPIRICA_CLI = str(EMPIRICA_ROOT / ".venv-mcp" / "bin" / "empirica")
```

This broke:
- PyPI installations
- Other repos (like Antigravity)
- Docker containers
- System-wide installs

**Solution:** New server uses `shutil.which("empirica")` to find empirica from PATH, with fallback locations.

---

## Installation

### Step 1: Install Packages

```bash
# Install core empirica (without MCP server)
pip install empirica

# Install MCP server (includes empirica as dependency)
pip install empirica-mcp
```

### Step 2: Verify Installation

```bash
# Check empirica CLI is in PATH
which empirica
# Should output: /path/to/bin/empirica

# Check empirica-mcp server is in PATH
which empirica-mcp
# Should output: /path/to/bin/empirica-mcp

# Test MCP server
empirica-mcp --help
```

---

## Configuration

### Claude Desktop

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

**New Configuration (v1.0.2+):**
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

**Key Points:**
- ✅ Uses `empirica-mcp` command (installed via pip)
- ✅ No `args` needed (server is self-contained)
- ✅ No `cwd` needed (works from current directory)
- ✅ No `env` needed (finds empirica from PATH)
- ✅ Works in ANY project directory

### Other Projects (e.g., Antigravity)

**Same configuration works everywhere:**

```json
{
  "mcpServers": {
    "empirica": {
      "command": "empirica-mcp",
      "description": "Empirica for Antigravity web development"
    }
  }
}
```

**The MCP server will:**
1. Find `empirica` CLI from PATH automatically
2. Use the current working directory (where `.empirica/` database exists)
3. Work seamlessly across all projects

---

## Migration Guide

### From Local File-Based Setup

**Old Configuration (DO NOT USE):**
```json
{
  "mcpServers": {
    "empirica": {
      "command": "python3",
      "args": ["mcp_local/empirica_mcp_server.py"],
      "cwd": "/home/yogapad/empirical-ai/empirica",
      "env": {
        "PYTHONPATH": "/home/yogapad/empirical-ai/empirica",
        "VIRTUAL_ENV": "/home/yogapad/empirical-ai/empirica/.venv-empirica"
      }
    }
  }
}
```

**New Configuration:**
```json
{
  "mcpServers": {
    "empirica": {
      "command": "empirica-mcp"
    }
  }
}
```

**Migration Steps:**
1. Install empirica-mcp: `pip install empirica-mcp`
2. Update Claude Desktop config to use `"command": "empirica-mcp"`
3. Remove `args`, `cwd`, `env` fields
4. Restart Claude Desktop

---

## Troubleshooting

### Issue: "empirica CLI not found in PATH"

**Cause:** The `empirica` package is not installed or not in PATH.

**Solution:**
```bash
# Install empirica
pip install empirica

# Verify it's in PATH
which empirica

# If not in PATH, add pip install location to PATH:
export PATH="$HOME/.local/bin:$PATH"  # Linux/macOS
```

### Issue: "empirica-mcp command not found"

**Cause:** The `empirica-mcp` package is not installed.

**Solution:**
```bash
pip install empirica-mcp
which empirica-mcp
```

### Issue: MCP server can't find .empirica/ database

**Cause:** The MCP server runs from the wrong directory.

**Solution:** The server uses the current working directory. Make sure Claude Desktop is launched from the project root where `.empirica/` exists, or:

```bash
# Create .empirica/ database in your project
cd /path/to/your/project
empirica session-create --ai-id your-agent
```

### Issue: Works in empirica repo but not in Antigravity

**Cause:** Using old local file-based configuration.

**Solution:** Update to package-based configuration (see Migration Guide above).

---

## Development Setup

### Using Local Development Version

If you're developing empirica-mcp itself:

```json
{
  "mcpServers": {
    "empirica-dev": {
      "command": "python3",
      "args": ["-m", "empirica_mcp.server"],
      "cwd": "/path/to/empirica",
      "env": {
        "PYTHONPATH": "/path/to/empirica"
      }
    }
  }
}
```

**For production use, always prefer the installed package.**

---

## Architecture Notes

### How empirica-mcp Works

1. **Installed as Python package:**
   ```bash
   pip install empirica-mcp
   ```

2. **Creates CLI command:**
   - Entry point: `empirica_mcp.server:main`
   - Installed as: `empirica-mcp` command

3. **Finds empirica CLI dynamically:**
   ```python
   EMPIRICA_CLI = shutil.which("empirica")  # Use PATH
   ```

4. **Routes MCP calls to empirica CLI:**
   ```python
   subprocess.run([EMPIRICA_CLI, "session-create", "--ai-id", "agent"])
   ```

### Benefits

- ✅ **Portable:** Works in any environment
- ✅ **No hardcoded paths:** Uses PATH resolution
- ✅ **Cross-repo:** Use in any project (Empirica, Antigravity, etc.)
- ✅ **Standard packaging:** Distributed via PyPI
- ✅ **Easy updates:** `pip install --upgrade empirica-mcp`

---

## Deprecated: mcp_local/

**The `mcp_local/` directory is deprecated and will be removed in v2.0.0.**

**Reasons:**
- Hardcoded paths break portability
- Requires specific directory structure
- Doesn't work across repositories
- Not distributed via PyPI

**Use the `empirica-mcp` package instead.**

---

## Summary

✅ **Install:** `pip install empirica-mcp`
✅ **Configure:** `{"command": "empirica-mcp"}`
✅ **Works everywhere:** Any project, any installation
✅ **No hardcoded paths:** Uses PATH automatically
✅ **Easy updates:** `pip install --upgrade empirica-mcp`

For issues, see: https://github.com/Nubaeon/empirica/issues
