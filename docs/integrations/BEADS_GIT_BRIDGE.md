# BEADS-Git Bridge: Linking Issues to Branches

**Status:** Design Phase (Phase 3 of BEADS Integration)

---

## The Problem

**Current gap:**
- BEADS tracks issue dependencies (what's unblocked)
- Empirica tracks epistemic state (what you know)
- Git branches exist independently
- **No automatic linkage between BEADS issues and git branches**

**What should happen:**
When an AI starts work on a BEADS issue, it should:
1. Create appropriate git branch (`epistemic/reasoning/issue-empirica-05j`)
2. Link branch to BEADS issue in mapping file
3. Track epistemic progress on that branch
4. Merge when issue closed

---

## Proposed Solution: goals-claim Command

### New Commands

#### 1. `empirica goals-claim`

**Purpose:** Start work on a goal, creating branch and linking to BEADS

**Usage:**
```bash
empirica goals-claim --goal-id <GOAL_ID> [--create-branch] [--run-preflight]
```

**What it does:**
1. Gets BEADS issue ID from goal
2. Updates BEADS status to `in_progress`
3. Creates branch: `epistemic/reasoning/issue-empirica-05j`
4. Checks out branch
5. Creates mapping in `.empirica/branch_mapping.json`
6. Optionally runs PREFLIGHT

**Example:**
```bash
$ empirica goals-ready --session-id sess-123
🎯 Ready Work (2 tasks):
1. [empirica-05j] Final test BEADS integration (fitness: 0.85)
2. [empirica-06k] Add unit tests (fitness: 0.78)

$ empirica goals-claim --goal-id de7ae57c --create-branch --run-preflight
✅ Claimed goal: de7ae57c
✅ Updated BEADS status: in_progress
✅ Created branch: epistemic/reasoning/issue-empirica-05j
✅ Branch mapping saved
🧠 Running PREFLIGHT...
   know: 0.8, uncertainty: 0.3
✅ Ready to start work!
```

#### 2. `empirica goals-complete`

**Purpose:** Finish work on a goal, merge branch, close BEADS issue

**Usage:**
```bash
empirica goals-complete --goal-id <GOAL_ID> [--run-postflight] [--merge-branch]
```

**What it does:**
1. Runs POSTFLIGHT (if flagged)
2. Closes BEADS issue with reason
3. Merges branch to main (if flagged)
4. Cleans up branch mapping
5. Creates handoff report

**Example:**
```bash
$ empirica goals-complete --goal-id de7ae57c --run-postflight --merge-branch
🧠 Running POSTFLIGHT...
   know: 0.9, uncertainty: 0.1
   Learning delta: know +0.1, uncertainty -0.2
✅ Closed BEADS issue: empirica-05j
✅ Merged branch: epistemic/reasoning/issue-empirica-05j → main
✅ Branch mapping cleaned up
📦 Handoff created: 378 tokens
```

---

## Branch Naming Convention

### Single AI Work

**Pattern:** `epistemic/<layer>/issue-<beads-id>`

**Examples:**
```
epistemic/reasoning/issue-empirica-05j
epistemic/acting/issue-empirica-06k
```

### Multi-AI Coordination

**Pattern:** `epistemic/<layer>/ai-<ai-id>/issue-<beads-id>`

**Examples:**
```
epistemic/reasoning/ai-rovodev/issue-empirica-05j
epistemic/acting/ai-copilot/issue-empirica-06k
```

### Subtasks

**Pattern:** `epistemic/<layer>/issue-<beads-id>.<subtask-num>`

**Examples:**
```
epistemic/reasoning/issue-empirica-05j.1  (subtask 1)
epistemic/reasoning/issue-empirica-05j.2  (subtask 2)
```

---

## Branch Mapping File

**Location:** `.empirica/branch_mapping.json`

**Purpose:** Track which BEADS issues are linked to which branches

**Schema:**
```json
{
  "mappings": {
    "empirica-05j": {
      "branch": "epistemic/reasoning/issue-empirica-05j",
      "goal_id": "de7ae57c-5c19-40e3-8037-735cca61a314",
      "beads_issue_id": "empirica-05j",
      "session_id": "3fcd4a42-a55d-4dcc-8d5f-bba42aa4ecc8",
      "ai_id": "rovodev",
      "started_at": "2025-12-13T10:30:00Z",
      "status": "in_progress",
      "preflight_vectors": {
        "know": 0.8,
        "uncertainty": 0.3
      }
    }
  }
}
```

**Features:**
- Quick lookup: BEADS issue → git branch
- Reverse lookup: git branch → BEADS issue
- Session tracking: which session owns which branch
- Multi-AI awareness: who's working on what
- Epistemic state: PREFLIGHT vectors for context

---

## Sentinel Integration

**Sentinel monitors branches:**

```python
# Sentinel watches git log for epistemic/* branches
def watch_branches():
    branches = git.branch('--list', 'epistemic/*')
    
    for branch in branches:
        # Get BEADS issue from branch name
        issue_id = extract_issue_id(branch)
        
        # Get branch mapping
        mapping = load_branch_mapping(issue_id)
        
        # Check epistemic progress
        latest_commit = git.log(branch, '-1')
        vectors = extract_vectors_from_commit(latest_commit)
        
        # Decision logic
        if vectors['confidence'] >= 0.8:
            sentinel.suggest_merge(branch)
        elif is_stale(branch, days=7):
            sentinel.flag_abandoned(branch)
        elif has_conflicts(branch):
            sentinel.request_resolution(branch)
```

**Actions Sentinel can take:**
- Suggest merge when confidence high
- Flag abandoned branches (stale work)
- Detect conflicts early
- Route work to capable AIs
- Clean up completed branches

---

## Implementation Plan

### Phase 3a: Basic Commands (Now)

**Priority: HIGH**

1. Create `empirica goals-claim` command
   - Update BEADS status
   - Create git branch
   - Save branch mapping
   - Checkout branch

2. Create `empirica goals-complete` command
   - Close BEADS issue
   - Merge branch (optional)
   - Clean up mapping

3. Update `goals-ready` to show branch info
   - Display current branch for in-progress goals
   - Show which AI owns which branch

**Files to modify:**
- `empirica/cli/command_handlers/goal_commands.py` (add new commands)
- `empirica/cli/cli_core.py` (register commands)
- `empirica/integrations/beads/adapter.py` (branch management methods)

### Phase 3b: Sentinel Monitoring (Future)

**Priority: MEDIUM**

1. Sentinel branch watcher
   - Monitor epistemic/* branches
   - Track progress via commits
   - Suggest actions

2. BEADS hooks
   - Auto-create branches on status change
   - Sync BEADS and git state

3. Multi-AI coordination
   - Detect branch conflicts
   - Suggest handoffs
   - Auto-merge when safe

---

## Example Workflow

### Full End-to-End

```bash
# 1. Find ready work
$ empirica goals-ready --session-id sess-123
🎯 Ready Work:
1. [empirica-05j] Implement OAuth2 (fitness: 0.85)
2. [empirica-06k] Add unit tests (fitness: 0.78)

# 2. Claim task
$ empirica goals-claim --goal-id abc123 --create-branch --run-preflight
✅ Claimed: Implement OAuth2
✅ Branch created: epistemic/reasoning/issue-empirica-05j
🧠 PREFLIGHT: know=0.7, uncertainty=0.4

# 3. Work on branch (automatic - you're already checked out)
$ git commit -m "Add OAuth2 client implementation"
$ git commit -m "Add token refresh logic"

# 4. Check progress (optional)
$ empirica check --session-id sess-123 \
  --findings '["OAuth2 client works", "Token refresh implemented"]' \
  --confidence 0.85
✅ CHECK: Ready to proceed (confidence: 0.85)

# 5. Complete work
$ empirica goals-complete --goal-id abc123 --run-postflight --merge-branch
🧠 POSTFLIGHT: know=0.9, uncertainty=0.1
   Learning delta: know +0.2, uncertainty -0.3
✅ Closed BEADS issue: empirica-05j
✅ Merged to main
📦 Handoff created
```

---

## Benefits

### For Individual AIs
- Automatic branch creation (no manual setup)
- Clear linkage: issue ↔ branch
- Epistemic tracking per branch
- Easy completion workflow

### For Multi-AI Teams
- See who's working on what (branch mapping)
- Avoid duplicate work (branch already exists)
- Coordinate handoffs (branch ownership transfer)
- Track epistemic progress collectively

### For Sentinel
- Monitor all work in progress (git log)
- Detect stale branches (abandoned work)
- Suggest merges (high confidence)
- Enforce policies (branch naming, commits)

---

## Configuration

**In `.empirica/config.yaml`:**

```yaml
beads_git_bridge:
  auto_create_branch: true
  branch_prefix: "epistemic"
  auto_run_preflight: true
  auto_merge_on_complete: false  # Safety: require manual merge
  stale_branch_days: 7
  naming_convention: "layer-issue"  # or "ai-layer-issue" for multi-AI
```

---

## Next Steps

**Immediate:**
1. Implement `goals-claim` and `goals-complete` commands
2. Create branch mapping file handler
3. Update AGENTS.md with new workflow
4. Test end-to-end integration

**Future:**
5. Sentinel branch monitoring
6. BEADS hooks integration
7. Multi-AI branch coordination
8. Automatic conflict resolution

---

**Status:** Design complete, ready for implementation
**Estimated effort:** 2-3 hours for Phase 3a
**Priority:** HIGH (completes BEADS integration)
