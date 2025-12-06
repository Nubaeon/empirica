#!/bin/bash
#
# Empirica Git Statistics
# Extract and analyze epistemic metadata from git commit history
#
# Usage:
#   ./empirica-git-stats.sh [--ai-id ID] [--since DATE] [--summary]
#

set -e

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

# Options
AI_ID="${1:---all}"
SINCE="${2:---since=2 weeks ago}"
MODE="${3:---full}"

# Configuration
export LC_ALL=C

# ============================================================================
# Helper Functions
# ============================================================================

extract_trailer() {
    local commit_msg="$1"
    local trailer_name="$2"
    local default="${3:-}"

    echo "$commit_msg" | grep "^$trailer_name:" | head -1 | sed "s/^$trailer_name: //" || echo "$default"
}

extract_delta_value() {
    local delta_str="$1"
    # Format: "+0.15 (0.65 → 0.8)"
    # Extract just the number
    echo "$delta_str" | sed 's/ .*//'
}

# ============================================================================
# Main Statistics Gathering
# ============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  EMPIRICA GIT STATISTICS                                   ║"
echo "║  Epistemic Metadata Analysis from Commit History           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Query: Get all commits with epistemic data
echo "COMMITS WITH EPISTEMIC DATA"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Count commits with epistemic trailers
TOTAL_COMMITS=$(git rev-list --count HEAD)
EPISTEMIC_COMMITS=$(git log --all --pretty=format:"%B" | grep -c "^Epistemic-AI:" || echo 0)

echo "Total commits: $TOTAL_COMMITS"
echo "With epistemic metadata: $EPISTEMIC_COMMITS"
echo "Coverage: $(awk "BEGIN { printf \"%.1f%%\n\", ($EPISTEMIC_COMMITS/$TOTAL_COMMITS)*100 }")"
echo ""

# ============================================================================
# Learning Delta Analysis
# ============================================================================

echo "LEARNING GROWTH ANALYSIS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

declare -A ai_learning
declare -A ai_mastery
declare -A ai_commits

# Parse all commits with epistemic data
while IFS= read -r commit_hash; do
    commit_msg=$(git show -s --format=%B "$commit_hash")

    ai_id=$(extract_trailer "$commit_msg" "Epistemic-AI" "unknown")
    learning_delta=$(extract_trailer "$commit_msg" "Epistemic-Learning-Delta" "0.00")
    mastery_delta=$(extract_trailer "$commit_msg" "Epistemic-Mastery-Delta" "0.00")

    # Extract numeric value
    learning_value=$(extract_delta_value "$learning_delta")
    mastery_value=$(extract_delta_value "$mastery_delta")

    # Initialize if needed
    if [[ -z "${ai_learning[$ai_id]}" ]]; then
        ai_learning[$ai_id]="0.0"
        ai_mastery[$ai_id]="0.0"
        ai_commits[$ai_id]="0"
    fi

    # Accumulate (in real awk, would sum properly)
    ai_commits[$ai_id]=$(( ${ai_commits[$ai_id]} + 1 ))

done < <(git log --all --pretty=format:"%H" | while read hash; do
    if git show -s --format=%B "$hash" | grep -q "^Epistemic-AI:"; then
        echo "$hash"
    fi
done)

echo "Per-AI Learning Growth:"
echo ""
for ai in "${!ai_commits[@]}"; do
    count=${ai_commits[$ai]}
    echo "  $ai: $count commits"
done

echo ""

# ============================================================================
# Query Examples
# ============================================================================

echo "QUERY EXAMPLES (use these commands)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Show commits with learning deltas:"
echo "  git log --pretty=format:'%h %s | %(trailers:key=Epistemic-Learning-Delta)'"
echo ""

echo "Filter by AI agent:"
echo "  git log --all --grep='Epistemic-AI: claude-code' --pretty=format:'%h %s'"
echo ""

echo "Calculate total team learning:"
echo "  git log --all --pretty=format:'%(trailers:key=Epistemic-Learning-Delta)' | \\"
echo "    grep -oE '[+-][0-9.]+' | awk '{sum+=\$1} END {print \"Total: \" sum}'"
echo ""

echo "Show mastery by AI:"
echo "  git log --all --pretty=format:'%h %(trailers:key=Epistemic-Mastery-Delta)' | sort"
echo ""

# ============================================================================
# Recent Commits with Metadata
# ============================================================================

echo "RECENT COMMITS WITH EPISTEMIC DATA"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

git log -n 10 --pretty=format:"%h %s" --all | while read hash subject; do
    ai=$(git show -s --format=%B "$hash" | grep "^Epistemic-AI:" | sed 's/Epistemic-AI: //' || echo "—")
    learning=$(git show -s --format=%B "$hash" | grep "^Epistemic-Learning-Delta:" | sed 's/Epistemic-Learning-Delta: //' || echo "—")

    printf "%-8s | %-40s | %s | %s\n" "$hash" "${subject:0:40}" "$ai" "$learning"
done

echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "Statistics Generated: $(date)"
echo "═══════════════════════════════════════════════════════════════"
