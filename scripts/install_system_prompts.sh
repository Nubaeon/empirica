#!/bin/bash
#
# Empirica System Prompt Installation Script
# Purpose: Install Empirica system prompts to various AI tool locations
# Version: 2.0 (uses sync_system_prompts.py)
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EMPIRICA_ROOT="$(dirname "$SCRIPT_DIR")"
PROMPTS_DIR="$EMPIRICA_ROOT/docs/system-prompts"

print_header() { echo -e "${BLUE}=== $1 ===${NC}"; }
print_success() { echo -e "${GREEN}[OK] $1${NC}"; }
print_info() { echo -e "${BLUE}[i] $1${NC}"; }

main() {
    print_header "Empirica System Prompt Installer v2.0"
    echo ""

    # Step 1: Sync prompts from canonical core
    print_info "Syncing prompts from CANONICAL_CORE.md..."
    python3 "$SCRIPT_DIR/sync_system_prompts.py"
    echo ""

    # Step 2: Install Claude prompt to ~/.claude/
    print_header "Installing Claude Code prompt"
    mkdir -p "$HOME/.claude"
    cp "$PROMPTS_DIR/CLAUDE.md" "$HOME/.claude/CLAUDE.md"
    print_success "Installed to ~/.claude/CLAUDE.md"
    echo ""

    # Step 3: Install Gemini prompt (if gemini dir exists)
    if [ -d "$HOME/.gemini" ] || [ -n "$GEMINI_SYSTEM_MD" ]; then
        print_header "Installing Gemini prompt"
        mkdir -p "$HOME/.gemini"
        cp "$PROMPTS_DIR/GEMINI.md" "$HOME/.gemini/system_empirica.md"
        print_success "Installed to ~/.gemini/system_empirica.md"
        print_info "Set: export GEMINI_SYSTEM_MD=~/.gemini/system_empirica.md"
        echo ""
    fi

    # Summary
    print_header "Installation Complete"
    echo ""
    echo "Installed prompts:"
    echo "  Claude:  ~/.claude/CLAUDE.md"
    [ -f "$HOME/.gemini/system_empirica.md" ] && echo "  Gemini:  ~/.gemini/system_empirica.md"
    echo ""
    echo "Source:    $PROMPTS_DIR/CANONICAL_CORE.md"
    echo "Sync cmd:  python3 scripts/sync_system_prompts.py"
    echo ""
    print_success "Done!"
}

main "$@"
