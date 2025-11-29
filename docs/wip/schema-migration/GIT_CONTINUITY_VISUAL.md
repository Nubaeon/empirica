# Git Session Continuity - Visual Guide

**Date:** 2025-01-XX  
**Purpose:** Visual reference for git-based AI collaboration

---

## 🗺️ Complete Storage Map

```
Git Repository
│
├── Code Changes (normal git commits)
│   └── Your actual code
│
└── Git Notes (Empirica metadata)
    │
    ├── refs/notes/empirica/checkpoints
    │   │   (Attached to each commit)
    │   │
    │   ├── Commit abc123
    │   │   └── Checkpoint {session: s1, ai: rovodev, phase: PREFLIGHT, vectors: {...}}
    │   │
    │   ├── Commit def456
    │   │   └── Checkpoint {session: s1, ai: rovodev, phase: CHECK, vectors: {...}}
    │   │
    │   └── Commit ghi789
    │       └── Checkpoint {session: s2, ai: mini-agent, phase: POSTFLIGHT, vectors: {...}}
    │
    ├── refs/notes/empirica/goals/<goal-id>
    │   │
    │   ├── goal-uuid-1
    │   │   └── {objective: "Auth", ai: rovodev, subtasks: [...], epistemic: {...}, lineage: [...]}
    │   │
    │   └── goal-uuid-2
    │       └── {objective: "API", ai: mini-agent, subtasks: [...], epistemic: {...}, lineage: [...]}
    │
    └── refs/notes/empirica/sessions/<session-id>
        │
        ├── session-abc-123
        │   └── {ai_id: rovodev, started: "10:00", status: "active"}
        │
        └── session-def-456
            └── {ai_id: mini-agent, started: "11:00", status: "complete"}
```

---

## 📊 Data Flow: Single AI Session

```
┌─────────────────────────────────────────────────────────────────┐
│ AI-1 (RovoDev) Working Session                                  │
└─────────────────────────────────────────────────────────────────┘

Step 1: BOOTSTRAP
├─> Creates session record
└─> git notes: refs/notes/empirica/sessions/s1

Step 2: PREFLIGHT
├─> Runs epistemic assessment
│   vectors: {engagement: 0.7, know: 0.6, clarity: 0.7, ...}
└─> ✅ CHECKPOINT created
    └─> git notes: refs/notes/empirica/checkpoints (on HEAD)
        {session: s1, ai: rovodev, phase: PREFLIGHT, vectors: {...}}

Step 3: CREATE GOAL
├─> Defines objective: "Implement OAuth"
├─> Creates subtasks
└─> ✅ GOAL stored
    └─> git notes: refs/notes/empirica/goals/goal-1
        {
          objective: "OAuth",
          subtasks: [{id: t1, desc: "Client"}, {id: t2, desc: "Refresh"}],
          epistemic_state: {know: 0.6, clarity: 0.7, ...},
          lineage: [{ai: rovodev, action: created}]
        }

Step 4: INVESTIGATE (no checkpoint - just work)

Step 5: CHECK
├─> Runs epistemic assessment
│   vectors: {know: 0.75, uncertainty: 0.4, ...} [improved!]
└─> ✅ CHECKPOINT created
    └─> git notes: refs/notes/empirica/checkpoints (on HEAD)
        {session: s1, ai: rovodev, phase: CHECK, vectors: {...}}

Step 6: AI-1 STOPS WORK
└─> Last checkpoint: CHECK phase with vectors
```

---

## 🔄 Data Flow: Cross-AI Handoff

```
┌─────────────────────────────────────────────────────────────────┐
│ Sentinel Discovers Work + AI-2 Resumes                          │
└─────────────────────────────────────────────────────────────────┘

DISCOVERY PHASE:
─────────────────

Sentinel queries git:
├─> git notes --ref=empirica/checkpoints list
│   └─> Finds: session s1, last checkpoint = CHECK
│
├─> git notes --ref=empirica/goals list
│   └─> Finds: goal-1 with incomplete subtasks
│
└─> Analyzes epistemic state from checkpoint:
    ├─> know: 0.6 (moderate)
    ├─> uncertainty: 0.7 (high)
    └─> Decision: Route to domain expert (AI-2)

HANDOFF EXECUTION:
──────────────────

AI-2 (Mini-Agent) starts:

Step 1: DISCOVER GOALS
├─> MCP tool: discover_goals(from_ai_id="rovodev")
└─> Returns: [goal-1: OAuth, subtasks, epistemic_state]

Step 2: LOAD CHECKPOINT
├─> MCP tool: load_git_checkpoint(session_id="s1")
└─> Returns: {
      phase: CHECK,
      vectors: {know: 0.6, uncertainty: 0.7, ...},
      metadata: {task: "OAuth", confidence: 0.63}
    }

Step 3: RESUME GOAL
├─> MCP tool: resume_goal(goal_id="goal-1", ai_id="mini-agent")
└─> Action:
    ├─> Loads goal data from git
    ├─> Adds lineage entry: {ai: mini-agent, action: resumed, timestamp: now}
    └─> Updates git note with new lineage

Step 4: CONTINUE CASCADE
├─> AI-2 runs CHECK (with better domain knowledge)
│   vectors: {know: 0.85, uncertainty: 0.3, ...} [improved!]
└─> ✅ CHECKPOINT created
    └─> git notes: refs/notes/empirica/checkpoints (on HEAD)
        {session: s1, ai: mini-agent, phase: CHECK, vectors: {...}}

Step 5: COMPLETE WORK
├─> AI-2 runs ACT + POSTFLIGHT
├─> Updates goal: subtasks complete
└─> ✅ CHECKPOINT created
    └─> git notes: refs/notes/empirica/checkpoints (on HEAD)
        {session: s1, ai: mini-agent, phase: POSTFLIGHT, completion: 1.0}
```

---

## 📈 Epistemic State Evolution (Visualized)

```
Timeline: OAuth Implementation

10:00 | RovoDev PREFLIGHT
      | know: ▂▂▂▂▂▂░░░░ 0.6  (moderate domain knowledge)
      | uncertainty: ▂▂▂▂▂▂▂░░░ 0.7  (high uncertainty)
      | ✅ Checkpoint created
      |
10:30 | RovoDev CHECK (after investigation)
      | know: ▂▂▂▂▂▂▂░░░ 0.7  (improved slightly)
      | uncertainty: ▂▂▂▂▂▂░░░░ 0.6  (reduced slightly)
      | ✅ Checkpoint created
      | 🛑 RovoDev stops work
      |
      | --- HANDOFF via git notes ---
      |
11:00 | Sentinel queries git
      | Finds: uncertainty still high (0.6)
      | Decision: Route to domain expert
      |
11:10 | Mini-Agent loads checkpoint
      | Sees: know=0.7, uncertainty=0.6
      | Decision: Run INVESTIGATE with domain focus
      |
11:20 | Mini-Agent CHECK (after deep investigation)
      | know: ▂▂▂▂▂▂▂▂▂░ 0.85  (strong domain knowledge!)
      | uncertainty: ▂▂▂░░░░░░░ 0.3  (low uncertainty!)
      | ✅ Checkpoint created
      |
11:30 | Mini-Agent POSTFLIGHT
      | completion: ▂▂▂▂▂▂▂▂▂▂ 1.0  (complete!)
      | ✅ Checkpoint created
      |
Result: Successful handoff, knowledge improved, task complete
```

---

## 🎯 Query Patterns

### Pattern 1: Find High-Uncertainty Sessions

```bash
# Sentinel queries for sessions needing help
git log --all --pretty=format:"%H" | while read hash; do
  git notes --ref=empirica/checkpoints show $hash 2>/dev/null
done | jq 'select(.vectors.uncertainty > 0.7) | {session_id, ai_id, phase, uncertainty: .vectors.uncertainty}'

# Output:
# {
#   "session_id": "s1",
#   "ai_id": "rovodev",
#   "phase": "CHECK",
#   "uncertainty": 0.7
# }
```

### Pattern 2: Find Work by Specific AI

```bash
# Discover goals created by RovoDev
empirica goals-discover --from-ai-id rovodev

# Or via git:
git notes --ref=empirica/goals list | while read note commit; do
  git notes --ref=empirica/goals show $commit 2>/dev/null
done | jq 'select(.ai_id == "rovodev")'

# Output: All goals with their subtasks and epistemic state
```

### Pattern 3: Track Goal Lineage

```bash
# See who worked on a goal
git notes --ref=empirica/goals show HEAD | jq '.lineage'

# Output:
# [
#   {"ai_id": "rovodev", "action": "created", "timestamp": "10:00"},
#   {"ai_id": "mini-agent", "action": "resumed", "timestamp": "11:10"},
#   {"ai_id": "mini-agent", "action": "completed", "timestamp": "11:30"}
# ]
```

---

## 🔍 MCP Tool Usage Examples

### Example 1: AI Resumes Previous Session

```python
# AI boots up, checks for previous work
session_id = "abc-123"

# Load last checkpoint
checkpoint = load_git_checkpoint(session_id=session_id)
# Returns: {
#   phase: "CHECK",
#   vectors: {know: 0.6, uncertainty: 0.7, ...},
#   metadata: {...}
# }

# Analyze epistemic state
if checkpoint['vectors']['uncertainty'] > 0.7:
    print("High uncertainty - need INVESTIGATE")
else:
    print("Ready to ACT")

# Continue from checkpoint
continue_cascade(session_id=session_id, from_phase=checkpoint['phase'])
```

### Example 2: AI Discovers Available Goals

```python
# AI checks for work from other AIs
goals = discover_goals(from_ai_id="rovodev")
# Returns: [
#   {
#     goal_id: "g1",
#     objective: "OAuth",
#     subtasks: [{status: "pending"}, {status: "in_progress"}],
#     epistemic_state: {know: 0.6, ...}
#   }
# ]

# Pick incomplete goal
incomplete_goals = [g for g in goals if any(t['status'] != 'completed' for t in g['subtasks'])]

if incomplete_goals:
    goal = incomplete_goals[0]
    
    # Resume the goal
    resume_goal(goal_id=goal['goal_id'], ai_id="mini-agent")
    # Action: Adds lineage entry, returns full context
    
    # Load associated checkpoint
    checkpoint = load_git_checkpoint(session_id=goal['session_id'])
    
    # Continue work with full context
    print(f"Resuming: {goal['objective']}")
    print(f"Epistemic state: know={goal['epistemic_state']['know']}")
    print(f"Last phase: {checkpoint['phase']}")
```

### Example 3: Sentinel Routes Based on Epistemic Gaps

```python
# Sentinel analyzes all active sessions
sessions = list_active_sessions()

for session in sessions:
    checkpoint = load_git_checkpoint(session_id=session['id'])
    
    # Epistemic gap analysis
    know = checkpoint['vectors']['know']
    uncertainty = checkpoint['vectors']['uncertainty']
    
    # Route logic
    if know < 0.6 and uncertainty > 0.7:
        # Low knowledge, high uncertainty → domain expert
        assign_session(
            session_id=session['id'],
            ai_id="domain-expert",
            reason="Epistemic gap: need domain knowledge"
        )
    elif checkpoint['phase'] == "ACT" and checkpoint['vectors']['do'] < 0.6:
        # Ready to act but low capability → specialist
        assign_session(
            session_id=session['id'],
            ai_id="implementation-specialist",
            reason="Need implementation expertise"
        )
```

---

## 💡 Key Insights

### 1. Checkpoints = Breadcrumbs
Every CASCADE phase leaves a checkpoint:
- **PREFLIGHT** → Initial epistemic state
- **CHECK** → Post-investigation state
- **POSTFLIGHT** → Final state + learning deltas

### 2. Goals = Work Contracts
Goals stored in git are like work tickets:
- Objective + success criteria
- Subtasks (pending/in-progress/complete)
- Epistemic state when created
- Lineage of who worked on it

### 3. Git Notes = Distributed Memory
- No central database needed
- Works across machines (git sync)
- Queryable with standard git commands
- ~350 bytes per checkpoint (97.5% token reduction)

### 4. Lineage = Audit Trail
Every goal tracks:
- Who created it
- Who resumed it
- Who completed it
- When each action happened

### 5. Epistemic State = Routing Signal
Sentinel uses vectors to route work:
- Low `know` → domain expert
- High `uncertainty` → investigator
- Low `do` → implementation specialist
- High `completion` → reviewer

---

## 🚀 Quick Commands

### For AI Agents
```bash
# Start work
empirica preflight "Task" --session-id s1 --ai-id my-ai

# Resume work
empirica checkpoint-load --session-id s1
empirica goals-discover --from-ai-id other-ai

# Continue CASCADE
empirica check --session-id s1 --continue
```

### For Sentinel
```bash
# Find work needing attention
empirica sessions-list --status active --high-uncertainty

# Route to specialist
empirica assign-session --session-id s1 --ai-id specialist
```

### For Debugging
```bash
# View checkpoint
git notes --ref=empirica/checkpoints show HEAD | jq '.'

# View goal
git notes --ref=empirica/goals show HEAD | jq '.'

# Search sessions
git log --all --pretty=format:"%H" | while read h; do
  git notes --ref=empirica/checkpoints show $h 2>/dev/null
done | jq -s 'group_by(.session_id)'
```

---

## 📊 Summary Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     GIT REPOSITORY                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Code: Normal git commits with your changes                     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Git Notes: Empirica Metadata                               │ │
│  ├────────────────────────────────────────────────────────────┤ │
│  │                                                            │ │
│  │  📍 Checkpoints (refs/notes/empirica/checkpoints)          │ │
│  │     - PREFLIGHT: Initial epistemic state                  │ │
│  │     - CHECK: Post-investigation state                     │ │
│  │     - POSTFLIGHT: Final state + deltas                    │ │
│  │     Size: ~350 bytes each                                 │ │
│  │                                                            │ │
│  │  🎯 Goals (refs/notes/empirica/goals/<id>)                 │ │
│  │     - Objective + success criteria                        │ │
│  │     - Subtasks (with status)                              │ │
│  │     - Epistemic state snapshot                            │ │
│  │     - Lineage (AI collaboration trail)                    │ │
│  │                                                            │ │
│  │  📋 Sessions (refs/notes/empirica/sessions/<id>)           │ │
│  │     - Session metadata                                    │ │
│  │     - AI handoffs                                         │ │
│  │                                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
          ▲                                    │
          │                                    │
          │ Query/Load                         │ Store
          │                                    ▼
┌─────────┴────────────┐         ┌──────────────────────┐
│  AI Agent            │         │  Sentinel            │
│  - Load checkpoints  │◄────────┤  - Query all work    │
│  - Resume goals      │         │  - Route by vectors  │
│  - Continue CASCADE  │         │  - Balance load      │
└──────────────────────┘         └──────────────────────┘
```

---

**Status:** ✅ Fully operational  
**Documentation:** Complete  
**Ready for:** Multi-AI collaboration + Sentinel orchestration

---

*"Git notes: Because context should persist, not perish."* ✨
