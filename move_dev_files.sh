#!/bin/bash
# Move development files to empirica-dev

set -e

SOURCE="/home/yogapad/empirical-ai/empirica"
TARGET="/home/yogapad/empirical-ai/empirica-dev"

echo "📦 Moving development files to empirica-dev"
echo "==========================================="

# Create empirica-dev if it doesn't exist
if [ ! -d "$TARGET" ]; then
    echo "Creating $TARGET..."
    mkdir -p "$TARGET"
    mkdir -p "$TARGET/sessions"
    mkdir -p "$TARGET/planning"
    mkdir -p "$TARGET/wip"
    mkdir -p "$TARGET/optimization"
fi

# Session Summaries → sessions/
echo ""
echo "📝 Moving Session Summaries..."
for file in \
    "CASCADE_GRANULARITY_FIX_COMPLETE.md" \
    "FINAL_SESSION_SUMMARY.md" \
    "SESSION_126d5c66_FINAL_SUMMARY.md" \
    "SESSION_CLEANUP_COMPLETE.md" \
    "SESSION_SUMMARY_2446122a.md" \
    "NEXT_SESSION_PLAN.md" \
    "PHASE_FIX_COMPLETION_REPORT.md"
do
    if [ -f "$SOURCE/$file" ]; then
        mv "$SOURCE/$file" "$TARGET/sessions/"
        echo "  ✅ $file → sessions/"
    fi
done

# Development Planning → planning/
echo ""
echo "📋 Moving Development Planning..."
for file in \
    "COMPREHENSIVE_TESTING_GUIDE.md" \
    "COMPREHENSIVE_TEST_RESULTS.md" \
    "DOCS_PRUNING_ACTIONABLE_PLAN.md" \
    "GOAL_ORCHESTRATOR_INTEGRATION_MASTER_PLAN.md" \
    "QWEN_DOCS_VALIDATION_PLAN.md" \
    "MINIMAX_TEST_VALIDATION.md"
do
    if [ -f "$SOURCE/$file" ]; then
        mv "$SOURCE/$file" "$TARGET/planning/"
        echo "  ✅ $file → planning/"
    fi
done

# Work in Progress → wip/
echo ""
echo "🚧 Moving Work in Progress..."
for file in \
    "HANDOFF_TO_MINI_AGENT.md" \
    "MINI_AGENT_WORK_PACKAGE.md" \
    "MCP_TOOL_VALIDATION_TEST_PLAN.md"
do
    if [ -f "$SOURCE/$file" ]; then
        mv "$SOURCE/$file" "$TARGET/wip/"
        echo "  ✅ $file → wip/"
    fi
done

# System Prompt Optimization → optimization/
echo ""
echo "⚡ Moving System Prompt Optimization..."
for file in \
    "MCP_TOOL_FIXES_COMPLETE.md" \
    "MCP_TOOL_ISSUES_FOUND.md" \
    "OPTIMIZATION_COMPLETE_V2.md" \
    "SYSTEM_PROMPT_COMPRESSION_COMPLETE.md" \
    "SYSTEM_PROMPT_IMPROVEMENTS_V2.md" \
    "SYSTEM_PROMPT_OPTIMIZATION_FINAL.md" \
    "SYSTEM_PROMPT_OPTIMIZATION_PLAN.md"
do
    if [ -f "$SOURCE/$file" ]; then
        mv "$SOURCE/$file" "$TARGET/optimization/"
        echo "  ✅ $file → optimization/"
    fi
done

# Move tests folder
echo ""
echo "🧪 Moving tests folder..."
if [ -d "$SOURCE/tests" ]; then
    mv "$SOURCE/tests" "$TARGET/"
    echo "  ✅ tests/ → empirica-dev/"
fi

# Create README in empirica-dev
echo ""
echo "📄 Creating empirica-dev README..."
cat > "$TARGET/README.md" << 'README'
# Empirica Development Files

This directory contains development-related files for the Empirica project.

## Directory Structure

- **sessions/** - Session summaries and completion reports
- **planning/** - Development planning documents and test plans
- **wip/** - Current work in progress (handoffs, work packages)
- **optimization/** - System prompt optimization work
- **tests/** - Test suite (pytest)

## Main Project

User-facing documentation and code is in the parent directory: `../empirica/`

## Purpose

Keeping development files separate keeps the main project clean for end users while preserving all development context and history.
README

echo "  ✅ Created README.md"

echo ""
echo "✅ Complete! Moved 23 files + tests to empirica-dev"
echo ""
echo "📊 Summary:"
echo "  - sessions/: 7 files"
echo "  - planning/: 6 files"
echo "  - wip/: 3 files"
echo "  - optimization/: 7 files"
echo "  - tests/: 1 folder"
echo ""
echo "Main folder now has:"
ls -1 "$SOURCE"/*.md 2>/dev/null | wc -l | xargs echo "  -" "markdown files"
