# Claude Code + Empirica Setup Guide

**Time:** 5 minutes | **No scripts** | **Just copy-paste**

This guide sets up Empirica for Claude Code users on regular systems (not Docker).

---

## What You're Installing

| Component | Purpose | Location |
|-----------|---------|----------|
| `empirica` | CLI + Python library | pip package |
| `empirica-mcp` | MCP server (optional) | pip package |
| System prompt | Teaches Claude how to use Empirica | `~/.claude/CLAUDE.md` |
| Hooks | Memory compact integration | `~/.claude/hooks/` |

---

## Step 1: Install Packages

```bash
pip install empirica empirica-mcp
```

Verify:
```bash
empirica --version
# Should show: 1.2.2
```

---

## Step 2: Add System Prompt

Create or edit `~/.claude/CLAUDE.md`:

```bash
mkdir -p ~/.claude
cat >> ~/.claude/CLAUDE.md << 'EOF'

# Empirica - Epistemic Self-Assessment Framework

You have access to Empirica for tracking what you know and learn.

## Session Workflow

```bash
# 1. Start session (do this first)
empirica session-create --ai-id claude-code --output json

# 2. Load project context
empirica project-bootstrap --session-id <ID> --output json

# 3. PREFLIGHT: Assess what you know BEFORE starting work
empirica preflight-submit -

# 4. Do your work...

# 5. POSTFLIGHT: Measure what you learned AFTER completing work
empirica postflight-submit -
```

## Core Vectors (0.0-1.0)

| Vector | Meaning | Ready Threshold |
|--------|---------|-----------------|
| **know** | Domain knowledge | >= 0.70 |
| **uncertainty** | Doubt level | <= 0.35 |
| **context** | Information access | >= 0.60 |
| **do** | Execution capability | >= 0.60 |

**Bias correction:** Add +0.10 to uncertainty, subtract -0.05 from know (AIs overestimate).

## Log As You Work

```bash
# Discoveries
empirica finding-log --finding "Discovered X works by Y" --impact 0.7

# Questions/unknowns
empirica unknown-log --unknown "Need to investigate Z"

# Failed approaches (prevent repeating)
empirica deadend-log --approach "Tried X" --why-failed "Failed because Y"
```

**Impact scale:** 0.1-0.3 trivial | 0.4-0.6 important | 0.7-0.9 critical

## When Uncertain

If uncertainty > 0.5 or you're unsure how to proceed:
```bash
empirica check-submit -
```
This returns `proceed` or `investigate` guidance.

## Key Commands

```bash
empirica --help              # All commands
empirica goals-list          # Active goals
empirica project-search --task "query"  # Search past learnings
empirica session-snapshot <ID>          # Save current state
```

## The Turtle Principle

"Turtles all the way down" = same epistemic rules at every meta-layer.
The Sentinel monitors using the same 13 vectors it monitors you with.

**Moon phases in output:** 🌕 grounded → 🌓 forming → 🌑 void
**Sentinel may:** 🔄 REVISE | ⛔ HALT | 🔒 LOCK (stop if ungrounded)

EOF
```

---

## Step 3: Add Statusline (Recommended)

The statusline shows real-time epistemic status in your Claude Code terminal.

Add to `~/.claude/settings.json`:
```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 $(pip show empirica | grep Location | cut -d' ' -f2)/empirica/../scripts/statusline_empirica.py",
    "refresh_ms": 5000
  }
}
```

Or if you installed from source:
```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 /path/to/empirica/scripts/statusline_empirica.py",
    "refresh_ms": 5000
  }
}
```

**Display modes** (set via `EMPIRICA_STATUS_MODE` env var):
- `basic`: Just confidence + phase
- `default`: Full status with vectors (recommended)
- `learning`: Focus on vector changes
- `full`: Everything with raw values

**Status indicators:**
- `⚡82%` = confidence score
- `NOETIC/PRAXIC` = cognitive phase
- `K:85% U:15% C:90%` = know/uncertainty/context vectors
- `✓ stable` / `⚠ drifting` = drift status

---

## Step 4: Install Empirica Plugin (Recommended)

The plugin enforces the CASCADE workflow and preserves epistemic state automatically.

**What it does:**
- **PreToolCall hooks** (`sentinel-gate.py`): Gates Edit/Write/Bash until valid CHECK exists
- **SessionStart hooks** (`session-init.py`, `post-compact.py`): Auto-creates session + bootstrap
- **SessionEnd hooks** (`session-end-postflight.py`): Auto-captures POSTFLIGHT

### Option A: Full Plugin (Recommended)

1. **Copy plugin to Claude plugins directory:**
```bash
# From Empirica source
cp -r /path/to/empirica/plugins/claude-code-integration ~/.claude/plugins/local/empirica-integration

# Or if installed via pip, find the path:
pip show empirica | grep Location
# Then copy from that location
```

2. **Register local marketplace** (create `~/.claude/plugins/known_marketplaces.json`):
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

3. **Add to installed plugins** (`~/.claude/plugins/installed_plugins.json`):
```json
{
  "version": 2,
  "plugins": {
    "empirica-integration@local": [
      {
        "scope": "user",
        "installPath": "~/.claude/plugins/local/empirica-integration",
        "version": "1.0.0",
        "isLocal": true
      }
    ]
  }
}
```

4. **Enable in settings** (`~/.claude/settings.json`):
```json
{
  "enabledPlugins": {
    "empirica-integration@local": true
  }
}
```

5. **Restart Claude Code**

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

If you also use Claude Desktop and want MCP tools:

Edit `~/.claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "empirica": {
      "command": "empirica-mcp",
      "env": {
        "EMPIRICA_AI_ID": "claude-desktop",
        "EMPIRICA_EPISTEMIC_MODE": "true",
        "EMPIRICA_PERSONALITY": "balanced_architect"
      }
    }
  }
}
```

---

## Step 6: Verify Setup

```bash
# Test CLI
empirica session-create --ai-id test-setup --output json

# Should return JSON with session_id

# Verify statusline (if configured)
python3 /path/to/empirica/scripts/statusline_empirica.py
# Should show: [empirica] ⚡82% │ NOETIC │ PREFLIGHT │ K:85% U:15% C:90% │ ✓ stable
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
# Test MCP server directly
empirica-mcp --help
```

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
PREFLIGHT:  empirica preflight-submit -
POSTFLIGHT: empirica postflight-submit -
CHECK:      empirica check-submit -
FINDING:    empirica finding-log --finding "..." --impact 0.7
UNKNOWN:    empirica unknown-log --unknown "..."
HELP:       empirica --help
```

---

**Setup complete!** Claude Code now has Empirica integration.
