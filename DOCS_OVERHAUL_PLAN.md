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

### Priority 3: docs/production/00_COMPLETE_SUMMARY.md

**File:** `docs/production/00_COMPLETE_SUMMARY.md`  
**Current Issues:**
- ❌ References "v2.0" throughout
- ❌ Shows old bootstrap workflow
- ❌ No mention of goals/subtasks (v4.0)
- ❌ Database section references old tables
- ❌ Missing unified reflexes table

**What to Fix:**
1. **Update to v4.0** throughout
2. **Rewrite bootstrap section** - Show session-create
3. **Add goals/subtasks section** - New v4.0 feature
4. **Update database section** - Reflexes table unified
5. **Update workflow examples** - Use current API
6. **Add CHECK phase** - Show optional mid-work gate
7. **Three separate concerns** - Clarify CASCADE/goals/implicit

**Target Structure:**
```markdown
# Empirica Production System - v4.0 Complete Summary

## What's New in v4.0
- Goal/subtask tracking (decision quality + continuity + audit)
- Unified reflexes table (all epistemic data)
- CHECK phase clarified (optional decision gate)
- Three separate concerns explained

## Architecture Overview
[Based on canonical prompt sections]

### Session Creation (v4.0)
empirica session-create --ai-id myai
[No bootstrap ceremony]

### 13 Epistemic Vectors
[Table with all 13 vectors]

### CASCADE Workflow
PREFLIGHT → [work] → CHECK (optional) → [work] → POSTFLIGHT
[Explain each phase]

### Goals/Subtasks (NEW v4.0)
- When to use: Complex investigations, high uncertainty
- create_goal(), create_subtask(), update_*()
- Integration with CHECK: query_unknowns_summary()
[Link to detailed guide]

### Storage Architecture
- Reflexes table (unified in v4.0)
- Git notes (checkpoints)
- Handoff reports

### Three Separate Concerns
1. CASCADE phases (epistemic checkpoints)
2. Goals/subtasks (investigation logging)
3. Implicit reasoning (natural work)

## Complete API Reference
[Link to detailed docs]

## Workflow Examples
[OAuth2 example with goals]

## Database Schema
[Reflexes table + goals + subtasks]
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

### Phase 3: docs/production/00_COMPLETE_SUMMARY.md
1. Update to v4.0 throughout
2. Rewrite architecture section
3. Add goals/subtasks section
4. Update workflow examples
5. Update database section
6. Add CHECK phase explanation
**Estimated:** 1-2 hours

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

### Step 1: Update README.md (30 min)
- Version badge
- Remove bootstrap
- Add goals
- Update quick start

### Step 2: Update docs/README.md (20 min)
- Verify links
- Add new guides
- Update structure

### Step 3: Rewrite 00_COMPLETE_SUMMARY.md (1-2 hours)
- v4.0 architecture
- Goals/subtasks section
- Updated examples
- Database section
- CHECK phase

### Step 4: Verify Consistency (15 min)
- Check all version refs
- Check all commands
- Check all links
- Cross-reference canonical prompt

**Total Time:** ~2-3 hours

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

**Status:** Ready for next session  
**Priority:** High (users see outdated info in overviews)  
**Complexity:** Medium (content exists, needs consolidation)  
**Time:** 2-3 hours estimated  

---

**See Also:**
- Canonical prompt: `docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md`
- Current detailed docs: `docs/production/`
- New guides: `docs/production/06_CASCADE_FLOW.md`, `docs/guides/GOAL_TREE_USAGE_GUIDE.md`
