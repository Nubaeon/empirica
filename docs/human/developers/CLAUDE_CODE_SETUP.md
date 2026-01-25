# Claude Code + Empirica Setup Guide

**Time:** 5 minutes | **Cross-platform** | **Automated or manual**

This guide sets up Empirica for Claude Code users on Linux, macOS, or Windows.

---

## What You're Installing

| Component | Purpose | Location |
|-----------|---------|----------|
| `empirica` | CLI + Python library | pip package |
| `empirica-mcp` | MCP server for Claude Code | pip package |
| Claude Code plugin | Noetic firewall + CASCADE workflow | `~/.claude/plugins/local/` |
| System prompt | Teaches Claude how to use Empirica | `~/.claude/CLAUDE.md` |
| Statusline | Real-time epistemic status display | Plugin scripts/ |
| MCP config | MCP server configuration | `~/.claude/mcp.json` |

The plugin (v1.4.2) now bundles everything in one package:
- **Sentinel gate** - Noetic firewall that gates praxic tools until CHECK passes
- **Session hooks** - Auto-creates sessions, bootstraps projects, captures POSTFLIGHT
- **Statusline script** - Shows epistemic state in terminal
- **Templates** - CLAUDE.md, mcp.json, settings snippets

---

## Quick Install (Recommended)

Run the interactive installer from the Empirica repository:

```bash
# Clone or navigate to Empirica repo
git clone https://github.com/Nubaeon/empirica.git
cd empirica

# Run installer
python scripts/install.py
```

The installer will:
- Install the Empirica package if needed
- Ask about autopilot, auto-postflight, sentinel looping preferences
- Configure Qdrant URL (for semantic search)
- Set up Ollama embeddings (recommends `nomic-embed-text`)
- Install the Claude Code plugin and skill
- Update your shell profile with environment variables

**Non-interactive mode** (use defaults):
```bash
python scripts/install.py --non-interactive
```

---

## Manual Installation

If you prefer manual setup or the installer doesn't work:

### Step 1: Install Package

```bash
pip install empirica

pip install empirica-mcp
```

Verify:
```bash
empirica --version
# Should show: 1.4.0 (or later)
```

---

## Step 2: Add System Prompt

The full system prompt teaches Claude how to use Empirica with calibration data, memory commands, and workflow guidance.

**Option A: Copy from plugin (recommended after Step 4):**
```bash
cp ~/.claude/plugins/local/empirica-integration/templates/CLAUDE.md ~/.claude/CLAUDE.md
```

**Option B: Copy from source:**
```bash
# If you have the Empirica repo cloned
cp /path/to/empirica/docs/human/developers/system-prompts/CLAUDE.md ~/.claude/CLAUDE.md
```

**Option C: Manual copy:**

The authoritative system prompt is maintained at:
- **Repo:** `docs/human/developers/system-prompts/CLAUDE.md`
- **Plugin:** `templates/CLAUDE.md` (synced copy)

Copy the full contents of that file to `~/.claude/CLAUDE.md`.

**What the system prompt includes:**
- Calibration data (253 trajectories, bias corrections per vector)
- CASCADE workflow (PREFLIGHT → CHECK → POSTFLIGHT)
- Core commands with correct flags
- Memory commands (Qdrant integration)
- Cognitive immune system (lessons decay)
- Proactive behaviors (pattern recognition, goal hygiene)
- Epistemic-first task structure

**Quick reference (subset):**
```bash
# Session lifecycle
empirica session-create --ai-id claude-code --output json
empirica project-bootstrap --session-id <ID> --output json

# CASCADE phases
empirica preflight-submit -     # Baseline (JSON stdin)
empirica check-submit -         # Gate (JSON stdin)
empirica postflight-submit -    # Learning delta (JSON stdin)

# Breadcrumbs
empirica finding-log --finding "..." --impact 0.7
empirica unknown-log --unknown "..."
empirica deadend-log --approach "..." --why-failed "..."
```

**Readiness gate:** know >= 0.70 AND uncertainty <= 0.35 (after bias correction)

---

## Step 3: Add Statusline (Recommended)

The statusline shows real-time epistemic status in your Claude Code terminal.

Add to `~/.claude/settings.json` (after installing the plugin in Step 4):
```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 ~/.claude/plugins/local/empirica-integration/scripts/statusline_empirica.py",
    "refresh_ms": 5000
  }
}
```

Or use the template from the plugin:
```bash
cat ~/.claude/plugins/local/empirica-integration/templates/settings-statusline.json
# Merge this into your settings.json
```

**Display modes** (set via `EMPIRICA_STATUS_MODE` env var):
- `basic`: Just confidence + phase
- `default`: Full status with vectors (recommended)
- `learning`: Focus on vector changes
- `full`: Everything with raw values

**Status indicators:**
- `⚡84%` = confidence score (⚡ high, 💡 good, 💫 uncertain, 🌑 low)
- `🎯3 ❓12/5` = open goals (3) and unknowns (12 total, 5 blocking goals)
- `PREFLIGHT/CHECK/POSTFLIGHT` = CASCADE workflow phase
- `K:90% U:15% C:90%` = know/uncertainty/context vectors
- `Δ K:+0.25 U:-0.15 ✓:+0.80` = learning deltas (K=know, U=uncertainty, ✓=completion)
- `✓ stable` / `⚠ drifting` / `✗ severe` = drift status

---

## Step 4: Install Empirica Plugin (Recommended)

The plugin (v1.4.2) enforces the CASCADE workflow and preserves epistemic state automatically.

**What it includes:**
- **Noetic firewall** (`sentinel-gate.py`): Gates praxic tools (Edit/Write/Bash) until CHECK passes
- **Session hooks** (`session-init.py`, `post-compact.py`): Auto-creates session, bootstraps projects, detects git repos
- **POSTFLIGHT capture** (`session-end-postflight.py`): Auto-captures learning at session end
- **Templates**: CLAUDE.md, mcp.json, statusline config - ready to copy
- **Statusline script**: Real-time epistemic state display

### Option A: Full Plugin (Recommended)

1. **Copy plugin to Claude plugins directory:**
```bash
# Create plugin directory
mkdir -p ~/.claude/plugins/local

# From Empirica source (if cloned)
cp -r /path/to/empirica/plugins/claude-code-integration ~/.claude/plugins/local/empirica-integration

# Or if installed via pip:
EMPIRICA_PATH=$(pip show empirica | grep Location | cut -d' ' -f2)
cp -r "$EMPIRICA_PATH/empirica/../plugins/claude-code-integration" ~/.claude/plugins/local/empirica-integration
```

2. **Copy templates to Claude config:**
```bash
# System prompt
cp ~/.claude/plugins/local/empirica-integration/templates/CLAUDE.md ~/.claude/CLAUDE.md

# MCP server config (merge with existing if you have one)
cp ~/.claude/plugins/local/empirica-integration/templates/mcp.json ~/.claude/mcp.json
```

3. **Register local marketplace** (create `~/.claude/plugins/known_marketplaces.json`):
```json
{
  "local": {
    "source": {
      "source": "directory",
      "path": "~/.claude/plugins/local"
    },
    "installLocation": "~/.claude/plugins/local"
  }
}
```

4. **Add to installed plugins** (`~/.claude/plugins/installed_plugins.json`):
```json
{
  "version": 2,
  "plugins": {
    "empirica-integration@local": [
      {
        "scope": "user",
        "installPath": "~/.claude/plugins/local/empirica-integration",
        "version": "1.4.2",
        "isLocal": true
      }
    ]
  }
}
```

5. **Enable in settings** (`~/.claude/settings.json`):
```json
{
  "enabledPlugins": {
    "empirica-integration@local": true
  }
}
```

6. **Add hooks to settings.json** (CRITICAL for Sentinel firewall):

The Sentinel gate (noetic firewall) requires PreToolUse hooks. Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{"type": "command", "command": "python3 ~/.claude/plugins/local/empirica-integration/hooks/sentinel-gate.py", "timeout": 10}]
      },
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "python3 ~/.claude/plugins/local/empirica-integration/hooks/sentinel-gate.py", "timeout": 10}]
      }
    ],
    "PreCompact": [
      {
        "matcher": "auto|manual",
        "hooks": [{"type": "command", "command": "python3 ~/.claude/plugins/local/empirica-integration/hooks/pre-compact.py", "timeout": 30}]
      }
    ],
    "SessionStart": [
      {
        "matcher": "compact",
        "hooks": [{"type": "command", "command": "python3 ~/.claude/plugins/local/empirica-integration/hooks/post-compact.py", "timeout": 30}]
      },
      {
        "matcher": "new|fresh",
        "hooks": [{"type": "command", "command": "python3 ~/.claude/plugins/local/empirica-integration/hooks/session-init.py", "timeout": 30}]
      }
    ],
    "SessionEnd": [
      {
        "matcher": ".*",
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/plugins/local/empirica-integration/hooks/session-end-postflight.py", "timeout": 20},
          {"type": "command", "command": "python3 ~/.claude/plugins/local/empirica-integration/hooks/curate-snapshots.py --output json", "timeout": 15, "allowFailure": true}
        ]
      }
    ]
  }
}
```

**Note:** Use absolute paths (replace `~` with your actual home directory like `/home/username`).

See `templates/settings-hooks.json` for reference.

7. **Restart Claude Code**

### Option B: Simple Shell Hooks (Lightweight Alternative)

If you prefer minimal setup without the full plugin:

```bash
mkdir -p ~/.claude/hooks
```

**Pre-compact hook** (`~/.claude/hooks/pre-compact.sh`):
```bash
cat > ~/.claude/hooks/pre-compact.sh << 'EOF'
#!/bin/bash
# Empirica pre-compact hook - saves epistemic state before memory compact
empirica session-snapshot "$(empirica sessions-list --output json 2>/dev/null | jq -r '.sessions[0].id // empty')" --output json 2>/dev/null || true
EOF
chmod +x ~/.claude/hooks/pre-compact.sh
```

**Post-compact hook** (`~/.claude/hooks/post-compact.sh`):
```bash
cat > ~/.claude/hooks/post-compact.sh << 'EOF'
#!/bin/bash
# Empirica post-compact hook - reminds Claude to restore context
echo "POST-COMPACT: Run 'empirica project-bootstrap' to restore epistemic context"
EOF
chmod +x ~/.claude/hooks/post-compact.sh
```

---

## Step 5: Configure MCP Server (Optional)

The MCP server gives Claude direct access to Empirica tools.

**Note:** Claude Code users typically don't need the MCP server—the CLI + hooks provide full functionality. The MCP server is primarily for Claude Desktop and Claude.ai integration where hooks aren't available.

**If you used the Quick Install:** `~/.claude/mcp.json` is auto-configured with the correct path.

**Manual configuration:** Edit `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "empirica": {
      "command": "/home/YOUR_USER/.local/bin/empirica-mcp",
      "args": ["--workspace", "/path/to/your/project"],
      "type": "stdio",
      "env": {
        "EMPIRICA_EPISTEMIC_MODE": "true"
      },
      "tools": ["*"],
      "description": "Empirica epistemic framework"
    }
  }
}
```

### Multi-Project Workspace Configuration (v1.4.2+)

The MCP server needs to know which project's `.empirica/` directory to use. Without this, sessions may be created in the wrong location.

**Option A: Explicit workspace (recommended for multi-project setups):**
```json
{
  "args": ["--workspace", "/home/user/my-project"]
}
```

**Option B: Auto-detection (works if MCP starts from project directory):**
The server will auto-detect from:
1. Git root (if `.empirica/` exists there)
2. Common paths: `~/empirical-ai/empirica`, `~/empirica`

**Option C: Environment variable:**
```json
{
  "env": {
    "EMPIRICA_WORKSPACE_ROOT": "/home/user/my-project"
  }
}
```

**IMPORTANT:** Use the **full absolute path** to `empirica-mcp`. Find it with:
```bash
which empirica-mcp
# Usually: ~/.local/bin/empirica-mcp (pipx) or ~/.local/bin/empirica-mcp (pip --user)
```

**If installed from source**, use the venv path:
```json
{
  "mcpServers": {
    "empirica": {
      "command": "/path/to/empirica/.venv-mcp/bin/empirica-mcp",
      "args": [],
      "type": "stdio",
      "env": {
        "PYTHONPATH": "/path/to/empirica",
        "EMPIRICA_EPISTEMIC_MODE": "true"
      },
      "tools": ["*"]
    }
  }
}
```

**Verify MCP is working** (in Claude Code):
```
/mcp
# Should show: empirica (connected)
```

---

## Step 6: Verify Setup

```bash
# Test CLI
empirica session-create --ai-id test-setup --output json

# Should return JSON with session_id

# Verify statusline (if configured)
python3 /path/to/empirica/scripts/statusline_empirica.py
# Should show: [empirica] ⚡84% │ 🎯3 ❓2 │ PREFLIGHT │ K:90% U:15% C:90% │ ✓ stable
#                                 ↑     ↑
#                           open goals  open unknowns (project-wide)
```

In Claude Code, ask:
> "Do you have access to Empirica? Try running `empirica --help`"

Claude should now know about Empirica from the system prompt.

---

## Troubleshooting

### "empirica: command not found"
```bash
# Add pip bin to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Claude doesn't know about Empirica
- Check `~/.claude/CLAUDE.md` exists and has content
- Restart Claude Code to reload system prompt

### Statusline not showing
- Check the path to `statusline_empirica.py` is correct
- Verify: `python3 /path/to/empirica/scripts/statusline_empirica.py`
- Check `~/.claude/settings.json` has valid JSON

### Plugin hooks not running
- Verify plugin is enabled: check `~/.claude/settings.json` → `enabledPlugins`
- Check hook logs: `.empirica/ref-docs/pre_summary_*.json`
- Ensure `EMPIRICA_AI_ID` env var matches your session's ai_id

### MCP server not working
```bash
# Verify MCP server is installed
which empirica-mcp

# Check mcp.json config syntax
python3 -c "import json; json.load(open('$HOME/.claude/mcp.json'))" && echo "Valid JSON"

# Test underlying CLI (MCP wraps this)
empirica --version
```
Note: `empirica-mcp` runs as stdio server, not CLI with --help.

---

## What's Next?

- **Full system prompt:** [CLAUDE.md](../system-prompts/CLAUDE.md) (179 lines)
- **All CLI commands:** [CLI Reference](../reference/CLI_COMMANDS_UNIFIED.md)
- **CASCADE workflow:** [Workflow Guide](../architecture/NOETIC_PRAXIC_FRAMEWORK.md)

---

## Quick Reference Card

```
SESSION:    empirica session-create --ai-id claude-code --output json
BOOTSTRAP:  empirica project-bootstrap --session-id <ID> --output json
GOAL:       empirica goals-create --session-id <ID> --objective "..."
PREFLIGHT:  empirica preflight-submit -
CHECK:      empirica check-submit -
COMPLETE:   empirica goals-complete --goal-id <ID> --reason "..."
POSTFLIGHT: empirica postflight-submit -
FINDING:    empirica finding-log --finding "..." --impact 0.7
UNKNOWN:    empirica unknown-log --unknown "..."
HELP:       empirica --help
```

---

**Setup complete!** Claude Code now has Empirica integration.
