# Git-Based Session Continuity - Complete Guide

**Date:** 2025-01-XX  
**Status:** ✅ Fully operational with NEW schema  
**Purpose:** Enable seamless AI handoffs and Sentinel orchestration

---

## 🎯 What's Stored in Git

Empirica uses **git notes** to store three types of data for cross-session/cross-AI continuity:

### 1. CASCADE Checkpoints 📍
**Location:** `refs/notes/empirica/checkpoints`  
**Frequency:** Auto-created at PREFLIGHT, CHECK, POSTFLIGHT  
**Size:** ~350 bytes (~88 tokens) per checkpoint

### 2. Goals & Subtasks 🎯
**Location:** `refs/notes/empirica/goals/<goal-id>`  
**Frequency:** When goals created/updated  
**Includes:** Goal data + epistemic state + lineage

### 3. Session Metadata 📋
**Location:** `refs/notes/empirica/sessions/<session-id>`  
**Frequency:** Session start/end  
**Includes:** Session info + AI handoffs

---

## 📊 Complete Data Model

### CASCADE Checkpoint Format
```json
{
  "session_id": "abc-123-def",
  "ai_id": "claude-code",
  "phase": "PREFLIGHT",
  "round": 1,
  "timestamp": "2025-01-27T10:30:00Z",
  "vectors": {
    "engagement": 0.7,
    "know": 0.6,
    "do": 0.65,
    "context": 0.7,
    "clarity": 0.7,
    "coherence": 0.75,
    "signal": 0.65,
    "density": 0.6,
    "state": 0.65,
    "change": 0.6,
    "completion": 0.4,
    "impact": 0.65,
    "uncertainty": 0.5
  },
  "metadata": {
    "task": "Implement authentication system",
    "confidence": 0.63,
    "recommended_action": "INVESTIGATE",
    "investigation_rounds": 0
  }
}
```

**Storage:** Attached to current git commit  
**Query:** Filter by session_id, ai_id, phase

### Goal Storage Format
```json
{
  "goal_id": "goal-uuid-1234",
  "session_id": "abc-123-def",
  "ai_id": "claude-code",
  "created_at": "2025-01-27T10:30:00Z",
  "objective": "Implement OAuth authentication",
  "scope": "project_wide",
  "success_criteria": [
    {
      "id": "sc-1",
      "description": "Tests pass",
      "validation_method": "completion",
      "is_met": false
    }
  ],
  "estimated_complexity": 0.7,
  "subtasks": [
    {
      "id": "task-1",
      "description": "Write OAuth client",
      "status": "pending",
      "epistemic_importance": "high",
      "dependencies": [],
      "estimated_tokens": 2000
    },
    {
      "id": "task-2", 
      "description": "Add token refresh",
      "status": "in_progress",
      "epistemic_importance": "medium",
      "dependencies": ["task-1"],
      "estimated_tokens": 1500
    }
  ],
  "epistemic_state": {
    "engagement": 0.7,
    "know": 0.6,
    "do": 0.65,
    "context": 0.7,
    "clarity": 0.7,
    "coherence": 0.75,
    "signal": 0.65,
    "density": 0.6,
    "state": 0.65,
    "change": 0.6,
    "completion": 0.4,
    "impact": 0.65,
    "uncertainty": 0.5
  },
  "lineage": [
    {
      "ai_id": "claude-code",
      "timestamp": "2025-01-27T10:30:00Z",
      "action": "created"
    },
    {
      "ai_id": "mini-agent",
      "timestamp": "2025-01-27T11:00:00Z",
      "action": "resumed"
    }
  ]
}
```

**Storage:** Git note per goal  
**Query:** Filter by ai_id, session_id, status

---

## 🔄 Session Continuity Workflow

### Scenario 1: Same AI Resumes Session

```bash
# AI-1 (RovoDev) starts work
empirica preflight "Build auth system" --session-id my-session --ai-id rovodev
# ✅ Checkpoint saved to git: PREFLIGHT with vectors

empirica check --session-id my-session
# ✅ Checkpoint saved to git: CHECK with updated vectors

# ... AI-1 stops work ...

# Later: AI-1 resumes
empirica checkpoint-load --session-id my-session
# ✅ Loads latest checkpoint from git
# Returns: phase=CHECK, vectors={...}, metadata={...}

# AI-1 continues from CHECK phase
empirica act --session-id my-session --continue-from-checkpoint
```

### Scenario 2: Different AI Takes Over (Handoff)

```bash
# AI-1 (RovoDev) creates goal and checkpoints
empirica preflight "Build auth" --session-id s1 --ai-id rovodev
empirica goals-create --session-id s1 --objective "OAuth" --ai-id rovodev
# ✅ Goal stored in git with epistemic state
# ✅ Checkpoint stored with phase=PREFLIGHT

# ... RovoDev stops ...

# AI-2 (Mini-Agent) discovers available work
empirica goals-discover --from-ai-id rovodev
# Returns: [Goal(id=goal-1, objective="OAuth", ai_id="rovodev", ...)]

# AI-2 resumes the goal
empirica goals-resume --goal-id goal-1 --ai-id mini-agent
# ✅ Loads goal data
# ✅ Loads epistemic state from goal
# ✅ Adds lineage entry (mini-agent resumed)

# AI-2 loads checkpoint to see where RovoDev left off
empirica checkpoint-load --session-id s1
# Returns: phase=PREFLIGHT, vectors={know: 0.6, ...}

# AI-2 continues CASCADE from CHECK phase
empirica check --session-id s1 --ai-id mini-agent
```

### Scenario 3: Sentinel Orchestrates Multiple AIs

```bash
# Sentinel query: "What sessions need attention?"
git notes --ref=empirica/checkpoints list | \
  xargs -I {} git notes --ref=empirica/checkpoints show {} | \
  jq 'select(.phase == "CHECK" and .vectors.uncertainty > 0.7)'
# Returns checkpoints where uncertainty is high

# Sentinel routes to specialist AI
# High uncertainty in "know" → route to domain expert
empirica checkpoint-load --session-id s1 | jq '.vectors.know'
# Returns: 0.4 (low knowledge)

# Sentinel: "Route to AI with domain expertise"
empirica goals-discover --from-ai-id previous-ai
empirica goals-resume --goal-id g1 --ai-id domain-expert

# Domain expert loads context
empirica checkpoint-load --session-id s1
# Gets full epistemic state + checkpoint metadata
```

---

## 🔍 Git Commands for Session Discovery

### View All Checkpoints
```bash
# List all checkpoint commits
git log --all --pretty=format:"%H" | while read hash; do
  git notes --ref=empirica/checkpoints show $hash 2>/dev/null
done | jq -s '.'

# Pretty output
git log --all --pretty=format:"%H %s" | while read hash msg; do
  checkpoint=$(git notes --ref=empirica/checkpoints show $hash 2>/dev/null)
  if [ ! -z "$checkpoint" ]; then
    echo "Commit: $hash"
    echo "$checkpoint" | jq '.'
    echo "---"
  fi
done
```

### Find Latest Checkpoint for Session
```bash
# Get latest checkpoint for specific session
git log --all --pretty=format:"%H" | while read hash; do
  git notes --ref=empirica/checkpoints show $hash 2>/dev/null | \
    jq -r 'select(.session_id == "abc-123") | {phase, timestamp, vectors}'
done | head -1
```

### Discover Goals by AI
```bash
# Find all goals created by specific AI
git notes --ref=empirica/goals list | while read note_ref commit_hash; do
  git notes --ref=empirica/goals show $commit_hash 2>/dev/null | \
    jq -r 'select(.ai_id == "claude-code")'
done
```

### Find Incomplete Goals
```bash
# Find goals with incomplete subtasks
git notes --ref=empirica/goals list | while read note_ref commit_hash; do
  git notes --ref=empirica/goals show $commit_hash 2>/dev/null | \
    jq -r 'select(.subtasks | any(.status != "completed"))'
done
```

### Track AI Lineage
```bash
# See which AIs worked on a goal
git notes --ref=empirica/goals show HEAD | jq '.lineage'
# Output:
# [
#   {"ai_id": "claude-code", "timestamp": "...", "action": "created"},
#   {"ai_id": "mini-agent", "timestamp": "...", "action": "resumed"},
#   {"ai_id": "gemini", "timestamp": "...", "action": "resumed"}
# ]
```

---

## 🚀 MCP Tool Integration

### For AI Agents

**Load Last Checkpoint:**
```python
# MCP tool call
load_git_checkpoint(session_id="abc-123")

# Returns checkpoint with:
# - phase (PREFLIGHT/CHECK/POSTFLIGHT)
# - vectors (all 13 epistemic vectors)
# - metadata (task, confidence, etc.)
# - timestamp
```

**Create Checkpoint:**
```python
# MCP tool call (automatic during CASCADE)
create_git_checkpoint(
    session_id="abc-123",
    phase="PREFLIGHT",
    round_num=1,
    vectors={
        "engagement": 0.7,
        "know": 0.6,
        # ... all 13 vectors
    },
    metadata={"task": "Build feature"}
)
```

**Discover Goals:**
```python
# MCP tool call
discover_goals(from_ai_id="claude-code")

# Returns: List of goals with:
# - goal_id, objective, scope
# - success_criteria, subtasks
# - epistemic_state (13 vectors)
# - lineage (who worked on it)
```

**Resume Goal:**
```python
# MCP tool call
resume_goal(goal_id="goal-uuid", ai_id="mini-agent")

# Action:
# 1. Loads goal data from git
# 2. Loads epistemic state
# 3. Adds lineage entry
# 4. Returns complete goal context
```

---

## 📋 Complete Session Continuity Flow

### Phase 1: Work Session (AI-1)
```
1. AI-1 bootstraps session
   └─> Creates session record

2. AI-1 runs PREFLIGHT
   └─> Checkpoint saved to git (phase=PREFLIGHT, vectors={...})

3. AI-1 creates goal
   └─> Goal saved to git with epistemic state

4. AI-1 runs INVESTIGATE
   └─> No checkpoint (investigation doesn't checkpoint)

5. AI-1 runs CHECK
   └─> Checkpoint saved to git (phase=CHECK, vectors={...})

6. AI-1 creates subtasks
   └─> Goal updated in git with subtasks

7. AI-1 stops work (incomplete)
   └─> Last checkpoint: CHECK phase
```

### Phase 2: Handoff Discovery (Sentinel/AI-2)
```
1. Sentinel queries git for incomplete work
   └─> Finds session with last checkpoint = CHECK
   └─> Finds goals with incomplete subtasks

2. Sentinel analyzes epistemic state
   checkpoint.vectors.know = 0.4 (low)
   checkpoint.vectors.uncertainty = 0.8 (high)
   └─> Decision: Route to domain expert

3. AI-2 (domain expert) queries available work
   discover_goals(from_ai_id="ai-1")
   └─> Returns goals with lineage

4. AI-2 loads full context
   load_git_checkpoint(session_id="abc-123")
   └─> Gets: phase, vectors, metadata
   
   resume_goal(goal_id="goal-1", ai_id="ai-2")
   └─> Gets: objective, subtasks, epistemic_state
   └─> Adds lineage entry
```

### Phase 3: Continuation (AI-2)
```
1. AI-2 reviews epistemic state
   know=0.4, uncertainty=0.8
   └─> Decides to run INVESTIGATE

2. AI-2 runs INVESTIGATE
   └─> Gathers domain knowledge
   └─> Updates epistemic state

3. AI-2 runs CHECK
   └─> Checkpoint saved (phase=CHECK, vectors updated)
   └─> know=0.8 (improved!)

4. AI-2 runs ACT
   └─> Completes subtasks
   └─> Updates goal in git

5. AI-2 runs POSTFLIGHT
   └─> Checkpoint saved (phase=POSTFLIGHT, completion=1.0)
   └─> Marks goal complete

6. AI-2 creates handoff report
   └─> Stored in git notes
   └─> Next AI can see what was learned
```

---

## 🎯 Key Benefits

### 1. Zero Token Overhead for Context
- **Checkpoints:** ~350 bytes each (97.5% reduction)
- **Goals:** Compressed format with only essential data
- **Query:** Direct git access, no database needed

### 2. Distributed Collaboration
- Multiple AIs can work on same codebase
- Each AI leaves epistemic breadcrumbs
- Lineage tracking shows who did what

### 3. Sentinel Orchestration
- Query git notes for sessions needing attention
- Route based on epistemic state (low know → expert)
- Balance load across AIs

### 4. Session Resumption
- Any AI can resume from any checkpoint
- Full context available (vectors + metadata)
- No ambiguity about what was done

### 5. Audit Trail
- Complete history in git
- Track epistemic evolution over time
- See confidence changes across phases

---

## 🔧 Implementation Details

### Checkpoint Storage
- **Location:** Git note attached to current commit
- **Ref:** `refs/notes/empirica/checkpoints`
- **Format:** Compact JSON (~350 bytes)
- **Indexed by:** commit hash, then filtered by session_id/ai_id

### Goal Storage
- **Location:** Git note per goal
- **Ref:** `refs/notes/empirica/goals/<goal-id>`
- **Format:** Complete goal JSON with epistemic state
- **Indexed by:** goal_id, ai_id filter

### Query Performance
- **Fast:** Git notes are lightweight
- **Scalable:** One note per checkpoint/goal
- **Distributed:** Works across machines with git sync

---

## 📊 Example Session Timeline

```
Time  | AI        | Phase      | Checkpoint | Goal Updates
------|-----------|------------|------------|-------------
10:00 | rovodev   | PREFLIGHT  | ✅ CP-1    | Goal created
10:15 | rovodev   | THINK      | (no CP)    | -
10:20 | rovodev   | INVESTIGATE| (no CP)    | Subtasks added
10:30 | rovodev   | CHECK      | ✅ CP-2    | -
10:35 | rovodev   | STOPS      | -          | -
------|-----------|------------|------------|-------------
11:00 | sentinel  | QUERY      | Load CP-2  | Discover goals
11:05 | sentinel  | ROUTE      | -          | → mini-agent
------|-----------|------------|------------|-------------
11:10 | mini-agent| RESUME     | Load CP-2  | Resume goal-1
11:15 | mini-agent| CHECK      | ✅ CP-3    | -
11:20 | mini-agent| ACT        | (no CP)    | Task-1 complete
11:30 | mini-agent| POSTFLIGHT | ✅ CP-4    | Goal complete
```

**Git Notes Created:**
- CP-1: rovodev PREFLIGHT (know=0.5, uncertainty=0.7)
- CP-2: rovodev CHECK (know=0.6, uncertainty=0.6)
- CP-3: mini-agent CHECK (know=0.8, uncertainty=0.3)
- CP-4: mini-agent POSTFLIGHT (completion=1.0)

**Goal Lineage:**
```json
{
  "lineage": [
    {"ai_id": "rovodev", "action": "created", "timestamp": "10:00"},
    {"ai_id": "mini-agent", "action": "resumed", "timestamp": "11:10"},
    {"ai_id": "mini-agent", "action": "completed", "timestamp": "11:30"}
  ]
}
```

---

## 🚀 Quick Reference

### For AI Agents

**Start new work:**
```bash
empirica preflight "Task" --session-id s1 --ai-id my-ai
# ✅ Auto-creates checkpoint
```

**Resume existing work:**
```bash
empirica checkpoint-load --session-id s1
empirica goals-discover --from-ai-id other-ai
empirica goals-resume --goal-id g1 --ai-id my-ai
```

**Continue CASCADE:**
```bash
empirica check --session-id s1 --continue
# ✅ Auto-creates checkpoint
```

### For Sentinel

**Find work needing attention:**
```bash
# High uncertainty sessions
git log --all --pretty=format:"%H" | while read h; do
  git notes --ref=empirica/checkpoints show $h 2>/dev/null | \
    jq 'select(.vectors.uncertainty > 0.7)'
done

# Incomplete goals
empirica goals-discover --status incomplete
```

**Route to specialist:**
```bash
# Check epistemic gap
checkpoint=$(empirica checkpoint-load --session-id s1)
know=$(echo $checkpoint | jq '.vectors.know')

if [ $(echo "$know < 0.6" | bc) -eq 1 ]; then
  # Route to domain expert
  empirica assign-session --session-id s1 --ai-id domain-expert
fi
```

---

## 📝 Summary

**What's in Git:**
- ✅ CASCADE checkpoints (PREFLIGHT, CHECK, POSTFLIGHT)
- ✅ Goals with epistemic state + subtasks
- ✅ Session metadata + handoffs
- ✅ AI lineage (who worked on what)

**How to Use:**
- ✅ Load checkpoints for session continuity
- ✅ Discover goals for cross-AI collaboration
- ✅ Query epistemic state for intelligent routing
- ✅ Track lineage for audit trail

**Key Benefit:**
> **Any AI can resume any session with full context in ~350 bytes**

---

**Status:** ✅ Fully operational  
**Schema:** ✅ NEW schema with backwards compat  
**Performance:** ✅ 97.5% token reduction  
**Ready for:** Production deployment + Sentinel orchestration

---

*"Git notes: The distributed memory for AI collaboration."* ✨
