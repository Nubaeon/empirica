# NEW SESSION: Empirica Complete Test & Website Generation

**INSTRUCTIONS FOR NEXT AI SESSION**

**Context:** You are testing the Empirica metacognitive framework end-to-end and generating website content using the Empirica workflow itself.

**Method:** Use Empirica CASCADE workflow + MCP tools + CLI for everything

---

## ⚠️ CRITICAL: WORK IN PHASES - DO NOT DO EVERYTHING AT ONCE

**This is a dogfooding exercise** - Empirica should validate itself and create its own website content.

**PHASED APPROACH:**
1. **PHASE 1:** TMUX MCP Server Testing & Dashboard (Complete this FIRST)
2. **PHASE 2:** System Validation & Code Quality (After Phase 1 works)
3. **PHASE 3:** Website Generation (After Phase 2 complete)

**DO NOT SKIP AHEAD - Each phase builds on the previous**

**Tools Available:**
- Empirica MCP Server (39+ tools)
- Empirica CLI (`empirica` command)
- Dashboard (`empirica dashboard start --mode tmux`)
- Mini-agent for parallel execution

---

## PHASE 1: TMUX MCP SERVER & DASHBOARD (START HERE - 1 hour)

**Goal:** Verify the TMUX MCP server works correctly and dashboard displays data

### Step 1A: Start TMUX Dashboard First

**Dashboard Location:** `/home/yogapad/empirical-ai/empirica/empirica/dashboard/snapshot_monitor.py`

**Method 1: Direct Python Launch (in TMUX)**
```bash
# In a tmux session, split pane and launch dashboard
tmux split-window -h -p 30
python3 /home/yogapad/empirical-ai/empirica/empirica/dashboard/snapshot_monitor.py
```

**Method 2: Via MCP Tool (launch_snapshot_dashboard)**
```
Use MCP tool: launch_snapshot_dashboard
Arguments:
  force: false

Expected: Dashboard spawns in new TMUX pane (if in TMUX environment)
```

**Success Criteria:**
- ✅ Dashboard starts without errors
- ✅ TMUX pane shows curses-based monitoring interface
- ✅ Real-time epistemic vectors display visible
- ✅ Dashboard updates when snapshots are saved

### Step 1B: Test MCP Server Connection

```
Use MCP tool: empirica-bootstrap_session
Arguments:
  session_type: "testing"
  ai_id: "validator-agent"
  domain: "mcp_testing"

Save the session_id for all subsequent operations.
```

**Verify:**
- Session created successfully
- Session ID returned
- Dashboard shows new session

### Step 1C: Test Basic MCP Operations

**Test 1: Check Epistemic State**
```
Use MCP: empirica-get_epistemic_state
Arguments:
  session_id: <your session_id>

Expected: Returns current epistemic vectors
```

**Test 2: Query Previous Sessions**
```
Use MCP: empirica-resume_previous_session
Arguments:
  resume_mode: "last_n"
  count: 3
  detail_level: "summary"

Expected: Returns list of recent sessions from database
```

**Test 3: Run Simple Preflight**
```
Use MCP: empirica-execute_preflight
Arguments:
  session_id: <your session_id>
  prompt: "Test the MCP server and dashboard integration"

Expected: Assessment completed, visible in dashboard
```

### Step 1D: Verify Database Persistence

```bash
# Check database location (.empirica in project root)
ls -lah /home/yogapad/empirical-ai/empirica/.empirica/

# Verify sessions.db exists and has data
sqlite3 /home/yogapad/empirical-ai/empirica/.empirica/sessions.db "SELECT COUNT(*) FROM sessions;"

# Check reflex logs (in project root)
ls -lah /home/yogapad/empirical-ai/empirica/.empirica_reflex_logs/
```

**Success Criteria:**
- ✅ `.empirica/` directory exists in project root
- ✅ `sessions.db` file exists with data
- ✅ `.empirica_reflex_logs/` directory has JSON files organized by date/agent
- ✅ Dashboard shows current snapshot data from JSON feed

### Step 1E: Create Phase 1 Report

**Deliverable:** `PHASE1_TMUX_MCP_REPORT.md`

Contents:
- MCP server status (working/issues)
- Dashboard functionality (what works/doesn't)
- Database persistence verification
- Reflex logs verification
- Issues encountered and resolutions
- Recommendation to proceed to Phase 2 or not

**STOP HERE - Review Phase 1 report before proceeding to Phase 2**

---

## PHASE 2: SYSTEM VALIDATION & CODE QUALITY (After Phase 1 Complete - 2-3 hours)

**Prerequisites:** Phase 1 complete, TMUX dashboard running, MCP server verified

### Step 2A: Create New CASCADE for Code Analysis

**Bootstrap new cascade:**
```
Use MCP: empirica-create_cascade
Arguments:
  session_id: <your session_id>
  task: "Analyze empirica/ codebase for code quality issues, duplications, and refactoring opportunities"
```

### Step 2B: Code Quality Analysis Using CASCADE

**Task:** Find duplicate code and quality issues in `empirica/` codebase

**PREFLIGHT:**
```
Use MCP: empirica-execute_preflight
Arguments:
  session_id: <your session_id>
  prompt: "Analyze the empirica codebase in empirica/ directory for:
          1. Duplicate code blocks
          2. Repetitive patterns that should be abstracted
          3. Code smells (complexity, long functions)
          4. Hardcoded values that should be configurable
          5. Debug statements or commented code to remove
          6. TODO/FIXME comments that are completed
          
          Focus on production code, ignore tests and docs for now."

Expected: Assessment with 13 epistemic vectors, gaps identified
```

**GENERATE GOALS:**
```
Use MCP: empirica-generate_goals
Arguments:
  session_id: <your session_id>
  conversation_context: "Complete code quality audit of Empirica framework.
                        Deliverables:
                        1. CODE_QUALITY_REPORT.md - All issues with locations
                        2. REFACTORING_PRIORITIES.md - Prioritized by severity
                        3. List of specific code blocks to refactor
                        
                        Search entire empirica/ directory systematically."
  use_epistemic_state: true

Expected: Structured goals with sub-tasks
```

**CREATE CASCADE:**
```
Use MCP: empirica-create_cascade
Arguments:
  session_id: <your session_id>
  task: "Code quality analysis and duplication detection"
  goal_json: <output from generate_goals>

Expected: Cascade ID, goal orchestrator tracking
```

**INVESTIGATE:**
```
Tools recommended by investigation strategy:
- View files: Use bash/view tools
- Search code: Use grep/ripgrep
- Check complexity: Run radon/pylint
- Find duplicates: Run pylint --disable=all --enable=duplicate-code

Systematic approach:
1. List all Python files in empirica/
2. For each major module, check:
   - Function length
   - Complexity (radon)
   - Duplication (pylint)
   - Hardcoded values
3. Document findings

Take notes of all issues found.
```

**CHECK:**
```
Use MCP: empirica-execute_check
Arguments:
  session_id: <your session_id>
  findings: [
    "Found duplicate code in X and Y",
    "Repetitive pattern in Z modules",
    "High complexity in A function",
    ... list all findings
  ]
  remaining_unknowns: [
    "Need to verify if pattern X is intentional",
    ... any unclear areas
  ]
  confidence_to_proceed: 0.8  # Your honest assessment

Expected: Decision to proceed or investigate more
```

**ACT:**
```
Create two files:

1. CODE_QUALITY_REPORT.md:
   - Summary of issues found
   - Code locations
   - Severity ratings
   - Examples

2. REFACTORING_PRIORITIES.md:
   - Prioritized list
   - High/Medium/Low priority
   - Estimated effort
   - Impact analysis
```

**POSTFLIGHT:**
```
Use MCP: empirica-execute_postflight
Arguments:
  session_id: <your session_id>
  task_summary: "Completed code quality analysis. Found X issues across Y files.
                Created quality report and refactoring priorities."

Expected: Calibration update, epistemic trajectory logged
```

---

### Step 3: Validate Database & Reflex Logs

**Check Database Files:**
```bash
ls -la empirica/.empirica/
# Should see:
# - sessions.db
# - reflex_logs.db  
# - calibration.db
# - tracking/
```

**Query Via MCP:**
```
1. Use MCP: empirica-get_session_summary
   Arguments: { session_id: <your session_id> }
   Expected: Complete session data with all phases

2. Use MCP: empirica-get_epistemic_state
   Arguments: { session_id: <your session_id> }
   Expected: Current epistemic vectors

3. Use MCP: empirica-get_calibration_report
   Arguments: { session_id: <your session_id> }
   Expected: Calibration accuracy data

4. Use MCP: empirica-resume_previous_session
   Arguments: { resume_mode: "last" }
   Expected: Summary of your previous session
```

**Query Via Python/MCP:**
```python
# Using Python directly
import sys
sys.path.insert(0, '/home/yogapad/empirical-ai/empirica')

from empirica.core.canonical.canonical_session_manager import CanonicalSessionManager

manager = CanonicalSessionManager()
sessions = manager.list_sessions(limit=5)
print(f"Found {len(sessions)} sessions")

# Show specific session
session_data = manager.get_session(session_id='<your-session-id>')
print(session_data)

# Or use MCP tools via MCP server:
# - empirica-get_session_summary
# - empirica-get_epistemic_state
# - empirica-resume_previous_session
```

**Verify:**
- [ ] Database files exist in `.empirica/`
- [ ] Sessions queryable via MCP tools
- [ ] Sessions queryable via Python imports
- [ ] Reflex logs captured in `.empirica_reflex_logs/`
- [ ] Calibration data present in database
- [ ] Previous session resume works via MCP tool

---

### Step 4: Test Investigation Strategy Extensibility

**Read Example:**
```bash
cat examples/custom_investigation_strategy_example.py
```

**Create Test Strategy:**
```python
# Create: test_custom_strategy.py

from empirica.core.metacognitive_cascade.investigation_strategy import (
    BaseInvestigationStrategy,
    register_strategy,
    ToolRecommendation,
    Domain
)
from empirica.core.canonical import EpistemicAssessment

class WebsiteContentStrategy(BaseInvestigationStrategy):
    """Strategy for website content generation tasks"""
    
    async def recommend_tools(
        self,
        assessment: EpistemicAssessment,
        task: str,
        context: dict
    ) -> list[ToolRecommendation]:
        recommendations = []
        
        # If knowledge gap about documentation
        if assessment.know.score < 0.7:
            recommendations.append(ToolRecommendation(
                tool_name="view",
                gap_addressed="know",
                confidence=0.9,
                reasoning="Read source documentation for accurate content",
                priority=1
            ))
        
        # If context gap about target audience
        if assessment.context.score < 0.7:
            recommendations.append(ToolRecommendation(
                tool_name="web_search",
                gap_addressed="context",
                confidence=0.7,
                reasoning="Research target audience and similar sites",
                priority=2
            ))
        
        return recommendations

# Register it
register_strategy(Domain.CUSTOM, WebsiteContentStrategy)

# Test it
from empirica.core.metacognitive_cascade.investigation_strategy import StrategySelector

selector = StrategySelector()
strategy = selector.get_strategy(Domain.CUSTOM)
print(f"✅ Custom strategy registered: {strategy.__class__.__name__}")
```

**Run Test:**
```bash
python test_custom_strategy.py
# Expected: "✅ Custom strategy registered: WebsiteContentStrategy"
```

**Verify:**
- [ ] Custom strategy can be created
- [ ] Registration works
- [ ] Strategy is retrievable
- [ ] Tool recommendations work

---

### Step 2E: Dashboard Validation

**Check Dashboard:**
- Dashboard should be running from Phase 1
- Should show your CASCADE execution
- Should update in real-time (from snapshot JSON feed)

**Verify Dashboard Shows:**
- [ ] Current snapshot info (session ID, AI ID)
- [ ] Current CASCADE phase
- [ ] 13 epistemic vectors (bar chart display)
- [ ] Overall confidence/compression metrics
- [ ] Narrative summary
- [ ] Timestamp of last update
- [ ] Feed status (fresh/stale indicator)

**If dashboard not updating:**
```bash
# Kill existing dashboard pane
tmux kill-pane -t <pane-id>

# Restart dashboard in new pane
tmux split-window -h -p 30
python3 /home/yogapad/empirical-ai/empirica/empirica/dashboard/snapshot_monitor.py

# Or use MCP tool
# Call: launch_snapshot_dashboard with force=true
```

**Dashboard reads from:** `/tmp/empirica_realtime/snapshot_status.json`
**Updates when:** Snapshot provider saves new snapshot (triggers action hook)

---

### Step 2F: Create Phase 2 Report

**Deliverable:** `PHASE2_VALIDATION_REPORT.md`

Contents:
- Code quality findings summary
- Investigation strategy extensibility verified
- Database/reflex logs validation results
- Dashboard functionality assessment
- Any issues encountered
- Recommendation to proceed to Phase 3 or not

**STOP HERE - Review Phase 2 report before proceeding to Phase 3**

---

## PHASE 3: WEBSITE CONTENT GENERATION (After Phase 2 Complete - 3-4 hours)

**Prerequisites:** 
- Phase 1 complete (TMUX/MCP working)
- Phase 2 complete (System validated)
- Dashboard still running

### Step 3A: Bootstrap Website Generation Session

**New Session for Website:**
```
Use MCP: empirica-bootstrap_session
Arguments:
  session_type: "production"
  ai_id: "website-content-creator"
  domain: "content_creation"

Save new session_id (different from validation session)
```

---

### Step 3B: Generate Homepage Using CASCADE

**PREFLIGHT:**
```
Use MCP: empirica-execute_preflight
Arguments:
  session_id: <website session_id>
  prompt: "Generate professional homepage content for Empirica framework website.
          
          Requirements:
          - Hero section with value proposition
          - Problem/Solution explanation
          - 4-6 key features
          - Quick start (3 steps)
          - Call-to-action
          
          Source: docs/ folder (README.md, ARCHITECTURE_OVERVIEW.md, SKILL.md)
          Audience: Software developers
          Tone: Professional but approachable"
```

**GENERATE GOALS:**
```
Use MCP: empirica-generate_goals
Arguments:
  session_id: <website session_id>
  conversation_context: "Create homepage with these sections:
                        1. Hero (headline + tagline)
                        2. Problem statement (why AI needs metacognition)
                        3. Solution (Empirica's approach)
                        4. Key features (4-6 main features)
                        5. Quick start (3-step getting started)
                        6. CTA (install command + docs link)
                        
                        Extract from docs/, maintain accuracy, use examples."
```

**CREATE CASCADE:**
```
Use MCP: empirica-create_cascade
Arguments:
  session_id: <website session_id>
  task: "Generate homepage content"
  goal_json: <from generate_goals>
```

**INVESTIGATE:**
```
Read source documentation:
1. docs/README.md - Overview and quick start
2. docs/reference/ARCHITECTURE_OVERVIEW.md - System design
3. docs/skills/SKILL.md - Complete workflow
4. docs/reference/CANONICAL_13_VECTOR_SYSTEM.md - Core concept

Extract:
- Value proposition
- Key features
- Installation steps
- Code examples
```

**CHECK:**
```
Use MCP: empirica-execute_check
Arguments:
  session_id: <website session_id>
  findings: [
    "Extracted value proposition: ...",
    "Identified 6 key features: ...",
    "Found quick start in README",
    "Code examples available"
  ]
  remaining_unknowns: []
  confidence_to_proceed: 0.85
```

**ACT:**
```
Create: website/content/index.md

Structure:
---
title: "Empirica - Metacognitive AI Framework"
description: "..."
---

# Empirica

## [Hero Section]
<Compelling headline>
<Tagline>

## Why Empirica?
[Problem: AI lacks self-awareness]
[Solution: Epistemic self-assessment + metacognitive workflow]

## Key Features

### 1. 13-Vector Epistemic Assessment
[Description + example]

### 2. CASCADE Workflow
[Description + example]

[... 4 more features ...]

## Quick Start

```bash
# 1. Install
pip install empirica

# 2. Run your first CASCADE
empirica cascade run "Your task"

# 3. View results
empirica sessions show --latest
```

## Get Started
[CTA buttons]
```

**POSTFLIGHT:**
```
Use MCP: empirica-execute_postflight
Arguments:
  session_id: <website session_id>
  task_summary: "Generated homepage content from documentation. 
                Created website/content/index.md with hero, features, quick start."
```

---

### Step 8: Generate Features Page

**Repeat CASCADE for Features Page:**

**Task:** "Generate features page with comprehensive feature descriptions"

**Source Docs:**
- docs/reference/*.md (all reference docs)
- docs/guides/*.md (all guides)

**Content Structure:**
```markdown
# Features

## Canonical 13-Vector System
[Description from CANONICAL_13_VECTOR_SYSTEM.md]
[Code example]

## CASCADE Workflow
[Description from CASCADE_WORKFLOW.md]
[Phase breakdown]
[Example]

## Investigation Strategy System
[From EXTENSIBLE_INVESTIGATION_STRATEGIES.md]
[Custom strategy example]

## MCP Server Integration
[From MCP_SERVER_INTEGRATION_STATUS.md]
[Tool list]

## Multi-AI Collaboration
[From MULTI_AI_COLLABORATION_GUIDE.md]
[Example workflow]

## Calibration & Learning
[From CALIBRATION_SYSTEM.md]
[How it adapts]

## Dashboard Monitoring
[From SESSION_TRACKING.md]
[Screenshot/description]

## Goal Orchestration
[Description]
[Example]
```

**Output:** `website/content/features.md`

---

### Step 9: Generate Getting Started Guide

**Task:** "Generate comprehensive getting started guide"

**Source:**
- docs/README.md
- docs/skills/SKILL.md
- examples/*.py

**Content:**
```markdown
# Getting Started

## Installation
[From README]

## Your First CASCADE
[From SKILL.md]
[Step-by-step example]

## Configuration
[From config docs]

## Understanding the Workflow
[PREFLIGHT → POSTFLIGHT explanation]

## Next Steps
[Links to advanced guides]
```

**Output:** `website/content/getting-started.md`

---

### Step 10: Use Goal Orchestrator for Remaining Pages

**Create Master Cascade:**
```
Use MCP: empirica-generate_goals
Arguments:
  session_id: <website session_id>
  conversation_context: "Generate remaining website pages in parallel:
                        
                        Pages needed:
                        1. API Reference (from docstrings)
                        2. Architecture (from architecture docs)
                        3. Use Cases (from examples)
                        4. Community Guide (from CONTRIBUTING.md)
                        5. FAQ (from common questions)
                        
                        All pages: website/content/*.md
                        Source: docs/ and examples/
                        Maintain consistency and accuracy"
```

**Goal orchestrator will create sub-tasks. Use mini-agent for parallel execution:**

```
For each page:
  Use MCP: empirica-query_ai
  Arguments:
    query: "Generate <page> content from <source docs>"
    adapter: "minimax"  # Or other fast model
    strategy: "balanced"
    session_id: <shared website session_id>

Let mini-agent handle ACT phase while you do PREFLIGHT/CHECK/POSTFLIGHT
```

**Expected Outputs:**
- website/content/api-reference.md
- website/content/architecture.md
- website/content/use-cases.md
- website/content/community.md
- website/content/faq.md

---

### Step 11: Validate All Generated Content

**For Each Page:**
```
Run mini validation CASCADE:
1. Read generated content
2. Compare with source docs
3. Verify accuracy
4. Check code examples work
5. Validate links
6. Ensure consistent tone
```

**Create Validation Report:**
```markdown
# Website Content Validation

## Homepage (index.md)
- [x] Accurate to docs
- [x] Code examples work
- [x] Links valid
- [x] Professional tone

## Features (features.md)
- [x] All features covered
- [x] Examples work
- [x] Accurate descriptions

[... etc for all pages ...]

## Issues Found
[List any problems]

## Recommendations
[Any improvements needed]
```

---

## PHASE 3 SUMMARY & REPORTING (30 minutes)

### Step 3I: Create Comprehensive Test Report

**Use POSTFLIGHT for Phase 3:**
```
Use MCP: empirica-execute_postflight
Arguments:
  session_id: <website session_id>
  task_summary: "Completed website content generation:
                - 8 pages created from documentation
                - All content validated for accuracy
                - Code examples tested
                - Consistent professional tone
                
                Website ready for deployment."
```

**Export Session Data:**
```python
# Using Python directly
from empirica.core.canonical.canonical_session_manager import CanonicalSessionManager
import json

manager = CanonicalSessionManager()

# Export session to JSON
session_data = manager.export_session(session_id='<session-id>')
with open('phase1_tmux_mcp.json', 'w') as f:
    json.dump(session_data, f, indent=2)

# Or use MCP tool: empirica-sessions_export
```

**Create Final Report:**
```markdown
# FINAL_COMPLETE_TEST_REPORT.md

## Executive Summary
- Total Phases: 3
- Time Taken: [X hours]
- Success Rate: [%]
- Production Ready: [Yes/No]

## Phase 1: TMUX MCP Server Testing
### Results
- MCP server: ✅/❌
- Dashboard: ✅/❌
- Database persistence: ✅/❌
- Issues: [List]

## Phase 2: System Validation
### Results
- Code quality analysis: ✅/❌
- Investigation extensibility: ✅/❌
- Database queries: ✅/❌
- Dashboard monitoring: ✅/❌
- Issues: [List]

## Phase 3: Website Generation
### Results
- Pages generated: X/8
- Accuracy: [High/Medium/Low]
- Mini-agent collaboration: ✅/❌
- Issues: [List]

## Overall Assessment
[Summary of all findings]

## Recommendations
[Any improvements needed]

## Next Steps
[What should happen next]
```

---

## CRITICAL REMINDERS

### ⚠️ DO NOT SKIP PHASES
- Complete Phase 1 fully before Phase 2
- Complete Phase 2 fully before Phase 3
- Create phase reports between each phase

### ⚠️ USE EMPIRICA FOR EVERYTHING
- Every task should use CASCADE workflow
- Use MCP tools, not direct CLI/bash when possible
- Let goal orchestrator manage tasks
- Monitor via dashboard continuously

### ⚠️ COLLABORATE WITH MINI-AGENT
- Use for parallel content generation
- Use for validation tasks
- Share session_id for coordination

### ⚠️ DOCUMENT EVERYTHING
- Create phase reports
- Export session data
- Capture findings
- Note any issues

---

## FINAL DELIVERABLES CHECKLIST

### Phase 1 Deliverables
- [ ] PHASE1_TMUX_MCP_REPORT.md

### Phase 2 Deliverables
- [ ] CODE_QUALITY_REPORT.md
- [ ] REFACTORING_PRIORITIES.md
- [ ] PHASE2_VALIDATION_REPORT.md

### Phase 3 Deliverables
- [ ] website/content/index.md (Homepage)
- [ ] website/content/features.md
- [ ] website/content/getting-started.md
- [ ] website/content/guides.md
- [ ] website/content/api-reference.md
- [ ] website/content/architecture.md
- [ ] website/content/use-cases.md
- [ ] website/content/community.md
- [ ] website/content/faq.md
- [ ] WEBSITE_CONTENT_VALIDATION.md

### Final Deliverables
- [ ] FINAL_COMPLETE_TEST_REPORT.md
- [ ] phase1_tmux_mcp.json (exported session)
- [ ] phase2_validation.json (exported session)
- [ ] phase3_website.json (exported session)

---

## SUCCESS METRICS

### Phase 1 Success
- ✅ TMUX dashboard running
- ✅ MCP tools responding
- ✅ Database queries working
- ✅ Can see previous sessions

### Phase 2 Success
- ✅ CASCADE workflow executed
- ✅ Code quality analyzed
- ✅ Investigation extensibility verified
- ✅ Dashboard shows real-time updates

### Phase 3 Success
- ✅ 8 website pages generated
- ✅ Content accurate to docs
- ✅ Mini-agent collaboration works
- ✅ All content validated

### Overall Success
- ✅ All 3 phases complete
- ✅ All deliverables created
- ✅ No critical issues
- ✅ System production-ready

---

## ESTIMATED TIME

- **Phase 1:** 1 hour (TMUX/MCP setup and testing)
- **Phase 2:** 2-3 hours (System validation)
- **Phase 3:** 3-4 hours (Website generation)
- **Total:** 6-8 hours

**Remember: Work in phases, create reports between phases, don't rush ahead!**
- Status: ✅ Ready for community extensions

### Dashboard
- Real-time monitoring: ✅
- Epistemic visualization: ✅
- Goal tracking: ✅
- Status: ✅ Functional

## Part 2: Website Generation

### Content Created
1. ✅ index.md (Homepage)
2. ✅ features.md
3. ✅ getting-started.md
4. ✅ api-reference.md
5. ✅ architecture.md
6. ✅ use-cases.md
7. ✅ community.md
8. ✅ faq.md

### Validation Status
- Accuracy: ✅ Verified against source
- Code examples: ✅ All work
- Links: ✅ All valid
- Consistency: ✅ Maintained
- Tone: ✅ Professional

### Issues
[List any problems encountered]

## Calibration Learning

### Validation Session
- Initial confidence: X
- Final confidence: Y
- Adjustment factor: Z
- Accuracy: A%

### Website Session
- Initial confidence: X
- Final confidence: Y
- Adjustment factor: Z
- Accuracy: A%

## Epistemic Trajectory

[Include graphs or data from both sessions showing how epistemic vectors evolved]

## Conclusion

Empirica successfully validated itself through its own metacognitive workflow:
- ✅ System validation complete
- ✅ Website content generated
- ✅ All components functional
- ✅ Ready for v1.0 release

## Recommendations

[Any final recommendations for improvements]

---

**Test Date:** 2025-11-XX
**AI:** <your-model-name>
**Duration:** X hours
**Status:** ✅ COMPLETE
```

---

## SUCCESS CRITERIA

Your test is successful if ALL of these are true:

**System Validation:**
- [x] All CASCADE phases executed
- [x] MCP tools functional (test at least 15-20 core tools)
- [x] Database persistence verified
- [x] Reflex logs captured
- [x] Investigation strategies extensible
- [x] Dashboard monitoring works
- [x] Goal orchestrator manages tasks
- [x] Calibration tracks and adapts
- [x] Code quality report created

**Website Content:**
- [x] 8 pages generated
- [x] All content accurate to source
- [x] Code examples work
- [x] Professional quality
- [x] Consistent tone and structure
- [x] Links valid
- [x] Ready for deployment

**Documentation:**
- [x] CODE_QUALITY_REPORT.md created
- [x] REFACTORING_PRIORITIES.md created
- [x] FINAL_VALIDATION_REPORT.md created
- [x] Session data exported
- [x] Issues documented

**Process:**
- [x] Used Empirica workflow throughout
- [x] Followed CASCADE phases
- [x] Used MCP tools properly
- [x] Monitored via dashboard
- [x] Leveraged goal orchestrator
- [x] Collaborated with mini-agent (if available)

---

## IMPORTANT NOTES

**1. Use Empirica for Everything:**
Don't just manually create content - use the CASCADE workflow. This validates the system AND generates content.

**2. Monitor Dashboard:**
Keep it running and check it regularly. It should show your progress.

**3. Check Reflex Logs:**
After each phase, verify logs captured the assessment.

**4. Be Thorough:**
This is a comprehensive test. Take time to do it properly.

**5. Document Issues:**
If you find problems, document them clearly with reproduction steps.

**6. Honest Assessment:**
Use accurate epistemic scores. Don't inflate confidence.

**7. Mini-Agent Collaboration:**
If available, use mini-agent for ACT phases to test AI-to-AI workflow.

**8. Save Everything:**
Export sessions, save reports, keep all generated content.

---

## DELIVERABLES CHECKLIST

**Code Quality:**
- [ ] CODE_QUALITY_REPORT.md
- [ ] REFACTORING_PRIORITIES.md

**Website Content:**
- [ ] website/content/index.md
- [ ] website/content/features.md
- [ ] website/content/getting-started.md
- [ ] website/content/api-reference.md
- [ ] website/content/architecture.md
- [ ] website/content/use-cases.md
- [ ] website/content/community.md
- [ ] website/content/faq.md

**Reports:**
- [ ] FINAL_VALIDATION_REPORT.md
- [ ] validation_session.json
- [ ] website_session.json

**Optional:**
- [ ] test_custom_strategy.py (if created)
- [ ] Screenshots of dashboard
- [ ] Reflex log exports

---

## ESTIMATED TIMELINE

- **Part 1 (Validation):** 2-3 hours
  - Code quality: 1 hour
  - Database/MCP: 1 hour  
  - Strategies/Dashboard: 30-60 min

- **Part 2 (Website):** 3-4 hours
  - Homepage: 45 min
  - Features: 45 min
  - Getting started: 30 min
  - Other pages: 1-2 hours
  - Validation: 30 min

- **Part 3 (Reporting):** 1 hour
  - Export data: 15 min
  - Create report: 45 min

**Total:** 6-8 hours for thorough testing

---

## SUPPORT

If you encounter issues:
1. Check MCP server status: `empirica mcp-status`
2. Verify database: `ls -la empirica/.empirica/`
3. Review reflex logs: `empirica monitor show --session-id <id>`
4. Check CLI help: `empirica --help`
5. Read error messages carefully
6. Document for human review

---

**Created:** 2025-11-13T20:58:00Z  
**For:** Next AI session  
**Purpose:** Complete Empirica validation + website generation  
**Method:** Dogfooding - Empirica validates itself  
**Expected Duration:** 6-8 hours  
**Status:** Ready to execute

---

## QUICK START COMMANDS

```bash
# Terminal 1: Start dashboard (in TMUX)
tmux split-window -h -p 30
python3 /home/yogapad/empirical-ai/empirica/empirica/dashboard/snapshot_monitor.py

# Terminal 2: Work with Empirica
# Use MCP tools via your IDE (Claude Desktop, Cursor, etc.)
# or Python imports directly:
python3
>>> import sys
>>> sys.path.insert(0, '/home/yogapad/empirical-ai/empirica')
>>> from empirica.core.canonical import CanonicalEpistemicAssessor
>>> # ... work with Empirica ...

# When done, export via Python
>>> from empirica.core.canonical.canonical_session_manager import CanonicalSessionManager
>>> manager = CanonicalSessionManager()
>>> manager.export_session('<session-id>', 'final_report.json')
```

**MCP Server Location:** `/home/yogapad/empirical-ai/empirica/mcp_local/empirica_tmux_mcp_server.py`
**Dashboard Script:** `/home/yogapad/empirical-ai/empirica/empirica/dashboard/snapshot_monitor.py`
**Main Package:** `/home/yogapad/empirical-ai/empirica/empirica/`

**Good luck! 🚀**

Remember: You're not just testing Empirica - you're demonstrating it can orchestrate its own validation and documentation. This is the ultimate dogfooding test!
