#!/bin/bash
# check_interagent_messages.sh - Cron job for checking interagent messages
#
# Syncs git notes from remotes and checks for new messages.
# Sends desktop notification if unread messages exist.
#
# Usage:
#   Add to crontab: */5 * * * * /path/to/check_interagent_messages.sh
#
# Environment:
#   EMPIRICA_AI_ID - AI identity to check inbox for (default: claude-code)
#   EMPIRICA_WORKSPACE - Workspace root to scan (default: ~/empirical-ai)
#   EMPIRICA_NOTIFY - Notification method: desktop, log, none (default: desktop)

set -euo pipefail

AI_ID="${EMPIRICA_AI_ID:-claude-code}"
# Messages live in the canonical empirica repo only (not scattered across all projects)
EMPIRICA_REPO="${EMPIRICA_REPO:-$HOME/empirical-ai/empirica}"
NOTIFY="${EMPIRICA_NOTIFY:-desktop}"
LOG_FILE="${HOME}/.empirica/message_check.log"
EMPIRICA_BIN="${HOME}/.venv/tmux/bin/empirica"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

notify() {
    local title="$1"
    local body="$2"

    case "$NOTIFY" in
        desktop)
            # Try notify-send (Linux) or osascript (macOS)
            if command -v notify-send &> /dev/null; then
                notify-send -u normal -i mail-unread "$title" "$body"
            elif command -v osascript &> /dev/null; then
                osascript -e "display notification \"$body\" with title \"$title\""
            fi
            ;;
        log)
            log "NOTIFICATION: $title - $body"
            ;;
        none)
            ;;
    esac
}

# Messages centralized in empirica repo (no multi-repo scanning)
get_message_repo() {
    echo "$EMPIRICA_REPO"
}

# Sync git notes from all remotes for a repo
sync_notes() {
    local repo="$1"
    cd "$repo" || return 1

    # Get all remotes
    local remotes
    remotes=$(git remote 2>/dev/null || echo "")

    for remote in $remotes; do
        # Fetch message notes specifically
        git fetch "$remote" 'refs/notes/empirica/messages/*:refs/notes/empirica/messages/*' 2>/dev/null || true
    done
}

# Check inbox for a specific repo
check_inbox() {
    local repo="$1"
    cd "$repo" || return 1

    # Get unread message count
    local result
    result=$("$EMPIRICA_BIN" message-inbox --ai-id "$AI_ID" --status unread --output json 2>/dev/null || echo '{"count": 0}')

    local count
    count=$(echo "$result" | jq -r '.count // 0' 2>/dev/null || echo "0")

    echo "$count"
}

main() {
    log "Starting message check for $AI_ID"

    local repo
    repo=$(get_message_repo)

    if [[ ! -d "$repo/.git" ]]; then
        log "ERROR: Empirica repo not found at $repo"
        exit 1
    fi

    # Sync notes from remotes
    sync_notes "$repo" 2>/dev/null

    # Check inbox
    local count
    count=$(check_inbox "$repo")

    if [[ "$count" -gt 0 ]]; then
        notify "Empirica Messages" "$count unread message(s)"
        log "Found $count unread message(s)"
    else
        log "No unread messages"
    fi

    log "Message check complete"
}

main "$@"
