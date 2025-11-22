#!/bin/bash
# Quick progress checker for mini-agent

echo "📊 Goal Progress for Session 126d5c66"
echo "======================================"
echo ""

cd /home/yogapad/empirical-ai/empirica

# Check both goals
.venv-mcp/bin/empirica goals-list --session-id 126d5c66-4680-40ba-a983-1366bdeabadd --output json | python3 << 'PYTHON'
import json
import sys

data = json.load(sys.stdin)
if data.get('ok'):
    for goal in data.get('goals', []):
        print(f"Goal: {goal['objective'][:60]}...")
        print(f"  Status: {goal['status']}")
        print(f"  Progress: {goal['completed_subtasks']}/{goal['total_subtasks']} ({goal['completion_percentage']:.0f}%)")
        print()
PYTHON

echo ""
echo "📋 To complete a subtask:"
echo "  empirica goals-complete-subtask --task-id <TASK_ID> --evidence \"Brief description\""
echo ""
echo "📚 Reference:"
echo "  - Work instructions: HANDOFF_TO_MINI_AGENT.md"
echo "  - Task IDs: See table in handoff doc"
echo "  - Patterns: docs/AI_VS_AGENT_EMPIRICA_PATTERNS.md"
