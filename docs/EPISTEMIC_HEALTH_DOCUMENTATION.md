# Empirica: Epistemic Health, Clarity & Relevance Documentation

## Overview

Empirica's `project-bootstrap` command captures comprehensive epistemic state to enable **epistemic continuity** across AI agent sessions. This document details what Empirica captures and how it enables three core epistemic dimensions:

1. **Epistemic Health**: AI readiness and uncertainty levels
2. **Epistemic Clarity**: Understanding depth and coherence
3. **Epistemic Relevance**: Context and decision evidence

---

## What Empirica Captures

### 1. AI-Specific Epistemic Handoff

**Location in Output:** `🧠 Epistemic Handoff (from [AI_ID])`

Captures the POSTFLIGHT checkpoint from the previous session - the exact epistemic state when the last AI finished work.

**Data Captured:**
```
Epistemic Vectors (13 dimensions):
├── Engagement (0.0-1.0)
│   └─ How focused/involved was the AI?
├── Foundation Layer
│   ├─ Know: Factual understanding (0.0-1.0)
│   ├─ Do: Practical capability (0.0-1.0)
│   └─ Context: Environmental understanding (0.0-1.0)
├── Comprehension Layer
│   ├─ Clarity: Concept clarity (0.0-1.0)
│   ├─ Coherence: Idea connectedness (0.0-1.0)
│   ├─ Signal: Pattern recognition (0.0-1.0)
│   └─ Density: Information richness (0.0-1.0)
├── Execution Layer
│   ├─ State: Current progress state (0.0-1.0)
│   ├─ Change: Rate of learning (0.0-1.0)
│   ├─ Completion: Task progress (0.0-1.0)
│   └─ Impact: Work significance (0.0-1.0)
└── Uncertainty (0.0-1.0)
    └─ Explicit doubt level
```

**Why This Matters:**
- **Epistemic Health**: High uncertainty + low foundation = needs deep bootstrap
- **Epistemic Clarity**: Low clarity/coherence = requires foundational context
- **Epistemic Relevance**: Vector trends show what learning happened

**Example:**
```
Previous Session State:
   Engagement: 0.80 (was highly focused)
   Foundation: know=0.65, do=0.75, context=0.55 (good practical ability, gaps in theory)
   Uncertainty: 0.75 (high doubt - needs validation)
```

**What Decisions This Enables:**
- If uncertainty high: Load more context (full/moderate vs minimal)
- If foundation low: Provide prerequisite explanations
- If change high: Recent learning is fresh, validate it
- If impact low: Previous session didn't move needle, need different approach

---

### 2. Git Status & Repository Context

**Location in Output:** `🌿 Git Status`

Real-time snapshot of repository state when bootstrap runs.

**Data Captured:**
```
Branch: epistemic/reasoning/goal-2393d8ff
Uncommitted: 6 file(s)
Untracked: 0 file(s)
Recent commits:
   • ca99caf3 feat: Phase 8 Batch 8 - Extract migration + session_summary
   • c3d44994 feat: Phase 8 Batch 7 - Token delegation + dead code removal
   • 69d47482 feat: Phase 8 Batch 6 - Delegate _load_goals_for_project
```

**Why This Matters:**
- **Epistemic Health**: Uncommitted changes = incomplete thought process
- **Epistemic Clarity**: Recent commits show what was worked on
- **Epistemic Relevance**: Branch name + commits = work context

**What Decisions This Enables:**
- If high uncommitted: Don't start new work, finish current thought
- If on feature branch: Understand the goal from branch name
- Recent commits: Know what problems were just solved
- Untracked files: May indicate exploratory dead ends

---

### 3. Auto-Captured Issues

**Location in Output:** `⚠️ Auto-Captured Issues`

Automatically detected errors, warnings, and TODOs from previous sessions, organized by severity.

**Data Captured:**
```
HIGH (4 issues):
   • bug: CHECK-SUBMIT command doesn't support JSON stdin/config input
     Location: <stdin>:7
   • todo: TODO (high): Implement connection pooling for database
     Location: /home/yogapad/empirica/core/issue_capture.py:261

MEDIUM (1 issue):
   • performance: Query user_profiles took 2500ms
     Location: core/issue_capture.py:237
```

**Issue Types Captured:**
- `bug`: Runtime errors and failures
- `todo`: Marked TODOs in code
- `performance`: Metrics exceeding thresholds
- `warning`: Static analysis warnings
- `style`: Code quality issues

**Why This Matters:**
- **Epistemic Health**: Critical issues = current system is broken, start with fixes
- **Epistemic Clarity**: Issue list = explicit blockers and known problems
- **Epistemic Relevance**: Severity + location = prioritization

**What Decisions This Enables:**
- If critical issues: Must fix before new work
- If many issues same area: Root cause investigation needed
- Issue history: Shows what was tried and failed
- Status lifecycle: Can see if issue was already investigated (status: investigating) or resolved (status: resolved)

---

### 4. Recent Findings

**Location in Output:** `📝 Recent Findings (last 10)`

Documented discoveries from previous sessions across the entire project.

**Data Captured:**
```
Finding: "CHECK now fully functional with evidence-based suggestions: 
auto-loads 294 findings + 51 unknowns, calculates drift, makes 
suggestive decisions based on evidence"

Finding: "Phase 1 complete: Extracted 24 database schemas into 5 
organized modules. Reduced _create_tables from 712 to 126 lines (82%)."
```

**Metadata Attached:**
- `created_timestamp`: When finding was discovered
- `session_id`: Which session found it
- `goal_id`: Related goal (if any)
- `finding_data`: Full JSON with additional context

**Why This Matters:**
- **Epistemic Health**: Finding recency = how fresh is the knowledge
- **Epistemic Clarity**: Findings are validated, not speculative
- **Epistemic Relevance**: Related goals show dependencies

**What Decisions This Enables:**
- Recent findings (< 1 hour old): Can act on without re-verification
- Old findings (days old): May need re-validation
- Related findings: Pattern recognition across work
- Finding count: Shows how much was learned

---

### 5. Unresolved Unknowns

**Location in Output:** `❓ Unresolved Unknowns`

Questions and blockers that need investigation, tracked with ownership.

**Data Captured:**
```
Unknown: "Exit codes fix (68 commands): Assigned to Qwen. 
All CLI handlers should return 0 or sys.exit(1)..."

Unknown: "Should pre-compact hook auto-commit working directory 
before snapshot?"
```

**Metadata:**
- `description`: The actual question/blocker
- `status`: new, investigating, resolved, wontfix, handoff
- `assigned_to`: Which AI should work on it (if assigned)
- `created_timestamp`: When discovered

**Why This Matters:**
- **Epistemic Health**: Unknown count = how complete is understanding
- **Epistemic Clarity**: Unknowns are explicit knowledge gaps
- **Epistemic Relevance**: Assignment shows priority and responsibility

**What Decisions This Enables:**
- If many unknowns same area: Deep learning session needed
- If unknowns assigned: Can see who is responsible
- Unknown age: Stale unknowns may be resolved elsewhere
- Unknown status: "investigating" = currently being worked on

---

### 6. Dead Ends (What Didn't Work)

**Location in Output:** `💀 Dead Ends (What Didn't Work)`

Failed approaches and attempts that didn't lead anywhere, preventing repetition.

**Data Captured:**
```
Dead End: "Using --project-id parameter with mistake-log command"
Reason: "Command doesn't accept --project-id parameter"

Dead End: "Test approach"
Reason: "Test failure reason"
```

**Why This Matters:**
- **Epistemic Health**: Dead end count = learning efficiency
- **Epistemic Clarity**: Knowing what doesn't work = clarity
- **Epistemic Relevance**: Location + reason = prevents rework

**What Decisions This Enables:**
- Don't retry failed approaches
- If pattern of same dead ends: May indicate misunderstanding
- Dead end age: Old dead ends may no longer apply
- Reason clarity: Good reasons prevent repetition, vague ones cause frustration

---

### 7. Recent Mistakes

**Location in Output:** `⚠️ Recent Mistakes to Avoid`

Critical errors and misunderstandings that caused rework or failures.

**Data Captured:**
```
Mistake: "Project bootstrap error: 'cost' key missing from breadcrumbs"
Impact: Command failed to load
Resolution: Added proper metadata structure
```

**Metadata:**
- `description`: What went wrong
- `context`: Where it happened
- `impact`: What broke or failed
- `resolution`: How it was fixed
- `created_timestamp`: When it happened

**Why This Matters:**
- **Epistemic Health**: Mistake recency = how stable is knowledge
- **Epistemic Clarity**: Mistakes show conceptual gaps
- **Epistemic Relevance**: Resolution = actionable prevention

**What Decisions This Enables:**
- Avoid repeating same mistakes (check before implementing)
- Understand root causes of failures
- If same mistake recurring: Need deeper learning
- Resolution pattern: Shows what fixes work

---

### 8. Project Metadata

**Location in Output:** `📋 Project Summary` & `📁 Project: [NAME]`

Static project information tying everything to context.

**Data Captured:**
```
📁 Project: empirica
🆔 ID: ea2f33a4-d808-434b-b776-b7246bd6134a
🔗 Repository: https://github.com/Nubaeon/empirica.git
💾 Database: .empirica/sessions/sessions.db
📍 Location: /home/yogapad/empirical-ai/empirica/.empirica
```

**Why This Matters:**
- **Epistemic Clarity**: Context for all findings/issues
- **Epistemic Relevance**: Ensures all data is from correct project
- **Epistemic Health**: Database location = know where state is stored

---

## How These Dimensions Work Together

### Epistemic Health Framework

**Definition:** AI's readiness, capability level, and certainty for work

**Indicators:**
```
✅ Healthy:
   - Low uncertainty (< 0.35)
   - High foundation vectors (> 0.70)
   - Few unresolved unknowns
   - Recent findings (< 2 hours old)
   - Completion vector trending up

⚠️  At Risk:
   - Moderate uncertainty (0.35-0.60)
   - Mixed foundation vectors
   - Several unknowns per workstream
   - No recent findings
   - Completion stalled

❌ Unhealthy:
   - High uncertainty (> 0.60)
   - Low foundation vectors (< 0.50)
   - Many unresolved unknowns
   - Stale findings (> 1 day old)
   - Mistake repetition
```

**Bootstrap Response:**
- Healthy: Use minimal context (~500 tokens), proceed quickly
- At Risk: Use moderate context (~1500 tokens), add CHECK gates
- Unhealthy: Use full context (~5000 tokens), require investigation

---

### Epistemic Clarity Framework

**Definition:** Depth of understanding, coherence of knowledge, signal strength

**Indicators:**
```
✅ Clear:
   - High clarity vector (> 0.80)
   - High coherence vector (> 0.75)
   - Findings well-connected across goals
   - Few contradictory findings
   - Dead ends documented with reasons

⚠️  Unclear:
   - Moderate clarity (0.60-0.80)
   - Mixed coherence (< 0.75)
   - Findings isolated to single areas
   - Some contradictions
   - Reasons vague

❌ Confused:
   - Low clarity (< 0.60)
   - Low coherence (< 0.50)
   - No connections between findings
   - Major contradictions
   - No documentation of why things failed
```

**Bootstrap Response:**
- Clear: Can skip prerequisite context, proceed to advanced topics
- Unclear: Request prerequisite context, add foundational docs
- Confused: Require comprehensive review, mandate CHECK gates

---

### Epistemic Relevance Framework

**Definition:** How aligned the loaded context is to current task

**Indicators:**
```
✅ Relevant:
   - Git branch name matches current goal
   - Recent commits in same area
   - Findings tagged with current goal_id
   - Issues located in current working files
   - Unknowns directly blocking current work

⚠️  Partially Relevant:
   - Related goals mentioned in findings
   - Issues in adjacent modules
   - Some unknowns blocking current path

❌ Irrelevant:
   - Findings from unrelated goals
   - Issues in untouched code
   - Unknowns from completed work
   - Dead ends in solved areas
```

**Bootstrap Response:**
- Relevant: Load as-is, trust it's needed
- Partially: Filter + contextualize
- Irrelevant: Hide or move to reference section

---

## Usage Examples

### Example 1: Healthy, Clear, Relevant Session

```
🧠 Epistemic Handoff:
   Engagement: 0.90
   Foundation: know=0.85, do=0.90, context=0.80
   Uncertainty: 0.25  ← Low = healthy

🌿 Git Status:
   Branch: feature/auth-refactor
   Uncommitted: 1 file(s)  ← Only one active change
   Recent commits: All auth-related

📝 Recent Findings:
   • "Auth module refactored, 340 tests passing"
   • "JWT validation complete and tested"

❓ Unresolved Unknowns: 2 (both auth-related)

💀 Dead Ends: None recent

⚠️ Issues: 0 critical, 1 low
```

**Decision:** Proceed immediately with minimal context. High confidence, clear path.

---

### Example 2: At Risk, Unclear, Partially Relevant Session

```
🧠 Epistemic Handoff:
   Engagement: 0.50
   Foundation: know=0.55, do=0.65, context=0.40  ← Low context
   Uncertainty: 0.65  ← High = risky

🌿 Git Status:
   Branch: debug/performance-issue
   Uncommitted: 12 file(s)  ← Many active changes
   Recent commits: Mixed - db, api, cache changes

📝 Recent Findings: 
   • "Query performance improved 30%"
   • "Caching layer added (not tested)"
   • "API response times inconsistent"

❓ Unresolved Unknowns: 8 (across 3 areas)

💀 Dead Ends: 3 (same performance issue attempted differently)

⚠️ Issues: 1 critical, 3 high
```

**Decision:** Load moderate context. Add CHECK gates. Require decision points:
1. Resolve critical issue first
2. Consolidate uncommitted changes
3. Investigate root cause (repeated dead ends in same area)

---

### Example 3: Unhealthy, Confused, Irrelevant Session

```
🧠 Epistemic Handoff:
   Engagement: 0.30
   Foundation: know=0.40, do=0.45, context=0.25  ← All low
   Uncertainty: 0.85  ← Very high

🌿 Git Status:
   Branch: experimental/refactor-attempt-7
   Uncommitted: 47 file(s)  ← Massive uncommitted state
   Recent commits: Contradictory changes, incomplete

📝 Recent Findings: 
   • "Architecture redesigned (incomplete)"
   • "Reverted changes, now 3 versions behind"
   • "Decision unclear on module boundaries"

❓ Unresolved Unknowns: 23 (scattered across project)

💀 Dead Ends: 12 (similar approaches tried 6 times)

⚠️ Issues: 4 critical, 8 high, 12 medium
```

**Decision:** Do NOT proceed. Required actions:
1. Create emergency investigation session
2. Load FULL context (all findings, dead ends, mistakes)
3. Mandate deep CHECK with expert review
4. Consider architectural reset or rollback
5. Document lessons learned to prevent repetition

---

## Technical Implementation

### Data Sources

| Data | Storage | Query Method |
|------|---------|--------------|
| Epistemic Handoff | `reflexes` table | POSTFLIGHT checkpoint for AI_ID |
| Git Status | Git repository | `git status`, `git log` commands |
| Auto-Captured Issues | `auto_captured_issues` table | Query by project_id, sort by severity |
| Recent Findings | `findings` table | Query by project_id, order by timestamp |
| Unknowns | `unknowns` table | Query by project_id, filter by status |
| Dead Ends | `dead_ends` table | Query by project_id, order by timestamp |
| Mistakes | `mistakes` table | Query by project_id, order by timestamp |
| Project Metadata | `projects` table | Query by project_id |

### Bootstrap Flow

```
project-bootstrap --project-id <ID> --ai-id <AI_ID>
    ↓
1. Resolve project metadata
    ↓
2. Load POSTFLIGHT checkpoint for AI_ID
    ↓
3. Capture git status (branch, uncommitted, commits)
    ↓
4. Load auto-captured issues (last 10, sorted by severity)
    ↓
5. Load recent findings (last 10)
    ↓
6. Load unresolved unknowns
    ↓
7. Load dead ends
    ↓
8. Load mistakes
    ↓
9. Aggregate and display in epistemic order
    ↓
Output: Complete epistemic health snapshot
```

### Display Order (Epistemic Relevance)

1. **Project Context** - Where are we?
2. **Git Status** - What's the current state?
3. **Epistemic Handoff** - Where were we?
4. **Auto-Captured Issues** - What's broken?
5. **Recent Findings** - What was learned?
6. **Unresolved Unknowns** - What's unclear?
7. **Dead Ends** - What doesn't work?
8. **Mistakes** - What failed and why?

---

## Benefits Summary

### For AI Agents

✅ **Reduced Context Loading Time**: Skip manual git archaeology, findings already loaded  
✅ **Decision Quality**: Base decisions on evidence, not guesses  
✅ **Error Prevention**: See what failed before, don't repeat  
✅ **Continuity**: Previous session's endpoint becomes your starting point  
✅ **Confidence**: Uncertainty levels guide decision gates

### For Project Health

✅ **Issue Tracking**: All bugs/TODOs auto-captured  
✅ **Knowledge Preservation**: Findings survive session boundaries  
✅ **Learning History**: Track what was learned and when  
✅ **Error Pattern Detection**: Mistakes and dead ends show gaps  
✅ **Cognitive Load Reduction**: System manages complexity

### For Teams

✅ **Multi-AI Handoffs**: Each AI sees exactly where others left off  
✅ **Mistake Prevention**: Shared dead ends database  
✅ **Progress Visibility**: Bootstrap shows actual project state  
✅ **Onboarding**: New AIs get complete epistemic snapshot  
✅ **Accountability**: All work logged with reasoning

---

## Next Steps

**Phase 3: Semantic Integration**
- Use Qdrant vector store to find semantically similar findings
- Auto-recommend related unknowns and dead ends
- Predict likely issues based on code changes

**Phase 4: Predictive Handoffs**
- Anticipate next AI's needs based on current trajectory
- Pre-stage relevant findings and unknowns
- Suggest optimal work priorities

**Phase 5: Cross-Project Learning**
- Share findings across projects with same tech stack
- Learn from mistakes in similar architectures
- Accelerate onboarding with project templates

---

## Conclusion

Empirica's `project-bootstrap` enables **true epistemic continuity** by capturing:
- **Health**: AI readiness and capability levels
- **Clarity**: Understanding depth and concept coherence
- **Relevance**: Context alignment to current work

Together, these dimensions create a system where AI agents hand off complete epistemic state, not just code - enabling genuine knowledge transfer and cumulative learning across session boundaries.
