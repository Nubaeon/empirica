# 📝 Documentation Cleanup TODO (Next Session)

## ✅ Already Updated:
1. CANONICAL_SYSTEM_PROMPT.md - Added sections VIII & IX (static context)
2. CHANGELOG.md - Comprehensive release notes for today's work
3. .github/copilot-instructions.md - AI naming convention added

## 🔴 NEEDS REMOVAL (Deprecated Commands):

### docs/reference/CLI_COMMANDS_*.md
**Search for and remove references to:**
- `assess`, `self-awareness`, `metacognitive`, `calibration`, `uvl` (5 assessment)
- `decision`, `decision-batch`, `feedback` (3 decision)
- `profile-list`, `profile-show`, `profile-create`, `profile-set-default` (4 profile)
- `list`, `explain`, `demo` (3 components)
- `bootstrap` (use `project-bootstrap` instead)

**Action:** 
```bash
# Find files mentioning deprecated commands
grep -l "assess\|profile-list\|decision-batch\|bootstrap[^-]" docs/reference/*.md

# Manual review and removal needed
```

### docs/guides/*.md
**Check for outdated workflow patterns:**
- Old assessment workflow (pre-CASCADE)
- References to removed commands
- Obsolete best practices

**Files to review:**
- SESSION_GOAL_WORKFLOW.md (might reference old commands)
- Any guides mentioning "assess your knowledge" (should use PREFLIGHT)

## 🟡 NEEDS ADDITION (New Features):

### 1. Flow State Metrics Guide
**File:** `docs/guides/FLOW_STATE_OPTIMIZATION.md` (NEW)
**Content:**
- 6 components explained (CASCADE, Bootstrap, Goals, Learning, CHECK, Continuity)
- How to interpret flow scores (⭐ 🟢 🟡 🔴)
- What actions improve each component
- Example: "File tree session scored 1.00 because..."

### 2. Epistemic Environmental Awareness Guide  
**File:** `docs/guides/ENVIRONMENTAL_AWARENESS.md` (NEW)
**Content:**
- File tree usage and caching
- DB schema summary (orthogonal view)
- Structure health analyzer (pattern detection)
- How to use bootstrap effectively

### 3. CLI Telemetry Reference
**File:** `docs/reference/CLI_TELEMETRY.md` (NEW)
**Content:**
- What's tracked (command, time, success, error)
- Privacy (all local, no external)
- How to query usage stats
- Legacy detection criteria

### 4. Static vs Dynamic Context
**File:** `docs/architecture/STATIC_DYNAMIC_CONTEXT.md` (NEW)
**Content:**
- What belongs in system prompts (static)
- What belongs in bootstrap (dynamic)
- Clear examples of each
- Why the separation matters

## 🟢 NEEDS UPDATE (Existing Files):

### docs/reference/CLI_COMMANDS_COMPLETE.md
**Updates needed:**
- Remove 16 deprecated commands
- Add notes about CASCADE superseding old assessment
- Update command count (54 → 38)

### docs/reference/MCP_CLI_MAPPING.md
**Updates needed:**
- Remove mappings for deprecated commands
- Ensure CASCADE commands are properly mapped

### docs/architecture/EMPIRICA_SYSTEM_OVERVIEW.md
**Updates needed:**
- Add flow state metrics system
- Add epistemic environmental awareness
- Update with static/dynamic context separation

### docs/guides/FIRST_TIME_SETUP.md
**Updates needed:**
- Reference new bootstrap features
- Mention AI naming convention
- Update example workflows

## 📋 Quick Scan Results:

**Files likely needing updates:**
- docs/reference/CLI_COMMANDS_*.md (remove deprecated)
- docs/guides/SESSION_GOAL_WORKFLOW.md (check for old patterns)
- docs/architecture/*.md (add new systems)

**New files to create:**
- FLOW_STATE_OPTIMIZATION.md
- ENVIRONMENTAL_AWARENESS.md
- CLI_TELEMETRY.md
- STATIC_DYNAMIC_CONTEXT.md

## 🎯 Priority for Next Session:

**HIGH:**
1. Remove deprecated command references (prevent confusion)
2. Create FLOW_STATE_OPTIMIZATION.md (document novel contribution)
3. Update CLI_COMMANDS_COMPLETE.md (accurate reference)

**MEDIUM:**
4. Create ENVIRONMENTAL_AWARENESS.md (explain new features)
5. Update SYSTEM_OVERVIEW.md (architectural changes)

**LOW:**
6. Create CLI_TELEMETRY.md (nice to have)
7. Create STATIC_DYNAMIC_CONTEXT.md (already in CANONICAL)

