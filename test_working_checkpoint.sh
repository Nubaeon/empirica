#!/bin/bash
# WORKING example for mini-agent checkpoint testing

set -e

SESSION_ID="test-working-$(date +%s)"
AI_ID="mini-agent"

echo "🧪 Phase 1 Checkpoint Test - CORRECT Workflow"
echo "Session: $SESSION_ID"
echo ""

# Step 1: Get prompt (optional for testing, but let's show it)
echo "Step 1: Getting prompt..."
empirica preflight "Test checkpoint" --ai-id "$AI_ID" --session-id "$SESSION_ID" --prompt-only > /tmp/prompt.json
echo "✓ Prompt received"
echo ""

# Step 2: Create assessment JSON (mini-agent would use genuine self-assessment)
# CORRECT FORMAT: Nested structure matching canonical_epistemic_assessment.py parser
echo "Step 2: Creating assessment..."
cat > /tmp/assessment.json << 'EOF'
{
  "engagement": {
    "score": 0.85,
    "rationale": "Testing Phase 1 git automation with genuine checkpoint creation"
  },
  "foundation": {
    "know": {
      "score": 0.70,
      "rationale": "Understanding checkpoint mechanism and git notes system"
    },
    "do": {
      "score": 0.75,
      "rationale": "Capable of executing test workflow"
    },
    "context": {
      "score": 0.80,
      "rationale": "Full test context provided"
    }
  },
  "comprehension": {
    "clarity": {
      "score": 0.85,
      "rationale": "Clear test objectives"
    },
    "coherence": {
      "score": 0.82,
      "rationale": "Coherent with Phase 1 goals"
    },
    "signal": {
      "score": 0.78,
      "rationale": "Focus on checkpoint creation"
    },
    "density": {
      "score": 0.40,
      "rationale": "Low complexity test"
    }
  },
  "execution": {
    "state": {
      "score": 0.75,
      "rationale": "Test environment mapped"
    },
    "change": {
      "score": 0.70,
      "rationale": "Tracking checkpoint changes"
    },
    "completion": {
      "score": 0.60,
      "rationale": "Verifiable via git notes"
    },
    "impact": {
      "score": 0.65,
      "rationale": "Test-only impact"
    }
  },
  "uncertainty": {
    "score": 0.25,
    "rationale": "Low uncertainty in test procedure"
  }
}
EOF
echo "✓ Assessment created"
echo ""

# Step 3: Submit with assessment (THIS creates checkpoint!)
echo "Step 3: Submitting assessment (checkpoint created here)..."
empirica preflight "Test checkpoint" \
  --ai-id "$AI_ID" \
  --session-id "$SESSION_ID" \
  --assessment-json /tmp/assessment.json \
  --json > /tmp/result.json

echo "✓ Assessment submitted"
echo ""

# Step 4: Verify checkpoint
echo "Step 4: Verifying checkpoint creation..."
sleep 1  # Give git a moment

CHECKPOINT_COUNT=$(git notes --ref=empirica/checkpoints list | wc -l)
echo "Total checkpoints: $CHECKPOINT_COUNT"

# Check HEAD for checkpoint
echo ""
echo "Checking HEAD for checkpoint..."
if git notes --ref=empirica/checkpoints show HEAD 2>/dev/null; then
    echo "✅ Checkpoint found on HEAD!"
else
    echo "⚠️  No checkpoint on HEAD, checking recent commits..."
    for commit in $(git log --oneline -5 | awk '{print $1}'); do
        if git notes --ref=empirica/checkpoints show "$commit" 2>/dev/null | grep -q "$SESSION_ID"; then
            echo "✅ Found checkpoint for session $SESSION_ID on commit $commit!"
            exit 0
        fi
    done
    echo "❌ Checkpoint not found in recent commits"
fi

# Cleanup
rm -f /tmp/prompt.json /tmp/assessment.json /tmp/result.json
