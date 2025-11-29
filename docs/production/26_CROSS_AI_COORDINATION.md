# 26. Cross-AI Coordination

**Multi-Agent Collaboration via Git Notes**

---

## Overview

Empirica enables **cross-AI coordination** through git-based goal storage and epistemic handoff. Multiple AI agents can discover, resume, and collaborate on goals across sessions and agents.

**Key Features:**
- **Goal Discovery**: Find goals created by other AIs
- **Goal Resumption**: Resume another AI's work with epistemic context
- **Lineage Tracking**: Track which AIs worked on which goals
- **Epistemic Handoff**: Transfer epistemic state between agents

**Storage**: Goals stored in git notes for persistence and shareability

---

## Core Concepts

### 1. Goal Discovery

Find goals created by other AI agents stored in git notes.

**Use Cases:**
- "What did Claude work on yesterday?"
- "Show me all authentication-related goals"
- "What goals are in progress?"

### 2. Goal Resumption

Resume another AI's goal with full epistemic context handoff.

**Includes:**
- Original goal definition
- Epistemic state when goal was created
- Lineage of which AIs worked on it
- Current progress and status

### 3. Lineage Tracking

Track the history of AI agents working on a goal.

**Lineage Entry:**
```python
{
    "ai_id": "claude-code",
    "action": "created",  # or "resumed", "completed", "updated"
    "timestamp": "2025-11-29T10:30:00Z",
    "epistemic_state": {...}
}
```

---

## CLI Commands

### `discover-goals` - Find Goals

**Syntax:**
```bash
empirica discover-goals [OPTIONS]
```

**Options:**
- `--from-ai-id <AI_ID>` - Filter by AI that created the goal
- `--session-id <SESSION_ID>` - Filter by session
- `--output json` - JSON output (default: human-readable)

**Examples:**
```bash
# Discover all goals from claude-code
empirica discover-goals --from-ai-id claude-code

# Discover goals from specific session
empirica discover-goals --session-id abc123

# Get JSON output
empirica discover-goals --from-ai-id minimax --output json
```

**Output:**
```
🔍 Discovered 3 goal(s):

1. Goal ID: 7a3f2b1c...
   Created by: claude-code
   Session: abc123de...
   Objective: Implement rate limiting middleware
   Scope: {breadth: 0.5, duration: 0.4, coordination: 0.3}
   Lineage: 2 action(s)
     • claude-code - created at 2025-11-28
     • minimax - resumed at 2025-11-29

2. Goal ID: 9e4d8a2f...
   Created by: claude-code
   Session: def456gh...
   Objective: Refactor authentication system
   Scope: {breadth: 0.7, duration: 0.6, coordination: 0.5}

💡 To resume a goal, use:
   empirica resume-goal <goal-id> --ai-id <your-ai-id>
```

---

### `resume-goal` - Resume Another AI's Goal

**Syntax:**
```bash
empirica resume-goal <GOAL_ID> --ai-id <YOUR_AI_ID> [OPTIONS]
```

**Options:**
- `--ai-id <AI_ID>` - Your AI identifier (required)
- `--output json` - JSON output

**Examples:**
```bash
# Resume goal as minimax
empirica resume-goal 7a3f2b1c --ai-id minimax

# Resume with JSON output
empirica resume-goal 7a3f2b1c --ai-id gemini --output json
```

**Output:**
```
✅ Goal resumed successfully
   Goal ID: 7a3f2b1c...
   Original AI: claude-code
   Resuming as: minimax
   Objective: Implement rate limiting middleware

📊 Epistemic State from claude-code:
   • KNOW: 0.75
   • DO: 0.80
   • UNCERTAINTY: 0.35
   • CLARITY: 0.85

💡 Next steps:
   1. Review original AI's epistemic state
   2. Run your own preflight: empirica preflight "<task>" --ai-id minimax
   3. Compare your vectors with original AI's
```

---

## Python API

### Goal Discovery

```python
from empirica.core.canonical.empirica_git import GitGoalStore

goal_store = GitGoalStore()

# Discover goals from specific AI
goals = goal_store.discover_goals(from_ai_id="claude-code")

for goal_data in goals:
    print(f"Goal: {goal_data['goal_data']['objective']}")
    print(f"Created by: {goal_data['ai_id']}")
    print(f"Scope: {goal_data['goal_data']['scope']}")
    print(f"Lineage: {len(goal_data['lineage'])} actions")
    print()
```

### Goal Resumption

```python
from empirica.core.canonical.empirica_git import GitGoalStore
from empirica.core.goals.repository import GoalRepository

goal_store = GitGoalStore()
goal_repo = GoalRepository()

# Load goal from git
goal_id = "7a3f2b1c-..."
goal_data = goal_store.load_goal(goal_id)

if goal_data:
    # Add lineage entry
    goal_store.add_lineage(goal_id, ai_id="minimax", action="resumed")
    
    # Get epistemic handoff
    original_epistemic = goal_data.get('epistemic_state', {})
    print(f"Original AI's KNOW: {original_epistemic.get('know', 'N/A')}")
    print(f"Original AI's UNCERTAINTY: {original_epistemic.get('uncertainty', 'N/A')}")
    
    # Import into local database
    # goal_repo.import_goal(goal_data)
```

### Creating Goals with Git Storage

```python
from empirica.core.goals.types import Goal, ScopeVector, SuccessCriterion
from empirica.core.canonical.empirica_git import GitGoalStore
import uuid

# Create goal
scope = ScopeVector(breadth=0.5, duration=0.4, coordination=0.3)
criteria = [
    SuccessCriterion(
        id=str(uuid.uuid4()),
        description="Rate limiter implemented",
        validation_method="completion",
        is_required=True
    )
]

goal = Goal.create(
    objective="Implement rate limiting middleware",
    success_criteria=criteria,
    scope=scope
)

# Store in git notes
goal_store = GitGoalStore()
goal_store.store_goal(
    goal_id=goal.id,
    goal_data=goal.to_dict(),
    ai_id="claude-code",
    session_id="abc123",
    epistemic_state={
        'know': 0.75,
        'do': 0.80,
        'uncertainty': 0.35
    }
)

print(f"Goal stored in git notes: {goal.id}")
```

---

## MCP Tools

### `discover_goals`

**Purpose**: Find goals from other AIs

**Parameters:**
```python
{
    "from_ai_id": "claude-code",  # Optional
    "session_id": "abc123"        # Optional
}
```

**Returns:**
```python
{
    "ok": True,
    "count": 3,
    "goals": [
        {
            "goal_id": "7a3f2b1c...",
            "ai_id": "claude-code",
            "session_id": "abc123",
            "goal_data": {...},
            "epistemic_state": {...},
            "lineage": [...]
        },
        ...
    ]
}
```

### `resume_goal`

**Purpose**: Resume another AI's goal

**Parameters:**
```python
{
    "goal_id": "7a3f2b1c...",
    "ai_id": "minimax"
}
```

**Returns:**
```python
{
    "ok": True,
    "goal_id": "7a3f2b1c...",
    "ai_id": "minimax",
    "original_ai": "claude-code",
    "objective": "Implement rate limiting middleware",
    "epistemic_state": {...}
}
```

---

## Collaboration Patterns

### Pattern 1: Sequential Handoff

One AI starts, another continues:

```
Claude Code:
  1. Create goal with PREFLIGHT epistemic state
  2. Begin investigation
  3. Store progress in git notes

Minimax:
  1. Discover Claude's goal
  2. Resume with epistemic handoff
  3. Compare own PREFLIGHT with Claude's
  4. Continue work
  5. Update lineage
```

**Example:**
```bash
# Claude Code
empirica create-goal \
  --session-id session1 \
  --objective "Implement auth" \
  --scope '{"breadth": 0.6, "duration": 0.5, "coordination": 0.4}'

# Minimax (later)
empirica discover-goals --from-ai-id claude-code
empirica resume-goal <goal-id> --ai-id minimax
```

---

### Pattern 2: Parallel Collaboration

Multiple AIs work on related goals:

```
Claude Code: Authentication module (breadth=0.6)
Minimax: Authorization module (breadth=0.5)
Gemini: Session management (breadth=0.4)

All goals have coordination=0.7 (high coordination needed)
```

**Discovery:**
```bash
# Each AI discovers related goals
empirica discover-goals --from-ai-id claude-code
empirica discover-goals --from-ai-id minimax

# Check for overlaps and dependencies
```

---

### Pattern 3: Epistemic Comparison

Compare epistemic states across AIs:

```python
# AI 1's assessment
ai1_state = {
    'know': 0.60,
    'do': 0.70,
    'uncertainty': 0.50
}

# AI 2's assessment (after resuming)
ai2_state = {
    'know': 0.75,  # Higher - learned from AI 1's work
    'do': 0.80,
    'uncertainty': 0.30  # Lower - reduced by AI 1's investigation
}

# Epistemic delta
delta_know = ai2_state['know'] - ai1_state['know']  # +0.15
delta_uncertainty = ai2_state['uncertainty'] - ai1_state['uncertainty']  # -0.20

print(f"Knowledge gained from handoff: +{delta_know:.2f}")
print(f"Uncertainty reduced: {delta_uncertainty:.2f}")
```

---

### Pattern 4: Multi-Session Continuity

Resume work across sessions:

```
Session 1 (Claude Code):
  - PREFLIGHT: KNOW=0.60, UNCERTAINTY=0.60
  - INVESTIGATE: Research authentication patterns
  - Store goal in git notes

Session 2 (Claude Code, next day):
  - Resume own goal
  - PREFLIGHT: KNOW=0.75, UNCERTAINTY=0.35
  - Continue from where left off
```

**Commands:**
```bash
# Session 1
empirica create-goal --session-id session1 --objective "..."

# Session 2 (next day)
empirica discover-goals --from-ai-id claude-code
empirica resume-goal <goal-id> --ai-id claude-code
```

---

## Lineage Tracking

### Viewing Lineage

```python
goal_data = goal_store.load_goal(goal_id)

for entry in goal_data['lineage']:
    print(f"{entry['ai_id']} - {entry['action']} at {entry['timestamp']}")
    if 'epistemic_state' in entry:
        print(f"  KNOW: {entry['epistemic_state'].get('know', 'N/A')}")
        print(f"  UNCERTAINTY: {entry['epistemic_state'].get('uncertainty', 'N/A')}")
```

**Output:**
```
claude-code - created at 2025-11-28T10:00:00Z
  KNOW: 0.60
  UNCERTAINTY: 0.60

minimax - resumed at 2025-11-29T09:00:00Z
  KNOW: 0.75
  UNCERTAINTY: 0.35

claude-code - updated at 2025-11-29T15:00:00Z
  KNOW: 0.85
  UNCERTAINTY: 0.25
```

### Adding Lineage Entries

```python
goal_store.add_lineage(
    goal_id=goal_id,
    ai_id="gemini",
    action="completed",
    epistemic_state={
        'know': 0.90,
        'uncertainty': 0.15
    }
)
```

---

## Best Practices

### 1. Always Check for Existing Goals

Before creating a new goal, check if related work exists:

```bash
# Search for related goals
empirica discover-goals --from-ai-id claude-code

# Check if your goal already exists
# If similar goal found, resume instead of creating duplicate
```

### 2. Provide Rich Epistemic Context

When creating goals, include detailed epistemic state:

```python
goal_store.store_goal(
    goal_id=goal.id,
    goal_data=goal.to_dict(),
    ai_id="claude-code",
    session_id=session_id,
    epistemic_state={
        'know': 0.75,
        'do': 0.80,
        'context': 0.70,
        'clarity': 0.85,
        'uncertainty': 0.35,
        # Include all 13 vectors for complete handoff
    }
)
```

### 3. Compare Epistemic States

When resuming, compare your assessment with the original:

```python
original = goal_data['epistemic_state']
current = my_preflight_assessment

print(f"Knowledge delta: {current['know'] - original['know']:+.2f}")
print(f"Uncertainty delta: {current['uncertainty'] - original['uncertainty']:+.2f}")

if current['know'] < original['know']:
    print("⚠️  Warning: Lower knowledge than original AI - investigate first")
```

### 4. Update Lineage Regularly

Track significant actions:

```python
# When resuming
goal_store.add_lineage(goal_id, "minimax", "resumed")

# When making progress
goal_store.add_lineage(goal_id, "minimax", "updated")

# When completing
goal_store.add_lineage(goal_id, "minimax", "completed")
```

---

## Git Notes Storage

### Storage Location

Goals are stored in git notes under the `empirica/goals` namespace:

```bash
# View git notes
git notes --ref=empirica/goals list

# Show specific goal
git notes --ref=empirica/goals show <commit-sha>
```

### Syncing Across Machines

```bash
# Push goals to remote
git push origin refs/notes/empirica/goals

# Pull goals from remote
git fetch origin refs/notes/empirica/goals:refs/notes/empirica/goals
```

---

## Next Reading

- **MCO Architecture**: [24_MCO_ARCHITECTURE.md](file:///home/yogapad/empirical-ai/empirica/docs/production/24_MCO_ARCHITECTURE.md)
- **ScopeVector Guide**: [25_SCOPEVECTOR_GUIDE.md](file:///home/yogapad/empirical-ai/empirica/docs/production/25_SCOPEVECTOR_GUIDE.md)
- **Session Continuity**: [23_SESSION_CONTINUITY.md](file:///home/yogapad/empirical-ai/empirica/docs/production/23_SESSION_CONTINUITY.md)

---

**Cross-AI Coordination - Collaborative Intelligence at Scale** 🤝
