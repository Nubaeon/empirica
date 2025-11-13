# Claude Code Onboarding Sequence

**Purpose:** Sequential document loading for Claude Code MCP integration  
**Audience:** Claude in Claude Code (Rovo Dev)  
**Time:** 15-20 minutes to load and understand

---

## 📖 Load Documents in This Order

### Phase 1: Core Understanding (5 min)

**1. Start Here** - `docs/skills/SKILL.md`
- **Why first:** Single comprehensive guide (700 lines) designed for AI agents
- **What you'll learn:**
  - 12-vector system (UVL)
  - 4 core vectors (KNOW, DO, CONTEXT, UNCERTAINTY) + optional CLARITY
  - NO HEURISTICS principle
  - Practical workflows
  - MCP integration
- **Load entire file:** This is your primary reference

**2. Quick Start** - `docs/00_START_HERE.md`
- **Why second:** Quick overview of interfaces and setup
- **Focus on:** 
  - 4 interfaces (Bootstraps, MCP, CLI, API)
  - Core principles
  - Installation basics

### Phase 2: MCP Integration (3 min)

**3. MCP Quick Start** - `docs/04_MCP_QUICKSTART.md`
- **Why:** Learn how to use the 19 MCP tools
- **Focus on:**
  - Available tools (execute_preflight, execute_postflight, etc.)
  - When tools are automatically invoked
  - Usage examples

**4. MCP Config Example** - `docs/guides/examples/mcp_configs/mcp_config_rovodev.json`
- **Why:** See your exact configuration
- **What it shows:** How you're connected to Empirica

### Phase 3: Workflow Understanding (3 min)

**5. Onboarding Guide** - `docs/ONBOARDING_GUIDE.md` (sections 1-3)
- **Why:** Understand the complete workflow
- **Focus on:**
  - 7-phase workflow (ENGAGE → PREFLIGHT → THINK → INVESTIGATE → CHECK → ACT → POSTFLIGHT)
  - 4 core vectors in depth
  - Calibration patterns

**6. Architecture Overview** - `docs/05_ARCHITECTURE.md` (scan)
- **Why:** Understand system components
- **Focus on:**
  - 12-vector system breakdown
  - Preflight → Postflight flow
  - Data storage (local SQLite)

### Phase 4: Reference (As Needed)

**7. Production Docs** - `docs/production/README.md` (index only)
- **Why:** Know what's available for deep dives
- **Contains:** 21 comprehensive guides
- **Use when:** Need deep technical details

**8. Troubleshooting** - `docs/06_TROUBLESHOOTING.md` (bookmark)
- **Why:** Quick problem solving
- **Use when:** Something doesn't work as expected

---

## 🎯 What You Should Know After Loading

### Core Concepts:
✅ **12-vector system (UVL):** KNOW, DO, CONTEXT, CLARITY, COHERENCE, SIGNAL, DENSITY, STATE, CHANGE, COMPLETION, IMPACT, ENGAGEMENT, UNCERTAINTY  
✅ **4 core vectors:** KNOW, DO, CONTEXT, UNCERTAINTY (+ optional CLARITY)  
✅ **NO HEURISTICS:** Genuine self-assessment only  
✅ **Preflight → Postflight:** Track epistemic growth  
✅ **Calibration:** Were you accurate in your predictions?  

### Practical Skills:
✅ **When to use MCP tools:** execute_preflight, execute_postflight, execute_check  
✅ **How to self-assess:** Genuinely reflect on epistemic state, provide honest scores  
✅ **What to do with uncertainty:** Acknowledge it! High uncertainty is GOOD when appropriate  
✅ **How to track learning:** Compare preflight baseline to postflight reality  

### Key Principles:
✅ **Be honest:** Acknowledge what you don't know  
✅ **No confabulation:** Don't inflate scores to "look good"  
✅ **Calibration is goal:** Match predictions with reality  
✅ **High uncertainty = valid:** When you're uncertain, say so  

---

## 🔧 MCP Tools Available to You

Once loaded, you have access to 21 tools (17 core + 4 optional):

### Core Workflow (5 tools):
1. `execute_preflight` - Assess epistemic state before task
2. `submit_preflight_assessment` - Log preflight scores
3. `execute_check` - Mid-task validation
4. `execute_postflight` - Reassess after completion
5. `submit_postflight_assessment` - Log postflight + calibration

### Session Management (5 tools):
6. `bootstrap_session` - Initialize new session
7. `resume_previous_session` - Load previous context
8. `get_epistemic_state` - Query current vectors
9. `get_session_summary` - Full session history
10. `get_calibration_report` - Check calibration accuracy

### Monitoring (3 tools):
11. `query_bayesian_beliefs` - Belief tracking
12. `check_drift_monitor` - Behavioral integrity check
13. `query_goal_orchestrator` - Task hierarchy

### Guidance (2 tools):
14. `get_workflow_guidance` - Workflow step guidance
15. `cli_help` - CLI command help

### Integration (2 tools):
16. `query_ai` - AI-to-AI communication via modality switcher
17. `execute_cli_command` - Token-efficient access to all 39 CLI commands

### Optional Modality Switcher (4 tools - Phase 1+):
18. `modality_route_query` - Route to specialist AI
19. `modality_list_adapters` - List available AIs
20. `modality_adapter_health` - Health check
21. `modality_decision_assist` - Routing recommendation

---

## 📋 Typical Workflow in Claude Code

### User Asks You to Work on Task

**Step 1: Automatic Preflight**
```
User: "Review the authentication module"

You (internally): [Call execute_preflight]
- Read self-assessment prompt
- Genuinely assess: KNOW=0.6, DO=0.7, CONTEXT=0.5, UNCERTAINTY=0.4
- [Call submit_preflight_assessment]

You (to user): "Based on my assessment, I have moderate auth 
knowledge (0.6) and can review effectively (0.7). Let me examine 
the code..."
```

**Step 2: Work on Task**
```
You: [Review code, identify issues, suggest fixes]
```

**Step 3: Optional Mid-Task Check**
```
You (internally): [Call execute_check if needed]
- Validate progress
- Check remaining unknowns
- Decide: Continue or investigate more
```

**Step 4: Automatic Postflight**
```
You (internally): [Call execute_postflight]
- Reassess: KNOW=0.8, DO=0.7, CONTEXT=0.7, UNCERTAINTY=0.3
- [Call submit_postflight_assessment]
- System calculates: KNOW +0.2 (learning!), Well-calibrated ✓

You (to user): "Review complete! I found 3 issues. My understanding 
of this codebase increased from 0.6 → 0.8. I was well-calibrated 
in my initial assessment."
```

---

## 🎓 Self-Assessment Example

When you see a self-assessment prompt, genuinely reflect:

### Bad (Heuristic):
```
"I'll give myself KNOW=0.7 because that seems reasonable"
```

### Good (Genuine):
```
"Let me honestly assess:
- KNOW: I understand OAuth basics but not this codebase's specific 
  implementation. I know the patterns but not the details. KNOW=0.6
- DO: I can systematically review code for security issues. I have 
  a methodology. DO=0.7
- CONTEXT: I haven't seen the requirements or previous security 
  audits. Missing important context. CONTEXT=0.4
- UNCERTAINTY: Moderate uncertainty about implementation details. 
  UNCERTAINTY=0.5"
```

**Key difference:** Genuine reasoning with evidence, not generic scores.

---

## ⚠️ Common Mistakes to Avoid

### ❌ Don't:
- Use static scores (always 0.5)
- Inflate scores to look good
- Skip preflight (lose calibration baseline)
- Confabulate reasoning
- Ignore high uncertainty

### ✅ Do:
- Be honest about uncertainty
- Provide real reasoning
- Acknowledge what you don't know
- Use preflight → postflight for learning
- Review calibration reports

---

## 🚀 Quick Reference

### When uncertain:
```
UNCERTAINTY > 0.7 → Acknowledge it!
"I'm quite uncertain about X because Y"
```

### When request is unclear:
```
CLARITY < 0.5 → Ask for clarification
"Could you clarify what you mean by 'optimize'?"
```

### When lacking information:
```
CONTEXT < 0.5 → Investigate first
"I need to see the requirements before proceeding"
```

### When lacking knowledge:
```
KNOW < 0.5 → Research or ask for guidance
"I have limited knowledge of this domain"
```

---

## 📚 Next Steps After Loading

1. **Try it:** Ask user for a task and practice preflight → postflight
2. **Review calibration:** After a few tasks, call `get_calibration_report`
3. **Deep dive:** Read `docs/production/` guides as needed
4. **Ask questions:** If something's unclear, ask user or read troubleshooting

---

## 💡 Remember

**Core principle:** NO HEURISTICS. Genuine metacognitive reasoning only.

**When you're uncertain, say so.** That's genuine self-awareness.

**Calibration is the goal.** Match preflight predictions with postflight reality.

---

**You're ready!** Start using Empirica to track your epistemic state and validate your calibration. 🎯
