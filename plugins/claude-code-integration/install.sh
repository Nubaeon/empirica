#!/bin/bash
# empirica-integration installer - one-line install for Claude Code
# Usage: curl -fsSL https://raw.githubusercontent.com/Nubaeon/empirica/main/plugins/claude-code-integration/install.sh | bash

set -e

PLUGIN_NAME="empirica-integration"
PLUGIN_VERSION="1.4.1"
PLUGIN_DIR="$HOME/.claude/plugins/local/$PLUGIN_NAME"
MARKETPLACE_DIR="$HOME/.claude/plugins/local/.claude-plugin"
SETTINGS_FILE="$HOME/.claude/settings.json"
INSTALLED_PLUGINS_FILE="$HOME/.claude/plugins/installed_plugins.json"
KNOWN_MARKETPLACES_FILE="$HOME/.claude/plugins/known_marketplaces.json"
REPO_URL="https://github.com/Nubaeon/empirica.git"
PLUGIN_PATH="plugins/claude-code-integration"

echo "🧠 Installing $PLUGIN_NAME plugin for Claude Code..."
echo ""

# ==================== PRE-FLIGHT CHECKS ====================

# Check git is available
if ! command -v git &>/dev/null; then
    echo "❌ Error: git is required but not installed"
    exit 1
fi

# Check Python 3 is available
if ! command -v python3 &>/dev/null; then
    echo "❌ Error: python3 is required but not installed"
    exit 1
fi

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

# Clone or update
if [ -d "$PLUGIN_DIR" ]; then
    echo "📦 Updating existing installation..."
    cd "$PLUGIN_DIR"
    git pull --ff-only origin main 2>/dev/null || (git fetch origin && git reset --hard origin/main) || true
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
if ! jq -e '.statusLine' "$SETTINGS_FILE" >/dev/null 2>&1; then
    jq --arg cmd "python3 $PLUGIN_DIR/scripts/statusline_empirica.py" \
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
    jq --arg sentinel_cmd "python3 $PLUGIN_DIR/hooks/sentinel-gate.py" \
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
    jq --arg precompact_cmd "python3 $PLUGIN_DIR/hooks/pre-compact.py" \
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

# Add SessionStart hooks (post-compact bootstrap + session-init)
if ! jq -e '.hooks.SessionStart[] | select(.hooks[].command | contains("post-compact.py"))' "$SETTINGS_FILE" >/dev/null 2>&1; then
    jq --arg postcompact_cmd "python3 $PLUGIN_DIR/hooks/post-compact.py" \
       --arg sessioninit_cmd "python3 $PLUGIN_DIR/hooks/session-init.py" \
       '.hooks.SessionStart = (.hooks.SessionStart // []) + [
         {
           "matcher": "compact",
           "hooks": [{"type": "command", "command": $postcompact_cmd, "timeout": 30}]
         },
         {
           "matcher": "new|fresh",
           "hooks": [{"type": "command", "command": $sessioninit_cmd, "timeout": 30}]
         }
       ]' "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp" && mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"
    echo "   ✓ SessionStart hooks configured"
else
    echo "   SessionStart hooks already configured"
fi

# Add SessionEnd hooks (postflight + snapshot curation)
if ! jq -e '.hooks.SessionEnd[] | select(.hooks[].command | contains("session-end-postflight.py"))' "$SETTINGS_FILE" >/dev/null 2>&1; then
    jq --arg postflight_cmd "python3 $PLUGIN_DIR/hooks/session-end-postflight.py" \
       --arg curate_cmd "python3 $PLUGIN_DIR/hooks/curate-snapshots.py --output json" \
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
