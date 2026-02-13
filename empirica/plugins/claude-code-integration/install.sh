#!/bin/bash
# empirica-integration installer - one-line install for Claude Code
# Usage: curl -fsSL https://raw.githubusercontent.com/Nubaeon/empirica/main/plugins/claude-code-integration/install.sh | bash

set -e

PLUGIN_NAME="empirica-integration"
PLUGIN_VERSION="1.5.1"
PLUGIN_DIR="$HOME/.claude/plugins/local/$PLUGIN_NAME"
MARKETPLACE_DIR="$HOME/.claude/plugins/local/.claude-plugin"
SETTINGS_FILE="$HOME/.claude/settings.json"
INSTALLED_PLUGINS_FILE="$HOME/.claude/plugins/installed_plugins.json"
KNOWN_MARKETPLACES_FILE="$HOME/.claude/plugins/known_marketplaces.json"
REPO_URL="https://github.com/Nubaeon/empirica.git"
PLUGIN_PATH="plugins/claude-code-integration"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=10

echo "🧠 Installing $PLUGIN_NAME plugin for Claude Code..."
echo ""

# ==================== PRE-FLIGHT CHECKS ====================

# Check git is available
if ! command -v git &>/dev/null; then
    echo "❌ Error: git is required but not installed"
    exit 1
fi

# Find a suitable Python >= 3.10
# On macOS, system python3 is often 3.9 — check versioned binaries and framework paths
find_python() {
    local candidates=()

    # Check common versioned binaries (highest first)
    for ver in 13 12 11 10; do
        command -v "python3.${ver}" &>/dev/null && candidates+=("python3.${ver}")
    done

    # Check plain python3
    command -v python3 &>/dev/null && candidates+=("python3")

    # Check macOS framework paths
    for ver in 13 12 11 10; do
        local fw="/Library/Frameworks/Python.framework/Versions/3.${ver}/bin/python3.${ver}"
        [ -f "$fw" ] && candidates+=("$fw")
    done

    # Check Homebrew paths (Apple Silicon + Intel)
    for ver in 13 12 11 10; do
        for prefix in /opt/homebrew /usr/local; do
            local brew="${prefix}/bin/python3.${ver}"
            [ -f "$brew" ] && candidates+=("$brew")
        done
    done

    # Test each candidate for minimum version
    for py in "${candidates[@]}"; do
        local py_ver
        py_ver=$("$py" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null) || continue
        local major minor
        major=$(echo "$py_ver" | cut -d. -f1)
        minor=$(echo "$py_ver" | cut -d. -f2)
        if [ "$major" -ge "$MIN_PYTHON_MAJOR" ] && [ "$minor" -ge "$MIN_PYTHON_MINOR" ]; then
            echo "$py"
            return 0
        fi
    done

    return 1
}

PYTHON_CMD=$(find_python)
if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Error: Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ is required"
    echo ""
    python3 --version 2>&1 | sed 's/^/   Found: /' || echo "   python3 not found"
    echo ""
    echo "   Install Python 3.10+ via:"
    echo "     macOS:  brew install python@3.11"
    echo "     Ubuntu: sudo apt install python3.11"
    echo "     pyenv:  pyenv install 3.11 && pyenv global 3.11"
    exit 1
fi

PYTHON_VERSION=$("$PYTHON_CMD" --version 2>&1)
echo "   Using: $PYTHON_CMD ($PYTHON_VERSION)"

# Check jq is available (required for JSON manipulation)
if ! command -v jq &>/dev/null; then
    echo "❌ Error: jq is required for installation"
    echo "   Install with: apt install jq (Debian/Ubuntu) or brew install jq (macOS)"
    exit 1
fi

# Check pipx for MCP server installation
PIPX_AVAILABLE=false
if command -v pipx &>/dev/null; then
    PIPX_AVAILABLE=true
fi

# ==================== INSTALL PLUGIN FILES ====================

# Create directories
mkdir -p "$HOME/.claude/plugins/local"
mkdir -p "$MARKETPLACE_DIR"
mkdir -p "$HOME/.claude"

# Create Empirica runtime directories (instance isolation + state)
mkdir -p "$HOME/.empirica/instance_projects"
mkdir -p "$HOME/.empirica/statusline_cache"

# Bootstrap active_work.json if it doesn't exist
if [ ! -f "$HOME/.empirica/active_work.json" ]; then
    cat > "$HOME/.empirica/active_work.json" << AWEOF
{
  "project_path": null,
  "folder_name": null,
  "claude_session_id": null,
  "empirica_session_id": null,
  "source": "install",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S+0000)"
}
AWEOF
    echo "   ✓ Created ~/.empirica/active_work.json"
fi

# Clone or update
if [ -d "$PLUGIN_DIR" ]; then
    echo "📦 Updating existing installation..."
    # Determine source: running from local repo checkout or remote?
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [ -d "$SCRIPT_DIR/hooks" ] && [ -f "$SCRIPT_DIR/hooks/sentinel-gate.py" ]; then
        # Running from local source checkout — rsync files to plugin dir
        echo "   Syncing from local source: $SCRIPT_DIR"
        rsync -a --exclude='__pycache__' --exclude='.git' "$SCRIPT_DIR/" "$PLUGIN_DIR/"
    elif [ -d "$PLUGIN_DIR/.git" ]; then
        # Plugin dir is a git repo — pull updates
        cd "$PLUGIN_DIR"
        git pull --ff-only origin main 2>/dev/null || (git fetch origin && git reset --hard origin/main) || true
    else
        echo "   ⚠️  Plugin dir exists but no git repo and not running from source."
        echo "   Re-run install.sh from the empirica source checkout to sync files."
    fi
else
    echo "📦 Installing plugin..."
    # Create temp dir for sparse checkout
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"

    # Sparse checkout just the plugin directory
    git clone --depth 1 --filter=blob:none --sparse "$REPO_URL" empirica-repo
    cd empirica-repo
    git sparse-checkout set "$PLUGIN_PATH"

    # Move plugin to destination
    mv "$PLUGIN_PATH" "$PLUGIN_DIR"

    # Cleanup
    cd "$HOME"
    rm -rf "$TEMP_DIR"
fi

# Make hooks executable
chmod +x "$PLUGIN_DIR/hooks/"*.py 2>/dev/null || true
chmod +x "$PLUGIN_DIR/hooks/"*.sh 2>/dev/null || true
chmod +x "$PLUGIN_DIR/scripts/"*.py 2>/dev/null || true

# ==================== INSTALL CLAUDE.md ====================

echo "📝 Installing CLAUDE.md system prompt..."
if [ -f "$PLUGIN_DIR/templates/CLAUDE.md" ]; then
    if [ -f "$HOME/.claude/CLAUDE.md" ]; then
        echo "   CLAUDE.md already exists - backing up to CLAUDE.md.bak"
        cp "$HOME/.claude/CLAUDE.md" "$HOME/.claude/CLAUDE.md.bak"
    fi
    cp "$PLUGIN_DIR/templates/CLAUDE.md" "$HOME/.claude/CLAUDE.md"
    echo "   ✓ CLAUDE.md installed to ~/.claude/CLAUDE.md"
else
    echo "   ⚠️  CLAUDE.md template not found"
fi

# ==================== CONFIGURE SETTINGS.JSON ====================

echo "⚙️  Configuring settings.json..."

# Create settings.json if it doesn't exist
if [ ! -f "$SETTINGS_FILE" ]; then
    echo '{}' > "$SETTINGS_FILE"
fi

# Add enabledPlugins if not present
if ! jq -e '.enabledPlugins' "$SETTINGS_FILE" >/dev/null 2>&1; then
    jq '.enabledPlugins = {}' "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp" && mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"
fi

# Enable the plugin
jq --arg name "$PLUGIN_NAME@local" '.enabledPlugins[$name] = true' "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp" && mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"
echo "   ✓ Plugin enabled in settings.json"

# Add StatusLine if not present
# NOTE: < /dev/null prevents stdin hangs when Claude Code invokes the statusline
if ! jq -e '.statusLine' "$SETTINGS_FILE" >/dev/null 2>&1; then
    jq --arg cmd "$PYTHON_CMD $PLUGIN_DIR/scripts/statusline_empirica.py < /dev/null" \
       '.statusLine = {"type": "command", "command": $cmd}' \
       "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp" && mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"
    echo "   ✓ StatusLine configured"
else
    echo "   StatusLine already configured"
fi

# Add PreToolUse hooks if not present (needed because hooks.json can't have them for local plugins)
if ! jq -e '.hooks.PreToolUse' "$SETTINGS_FILE" >/dev/null 2>&1; then
    jq '.hooks = (.hooks // {})' "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp" && mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"
fi

# Check if sentinel hooks already present
if ! jq -e '.hooks.PreToolUse[] | select(.hooks[].command | contains("sentinel-gate"))' "$SETTINGS_FILE" >/dev/null 2>&1; then
    jq --arg sentinel_cmd "$PYTHON_CMD $PLUGIN_DIR/hooks/sentinel-gate.py" \
       '.hooks.PreToolUse = (.hooks.PreToolUse // []) + [
         {
           "matcher": "Edit|Write",
           "hooks": [{"type": "command", "command": $sentinel_cmd, "timeout": 10}]
         },
         {
           "matcher": "Bash",
           "hooks": [{"type": "command", "command": $sentinel_cmd, "timeout": 10}]
         }
       ]' "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp" && mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"
    echo "   ✓ PreToolUse (Sentinel) hooks configured"
else
    echo "   PreToolUse hooks already configured"
fi

# Add PreCompact hook (empirica pre-compact snapshot)
if ! jq -e '.hooks.PreCompact[] | select(.hooks[].command | contains("pre-compact.py"))' "$SETTINGS_FILE" >/dev/null 2>&1; then
    jq --arg precompact_cmd "$PYTHON_CMD $PLUGIN_DIR/hooks/pre-compact.py" \
       '.hooks.PreCompact = (.hooks.PreCompact // []) + [
         {
           "matcher": "auto|manual",
           "hooks": [{"type": "command", "command": $precompact_cmd, "timeout": 30}]
         }
       ]' "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp" && mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"
    echo "   ✓ PreCompact hook configured"
else
    echo "   PreCompact hook already configured"
fi

# Add SessionStart hooks (post-compact bootstrap + session-init + EWM protocol loader)
if ! jq -e '.hooks.SessionStart[] | select(.hooks[].command | contains("post-compact.py"))' "$SETTINGS_FILE" >/dev/null 2>&1; then
    jq --arg postcompact_cmd "$PYTHON_CMD $PLUGIN_DIR/hooks/post-compact.py" \
       --arg sessioninit_cmd "$PYTHON_CMD $PLUGIN_DIR/hooks/session-init.py" \
       --arg ewm_cmd "$PYTHON_CMD $PLUGIN_DIR/hooks/ewm-protocol-loader.py" \
       '.hooks.SessionStart = (.hooks.SessionStart // []) + [
         {
           "matcher": "compact",
           "hooks": [
             {"type": "command", "command": $postcompact_cmd, "timeout": 30},
             {"type": "command", "command": $ewm_cmd, "timeout": 10, "allowFailure": true}
           ]
         },
         {
           "matcher": "new|fresh",
           "hooks": [
             {"type": "command", "command": $sessioninit_cmd, "timeout": 30},
             {"type": "command", "command": $ewm_cmd, "timeout": 10, "allowFailure": true}
           ]
         }
       ]' "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp" && mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"
    echo "   ✓ SessionStart hooks configured (with EWM protocol loader)"
else
    # Check if EWM loader is missing from existing SessionStart hooks
    if ! jq -e '.hooks.SessionStart[] | select(.hooks[].command | contains("ewm-protocol-loader"))' "$SETTINGS_FILE" >/dev/null 2>&1; then
        jq --arg ewm_cmd "$PYTHON_CMD $PLUGIN_DIR/hooks/ewm-protocol-loader.py" \
           '(.hooks.SessionStart[] | .hooks) += [{"type": "command", "command": $ewm_cmd, "timeout": 10, "allowFailure": true}]' \
           "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp" && mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"
        echo "   ✓ EWM protocol loader added to SessionStart"
    else
        echo "   SessionStart hooks already configured"
    fi
fi

# Add SessionEnd hooks (postflight + snapshot curation)
if ! jq -e '.hooks.SessionEnd[] | select(.hooks[].command | contains("session-end-postflight.py"))' "$SETTINGS_FILE" >/dev/null 2>&1; then
    jq --arg postflight_cmd "$PYTHON_CMD $PLUGIN_DIR/hooks/session-end-postflight.py" \
       --arg curate_cmd "$PYTHON_CMD $PLUGIN_DIR/hooks/curate-snapshots.py --output json" \
       '.hooks.SessionEnd = (.hooks.SessionEnd // []) + [
         {
           "matcher": ".*",
           "hooks": [
             {"type": "command", "command": $postflight_cmd, "timeout": 20},
             {"type": "command", "command": $curate_cmd, "timeout": 15, "allowFailure": true}
           ]
         }
       ]' "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp" && mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"
    echo "   ✓ SessionEnd hooks configured"
else
    echo "   SessionEnd hooks already configured"
fi

# Add SubagentStart hook (agent tracking)
if ! jq -e '.hooks.SubagentStart' "$SETTINGS_FILE" >/dev/null 2>&1 || ! jq -e '.hooks.SubagentStart[] | select(.hooks[].command | contains("subagent-start.py"))' "$SETTINGS_FILE" >/dev/null 2>&1; then
    jq --arg substart_cmd "$PYTHON_CMD $PLUGIN_DIR/hooks/subagent-start.py" \
       '.hooks.SubagentStart = (.hooks.SubagentStart // []) + [
         {
           "matcher": ".*",
           "hooks": [{"type": "command", "command": $substart_cmd, "timeout": 10, "allowFailure": true}]
         }
       ]' "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp" && mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"
    echo "   ✓ SubagentStart hook configured"
else
    echo "   SubagentStart hook already configured"
fi

# Add SubagentStop hook (agent result tracking)
if ! jq -e '.hooks.SubagentStop' "$SETTINGS_FILE" >/dev/null 2>&1 || ! jq -e '.hooks.SubagentStop[] | select(.hooks[].command | contains("subagent-stop.py"))' "$SETTINGS_FILE" >/dev/null 2>&1; then
    jq --arg substop_cmd "$PYTHON_CMD $PLUGIN_DIR/hooks/subagent-stop.py" \
       '.hooks.SubagentStop = (.hooks.SubagentStop // []) + [
         {
           "matcher": ".*",
           "hooks": [{"type": "command", "command": $substop_cmd, "timeout": 15, "allowFailure": true}]
         }
       ]' "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp" && mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"
    echo "   ✓ SubagentStop hook configured"
else
    echo "   SubagentStop hook already configured"
fi

# Add UserPromptSubmit hook (epistemic tool router + AAP hedge detection)
if ! jq -e '.hooks.UserPromptSubmit' "$SETTINGS_FILE" >/dev/null 2>&1 || ! jq -e '.hooks.UserPromptSubmit[] | select(.hooks[].command | contains("tool-router.py"))' "$SETTINGS_FILE" >/dev/null 2>&1; then
    jq --arg router_cmd "$PYTHON_CMD $PLUGIN_DIR/hooks/tool-router.py" \
       '.hooks.UserPromptSubmit = (.hooks.UserPromptSubmit // []) + [
         {
           "matcher": ".*",
           "hooks": [{"type": "command", "command": $router_cmd, "timeout": 3, "allowFailure": true}]
         }
       ]' "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp" && mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"
    echo "   ✓ UserPromptSubmit hook configured (tool router + AAP)"
else
    echo "   UserPromptSubmit hook already configured"
fi

# ==================== MARKETPLACE REGISTRATION ====================

echo "📋 Registering in marketplace..."

# Create marketplace.json if not exists
if [ ! -f "$MARKETPLACE_DIR/marketplace.json" ]; then
    cat > "$MARKETPLACE_DIR/marketplace.json" << 'EOF'
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "local",
  "description": "Local development plugins",
  "owner": { "name": "Local", "email": "dev@localhost" },
  "plugins": []
}
EOF
fi

# Add plugin to marketplace if not already present
if ! grep -q "\"name\": \"$PLUGIN_NAME\"" "$MARKETPLACE_DIR/marketplace.json" 2>/dev/null; then
    jq --arg name "$PLUGIN_NAME" --arg version "$PLUGIN_VERSION" '.plugins += [{
        "name": $name,
        "description": "Noetic firewall + CASCADE workflow automation for Claude Code",
        "version": $version,
        "author": { "name": "Empirica Project", "url": "https://github.com/Nubaeon/empirica" },
        "source": "./" + $name,
        "category": "productivity"
    }]' "$MARKETPLACE_DIR/marketplace.json" > "$MARKETPLACE_DIR/marketplace.json.tmp"
    mv "$MARKETPLACE_DIR/marketplace.json.tmp" "$MARKETPLACE_DIR/marketplace.json"
    echo "   ✓ Added to marketplace.json"
fi

# ==================== INSTALLED PLUGINS REGISTRATION ====================

echo "📦 Registering installed plugin..."

# Create installed_plugins.json if not exists
if [ ! -f "$INSTALLED_PLUGINS_FILE" ]; then
    echo '{"version": 2, "plugins": {}}' > "$INSTALLED_PLUGINS_FILE"
fi

# Add plugin entry
INSTALL_DATE=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
jq --arg name "$PLUGIN_NAME@local" --arg path "$PLUGIN_DIR" --arg version "$PLUGIN_VERSION" --arg date "$INSTALL_DATE" \
   '.plugins[$name] = [{
     "scope": "user",
     "installPath": $path,
     "version": $version,
     "installedAt": $date,
     "lastUpdated": $date,
     "isLocal": true
   }]' "$INSTALLED_PLUGINS_FILE" > "$INSTALLED_PLUGINS_FILE.tmp" && mv "$INSTALLED_PLUGINS_FILE.tmp" "$INSTALLED_PLUGINS_FILE"
echo "   ✓ Added to installed_plugins.json"

# ==================== KNOWN MARKETPLACES ====================

echo "🗂️  Registering local marketplace..."

# Create known_marketplaces.json if not exists
if [ ! -f "$KNOWN_MARKETPLACES_FILE" ]; then
    echo '{}' > "$KNOWN_MARKETPLACES_FILE"
fi

# Add local marketplace if not present
if ! jq -e '.local' "$KNOWN_MARKETPLACES_FILE" >/dev/null 2>&1; then
    jq --arg path "$HOME/.claude/plugins/local" --arg date "$INSTALL_DATE" \
       '.local = {
         "source": {"source": "directory", "path": $path},
         "installLocation": $path,
         "lastUpdated": $date
       }' "$KNOWN_MARKETPLACES_FILE" > "$KNOWN_MARKETPLACES_FILE.tmp" && mv "$KNOWN_MARKETPLACES_FILE.tmp" "$KNOWN_MARKETPLACES_FILE"
    echo "   ✓ Local marketplace registered"
fi

# ==================== INSTALL EMPIRICA-MCP ====================

echo "🔌 Installing empirica-mcp server..."

if [ "$PIPX_AVAILABLE" = true ]; then
    # Check if already installed
    if pipx list 2>/dev/null | grep -q "empirica-mcp"; then
        echo "   empirica-mcp already installed, upgrading..."
        pipx upgrade empirica-mcp 2>/dev/null || pipx install --force empirica-mcp 2>/dev/null || echo "   ⚠️  Could not upgrade empirica-mcp"
    else
        pipx install empirica-mcp 2>/dev/null || echo "   ⚠️  Could not install empirica-mcp via pipx"
    fi
    echo "   ✓ empirica-mcp installed"
else
    echo "   ⚠️  pipx not available - install manually:"
    echo "      pipx install empirica-mcp"
    echo "      Or: pip install empirica-mcp"
fi

# ==================== CONFIGURE MCP.JSON ====================

echo "⚙️  Configuring MCP server..."

MCP_FILE="$HOME/.claude/mcp.json"

# Find empirica-mcp path (pipx or pip)
MCP_CMD=""
if command -v empirica-mcp &>/dev/null; then
    MCP_CMD=$(which empirica-mcp)
elif [ -f "$HOME/.local/bin/empirica-mcp" ]; then
    MCP_CMD="$HOME/.local/bin/empirica-mcp"
fi

if [ -n "$MCP_CMD" ]; then
    # Create mcp.json if it doesn't exist
    if [ ! -f "$MCP_FILE" ]; then
        echo '{"mcpServers":{}}' > "$MCP_FILE"
    fi

    # Add empirica MCP server if not present
    if ! jq -e '.mcpServers.empirica' "$MCP_FILE" >/dev/null 2>&1; then
        jq --arg cmd "$MCP_CMD" \
           '.mcpServers.empirica = {
             "command": $cmd,
             "args": [],
             "type": "stdio",
             "env": {"EMPIRICA_EPISTEMIC_MODE": "true"},
             "tools": ["*"],
             "description": "Empirica epistemic framework - CASCADE workflow, goals, findings"
           }' "$MCP_FILE" > "$MCP_FILE.tmp" && mv "$MCP_FILE.tmp" "$MCP_FILE"
        echo "   ✓ MCP server configured in ~/.claude/mcp.json"
    else
        echo "   MCP server already configured"
    fi
else
    echo "   ⚠️  empirica-mcp not found in PATH - configure mcp.json manually"
    echo "      See: ~/.claude/plugins/local/empirica-integration/templates/mcp.json"
fi

# ==================== CREATE INITIAL SESSION ====================

if command -v empirica &>/dev/null; then
    echo ""
    echo "🔧 Creating initial Empirica session..."
    empirica session-create --ai-id claude-code --output json 2>/dev/null && echo "   ✓ Session created!" || echo "   (Session creation skipped - may already exist)"
fi

# ==================== VERIFY ====================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ $PLUGIN_NAME v$PLUGIN_VERSION installed successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Plugin:     $PLUGIN_DIR"
echo "📝 CLAUDE.md:  ~/.claude/CLAUDE.md"
echo "⚙️  Settings:   ~/.claude/settings.json"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "WHAT'S INCLUDED:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🛡️  Sentinel Gate (Noetic Firewall)"
echo "    - Noetic tools (Read, Grep, etc.) always allowed"
echo "    - Praxic tools (Edit, Write, Bash) require CHECK"
echo ""
echo "📋 CASCADE Workflow (Pre/Post Compact)"
echo "    - Auto-saves epistemic state before compact"
echo "    - Auto-loads context after compact"
echo ""
echo "📊 StatusLine"
echo "    - Shows session ID, phase, know/uncertainty vectors"
echo ""
echo "🔌 MCP Server"
echo "    - Full Empirica API available to Claude"
echo ""
echo "🎯 Skills"
echo "    - /empirica-framework - Full command reference"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "NEXT STEPS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Restart Claude Code to load the plugin"
echo ""
echo "2. Verify with: /plugin"
echo "   Should show: $PLUGIN_NAME@local"
echo ""
echo "3. Connect MCP server: /mcp"
echo "   Should show: empirica connected"
echo ""
echo "To disable sentinel gating temporarily:"
echo "  export EMPIRICA_SENTINEL_LOOPING=false"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "OPTIONAL: Install breadcrumbs for enhanced continuity"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "curl -fsSL https://raw.githubusercontent.com/Nubaeon/breadcrumbs/main/install.sh | bash"
echo ""
echo "🧠 Happy epistemic coding!"
