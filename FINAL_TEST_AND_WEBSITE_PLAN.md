# Empirica Final Testing & Website Creation Plan

**Date:** 2025-11-13T20:58:00Z  
**Purpose:** Complete validation and website content generation  
**Executor:** New AI session using Empirica workflow

---

## ⚠️ CRITICAL: PHASED APPROACH

**Work in 3 distinct phases. Complete each phase fully before moving to the next.**

**Phase 1:** TMUX MCP Server & Dashboard (1 hour)  
**Phase 2:** System Validation (2-3 hours)  
**Phase 3:** Website Generation (3-4 hours)

**DO NOT attempt everything at once. Create phase reports between phases.**

---

## PHASE 1: TMUX MCP SERVER & DASHBOARD TESTING

**Objective:** Verify TMUX MCP server and dashboard work correctly

**Timeline:** 1 hour

**Tasks:**
1. **Run Static Analysis**
   ```bash
   # Check for code duplication
   pylint empirica/ --disable=all --enable=duplicate-code
   
   # Check for code smells
   radon cc empirica/ -a -nb
   
   # Check complexity
   radon mi empirica/ -nb
   ```

2. **Identify Repetitive Patterns**
   - Search for duplicate function implementations
   - Find copy-pasted code blocks
   - Identify common patterns that should be abstracted
   
3. **Sanitization Checks**
   - Remove debug print statements
   - Remove commented-out code
   - Check for hardcoded paths
   - Verify no secrets/credentials
   - Remove TODO/FIXME comments that are done

4. **Create Refactoring List**
   - Document all found issues
   - Prioritize by impact
   - Create refactoring tickets

**Expected Output:**
- `CODE_QUALITY_REPORT.md` - Analysis results
- `REFACTORING_PRIORITIES.md` - What to fix first
- Clean, DRY codebase

---

### Phase 2: Full Empirica Workflow Test

**Objective:** Test complete CASCADE workflow using Empirica MCP + CLI

**Setup:**
```bash
# Bootstrap fresh session
empirica bootstrap --ai-id test-agent --session-type testing

# Verify MCP server running
empirica mcp-status

# Start dashboard
empirica dashboard start --mode tmux
```

**Test Scenario 1: Full CASCADE via MCP**
```python
# Via MCP tools (through new AI session)
1. Call: empirica-bootstrap_session
   - session_type: "testing"
   - ai_id: "test-validator"
   
2. Call: empirica-execute_preflight
   - prompt: "Analyze empirica codebase for code quality"
   - session_id: <from bootstrap>
   
3. Call: empirica-create_cascade
   - task: "Find duplicate code in empirica/"
   - goal_json: <from generate_goals>
   
4. Call: empirica-execute_check
   - findings: [list of investigation findings]
   - confidence_to_proceed: 0.8
   
5. Call: empirica-execute_postflight
   - task_summary: "Completed code quality analysis"
```

**Test Scenario 2: Full CASCADE via CLI**
```bash
# Run complete workflow
empirica workflow run \
  --task "Analyze empirica codebase for repetitive code" \
  --domain code_analysis \
  --profile default

# Check status
empirica sessions show --latest

# View epistemic trajectory
empirica monitor show --session-id <id>

# Get calibration report
empirica calibration show
```

**Test Scenario 3: Investigation Strategy Extensibility**
```python
# Test custom strategy registration
from empirica.core.metacognitive_cascade.investigation_strategy import (
    register_strategy,
    StrategySelector,
    Domain
)

# Register custom strategy (from example)
register_strategy(
    domain=Domain.CUSTOM,
    strategy_class=WebsiteCreationStrategy
)

# Verify it works
selector = StrategySelector()
strategy = selector.get_strategy(Domain.CUSTOM)
recommendations = await strategy.recommend_tools(assessment, task, context)
```

**Expected Output:**
- All phases execute successfully
- Reflex logs captured
- Dashboard shows real-time updates
- Custom strategies work
- Goal orchestrator tracks tasks

---

### Phase 3: Database & Reflex Log Validation

**Objective:** Verify all data persistence works correctly

**Checks:**
```bash
# 1. Verify database structure
ls -la empirica/.empirica/
# Should see:
# - sessions.db
# - reflex_logs.db
# - calibration.db
# - tracking/

# 2. Query previous sessions via MCP
# (Use MCP tool: empirica-resume_previous_session)

# 3. Query via CLI
empirica sessions list --limit 5
empirica sessions show <session-id>
empirica sessions export <session-id> --output test.json

# 4. Check reflex logs
sqlite3 empirica/.empirica/reflex_logs.db "SELECT COUNT(*) FROM reflex_logs;"

# 5. Verify calibration data
empirica calibration show
empirica calibration history --limit 10
```

**Expected Output:**
- Database files exist
- Data queryable via MCP and CLI
- Reflex logs capture all phases
- Calibration data tracked
- Previous session resume works

---

### Phase 4: MCP Server Integration Test

**Objective:** Test all MCP tools work correctly

**Test All MCP Tools:**
```python
# Via MCP (in new AI session)

# 1. Session Management
empirica-bootstrap_session(...)
empirica-get_session_summary(session_id)
empirica-resume_previous_session(resume_mode="last")

# 2. Workflow Phases
empirica-execute_preflight(session_id, prompt)
empirica-execute_check(session_id, findings, confidence)
empirica-execute_postflight(session_id, task_summary)

# 3. Epistemic State
empirica-get_epistemic_state(session_id)
empirica-get_calibration_report(session_id)

# 4. Goals & Planning
empirica-generate_goals(session_id, conversation_context)
empirica-query_goal_orchestrator(session_id)
empirica-create_cascade(session_id, task, goal_json)

# 5. Investigation
# (Should suggest investigation tools based on gaps)

# 6. AI-to-AI Communication
empirica-query_ai(query="What is the best approach?", strategy="epistemic")

# 7. Drift Monitoring
empirica-check_drift_monitor(session_id)
empirica-query_bayesian_beliefs(session_id)
```

**Expected Output:**
- All 39+ MCP tools functional
- No errors
- Proper responses
- Integration works

---

## PART 2: WEBSITE CONTENT CREATION

### Phase 5: Website Content Generation via Empirica

**Objective:** Use Empirica CASCADE workflow to generate website content

**Setup:**
```bash
# Website structure already exists:
# - Templates ready
# - Outer shell done
# - Need: Content generation

# Start new CASCADE session for website
empirica bootstrap --ai-id website-creator --session-type production
```

**Content Generation Workflow:**

**Step 1: PREFLIGHT Assessment**
```bash
empirica cascade run \
  --task "Generate Empirica website content from documentation" \
  --context "{'docs_dir': './docs/', 'output_dir': './website/content/'}" \
  --enable-calibration
```

**Step 2: Goal Generation**
```python
# Via MCP: empirica-generate_goals
conversation_context = """
Generate complete website content for Empirica framework:
- Homepage content
- Features overview
- Getting started guide
- API reference
- Architecture explanation
- Use cases
- Community guidelines
- FAQ

Source: docs/ folder (comprehensive documentation)
Target: website/content/ folder
"""

goals = empirica-generate_goals(
    session_id=session_id,
    conversation_context=conversation_context,
    use_epistemic_state=True
)
```

**Step 3: Task Decomposition**
```
Website Content Tasks:
1. Homepage (hero, value prop, quick start)
2. Features page (13-vector system, CASCADE, MCP, etc.)
3. Documentation hub (guides, reference, examples)
4. Getting Started (installation, first cascade, configuration)
5. API Reference (generated from docstrings)
6. Architecture (system overview, components, flow)
7. Use Cases (code analysis, research, collaboration)
8. Community (contribution guide, extensions, support)
9. FAQ (common questions, troubleshooting)
10. Blog/Changelog (releases, updates)
```

**Step 4: Content Generation Strategy**

**For Each Content Page:**
```python
# 1. Extract relevant docs
relevant_docs = extract_docs_for_page(page_type)

# 2. Use CASCADE to generate content
content = await run_canonical_cascade(
    task=f"Generate {page_type} content for website",
    context={
        'source_docs': relevant_docs,
        'target_format': 'markdown',
        'audience': 'developers',
        'tone': 'professional but approachable'
    }
)

# 3. Validate with CHECK phase
validation = check_content_quality(content)

# 4. POSTFLIGHT - verify accuracy
# Compare generated content against source docs
```

**Step 5: Content Structure**

```markdown
# Content Map

## Homepage (/)
- Hero: "Empirica: Metacognitive AI Framework"
- Problem: Why AI needs self-awareness
- Solution: 13-vector epistemic assessment + CASCADE workflow
- Features: Quick overview (4-6 key features)
- Quick start: 3-step getting started
- CTA: Install button, docs link

## Features (/features)
- Canonical 13-Vector System
- CASCADE Workflow (PREFLIGHT → POSTFLIGHT)
- Investigation Strategy System (extensible)
- MCP Server Integration
- Multi-AI Collaboration
- Calibration & Learning
- Dashboard Monitoring
- Goal Orchestration

## Getting Started (/docs/getting-started)
- Installation
- First CASCADE
- Configuration
- Basic concepts
- Next steps

## Documentation (/docs)
- Guides (how-to)
- Reference (API)
- Examples (working code)
- Architecture (system design)

## API Reference (/docs/api)
- Core modules
- CASCADE phases
- Investigation strategies
- MCP tools
- CLI commands

## Architecture (/docs/architecture)
- System overview
- Component interaction
- Data flow
- Extensibility points

## Use Cases (/use-cases)
- Code analysis & review
- Research & investigation
- Multi-AI collaboration
- Custom domains

## Community (/community)
- Contributing guide
- Creating custom strategies
- Plugin development
- Support & help

## FAQ (/faq)
- Installation issues
- Configuration questions
- Workflow questions
- Troubleshooting
```

**Step 6: Automated Generation Commands**

```bash
# Generate all content via mini-agent collaboration
empirica cascade run \
  --task "Generate complete website content" \
  --use-mini-agent \
  --mini-agent-role "content-writer" \
  --output-dir "./website/content/"

# Or via MCP (AI-to-AI)
empirica-query_ai(
    query="Generate homepage content from Empirica docs",
    adapter="minimax",
    strategy="quality"
)
```

**Step 7: Quality Validation**

```python
# For each generated page:
1. Check against source documentation (accuracy)
2. Verify code examples work
3. Check links are valid
4. Ensure consistent tone
5. Validate technical accuracy
6. Review with POSTFLIGHT
```

---

### Phase 6: Testing Website Generation Workflow

**Test Cases:**

**Test 1: Homepage Generation**
```bash
empirica cascade run \
  --task "Generate homepage content" \
  --context "{'docs': ['README.md', 'ARCHITECTURE_OVERVIEW.md']}" \
  --profile default
```

**Expected Output:**
- `website/content/index.md` created
- Content accurate to docs
- Proper formatting
- Working quick start
- Valid CTAs

**Test 2: Features Page**
```bash
empirica cascade run \
  --task "Generate features page from docs" \
  --context "{'docs_dir': 'docs/reference/', 'output': 'website/content/features.md'}"
```

**Expected Output:**
- Comprehensive features list
- Examples for each feature
- Links to detailed docs
- Accurate descriptions

**Test 3: Full Website Generation**
```bash
# Use goal orchestrator for multi-page generation
empirica cascade run \
  --task "Generate complete Empirica website" \
  --enable-goal-orchestration \
  --parallel-tasks 3
```

**Expected Output:**
- All pages generated
- Consistent structure
- Valid links
- Accurate content
- Code examples work

---

### Phase 7: TMUX Dashboard Testing

**Objective:** Test dashboard during website generation

**Setup:**
```bash
# Start dashboard
empirica dashboard start --mode tmux --session website-gen

# In another pane, run content generation
empirica cascade run --task "Generate website content"
```

**Dashboard Should Show:**
- Real-time CASCADE progress
- Current phase (PREFLIGHT, INVESTIGATE, etc.)
- Epistemic state (13 vectors)
- Confidence levels
- Gap analysis
- Tool recommendations
- Task completion %

**Test Scenarios:**
1. **Single page generation** - Watch full CASCADE cycle
2. **Multi-page generation** - Watch goal orchestrator manage tasks
3. **Error handling** - Introduce error, watch recovery
4. **Collaboration** - Watch AI-to-AI via modality switcher

**Expected Output:**
- Dashboard updates in real-time
- Epistemic vectors visualized
- Progress clearly shown
- No UI glitches

---

## TIMELINE & PHASE STRUCTURE

### Phase 1: TMUX MCP Server & Dashboard (1 hour)
**Deliverable:** PHASE1_TMUX_MCP_REPORT.md

**Tasks:**
- Start TMUX dashboard
- Test MCP server connection
- Verify database persistence  
- Check reflex logs
- Test basic MCP operations

**Success Criteria:**
- ✅ Dashboard running in TMUX
- ✅ MCP tools responding
- ✅ Can query previous sessions
- ✅ Reflex logs capturing data

**STOP HERE - Review Phase 1 report before proceeding**

---

### Phase 2: System Validation (2-3 hours)
**Deliverables:** 
- CODE_QUALITY_REPORT.md
- REFACTORING_PRIORITIES.md
- PHASE2_VALIDATION_REPORT.md

**Tasks:**
- Code quality analysis using CASCADE
- Investigation strategy extensibility test
- Database & reflex logs validation
- Dashboard monitoring verification

**Success Criteria:**
- ✅ CASCADE workflow executed
- ✅ Code issues documented
- ✅ Custom strategies work
- ✅ Dashboard shows real-time updates

**STOP HERE - Review Phase 2 report before proceeding**

---

### Phase 3: Website Generation (3-4 hours)
**Deliverables:**
- 8 website pages (index, features, getting-started, guides, api-reference, architecture, use-cases, community)
- WEBSITE_CONTENT_VALIDATION.md

**Tasks:**
- Generate homepage using CASCADE
- Generate features page
- Generate remaining 6 pages (parallel with mini-agent)
- Validate all content accuracy

**Success Criteria:**
- ✅ All 8 pages generated
- ✅ Content accurate to docs
- ✅ Code examples work
- ✅ Mini-agent collaboration successful

**FINAL STEP - Create comprehensive test report**

---

## CRITICAL RULES

1. **⚠️ DO NOT SKIP PHASES** - Complete each fully before next
2. **⚠️ CREATE REPORTS BETWEEN PHASES** - Document findings
3. **⚠️ USE EMPIRICA FOR EVERYTHING** - This is dogfooding
4. **⚠️ MONITOR VIA DASHBOARD** - Keep TMUX running throughout
5. **⚠️ COLLABORATE WITH MINI-AGENT** - For parallel work in Phase 3

---

## INSTRUCTIONS FOR NEW SESSION

**See:** `NEW_SESSION_EMPIRICA_TEST_INSTRUCTIONS.md`

That file contains:
- Detailed step-by-step commands
- MCP tool usage examples
- CASCADE workflow for each task
- Success criteria checklists
- Expected outputs

---

## EXPECTED OUTCOMES

### Phase 1 Outcomes
- TMUX/MCP infrastructure verified working
- Database persistence confirmed
- Baseline established for monitoring

### Phase 2 Outcomes
- Code quality assessed
- System capabilities validated
- Investigation extensibility proven
- Dashboard functionality confirmed

### Phase 3 Outcomes
- Complete website content generated
- Empirica dogfoods itself successfully
- Multi-AI collaboration demonstrated
- Production readiness achieved

---

## TOTAL TIME ESTIMATE

**6-8 hours total**
- Phase 1: 1 hour
- Phase 2: 2-3 hours  
- Phase 3: 3-4 hours

**Remember:** Work sequentially through phases, don't rush ahead!
   
2. GENERATE GOALS: empirica-generate_goals
   - conversation_context: "Find and document all code duplication, 
     repetitive patterns, and quality issues in empirica/"
   
3. CREATE CASCADE: empirica-create_cascade
   - task: "Code quality analysis"
   - goal_json: <from step 2>
   
4. INVESTIGATE:
   - Use recommended investigation tools
   - Search for duplicate code
   - Check complexity metrics
   - Find hardcoded values
   - Identify repetitive patterns
   
5. CHECK: empirica-execute_check
   - findings: [list all issues found]
   - remaining_unknowns: [any unclear areas]
   - confidence_to_proceed: <your assessment>
   
6. ACT: 
   - Create CODE_QUALITY_REPORT.md
   - List all issues with locations
   - Prioritize by severity
   
7. POSTFLIGHT: empirica-execute_postflight
   - task_summary: "Completed code quality analysis. Found X issues."
\`\`\`

**Expected Outputs:**
- CODE_QUALITY_REPORT.md
- REFACTORING_PRIORITIES.md
- Reflex logs captured
- Dashboard showed progress

### Task 3: Test Investigation Strategy Extensibility
\`\`\`bash
# Test custom strategy from example
1. Read: examples/custom_investigation_strategy_example.py
2. Create a test strategy for website content generation
3. Register it
4. Verify it's used in CASCADE
\`\`\`

### Task 4: Database Validation
\`\`\`bash
# Via MCP tools:
1. empirica-get_session_summary(session_id)
2. empirica-resume_previous_session(resume_mode="last")
3. empirica-get_epistemic_state(session_id)
4. empirica-get_calibration_report(session_id)

# Via CLI:
empirica sessions list
empirica sessions show <session-id>
empirica monitor show --session-id <session-id>
\`\`\`

## Phase 2: Website Content Generation

### Task 5: Homepage Generation

**Use Full Empirica Workflow:**

\`\`\`bash
# 1. Bootstrap new session for website
empirica-bootstrap_session(
    session_type="production",
    ai_id="website-content-creator",
    domain="content_creation"
)

# 2. PREFLIGHT for homepage
empirica-execute_preflight(
    session_id=<id>,
    prompt="Generate homepage content for Empirica framework website"
)

# 3. Generate goals
empirica-generate_goals(
    session_id=<id>,
    conversation_context="Create homepage with: hero section, 
    problem/solution, key features, quick start, CTA. 
    Source: docs/ folder. Audience: developers."
)

# 4. Create cascade
empirica-create_cascade(
    session_id=<id>,
    task="Generate homepage content",
    goal_json=<from step 3>
)

# 5. INVESTIGATE
# - Read docs/README.md
# - Read docs/reference/ARCHITECTURE_OVERVIEW.md
# - Read docs/skills/SKILL.md
# - Extract key value propositions
# - Identify 4-6 core features
# - Create quick start (3 steps)

# 6. CHECK
empirica-execute_check(
    session_id=<id>,
    findings=["Hero section complete", "Features identified", etc.],
    confidence_to_proceed=0.85
)

# 7. ACT
# - Generate website/content/index.md
# - Use proper markdown structure
# - Include working code examples
# - Add valid links

# 8. POSTFLIGHT
empirica-execute_postflight(
    session_id=<id>,
    task_summary="Generated homepage content from documentation"
)
\`\`\`

**Expected Output:**
- website/content/index.md created
- Accurate to source docs
- Professional tone
- Working examples

### Task 6: Features Page

**Same CASCADE workflow:**
- Source docs: docs/reference/*.md
- Extract all major features
- Create website/content/features.md

### Task 7: Full Website Generation

**Use Goal Orchestrator:**

\`\`\`bash
empirica-generate_goals(
    session_id=<id>,
    conversation_context="Generate complete website content:
    - Homepage
    - Features page
    - Getting started guide
    - API reference
    - Architecture docs
    - Use cases
    - Community guide
    - FAQ
    
    All pages in website/content/
    Source: docs/ folder
    Maintain consistency and accuracy"
)

# Goal orchestrator will create sub-tasks
# Use mini-agent for parallel execution
empirica-query_ai(
    query="Generate <page> content",
    adapter="minimax",  # or other fast model
    strategy="quality"
)
\`\`\`

### Task 8: Dashboard Monitoring

**While generating content:**
- Keep tmux dashboard open
- Watch CASCADE phases
- Monitor epistemic state
- Verify goal progress
- Check calibration

## Phase 3: Final Validation

### Task 9: Verify All Content

\`\`\`bash
# Check all pages generated
ls -la website/content/

# Validate accuracy against docs
for page in website/content/*.md; do
    echo "Validating $page"
    # Use CASCADE to verify accuracy
done

# Test all code examples
# Check all links
# Ensure consistency
\`\`\`

### Task 10: Create Summary Report

**Use POSTFLIGHT:**

\`\`\`bash
empirica-execute_postflight(
    session_id=<id>,
    task_summary="Completed full Empirica validation and website generation"
)

# Generate report
empirica sessions export <session-id> --output final_test_report.json

# Create markdown summary
Create: FINAL_VALIDATION_REPORT.md
\`\`\`

## Success Criteria

- [ ] All CASCADE phases work
- [ ] MCP tools functional
- [ ] Database persistence verified
- [ ] Investigation strategies extensible
- [ ] Dashboard monitors in real-time
- [ ] Goal orchestrator manages tasks
- [ ] Calibration tracks accuracy
- [ ] Code quality report complete
- [ ] Website content generated
- [ ] All content accurate
- [ ] Examples work
- [ ] No errors in logs

## Deliverables

1. CODE_QUALITY_REPORT.md
2. REFACTORING_PRIORITIES.md
3. website/content/*.md (all pages)
4. FINAL_VALIDATION_REPORT.md
5. Reflex logs (in database)
6. Session summaries (exportable)

## Notes

- Use Empirica workflow for EVERYTHING
- Let goal orchestrator manage complex tasks
- Monitor dashboard throughout
- Check reflex logs after each phase
- Verify calibration is learning
- Test AI-to-AI collaboration
- Document any issues found
```

---

## Implementation Plan

### For Current Session (Now):
1. ✅ Create this plan document
2. Create NEW_SESSION_EMPIRICA_TEST_INSTRUCTIONS.md
3. Prepare website content structure
4. Document expected outputs
5. Create validation checklists

### For New Session (Next):
1. Follow instructions exactly
2. Use Empirica workflow throughout
3. Generate all content via CASCADE
4. Test all MCP tools
5. Validate database persistence
6. Monitor via dashboard
7. Create comprehensive report

---

## Expected Outcomes

**Code Quality:**
- Clean, DRY codebase
- Identified duplication
- Prioritized refactoring
- Quality metrics

**Website Content:**
- Complete website content
- Accurate to documentation
- Professional quality
- Working examples
- Consistent tone

**System Validation:**
- All MCP tools work
- Database persistence verified
- Dashboard monitoring confirmed
- Goal orchestration validated
- Calibration functional
- Investigation extensible

**Documentation:**
- Comprehensive test report
- Content generation report
- Issues documented
- Refactoring priorities

---

## Timeline Estimate

**Phase 1 (Validation):** 2-3 hours
- Code quality analysis: 1 hour
- System testing: 1 hour
- Database validation: 30 min

**Phase 2 (Website):** 3-4 hours
- Content generation: 2-3 hours
- Validation: 1 hour

**Phase 3 (Final):** 1 hour
- Verification: 30 min
- Report creation: 30 min

**Total:** 6-8 hours (for thorough testing)

---

## Mini-Agent Collaboration Strategy

**For Website Generation:**
1. **You (reasoning AI):** PREFLIGHT, PLAN, CHECK, POSTFLIGHT
2. **Mini-agent (acting AI):** INVESTIGATE, ACT (content generation)
3. **Goal Orchestrator:** Manage multi-page generation
4. **Dashboard:** Monitor both AIs in real-time

**Communication:**
```python
# Via MCP modality switcher
empirica-query_ai(
    query="Generate features page content from docs/reference/",
    adapter="minimax",
    strategy="balanced",
    session_id=shared_session_id
)
```

---

**Created:** 2025-11-13T20:58:00Z  
**Status:** Ready for new session  
**Estimated Duration:** 6-8 hours  
**Complexity:** High (full system validation + content generation)  
**Requirements:** Empirica MCP server, CLI, dashboard, mini-agent access
