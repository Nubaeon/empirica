#!/bin/bash
# empirica-integration installer - one-line install for Claude Code
# Usage: curl -fsSL https://raw.githubusercontent.com/Nubaeon/empirica/main/plugins/claude-code-integration/install.sh | bash

set -e

PLUGIN_NAME="empirica-integration"
PLUGIN_DIR="$HOME/.claude/plugins/local/$PLUGIN_NAME"
MARKETPLACE_DIR="$HOME/.claude/plugins/local/.claude-plugin"
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

# Check if empirica CLI is installed
if ! command -v empirica &>/dev/null; then
    echo "⚠️  Warning: empirica CLI not found"
    echo "   Install with: pip install empirica"
    echo "   Or from source: pip install -e /path/to/empirica"
    echo ""
    echo "   The plugin requires the empirica CLI for full functionality."
    echo ""
fi

# Check jq is available (optional but recommended)
if ! command -v jq &>/dev/null; then
    echo "⚠️  Warning: jq not installed (optional)"
    echo "   Some features work better with jq. Install with:"
    echo "   apt install jq (Debian/Ubuntu) or brew install jq (macOS)"
    echo ""
fi

# ==================== INSTALL ====================

# Create directories
mkdir -p "$HOME/.claude/plugins/local"
mkdir -p "$MARKETPLACE_DIR"

# Clone or update
if [ -d "$PLUGIN_DIR" ]; then
    echo "📦 Updating existing installation..."
    cd "$PLUGIN_DIR"
    git pull --ff-only origin main 2>/dev/null || git fetch origin && git reset --hard origin/main
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

# Create marketplace.json if not exists
if [ ! -f "$MARKETPLACE_DIR/marketplace.json" ]; then
    echo "📝 Creating local marketplace config..."
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
    echo "📝 Registering plugin in marketplace..."
    if command -v jq &>/dev/null; then
        jq --arg name "$PLUGIN_NAME" '.plugins += [{
            "name": $name,
            "description": "Noetic firewall + CASCADE workflow automation for Claude Code",
            "version": "1.5.0",
            "author": { "name": "Empirica Project", "url": "https://github.com/Nubaeon/empirica" },
            "source": "./" + $name,
            "category": "productivity"
        }]' "$MARKETPLACE_DIR/marketplace.json" > "$MARKETPLACE_DIR/marketplace.json.tmp"
        mv "$MARKETPLACE_DIR/marketplace.json.tmp" "$MARKETPLACE_DIR/marketplace.json"
    else
        echo "⚠️  jq not available - manually add $PLUGIN_NAME to marketplace.json"
    fi
fi

# Make hooks executable
chmod +x "$PLUGIN_DIR/hooks/"*.py 2>/dev/null || true
chmod +x "$PLUGIN_DIR/hooks/"*.sh 2>/dev/null || true
chmod +x "$PLUGIN_DIR/scripts/"*.py 2>/dev/null || true

# ==================== CREATE INITIAL SESSION ====================

if command -v empirica &>/dev/null; then
    echo ""
    echo "🔧 Creating initial Empirica session..."
    empirica session-create --ai-id claude-code --output json 2>/dev/null && echo "   Session created!" || echo "   (Session creation skipped)"
fi

# ==================== VERIFY ====================

echo ""
echo "✅ $PLUGIN_NAME installed successfully!"
echo ""
echo "📍 Location: $PLUGIN_DIR"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "WHAT'S INCLUDED:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🛡️  Sentinel Gate (PreToolUse hooks)"
echo "    - Noetic tools (Read, Grep, etc.) always allowed"
echo "    - Praxic tools (Edit, Write, Bash) require CHECK"
echo ""
echo "📋 CASCADE Workflow (Pre/Post Compact)"
echo "    - Auto-saves epistemic state before compact"
echo "    - Auto-loads context after compact"
echo ""
echo "🎯 Skills"
echo "    - /empirica-framework - Full command reference"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "USAGE:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "The plugin runs automatically. Hooks are registered in:"
echo "  $PLUGIN_DIR/hooks/hooks.json"
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
