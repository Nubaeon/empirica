# Schema Migration Investigation - Using Empirica CASCADE

## Investigation Goal

Use Empirica's CASCADE workflow to deeply investigate the schema migration questions before making changes.

## Questions to Answer

### Question 1: CLI Format During Transition
**Should CLI accept both formats during transition period, or force immediate migration?**

Investigation approach:
- Map all CLI command consumers (who/what calls them?)
- Check if any external tools/scripts parse CLI output
- Assess risk of breaking changes
- User preference: "force migration" - but verify implications

### Question 2: PersonaHarness Schema Usage
**Does PersonaHarness already use EpistemicAssessmentSchema from Phase 3 work?**

Investigation approach:
- Examine `empirica/core/persona/harness/persona_harness.py`
- Check what assessment format it creates/consumes
- Look for imports of either schema
- Test if it's already compatible

### Question 3: VectorState Backwards Compatibility
**Should we keep VectorState for backwards compatibility in git notes, or force full migration?**

Investigation approach:
- Check git notes format in existing repos
- See if any git notes exist with OLD format
- Assess cost of conversion vs keeping compatibility
- User preference: "force migration" acceptable

## CASCADE Workflow for Investigation

### PREFLIGHT Assessment

**Task**: Investigate schema migration questions to inform technical decisions

**Context**:
- Two schemas exist: OLD (reflex_frame.py) and NEW (schemas/epistemic_assessment.py)
- User wants to force migration, acceptable to break things
- Need to understand: CLI usage, PersonaHarness integration, git notes format
- Critical: Make informed decision before changing core architecture

**Initial Epistemic State**:
- ENGAGEMENT: 0.85 (high - important architecture decision)
- KNOW: 0.40 (low - don't know current PersonaHarness implementation)
- DO: 0.70 (can investigate code, search patterns)
- CONTEXT: 0.60 (understand CASCADE and schemas, but not full integration)
- CLARITY: 0.75 (questions are clear, outcomes defined)
- COHERENCE: 0.70 (logical investigation plan)
- SIGNAL: 0.65 (know where to look)
- DENSITY: 0.50 (moderate complexity - 3 focused questions)
- STATE: 0.45 (starting point - no investigation done yet)
- CHANGE: 0.40 (investigation will gather new info)
- COMPLETION: 0.0 (haven't started)
- IMPACT: 0.85 (high - affects core architecture decision)
- UNCERTAINTY: 0.60 (moderate - code exists, just need to read it)

**Recommended Action**: INVESTIGATE

### INVESTIGATE Phase - Round 1

#### Investigation Strategy 1: PersonaHarness Schema Usage

**Objective**: Determine if PersonaHarness uses EpistemicAssessmentSchema

**Tools to use**:
1. `grep` - search for schema imports
2. `open_files` - read PersonaHarness implementation
3. `expand_code_chunks` - examine assessment handling

**Commands**:
```bash
# Find schema imports in PersonaHarness
grep -r "from empirica.core.schemas" empirica/core/persona/

# Find any assessment creation/usage
grep -r "EpistemicAssessment" empirica/core/persona/

# Check what PersonaHarness returns
grep -A 20 "def assess" empirica/core/persona/harness/persona_harness.py
```

**Expected findings**:
- Import statements showing which schema is used
- Assessment creation code
- Assessment handling/processing code

#### Investigation Strategy 2: CLI Command Consumers

**Objective**: Understand who/what depends on current CLI format

**Tools to use**:
1. `grep` - search for CLI command calls
2. Search documentation for CLI examples
3. Check test files for CLI usage patterns

**Commands**:
```bash
# Find CLI command calls in codebase
grep -r "empirica preflight" .
grep -r "empirica check" .
grep -r "empirica postflight" .

# Check MCP server (wraps CLI)
grep -A 10 "submit.*assessment" mcp_local/empirica_mcp_server.py

# Check if any scripts parse CLI output
find . -name "*.sh" -o -name "*.py" | xargs grep "empirica.*json"
```

**Expected findings**:
- MCP server is main consumer (wraps CLI)
- Test files may call CLI directly
- Documentation examples show format

#### Investigation Strategy 3: Git Notes Format Analysis

**Objective**: Determine if git notes contain OLD format assessments

**Tools to use**:
1. `bash` - check git notes in current repo
2. `grep` - search for VectorState in git notes storage code
3. Examine serialization logic

**Commands**:
```bash
# Check if git notes exist in this repo
git notes list | head -5

# Examine one if exists
git notes show $(git notes list | head -1) 2>/dev/null | head -30

# Check serialization code
grep -A 20 "def.*serialize" empirica/core/canonical/git_enhanced_reflex_logger.py
```

**Expected findings**:
- Current git notes format (if any exist)
- Serialization strategy (JSON? pickle? custom?)
- Whether format version is tracked

### CHECK Phase - Decision Criteria

After investigation, can proceed if:
- ✅ Know whether PersonaHarness uses NEW schema
- ✅ Know who consumes CLI output (MCP only? others?)
- ✅ Know if git notes contain OLD format data
- ✅ Confidence >= 0.75 to make architecture decision

**If confidence < 0.75**: Need more investigation rounds

### ACT Phase - Document Findings

Create decision matrix:
```markdown
| Question | Finding | Decision | Rationale |
|----------|---------|----------|-----------|
| CLI format during transition | ... | Force migration | ... |
| PersonaHarness schema | ... | Already uses NEW / Needs update | ... |
| VectorState git notes | ... | Force migration / Keep compat | ... |
```

### POSTFLIGHT - Learning Assessment

**What did we learn?**
- Actual state of PersonaHarness integration
- Real CLI consumer patterns
- Git notes format implications

**Epistemic deltas**:
- KNOW: 0.40 → 0.85 (learned implementation details)
- CONTEXT: 0.60 → 0.90 (understand full integration picture)
- UNCERTAINTY: 0.60 → 0.25 (can make informed decision)
- COMPLETION: 0.0 → 1.0 (investigation complete)

**Calibration check**:
- Did findings match expectations?
- Were there surprises?
- Do we need additional investigation?

---

## Execution

Let's run this investigation now using the tools...
