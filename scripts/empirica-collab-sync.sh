#!/usr/bin/env bash
# Empirica Collaboration Sync Script
# Syncs configs and validates setup between collaborators via Tailscale SSH
#
# Usage:
#   ./empirica-collab-sync.sh <target>          # Full sync to target
#   ./empirica-collab-sync.sh <target> --check  # Check only, no changes
#   ./empirica-collab-sync.sh <target> --pull   # Pull from target to local
#
# Targets can be:
#   - Tailscale hostname: philipps-macbook-pro.tail3e4ac9.ts.net
#   - SSH alias from ~/.ssh/config
#   - user@host format

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Defaults
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EMPIRICA_ROOT="$(dirname "$SCRIPT_DIR")"
MODE="sync"
TARGET=""

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --check) MODE="check"; shift ;;
        --pull) MODE="pull"; shift ;;
        --help|-h)
            echo "Usage: $0 <target> [--check|--pull]"
            echo ""
            echo "Syncs Empirica configs between collaborators via Tailscale SSH"
            echo ""
            echo "Options:"
            echo "  --check  Check differences only, don't sync"
            echo "  --pull   Pull configs from target to local"
            echo ""
            echo "Examples:"
            echo "  $0 philipps-macbook-pro.tail3e4ac9.ts.net"
            echo "  $0 philipp@hostname --check"
            exit 0
            ;;
        *)
            if [[ -z "$TARGET" ]]; then
                TARGET="$1"
            fi
            shift
            ;;
    esac
done

if [[ -z "$TARGET" ]]; then
    echo -e "${RED}Error: No target specified${NC}"
    echo "Usage: $0 <target> [--check|--pull]"
    exit 1
fi

# Add user@ if not present
if [[ "$TARGET" != *"@"* ]]; then
    # Try to infer user from hostname
    if [[ "$TARGET" == *"philipps"* ]] || [[ "$TARGET" == *"philipp"* ]]; then
        TARGET="philippschwinger@$TARGET"
    else
        echo -e "${YELLOW}Warning: No user specified, using current user${NC}"
        TARGET="$(whoami)@$TARGET"
    fi
fi

echo -e "${BLUE}=== Empirica Collaboration Sync ===${NC}"
echo -e "Target: ${GREEN}$TARGET${NC}"
echo -e "Mode: ${GREEN}$MODE${NC}"
echo ""

# Test SSH connection
echo -e "${BLUE}Testing SSH connection...${NC}"
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "$TARGET" "echo 'Connected'" 2>/dev/null; then
    echo -e "${RED}Failed to connect to $TARGET${NC}"
    echo "Make sure:"
    echo "  1. Tailscale is running: tailscale status"
    echo "  2. SSH key is authorized on target"
    exit 1
fi
echo -e "${GREEN}SSH connection OK${NC}"
echo ""

# Get remote info
echo -e "${BLUE}Gathering remote info...${NC}"
REMOTE_INFO=$(ssh "$TARGET" 'echo "REMOTE_USER=$(whoami)"; echo "REMOTE_HOME=$HOME"; echo "EMPIRICA_CLI=$(which empirica 2>/dev/null || echo missing)"; echo "MCP_CLI=$(which empirica-mcp 2>/dev/null || echo missing)"')
eval "$REMOTE_INFO"
echo "  Remote user: $REMOTE_USER"
echo "  Remote home: $REMOTE_HOME"
echo "  Empirica CLI: $EMPIRICA_CLI"
echo "  MCP CLI: $MCP_CLI"
echo ""

# Local paths
LOCAL_HOME="$HOME"

# Files to sync
declare -A SYNC_FILES=(
    ["CLAUDE.md"]="$HOME/.claude/CLAUDE.md"
)

# Check/sync each file
sync_file() {
    local name="$1"
    local local_path="$2"
    local remote_path="$3"

    echo -e "${BLUE}Checking $name...${NC}"

    if [[ ! -f "$local_path" ]]; then
        echo -e "  ${YELLOW}Local file missing: $local_path${NC}"
        return 1
    fi

    # Get remote file
    local remote_content
    remote_content=$(ssh "$TARGET" "cat '$remote_path' 2>/dev/null" || echo "__MISSING__")

    if [[ "$remote_content" == "__MISSING__" ]]; then
        echo -e "  ${YELLOW}Remote file missing: $remote_path${NC}"
        if [[ "$MODE" == "sync" ]]; then
            echo -e "  ${GREEN}Copying to remote...${NC}"
            scp "$local_path" "$TARGET:$remote_path"
        fi
        return 0
    fi

    # Compare
    local local_hash remote_hash
    local_hash=$(md5sum "$local_path" | cut -d' ' -f1)
    remote_hash=$(echo "$remote_content" | md5sum | cut -d' ' -f1)

    if [[ "$local_hash" == "$remote_hash" ]]; then
        echo -e "  ${GREEN}In sync${NC}"
    else
        echo -e "  ${YELLOW}Files differ${NC}"

        if [[ "$MODE" == "check" ]]; then
            echo "  Local version: $(head -1 "$local_path" | tr -d '\n')"
            echo "  Remote version: $(echo "$remote_content" | head -1 | tr -d '\n')"
        elif [[ "$MODE" == "sync" ]]; then
            echo -e "  ${GREEN}Pushing local to remote...${NC}"
            scp "$local_path" "$TARGET:$remote_path"
        elif [[ "$MODE" == "pull" ]]; then
            echo -e "  ${GREEN}Pulling remote to local...${NC}"
            echo "$remote_content" > "$local_path"
        fi
    fi
}

# Sync CLAUDE.md
LOCAL_CLAUDE="$LOCAL_HOME/.claude/CLAUDE.md"
REMOTE_CLAUDE="$REMOTE_HOME/.claude/CLAUDE.md"
sync_file "CLAUDE.md" "$LOCAL_CLAUDE" "$REMOTE_CLAUDE"

echo ""

# Check git repos
echo -e "${BLUE}Checking git repo status...${NC}"

check_repo() {
    local name="$1"
    local remote_path="$2"
    local expected_remote="$3"

    echo -e "  ${BLUE}$name:${NC}"

    local repo_info
    repo_info=$(ssh "$TARGET" "cd '$remote_path' 2>/dev/null && git remote get-url origin 2>/dev/null && git log --oneline -1 2>/dev/null" || echo "__MISSING__")

    if [[ "$repo_info" == "__MISSING__" ]]; then
        echo -e "    ${RED}Not found at $remote_path${NC}"
        return 1
    fi

    local remote_url commit
    remote_url=$(echo "$repo_info" | head -1)
    commit=$(echo "$repo_info" | tail -1)

    echo "    Remote: $remote_url"
    echo "    Commit: $commit"

    if [[ "$expected_remote" != "" ]] && [[ "$remote_url" != *"$expected_remote"* ]]; then
        echo -e "    ${YELLOW}Warning: Expected remote containing '$expected_remote'${NC}"
    fi
}

check_repo "empirica" "$REMOTE_HOME/empirica" "Nubaeon/empirica"
check_repo "empirica-crm" "$REMOTE_HOME/empirica-crm" "Nubaeon/empirica-crm"

echo ""

# Summary
echo -e "${BLUE}=== Summary ===${NC}"
if [[ "$MODE" == "check" ]]; then
    echo "Run without --check to sync files"
elif [[ "$MODE" == "sync" ]]; then
    echo -e "${GREEN}Sync complete!${NC}"
    echo ""
    echo "Next steps for collaborator:"
    echo "  1. Pull latest empirica: cd ~/empirica && git pull origin develop"
    echo "  2. Pull latest empirica-crm: cd ~/empirica-crm && git pull origin main"
    echo "  3. Reinstall: pip install -e ~/empirica -e ~/empirica/empirica-mcp -e ~/empirica-crm"
    echo "  4. Restart Claude Code to pick up MCP changes"
elif [[ "$MODE" == "pull" ]]; then
    echo -e "${GREEN}Pull complete!${NC}"
fi
