#!/bin/bash
# Set EMPIRICA_SESSION_ID to latest active claude-code session
# Source this in your shell: source ~/.claude/plugins/local/empirica-integration/hooks/set-session-env.sh

# Try to get latest active claude-code* session
SESSION_ID=$(empirica sessions-list --output json 2>/dev/null | python3 -c "
import json
import sys
try:
    data = json.load(sys.stdin)
    sessions = data.get('sessions', [])

    # Filter for active claude-code* sessions
    active_claude = [s for s in sessions
                     if s['ai_id'].startswith('claude-code') and s['end_time'] is None]

    if active_claude:
        # Sort by start_time, get most recent
        active_claude.sort(key=lambda x: x.get('start_time', ''), reverse=True)
        print(active_claude[0]['session_id'])
    else:
        sys.exit(1)
except:
    sys.exit(1)
")

if [ $? -eq 0 ] && [ -n "$SESSION_ID" ]; then
    export EMPIRICA_SESSION_ID="$SESSION_ID"
    echo "✅ EMPIRICA_SESSION_ID set to: ${SESSION_ID:0:8}..."
    echo "   Hooks will now use this session automatically"
else
    echo "⚠️  No active claude-code session found"
    echo "   Create one with: empirica session-create --ai-id claude-code"
fi
