#!/bin/bash
# Install Empirica Integration Plugin for Claude Code
# This script installs the plugin from the Empirica repository

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_SOURCE="$SCRIPT_DIR/../plugins/claude-code-integration"
PLUGIN_DEST="$HOME/.claude/plugins/local/empirica-integration"
SETTINGS_FILE="$HOME/.claude/settings.json"

echo "🔧 Installing Empirica Integration Plugin for Claude Code..."
echo ""

# Check if Claude Code directory exists
if [ ! -d "$HOME/.claude" ]; then
    echo "❌ Error: Claude Code directory not found at $HOME/.claude"
    echo "   Please install Claude Code first."
    exit 1
fi

# Check if plugin source exists
if [ ! -d "$PLUGIN_SOURCE" ]; then
    echo "❌ Error: Plugin source not found at $PLUGIN_SOURCE"
    echo "   Are you running this from the Empirica repository?"
    exit 1
fi

# Create local plugins directory
mkdir -p "$HOME/.claude/plugins/local"

# Copy plugin
echo "📦 Copying plugin files..."
cp -r "$PLUGIN_SOURCE" "$PLUGIN_DEST"
echo "   ✅ Plugin copied to: $PLUGIN_DEST"
echo ""

# Check if plugin is already enabled
if [ -f "$SETTINGS_FILE" ]; then
    if grep -q '"empirica-integration@local"' "$SETTINGS_FILE"; then
        echo "✅ Plugin already enabled in settings.json"
    else
        echo "⚠️  Plugin copied but not enabled."
        echo "   Add to $SETTINGS_FILE:"
        echo '   "enabledPlugins": {'
        echo '     "empirica-integration@local": true'
        echo '   }'
    fi
else
    echo "⚠️  Settings file not found. You'll need to enable the plugin manually."
fi

echo ""
echo "📚 Next steps:"
echo "   1. Complete manual setup (see $PLUGIN_DEST/INSTALL.md)"
echo "   2. Register local marketplace in known_marketplaces.json"
echo "   3. Add plugin to installed_plugins.json"
echo "   4. Enable plugin in settings.json (if not already done)"
echo "   5. Restart Claude Code"
echo ""
echo "💡 For detailed instructions, see:"
echo "   $PLUGIN_DEST/INSTALL.md"
echo ""
echo "✅ Installation complete!"
