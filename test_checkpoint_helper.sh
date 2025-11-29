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
# IMPORTANT: Use NESTED format matching parse_llm_response() expectations
echo ""
echo "Step 2: Performing self-assessment..."
cat > /tmp/mini_assessment.json << 'EOF'
{
  "engagement": {"score": 0.85, "rationale": "Testing checkpoint creation"},
  "foundation": {
    "know": {"score": 0.70, "rationale": "Understanding test workflow"},
    "do": {"score": 0.75, "rationale": "Can execute tests"},
    "context": {"score": 0.80, "rationale": "Test context clear"}
  },
  "comprehension": {
    "clarity": {"score": 0.85, "rationale": "Clear test goals"},
    "coherence": {"score": 0.82, "rationale": "Coherent test flow"},
    "signal": {"score": 0.78, "rationale": "Focused on checkpoints"},
    "density": {"score": 0.40, "rationale": "Simple test"}
  },
  "execution": {
    "state": {"score": 0.75, "rationale": "Environment ready"},
    "change": {"score": 0.70, "rationale": "Tracking changes"},
    "completion": {"score": 0.60, "rationale": "Verifiable"},
    "impact": {"score": 0.65, "rationale": "Test only"}
  },
  "uncertainty": {"score": 0.25, "rationale": "Low uncertainty"}
}
EOF
echo "✓ Assessment complete"

# Step 3: Submit assessment (this creates checkpoint!)
echo ""
echo "Step 3: Submitting assessment (checkpoint creation happens here)..."

# Submit using preflight command with assessment JSON file
empirica preflight "Test checkpoint creation" \
    --ai-id "$AI_ID" \
    --session-id "$SESSION_ID" \
    --assessment-json /tmp/mini_assessment.json \
    --json > /tmp/result.json

if [ $? -eq 0 ]; then
    echo "✓ Assessment submitted successfully"
else
    echo "❌ Assessment submission failed"
    cat /tmp/result.json 2>/dev/null
    exit 1
fi

rm -f /tmp/mini_assessment.json /tmp/result.json

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
