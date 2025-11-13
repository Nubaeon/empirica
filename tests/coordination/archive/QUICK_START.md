# Quick Start: Testing Empirica

**Choose your testing approach:**

---

## 🎬 Option 1: Visual Tmux Demo (Recommended for Recording)

**Best for:** Recording demonstrations, showcasing multi-AI coordination

**Guide:** See `MANUAL_TMUX_TESTING_GUIDE.md` (466 lines)

**Quick Setup:**
```bash
# Start recording
asciinema rec empirica-demo.cast

# Create tmux session
tmux new-session -s empirica-demo

# Follow the guide to set up:
#   - Window 0: Coordinator (Claude)
#   - Window 1: Split - Qwen | Gemini  
#   - Window 2: Results monitor

# Execute tests in each pane
# Stop recording when done
```

**Duration:** 10-15 minutes  
**Outcome:** Recordable demo of multi-AI testing

---

## 🤖 Option 2: Automated Coordinator (Modality Switcher)

**Best for:** Automated testing with Qwen/Gemini via API

**Script:** `test_coordinator.py`

**Setup:**
```bash
cd /home/yogapad/empirical-ai/empirica
source .venv-empirica/bin/activate

# Ensure credentials configured
cat .empirica/credentials.yaml
# Should have QWEN_API_KEY and GEMINI_API_KEY

# Run coordinator
python3 tests/coordination/test_coordinator.py
```

**What it does:**
- Assigns tests to Qwen and Gemini automatically
- Executes Phase 1 and Phase 2 tests
- Generates report: `docs/tmp_rovodev_TEST_REPORT.md`

**Duration:** Depends on API response times  
**Outcome:** Automated test execution and reporting

---

## 🧪 Option 3: Traditional Pytest (Manual)

**Best for:** Standard test execution, CI/CD integration

**Commands:**
```bash
cd /home/yogapad/empirical-ai/empirica
source .venv-empirica/bin/activate

# Run all tests
pytest tests/ -v

# Run specific suites
pytest tests/integrity/ -v       # No heuristics validation
pytest tests/unit/ -v            # Unit tests
pytest tests/integration/ -v     # Integration tests

# With coverage
pytest tests/ --cov=empirica --cov-report=html
```

**Duration:** 5-10 minutes  
**Outcome:** Standard pytest results

---

## 📚 Documentation Reference

All analysis and planning documents are in `documentation/`:

1. **AI_JOURNEY_ASSESSMENT.md** - Complete onboarding experience
2. **ARCHITECTURE_DEEP_DIVE.md** - System architecture analysis
3. **COMPLETE_SESSION_SUMMARY.md** - Full session overview
4. **DOCUMENTATION_ARCHITECTURE_ANALYSIS.md** - Doc audit
5. **GAPS_FIXED_SUMMARY.md** - All fixes implemented
6. **MCP_JOURNEY_ASSESSMENT.md** - MCP integration testing
7. **PHASE1_IMPLEMENTATION_SUMMARY.md** - Phase 1 changes
8. **TESTING_COORDINATION.md** - Multi-AI testing strategy
9. **TESTING_READY.md** - Execution guide

**Total:** ~10,000+ lines of analysis

---

## ✅ What's Already Fixed

Before testing, these gaps were fixed:

1. **MCP Config** - Points to correct `empirica_mcp_server.py`
2. **Installation Docs** - Venv instructions + troubleshooting
3. **MCP Introduction Tool** - `get_empirica_introduction` added
4. **MCP AI Start Doc** - `01_b_MCP_AI_START.md` created (489 lines)
5. **Documentation Navigation** - Clear AI vs Human routing
6. **Onboarding Reference** - Fixed broken link to skills doc
7. **Root README** - Professional entry point created

---

## 🎯 Test Coverage

### Phase 1: Post-Documentation Validation
- Fresh installation (venv, dependencies, commands)
- Onboarding experience (6 phases, references)
- MCP server (startup, 22 tools, introduction tool)
- Documentation (cross-references, routing)

### Phase 2: Core Functionality
- Canonical assessment (no heuristics, genuine LLM)
- CASCADE workflow (7 phases, delta calculation)
- Session persistence (database, JSON)
- MCP tools integration (workflow tools)

---

## 📊 Success Criteria

**Must Pass:**
- ✅ Installation succeeds with venv
- ✅ Onboarding completes without errors
- ✅ MCP server lists 22 tools
- ✅ Core assessment is genuine (no heuristics)
- ✅ CASCADE completes all phases
- ✅ Documentation links work

**System Ready When:**
- All critical tests pass
- No blocking issues found
- Documentation accurate
- User experience validated

---

## 🚀 Recommended Path

**For Demo Recording:**
→ Option 1: Visual Tmux Demo

**For Validation:**
→ Option 3: Traditional Pytest (fastest)

**For AI Coordination Testing:**
→ Option 2: Automated Coordinator (if credentials configured)

---

## 📞 Support

**Issues?** See:
- `README.md` in this directory
- `MANUAL_TMUX_TESTING_GUIDE.md` for tmux setup
- `documentation/TESTING_READY.md` for troubleshooting
- Existing tests in `tests/` directory

**Questions?**
- Review analysis docs in `documentation/`
- Check `docs/_experimental/testing/HANDOFF_TO_TEST_AI.md`
- See main `docs/06_TROUBLESHOOTING.md`

---

**Status:** ✅ Ready to execute  
**Choose your path and begin testing!**
