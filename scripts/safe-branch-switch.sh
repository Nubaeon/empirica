#!/bin/bash
# Safe branch switching script for Empirica
# Backs up ignored files before switching branches, restores after

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Files and directories to preserve during branch switch
PRESERVE_ITEMS=(
    ".empirica_reflex_logs"
    ".agent_memory.json"
)

# Backup location (outside repo to be safe)
BACKUP_DIR="$HOME/.empirica_branch_backups/$(date +%Y%m%d_%H%M%S)"

if [ $# -eq 0 ]; then
    echo -e "${RED}Error: No branch specified${NC}"
    echo "Usage: $0 <branch-name>"
    echo "Example: $0 gh-pages"
    exit 1
fi

TARGET_BRANCH="$1"
CURRENT_BRANCH=$(git branch --show-current)

echo -e "${YELLOW}=== Safe Branch Switch ===${NC}"
echo "Current branch: $CURRENT_BRANCH"
echo "Target branch:  $TARGET_BRANCH"
echo ""

# Check if target branch exists
if ! git rev-parse --verify "$TARGET_BRANCH" >/dev/null 2>&1; then
    echo -e "${RED}Error: Branch '$TARGET_BRANCH' does not exist${NC}"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"
echo -e "${GREEN}Created backup directory: $BACKUP_DIR${NC}"

# Backup files
echo ""
echo "Backing up ignored files..."
for item in "${PRESERVE_ITEMS[@]}"; do
    if [ -e "$item" ]; then
        echo "  - Backing up: $item"
        cp -r "$item" "$BACKUP_DIR/"
    else
        echo "  - Skipping (not found): $item"
    fi
done

# Also backup ~/.empirica directory
if [ -d "$HOME/.empirica" ]; then
    echo "  - Backing up: ~/.empirica"
    mkdir -p "$BACKUP_DIR/.empirica_home"
    cp -r "$HOME/.empirica/." "$BACKUP_DIR/.empirica_home/"
fi

echo -e "${GREEN}Backup complete!${NC}"
echo ""

# Switch branches
echo "Switching to branch: $TARGET_BRANCH"
git checkout "$TARGET_BRANCH"

echo ""
echo "Restoring backed up files..."

# Restore files
for item in "${PRESERVE_ITEMS[@]}"; do
    if [ -e "$BACKUP_DIR/$item" ]; then
        echo "  - Restoring: $item"
        rm -rf "$item"  # Remove any existing version
        cp -r "$BACKUP_DIR/$item" .
    fi
done

# Restore ~/.empirica directory
if [ -d "$BACKUP_DIR/.empirica_home" ]; then
    echo "  - Restoring: ~/.empirica"
    rm -rf "$HOME/.empirica"
    mkdir -p "$HOME/.empirica"
    cp -r "$BACKUP_DIR/.empirica_home/." "$HOME/.empirica/"
fi

echo -e "${GREEN}Restore complete!${NC}"
echo ""
echo -e "${GREEN}✓ Successfully switched to $TARGET_BRANCH with data preserved${NC}"
echo ""
echo "Backup saved at: $BACKUP_DIR"
echo "(You can delete this after verifying everything works)"
