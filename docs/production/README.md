# 📚 Empirica Production Documentation

**Version:** 2.1.0  
**Date:** 2025-10-30  
**Status:** Production Ready (Enhanced Cascade Workflow)

This folder contains comprehensive documentation for the production-ready Empirica Canonical Epistemic Cascade system.

⚠️ **IMPORTANT FOR AI AGENTS:** If you experience confusion about system components or memory compression issues, immediately read [`/docs/ARCHITECTURE_MAP.md`](/docs/ARCHITECTURE_MAP.md) - it provides a clear visual reference to prevent drift.

---

## 🗺️ **START HERE: Orientation for AI Agents**

**CRITICAL:** If you're an AI agent experiencing memory compression or confusion, read these docs in order:

1. **[`EMPIRICA_SYSTEM_OVERVIEW.md`](/docs/EMPIRICA_SYSTEM_OVERVIEW.md)** ⭐⭐⭐ **NEW - READ FIRST**
   - Complete privacy-first architecture
   - Data flow (DB → Reflex logs → Tmux → MCP/CLI)
   - Knowledge transfer without sensitive data
   - 10-minute orientation for AI agents

2. **[`MEMORY_COMPRESSION.md`](/docs/MEMORY_COMPRESSION.md)** ⭐⭐ **NEW - AFTER COMPRESSION**
   - Why reasoning degrades during memory compression
   - Re-orientation protocol (docs → DB → reflex logs → assess)
   - Epistemic checkpointing strategy
   - Integration with DB, reflex logs, tmux, MCP/CLI

3. **[`DECISIONS.md`](/docs/DECISIONS.md)** ⭐⭐ **NEW - DECISION CONTEXT**
   - Major architectural decisions with epistemic weights
   - Rationale for "why" not just "what"
   - Caveats and validation criteria
   - Machine-readable + human-readable

4. **[`ARCHITECTURE_MAP.md`](/docs/ARCHITECTURE_MAP.md)** ⭐ **COMPONENT REFERENCE**
   - Visual map of all components and their locations
   - Clarifies the canonical 13-vector system vs legacy 12-vector system
   - Resolves common confusion points
   - Prevents duplicate folder creation during memory compression

**After orientation, proceed to production docs below.**

---

## Documentation Structure

### 🚀 AI Agent Orientation (Read First!)
- **[`EMPIRICA_SYSTEM_OVERVIEW.md`](/docs/EMPIRICA_SYSTEM_OVERVIEW.md)** ⭐⭐⭐ **NEW - Complete system architecture**
- **[`MEMORY_COMPRESSION.md`](/docs/MEMORY_COMPRESSION.md)** ⭐⭐ **NEW - Memory compression strategy**
- **[`DECISIONS.md`](/docs/DECISIONS.md)** ⭐⭐ **NEW - Decision log with epistemic weights**
- **[`ARCHITECTURE_MAP.md`](/docs/ARCHITECTURE_MAP.md)** ⭐ **Visual component reference**
- **[`HOW_TO_RESUME_SESSION.md`](/docs/HOW_TO_RESUME_SESSION.md)** ⭐ **Session resumption guide**

### Getting Started
- `01_QUICK_START.md` - Get up and running in 5 minutes ✅
- `02_INSTALLATION.md` - Complete installation guide
- `03_BASIC_USAGE.md` - Basic usage patterns and examples

### Core Concepts
- `00_COMPLETE_SUMMARY.md` - High-level system overview ✅
- `04_ARCHITECTURE_OVERVIEW.md` - System architecture and design ✅
- `05_EPISTEMIC_VECTORS.md` - Understanding the 13 epistemic dimensions ✅
- `SYSTEM_ARCHITECTURE_DEEP_DIVE.md` - Complete technical deep dive ⭐ ✅ (Updated v2.1)
- `06_CASCADE_FLOW.md` - How the cascade works (7-phase workflow)
- `CASCADE_PHASE_TRACKING.md` - Multi-phase planning & necessity assessment ⭐ ✅
- `ENHANCED_CASCADE_WORKFLOW_SPEC.md` - 7-phase workflow specification ⭐ ✅
- `REFLEX_FRAME_ARCHIVAL_STRATEGY.md` - Auto-tracking & log management ⭐ ✅ (Updated v2.1)

### Features
- `07_INVESTIGATION_SYSTEM.md` - Strategic investigation and tool mapping
- `08_BAYESIAN_GUARDIAN.md` - Evidence-based belief tracking ✅
- `09_DRIFT_MONITOR.md` - Behavioral integrity monitoring ✅
- `10_PLUGIN_SYSTEM.md` - Extending with custom tools ✅
- `11_DASHBOARD_MONITORING.md` - Real-time tmux dashboard

### Integration
- `12_MCP_INTEGRATION.md` - Using with Claude Desktop and MCP clients ✅
- `13_PYTHON_API.md` - Direct Python API usage
- `14_CUSTOM_PLUGINS.md` - Creating domain-specific plugins

### Advanced
- `15_CONFIGURATION.md` - Advanced configuration options ✅
- `16_TUNING_THRESHOLDS.md` - Calibrating for your domain ✅
- `17_PRODUCTION_DEPLOYMENT.md` - Deploying to production ✅
- `18_MONITORING_LOGGING.md` - Production monitoring and logs ✅

### Reference
- `19_API_REFERENCE.md` - Complete API documentation ✅
- `20_TOOL_CATALOG.md` - All available investigation tools ✅
- `21_TROUBLESHOOTING.md` - Common issues and solutions ✅
- `22_FAQ.md` - Frequently asked questions ✅

### Development
- `23_CONTRIBUTING.md` - Contributing guidelines
- `24_TESTING.md` - Running tests and validation
- `25_ROADMAP.md` - Future enhancements

---

## Quick Links

### Most Important Docs (AI Agents - Read in Order):
1. **New AI agent or memory compressed?** → [`EMPIRICA_SYSTEM_OVERVIEW.md`](/docs/EMPIRICA_SYSTEM_OVERVIEW.md) ⭐⭐⭐ **START HERE**
2. **After memory compression?** → [`MEMORY_COMPRESSION.md`](/docs/MEMORY_COMPRESSION.md) ⭐⭐
3. **Need decision context?** → [`DECISIONS.md`](/docs/DECISIONS.md) ⭐⭐
4. **Confused about components?** → [`ARCHITECTURE_MAP.md`](/docs/ARCHITECTURE_MAP.md) ⭐
5. **Resuming session?** → [`HOW_TO_RESUME_SESSION.md`](/docs/HOW_TO_RESUME_SESSION.md) ⭐

### Most Important Docs (Human Users):
1. First time user? → `01_QUICK_START.md` ✅
2. Understand the system → `SYSTEM_ARCHITECTURE_DEEP_DIVE.md` ⭐
3. Use the API → `13_PYTHON_API.md`
4. Deploy → `17_PRODUCTION_DEPLOYMENT.md`

### Current Status: 26/28 docs complete ✅
All essential documentation is complete. System is production-ready.

**Recently Added (v3.0 - 2025-11-07):** ⭐ **NEW**
- ✅ **EMPIRICA_SYSTEM_OVERVIEW.md** - Complete privacy-first architecture ⭐⭐⭐ **ESSENTIAL**
- ✅ **MEMORY_COMPRESSION.md** - Memory compression strategy with system integration ⭐⭐
- ✅ **DECISIONS.md** - Decision log with epistemic weights ⭐⭐
- ✅ Updated HOW_TO_RESUME_SESSION.md - Added memory compression docs to reading list
- ✅ Updated ARCHITECTURE_MAP.md - Enhanced re-orientation protocol

**Previously Added (v2.1):**
- ✅ **ARCHITECTURE_MAP.md** - Visual component map to prevent drift ⭐
- ✅ CASCADE_PHASE_TRACKING.md - Multi-phase planning & necessity
- ✅ ENHANCED_CASCADE_WORKFLOW_SPEC.md - 7-phase workflow specification
- ✅ Updated SYSTEM_ARCHITECTURE_DEEP_DIVE.md - Now references architecture map
- ✅ 15_CONFIGURATION.md - Complete configuration guide
- ✅ 16_TUNING_THRESHOLDS.md - Domain calibration & tuning
- ✅ 17_PRODUCTION_DEPLOYMENT.md - Deployment guide
- ✅ 18_MONITORING_LOGGING.md - 3-format logging system
- ✅ 19_API_REFERENCE.md - Complete API documentation
- ✅ 20_TOOL_CATALOG.md - 11 enterprise components documented
- ✅ 21_TROUBLESHOOTING.md - Common issues and solutions
- ✅ 22_FAQ.md - Frequently asked questions

### For Specific Features:
- Want to add custom tools? → `10_PLUGIN_SYSTEM.md` or `20_TOOL_CATALOG.md`
- Need evidence tracking? → `08_BAYESIAN_GUARDIAN.md`
- Monitor behavior? → `09_DRIFT_MONITOR.md`
- Live dashboard? → `11_DASHBOARD_MONITORING.md`
- Configure system? → `15_CONFIGURATION.md`
- Tune thresholds? → `16_TUNING_THRESHOLDS.md`
- Monitor logs? → `18_MONITORING_LOGGING.md`
- Multi-phase planning? → `CASCADE_PHASE_TRACKING.md` ⭐
- Live dashboard? → `11_DASHBOARD_MONITORING.md`
- Configure system? → `15_CONFIGURATION.md`
- Tune thresholds? → `16_TUNING_THRESHOLDS.md`
- Monitor logs? → `18_MONITORING_LOGGING.md`

### For Integration:
- Claude Desktop → `12_MCP_INTEGRATION.md`
- Python apps → `13_PYTHON_API.md`
- Custom domains → `14_CUSTOM_PLUGINS.md`

---

## Documentation Philosophy

This documentation follows these principles:

1. **Practical First** - Start with working examples, explain theory later
2. **Progressive Disclosure** - Simple → intermediate → advanced
3. **Production Focus** - Real-world usage, not just tutorials
4. **Complete Coverage** - Everything documented, no gaps
5. **Maintained** - Updated with every release

---

## What's New in 2.1.0 ⭐ (Current)

### Enhanced Cascade Workflow (7-Phase):
- ✅ **PREFLIGHT Assessment** - Baseline epistemic state before work begins
- ✅ **Think → Plan → Investigate → Check → Act** - Structured phases
- ✅ **POSTFLIGHT Assessment** - Final epistemic state after completion
- ✅ **Δ Vector Tracking** - Measure actual improvement (calibration validation)
- ✅ **Self-Prompting Clarity** - AI performs its own assessments (not external scoring)
- ✅ **Investigation Self-Check** - AI decides when to stop investigating
- ✅ **Workflow Components** (`empirica/workflow/`):
  - `preflight_assessor.py` - Pre-work baseline assessment
  - `postflight_assessor.py` - Post-work validation assessment
  - `cascade_workflow_orchestrator.py` - 7-phase coordination
- ✅ **Database Schema** - Dedicated `preflight_assessments` and `postflight_assessments` tables
- ✅ **Updated MCP Server** - New workflow tools integrated

### Documentation Updates (v2.1):
- ✅ `ENHANCED_CASCADE_WORKFLOW_SPEC.md` - Complete 7-phase spec ⭐ NEW
- ✅ `SYSTEM_ARCHITECTURE_DEEP_DIVE.md` - Updated with workflow architecture
- ✅ `REFLEX_FRAME_ARCHIVAL_STRATEGY.md` - Updated for preflight/postflight frames
- ✅ Skills documentation updated (Claude, recursive refinement, quick reference)
- ✅ MCP server integrated with workflow tools

### Philosophy Enhancement:
> "The AI self-assesses before and after every cascade, measuring genuine epistemic improvement through Δ vectors. Not external evaluation - self-reflection with accountability."

**Result:** Empirica now validates its own calibration accuracy by measuring whether investigation actually improved epistemic state.

---

## What Was New in 2.0.0

### Major Features:
- ✅ **13-vector epistemic system** (added explicit UNCERTAINTY vector)
- ✅ **Auto-tracking** (3 formats: SQLite + JSON + Reflex)
- ✅ **Pre/post-flight validation** (Δuncertainty measurement)
- ✅ **11 enterprise components** (investigation tools in empirica/components/)
- ✅ **Cognitive benchmarking** (ERB framework in empirica/cognitive_benchmarking/)
- ✅ **CLI system** (empirica/cli/ for command-line operations)
- ✅ **Cascade phase tracking** (multi-phase planning with necessity assessment)
- ✅ **Tmux self-orchestration** (real-time dashboard)
- ✅ **Advanced configuration** (environment, domain tuning)
- ✅ **Production monitoring** (comprehensive logging)

### Documentation Updates:
- ✅ Complete architecture documentation (SYSTEM_ARCHITECTURE_DEEP_DIVE.md)
- ✅ Cascade phase tracking & necessity (CASCADE_PHASE_TRACKING.md) ⭐ NEW
- ✅ Auto-tracking integration guide
- ✅ 13th vector (UNCERTAINTY) documentation
- ✅ Configuration guide (15_CONFIGURATION.md)
- ✅ Threshold tuning guide (16_TUNING_THRESHOLDS.md)
- ✅ Monitoring & logging guide (18_MONITORING_LOGGING.md)
- ✅ Tool catalog with 11 enterprise components (20_TOOL_CATALOG.md)
- ✅ All empirica references migrated to empirica

### Philosophy:
> "Non-heuristic epistemic reasoning. The system measures and validates genuine uncertainty through LLM-powered assessment, not keyword matching. Δuncertainty validates learning."

**Result:** Production-grade epistemic reasoning that measures, learns, and evolves.

---

## Getting Help

### Documentation Issues:
- Missing information? Open an issue
- Unclear explanations? Request clarification
- Found errors? Submit corrections

### Technical Support:
- Check `21_TROUBLESHOOTING.md` first
- Review `22_FAQ.md` for common questions
- See examples in each doc for patterns

### Community:
- Share your use cases
- Contribute plugins
- Improve documentation

---

## License

See LICENSE file in root directory.

---

## Reading Sequence for AI Agents

**If you're an AI agent starting fresh or after memory compression:**

1. **Orientation** (15 minutes):
   - [`EMPIRICA_SYSTEM_OVERVIEW.md`](/docs/EMPIRICA_SYSTEM_OVERVIEW.md) ⭐⭐⭐
   - [`MEMORY_COMPRESSION.md`](/docs/MEMORY_COMPRESSION.md) ⭐⭐
   - [`DECISIONS.md`](/docs/DECISIONS.md) ⭐⭐
   - [`ARCHITECTURE_MAP.md`](/docs/ARCHITECTURE_MAP.md) ⭐

2. **Skills & Capabilities** (10 minutes):
   - [`CLAUDE_SKILLS_EMPIRICA_v1_UPDATED.md`](/docs/empirica_skills/CLAUDE_SKILLS_EMPIRICA_v1_UPDATED.md)
   - [`QUICK_REFERENCE.md`](/QUICK_REFERENCE.md)

3. **Production Usage** (as needed):
   - `01_QUICK_START.md` - Get started
   - `ENHANCED_CASCADE_WORKFLOW_SPEC.md` - 7-phase workflow
   - `12_MCP_INTEGRATION.md` - MCP tools
   - `13_PYTHON_API.md` - Python API

**Total orientation time: ~25 minutes for full context**

---

**Start with (Human Users):** `01_QUICK_START.md` →
**Start with (AI Agents):** [`EMPIRICA_SYSTEM_OVERVIEW.md`](/docs/EMPIRICA_SYSTEM_OVERVIEW.md) →
