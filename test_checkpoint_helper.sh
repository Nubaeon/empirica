#!/bin/bash
# Helper script for mini-agent to test checkpoints properly
# This demonstrates the complete 3-step workflow

set -e

SESSION_ID="test-mini-agent-$(date +%s)"
AI_ID="mini-agent"

echo "🧪 Testing Phase 1 Checkpoint Creation"
echo "Session: $SESSION_ID"
echo ""

# Step 1: Get prompt
echo "Step 1: Getting self-assessment prompt..."
PROMPT=$(empirica preflight "Test checkpoint creation" --ai-id "$AI_ID" --session-id "$SESSION_ID" --prompt-only)
echo "✓ Prompt received"

# Step 2: Simulate self-assessment (mini-agent would do this)
echo ""
echo "Step 2: Performing self-assessment..."
ASSESSMENT='{
  "vectors": {
    "engagement": 0.85,
    "know": 0.70,
    "do": 0.65,
    "context": 0.75,
    "clarity": 0.80,
    "coherence": 0.82,
    "signal": 0.78,
    "density": 0.60,
    "state": 0.70,
    "change": 0.50,
    "completion": 0.40,
    "impact": 0.55,
    "uncertainty": 0.25
  }
}'
echo "✓ Assessment complete"

# Step 3: Submit assessment (this creates checkpoint!)
echo ""
echo "Step 3: Submitting assessment (checkpoint creation happens here)..."

# Create temp file for assessment
TEMP_ASSESSMENT=$(mktemp)
echo "$ASSESSMENT" > "$TEMP_ASSESSMENT"

# Submit using preflight-submit (no --ai-id needed, stored in session)
if empirica preflight-submit --help &>/dev/null; then
    empirica preflight-submit \
        --session-id "$SESSION_ID" \
        --vectors "$ASSESSMENT" \
        --output json
else
    # Alternative: use Python to call the handler directly
    python3 << PYEOF
from empirica.cli.command_handlers.cascade_commands import handle_preflight_submit_command
import argparse
import json

args = argparse.Namespace(
    session_id='$SESSION_ID',
    ai_id='$AI_ID',
    vectors='$ASSESSMENT',
    output='json',
    verbose=False
)

try:
    result = handle_preflight_submit_command(args)
    print("✓ Assessment submitted")
except Exception as e:
    print(f"Error: {e}")
PYEOF
fi

rm -f "$TEMP_ASSESSMENT"

# Step 4: Verify checkpoint was created
echo ""
echo "Step 4: Verifying checkpoint..."
CHECKPOINT_COUNT=$(git notes --ref=empirica/checkpoints list | wc -l)
echo "Total checkpoints: $CHECKPOINT_COUNT"

# Find our checkpoint
echo ""
echo "Looking for our session checkpoint..."
for commit in $(git notes --ref=empirica/checkpoints list | awk '{print $2}'); do
    CHECKPOINT_DATA=$(git notes --ref=empirica/checkpoints show "$commit" 2>/dev/null || echo "{}")
    if echo "$CHECKPOINT_DATA" | grep -q "$SESSION_ID"; then
        echo "✅ FOUND OUR CHECKPOINT!"
        echo "$CHECKPOINT_DATA" | python3 -m json.tool | head -15
        exit 0
    fi
done

echo "⚠️  Checkpoint not found yet (may need to commit changes)"
echo ""
echo "Current git status:"
git status --short

echo ""
echo "💡 Note: Checkpoints are attached to commits."
echo "   If no new commit, checkpoint attaches to HEAD."
echo "   Try: git notes --ref=empirica/checkpoints show HEAD"
