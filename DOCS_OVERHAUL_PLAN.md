# Documentation Overhaul Plan - Overview & Summary Docs

**Date:** 2025-12-05  
**Status:** Planning Phase  
**Goal:** Create comprehensive, accurate overview documentation based on current v4.0 architecture  
**Source of Truth:** `docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md` (v4.0)  

---

## Context

### Current State

We have **excellent detailed documentation** but **outdated/fragmented overview docs**:

**✅ Good Detailed Docs:**
- `docs/production/13_PYTHON_API.md` - Complete API reference
- `docs/production/03_BASIC_USAGE.md` - Workflow examples
- `docs/production/12_SESSION_DATABASE.md` - Database schema
- `docs/production/06_CASCADE_FLOW.md` - CASCADE guide (NEW)
- `docs/guides/GOAL_TREE_USAGE_GUIDE.md` - Goal tracking guide (NEW)

**⚠️ Needs Update:**
- `README.md` - Root overview (references v1.0-beta, has "bootstrap" command)
- `docs/README.md` - Docs hub (good structure, needs content refresh)
- `docs/production/00_COMPLETE_SUMMARY.md` - Complete overview (outdated v2.0 references)

### The Problem

1. **Version mismatch** - README says v1.0-beta, docs say v2.0, canonical prompt is v4.0
2. **Command outdated** - README shows `empirica bootstrap`, should be `empirica session-create`
3. **Missing features** - Goals/subtasks (v4.0) not mentioned in overviews
4. **Fragmented story** - No single place that explains the complete system

### The Solution

**Create authoritative overview docs that:**
1. Match canonical prompt v4.0 (source of truth)
2. Reference detailed docs appropriately
3. Tell a coherent story from beginner → advanced
4. Update version numbers consistently

---

## Source of Truth: Canonical Prompt v4.0

**Location:** `docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md`

**Key Architecture Points:**

### What Empirica Is
- Epistemic self-awareness framework
- Tracks what AI knows vs guesses
- Measures uncertainty explicitly
- Learns systematically
- Resumes work efficiently

### Core Components (v4.0)

1. **Session Creation** - Simple, no ceremony
   ```bash
   empirica session-create --ai-id myai --output json
   ```

2. **13 Epistemic Vectors** - Self-assessment dimensions
   - ENGAGEMENT (gate)
   - Foundation: KNOW, DO, CONTEXT
   - Comprehension: CLARITY, COHERENCE, SIGNAL, DENSITY
   - Execution: STATE, CHANGE, COMPLETION, IMPACT
   - Meta: UNCERTAINTY

3. **CASCADE Workflow** - Epistemic checkpoints
   - PREFLIGHT (before work)
   - CHECK (optional, mid-work decision gate)
   - POSTFLIGHT (after work)
   - **Not prescriptive** - observes implicit reasoning

4. **Goals/Subtasks (NEW v4.0)** - Investigation tracking
   - Decision quality (unknowns inform CHECK)
   - Continuity (handoff complete investigation)
   - Audit trail (findings/unknowns/dead_ends)

5. **Storage Architecture**
   - SQLite database (reflexes table unified in v4.0)
   - Git notes (checkpoints)
   - Handoff reports

6. **Three Separate Concerns**
   - CASCADE phases (epistemic checkpoints)
   - Goals/subtasks (investigation logging)
   - Implicit reasoning (natural work)

---

## Files to Update

### Priority 1: Root README.md

**File:** `README.md`  
**Current Issues:**
- ❌ Version badge says "1.0.0-beta"
- ❌ Shows `empirica bootstrap` command
- ❌ No mention of goals/subtasks
- ❌ CASCADE described as v1.0 (4 steps)
- ❌ References to old "Extended Bootstrap"

**What to Fix:**
1. Update version to "4.0"
2. Replace `empirica bootstrap` → `empirica session-create`
3. Add goals/subtasks to features
4. Update CASCADE description (PREFLIGHT/CHECK/POSTFLIGHT)
5. Remove bootstrap terminology (reserved for system prompts)
6. Add note: "Bootstrap = system prompts only, session-create for sessions"

**Target Structure:**
```markdown
# Empirica - Epistemic Self-Awareness for AI

> v4.0 - Know what you know, track what you don't

## What is Empirica?
[Current description is good, keep it]

## Key Features (v4.0)
- 13-vector epistemic assessment
- CASCADE workflow (PREFLIGHT/CHECK/POSTFLIGHT)
- Goals/subtasks for investigation tracking [NEW]
- Unified reflexes table database
- Multi-session continuity
- MCP server integration

## Quick Start
empirica session-create --ai-id myai
[Point to detailed guides]

## Learn More
[Update links to current docs]
```

---

### Priority 2: docs/README.md

**File:** `docs/README.md`  
**Current State:** Good structure, needs content refresh  

**What to Fix:**
1. Update "Quickstart" section links
2. Verify all file references exist
3. Add goals/subtasks to feature list
4. Update workflow description to v4.0

**Target Structure:**
```markdown
# Empirica Documentation

**Version:** 4.0
**Source of Truth:** CANONICAL_SYSTEM_PROMPT.md

## For AI Agents
- Start here: 01_a_AI_AGENT_START.md
- Quick reference: 03_CLI_QUICKSTART.md

## For Developers
- Installation: COMPLETE_INSTALLATION_GUIDE.md
- MCP setup: 04_MCP_QUICKSTART.md
- Python API: production/13_PYTHON_API.md

## Core Concepts
- CASCADE workflow: production/06_CASCADE_FLOW.md [NEW]
- Goal tracking: guides/GOAL_TREE_USAGE_GUIDE.md [NEW]
- Database: production/12_SESSION_DATABASE.md

## Complete Reference
- Full system: production/00_COMPLETE_SUMMARY.md
- [Updated with v4.0 architecture]
```

---

### Priority 3: docs/production/00_COMPLETE_SUMMARY.md → 00_DOCUMENTATION_MAP.md

**Decision:** Replace with pointer/map doc instead of duplication

**Rationale:**
- CANONICAL_SYSTEM_PROMPT.md is single source of truth
- Avoid duplicating architecture info
- Keep docs DRY (Don't Repeat Yourself)
- Make navigation easier

**What to Do:**
1. **Rename:** `00_COMPLETE_SUMMARY.md` → `00_DOCUMENTATION_MAP.md`
2. **New approach:** Navigation guide pointing to authoritative sources
3. **Keep:** Examples, quick references that belong in one place
4. **Link to:** Detailed docs for deep dives

**Target Structure:**
```markdown
# Empirica v4.0 - Complete Documentation Map

## Quick Reference

### Getting Started
- **For AI Agents:** `docs/01_a_AI_AGENT_START.md` - Agent-focused introduction
- **For Developers:** `docs/COMPLETE_INSTALLATION_GUIDE.md` - Setup and installation
- **Quick Start:** `docs/03_CLI_QUICKSTART.md` - 5-minute quick start

### One-Minute Overview
```bash
# 1. Create session
empirica session-create --ai-id myai --output json

# 2. Run PREFLIGHT (assess baseline)
empirica preflight --session-id <ID> --prompt "Your task"

# 3. Do your work (implicit reasoning: THINK, INVESTIGATE, PLAN, ACT)

# 4. Run POSTFLIGHT (measure learning)
empirica postflight --session-id <ID> --task-summary "Completed"
```

## Core Concepts

### Understanding Empirica
→ **What is Empirica?** See: `docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md` (Section I-II)
- Epistemic self-awareness framework
- Tracks knowledge vs. uncertainty
- Measures learning systematically

### CASCADE Workflow (PREFLIGHT/CHECK/POSTFLIGHT)
→ **Complete guide:** `docs/production/06_CASCADE_FLOW.md`
- **PREFLIGHT** - Baseline epistemic assessment
- **CHECK** - Optional mid-work decision gate (0-N times)
- **POSTFLIGHT** - Final assessment, measure learning delta

### Goal/Subtask Tracking (NEW in v4.0)
→ **Complete guide:** `docs/guides/GOAL_TREE_USAGE_GUIDE.md`
- Decision Quality: Unknowns inform CHECK decisions
- Continuity: Goal tree included in handoff
- Audit Trail: Complete investigation path visible
- When to use: Complex tasks, high uncertainty, multi-session work

### 13 Epistemic Vectors
→ **Complete reference:** `docs/production/05_EPISTEMIC_VECTORS.md`

**Quick list:**
- **Foundation (Gate ≥0.6):** engagement, know, do, context
- **Comprehension:** clarity, coherence, signal, density
- **Execution:** state, change, completion, impact
- **Meta:** uncertainty (explicit doubt)

### Three Separate Concerns (v4.0 Architecture)
1. **CASCADE Phases** - Epistemic checkpoints (PREFLIGHT/CHECK/POSTFLIGHT)
2. **Goals/Subtasks** - Investigation logging (optional, during work)
3. **Implicit Reasoning** - Natural work (THINK, INVESTIGATE, PLAN, ACT, EXPLORE, REFLECT)

→ **Full explanation:** `docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md` (Sections IV, VI)

## API & Implementation

### Python API
→ **Full reference:** `docs/production/13_PYTHON_API.md`

**Session Management:**
```python
from empirica.data.session_database import SessionDatabase
db = SessionDatabase()
session_id = db.create_session(ai_id="myai")
```

**Goal/Subtask Operations (NEW v4.0):**
```python
goal_id = db.create_goal(session_id, objective, scope={...})
subtask_id = db.create_subtask(goal_id, description)
db.update_subtask_findings(subtask_id, [...])
db.update_subtask_unknowns(subtask_id, [...])
summary = db.query_unknowns_summary(session_id)  # For CHECK decisions
```

### CLI Commands
→ **All commands:** Run `empirica --help`

**Essential commands:**
```bash
empirica session-create --ai-id myai              # Create session
empirica preflight --session-id <ID> --prompt    # PREFLIGHT assessment
empirica check --session-id <ID> --confidence     # CHECK gate
empirica postflight --session-id <ID>             # POSTFLIGHT assessment
empirica goals-create --session-id <ID>           # Create goal (v4.0)
empirica goals-list <ID>                          # List goals
```

### MCP Tools
→ **All MCP tools:** See `docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md` (Section XV)

**Essential tools for MCP usage:**
- Session: `session_create`, `get_session_summary`, `get_epistemic_state`
- CASCADE: `execute_preflight`, `submit_preflight_assessment`, `execute_check`, `submit_check_assessment`, `execute_postflight`, `submit_postflight_assessment`
- Goals: `create_goal`, `add_subtask`, `complete_subtask`
- Continuity: `create_handoff_report`, `query_handoff_reports`

## Database & Storage

### Schema
→ **Complete schema:** `docs/production/12_SESSION_DATABASE.md`

**Key tables:**
- **reflexes** - All CASCADE assessments (PREFLIGHT, CHECK, POSTFLIGHT)
- **goals** - Investigation goals with scope vectors (NEW v4.0)
- **subtasks** - Investigation items with findings/unknowns/dead_ends (NEW v4.0)

### Storage Architecture
→ **Full details:** `docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md` (Section III)

**Three-layer atomic writes:**
1. SQLite database (reflexes, goals, subtasks tables)
2. Git notes (checkpoints, handoffs - 97.5% token reduction)
3. JSON logs (full audit trail)

## Detailed Guides

| Topic | Location | For |
|-------|----------|-----|
| CASCADE Workflow | `production/06_CASCADE_FLOW.md` | Understanding phases, using CHECK gates |
| Goal Tracking | `guides/GOAL_TREE_USAGE_GUIDE.md` | Complex investigations, high uncertainty |
| Basic Usage | `production/03_BASIC_USAGE.md` | Getting started, simple examples |
| Database | `production/12_SESSION_DATABASE.md` | Schema details, data model |
| Python API | `production/13_PYTHON_API.md` | Complete API reference |
| Vectors | `production/05_EPISTEMIC_VECTORS.md` | Understanding all 13 vectors |

## Working Examples

### Example: OAuth2 Implementation Investigation

**Scenario:** Research OAuth2 implementation requirements before coding

**Steps:**
```bash
# 1. Create session
session_id=$(empirica session-create --ai-id oauth-researcher --output json | jq -r .session_id)

# 2. PREFLIGHT: Assess baseline uncertainty
empirica preflight --session-id $session_id --prompt "Understand OAuth2 implementation"
# Submit: know=0.6, uncertainty=0.5, context=0.55

# 3. Create investigation goal
empirica goals-create --session-id $session_id \
  --objective "Understand OAuth2 implementation requirements" \
  --complexity 0.65

# 4. Investigate (implicit work phase)
# - Create subtasks: "Map endpoints", "Research PKCE", etc.
# - Log findings as discovered
# - Update unknowns: "Token rotation interval?", "Storage best practice?"

# 5. CHECK: Query unknowns to assess readiness
# unknowns_summary → 2 unknowns remain (manageable)
# confidence=0.75 → proceed with implementation
empirica check --session-id $session_id --confidence 0.75

# 6. POSTFLIGHT: Measure learning
empirica postflight --session-id $session_id --task-summary "OAuth2 requirements documented"
# Submit: know=0.85 (+0.25 learned), uncertainty=0.25 (-0.25 resolved)
```

**Result:** Goal tree in handoff shows what was investigated, what was learned, what remains unclear

## FAQ & Common Questions

**Q: Do I have to use goals/subtasks?**
A: No, they're optional. Use for complex investigations or high uncertainty. PREFLIGHT/CHECK/POSTFLIGHT work standalone.

**Q: What's the difference between CASCADE and goals?**
A: CASCADE = epistemic checkpoints (when you formally assess). Goals = investigation logging (optional, during work). They're separate but can interact (CHECK queries unknowns from goals).

**Q: What's "bootstrap" vs "session-create"?**
A: Bootstrap = system prompts (AI instructions). session-create = command to create a session. Don't confuse them.

**Q: How do I know if I'm ready for CHECK?**
A: Query unknowns_summary(). If unknowns ≤2 and confidence ≥0.75, ready. Otherwise, investigate more.

**Q: Can I resume a previous session?**
A: Yes. Handoff reports preserve goal tree + learnings. Next AI loads handoff and continues.

→ **More FAQs:** `docs/production/22_FAQ.md`

## Architecture Diagram

```
SESSION CREATION (instant, no ceremony)
    ↓
PREFLIGHT → Baseline epistemic assessment (13 vectors)
    ↓
[WORK PHASE - Implicit reasoning states: THINK, INVESTIGATE, PLAN, ACT, EXPLORE, REFLECT]
    ├─ (OPTIONAL) Create goal → Create subtasks → Log findings/unknowns
    ├─ (0-N TIMES) CHECK gate → Query unknowns → Decide readiness
    └─ Refine investigation based on CHECK decision
    ↓
POSTFLIGHT → Final assessment (13 vectors, measure PREFLIGHT→POSTFLIGHT delta)
    ↓
HANDOFF REPORT → Goal tree + learnings + next session context
    ↓
(NEXT SESSION) Load handoff → Resume with complete investigation history
```

## Next Steps

### For New Users
1. Read: "One-Minute Overview" above
2. Read: `docs/01_a_AI_AGENT_START.md`
3. Try: `empirica session-create --ai-id myai` → `empirica preflight ...`

### For Developers
1. Read: `docs/COMPLETE_INSTALLATION_GUIDE.md`
2. Read: `docs/production/13_PYTHON_API.md`
3. Try: Create session via Python API

### For Understanding Everything
- Start: This file (navigation)
- Deep dive: `docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md` (v4.0)
- Details: Linked guides above

## Source of Truth

**All information in this map references:**
- `docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md` - v4.0 canonical
- `empirica/data/session_database.py` - Implementation code
- Detailed guides in `docs/production/` and `docs/guides/`

**Last updated:** 2025-12-06
**Version:** v4.0
```

---

## Consistency Requirements

### Version Numbers
- **All docs:** v4.0
- **No references to:** v1.0, v2.0, v3.0 (except historical notes)

### Commands
- **Correct:** `empirica session-create`
- **Incorrect:** `empirica bootstrap` (reserved for system prompts)

### Terminology
- **Session creation** - NOT "bootstrapping sessions"
- **Bootstrap** - Only for system prompts
- **Goals/subtasks** - Investigation tracking (v4.0 feature)
- **Reflexes table** - Unified storage (v4.0 architecture)

### Architecture Concepts
- **CASCADE** - PREFLIGHT/CHECK/POSTFLIGHT (epistemic checkpoints)
- **Goals** - Investigation logging (separate from CASCADE)
- **Implicit reasoning** - Natural work (observed, not prescribed)

---

## Examples to Use

### OAuth2 Authentication
**Why:** Already used throughout detailed docs, consistent example

**Scenario:**
- Initial uncertainty: 0.6 (high)
- Create goal: "Understand OAuth2 flow"
- Investigation: Map endpoints, understand PKCE
- Findings: 4-5 discoveries
- Unknowns: 2-3 questions
- CHECK: Query unknowns → decide readiness
- Implementation: Use findings from investigation
- POSTFLIGHT: Include goal_tree in handoff

### Session Creation
```bash
# Simple
empirica session-create --ai-id myagent

# With bootstrap level
empirica session-create --ai-id myagent --bootstrap-level 1
```

### Python API
```python
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()
session_id = db.create_session(ai_id="myagent")
db.close()
```

---

## Links to Update

### Internal Links (Within Docs)
- Point to new CASCADE flow guide: `production/06_CASCADE_FLOW.md`
- Point to goal tree guide: `guides/GOAL_TREE_USAGE_GUIDE.md`
- Update database reference: `production/12_SESSION_DATABASE.md`

### External Links
- GitHub repo (if any)
- Website (when available)

---

## Content to Reference

### Detailed Guides (Already Complete)
- `production/06_CASCADE_FLOW.md` - CASCADE workflow
- `guides/GOAL_TREE_USAGE_GUIDE.md` - Goal tracking
- `production/13_PYTHON_API.md` - API reference
- `production/12_SESSION_DATABASE.md` - Database schema
- `production/03_BASIC_USAGE.md` - Quick start

### Canonical Prompt Sections to Pull From
- Section I: What is Empirica?
- Section II: Architecture
- Section V: CASCADE workflow
- Section VI: Git integration & goal tracking
- Section XI: MCP tools reference
- Section XII: CLI commands reference

---

## Success Criteria

### After Update, Users Should Be Able To:
1. **Understand Empirica** - Read README, get clear picture
2. **Start quickly** - Follow quick start, create session
3. **Find details** - Navigate to detailed docs
4. **See consistency** - Same terminology, commands, examples throughout

### Documentation Should:
1. **Match v4.0** - All references current
2. **No bootstrap confusion** - Clear that bootstrap = system prompts
3. **Show goals** - v4.0 feature prominently documented
4. **Tell coherent story** - Overview → detailed guides
5. **Be accurate** - All commands, APIs match implementation

---

## Implementation Approach

### Phase 1: README.md (Root)
1. Update version badge → v4.0
2. Replace bootstrap commands → session-create
3. Add goals/subtasks feature
4. Update quick start
5. Update links
**Estimated:** 30-45 minutes

### Phase 2: docs/README.md (Docs Hub)
1. Update version reference
2. Verify all links
3. Add new guides
4. Refresh structure
**Estimated:** 20-30 minutes

### Phase 3: docs/production/00_DOCUMENTATION_MAP.md (NEW)
**Decision:** Create new navigation guide instead of duplicating architecture
1. Create 00_DOCUMENTATION_MAP.md from scratch
2. Build comprehensive navigation structure
3. Include quick reference + one-minute overview
4. Add FAQ section
5. Include working examples (OAuth2)
6. Architecture diagram
7. Link all detailed docs appropriately
**Estimated:** 1-1.5 hours

**What NOT to do:** Don't keep/update 00_COMPLETE_SUMMARY.md
**Rationale:** Avoid duplication; CANONICAL_SYSTEM_PROMPT.md is source of truth

---

## Verification Checklist

### Before Committing:
- [ ] All version numbers = v4.0
- [ ] No "empirica bootstrap" for sessions
- [ ] Goals/subtasks mentioned in features
- [ ] CASCADE = PREFLIGHT/CHECK/POSTFLIGHT
- [ ] Three separate concerns explained
- [ ] All links work
- [ ] Examples match API
- [ ] Consistent terminology

### Cross-Check Against:
- [ ] Canonical prompt v4.0
- [ ] Detailed docs (03, 06, 12, 13)
- [ ] Implementation (session_database.py)

---

## Files Created This Session

**Goals/Subtasks Documentation (v4.0):**
1. `docs/production/13_PYTHON_API.md` - Updated with goals section
2. `docs/production/03_BASIC_USAGE.md` - Added goal tracking example
3. `docs/production/12_SESSION_DATABASE.md` - Added goals/subtasks tables
4. `docs/production/06_CASCADE_FLOW.md` - New CASCADE guide
5. `docs/guides/GOAL_TREE_USAGE_GUIDE.md` - New comprehensive guide

**Summaries:**
6. `GOALS_SUBTASKS_DOCS_COMPLETE.md` - Goals docs completion summary
7. `COMPLETE_DOCS_MIGRATION_SUMMARY.md` - Database migration summary
8. `DOCS_OVERHAUL_PLAN.md` - This file

**Total:** ~2,000 lines of documentation added this session

---

## Next Session Plan

### Step 1: Update README.md (45 min)
- Version badge → v4.0
- Remove bootstrap references
- Add goals/subtasks feature
- Update quick start section
- Verify all links work

### Step 2: Update docs/README.md (30 min)
- Verify all links exist
- Add new guides (CASCADE, Goals)
- Update structure if needed
- Ensure consistent v4.0 version

### Step 3: Create 00_DOCUMENTATION_MAP.md (1-1.5 hours)
- Create from scratch (don't duplicate CANONICAL_SYSTEM_PROMPT.md)
- Quick reference section
- One-minute overview (4 commands)
- Core concepts with links
- API reference section
- Working examples (OAuth2 end-to-end)
- FAQ section
- Architecture diagram
- Next steps

### Step 4: Verify Consistency (15 min)
- Check all version refs = v4.0
- Check all commands exist and work
- Check all links are valid
- Cross-reference against canonical prompt
- Verify examples run without errors

### Step 5: Wait for Qwen's Testing (parallel, 2-3 hours)
- Qwen tests full workflow
- Documents any issues found
- May reveal doc gaps

### Step 6: Integrate Qwen's Findings (20-30 min)
- Add clarifications based on testing
- Fix any command examples that failed
- Update FAQ with issues discovered

**Total Time:** 2.5-3 hours (before Qwen testing) + 30 min (after Qwen)

---

## Notes

### What NOT to Change
- Detailed guides (already updated)
- API reference docs (accurate)
- Database schema docs (updated)
- Guide docs (new and complete)

### What TO Change
- Overview docs (version, commands, features)
- Quick start sections (bootstrap → session-create)
- Feature lists (add goals/subtasks)
- Architecture descriptions (v4.0 updates)

### Key Message
**Empirica v4.0** provides:
- Epistemic self-awareness through 13 vectors
- CASCADE checkpoints (PREFLIGHT/CHECK/POSTFLIGHT)
- Goal tracking for investigation (NEW)
- Unified database architecture
- Multi-session continuity

---

**Status:** Ready for next session (Sonnet to execute)
**Priority:** High (users see outdated info in overviews)
**Complexity:** Medium (content exists, needs consolidation + curation)
**Time:** 2.5-3 hours (plus 30 min after Qwen testing)
**Timing:** Can start in parallel with Qwen's testing (no dependency)

---

## Integration with Qwen's Testing

**Dependency:** None (docs work can proceed in parallel)

**Expected improvements from Qwen's findings:**
- Examples validated to actually work
- CLI commands verified as accurate
- Parameter names confirmed
- Error scenarios documented
- FAQ enhanced with common issues

**Timeline:**
1. Sonnet: Start docs overhaul (2.5-3 hours)
2. Qwen: Start testing (parallel, 2-3 hours)
3. Both complete ~same time
4. Sonnet: 20-30 min to integrate Qwen's findings
5. Final: Comprehensive, tested, accurate docs + verified tools

---

**See Also:**
- Canonical prompt: `docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md`
- Current detailed docs: `docs/production/`
- New guides: `docs/production/06_CASCADE_FLOW.md`, `docs/guides/GOAL_TREE_USAGE_GUIDE.md`
- Qwen testing plan: `/tmp/QWEN_WORKFLOW_TEST_SPEC.md`
