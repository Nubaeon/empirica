# Testing Coordination for Empirica

This directory contains testing infrastructure and documentation for coordinating multi-AI testing of Empirica.

## Structure

```
tests/coordination/
├── README.md                    # This file
├── test_coordinator.py          # Automated test coordinator (Qwen + Gemini)
├── scripts/                     # Testing scripts
└── documentation/               # Analysis and testing documentation
    ├── tmp_rovodev_AI_JOURNEY_ASSESSMENT.md
    ├── tmp_rovodev_ARCHITECTURE_DEEP_DIVE.md
    ├── tmp_rovodev_COMPLETE_SESSION_SUMMARY.md
    ├── tmp_rovodev_DOCUMENTATION_ARCHITECTURE_ANALYSIS.md
    ├── tmp_rovodev_GAPS_FIXED_SUMMARY.md
    ├── tmp_rovodev_MCP_JOURNEY_ASSESSMENT.md
    ├── tmp_rovodev_PHASE1_IMPLEMENTATION_SUMMARY.md
    ├── tmp_rovodev_TESTING_COORDINATION.md
    └── tmp_rovodev_TESTING_READY.md
```

## Purpose

These files document the complete assessment, architectural analysis, and testing preparation for Empirica's production readiness.

### Analysis Documents (documentation/)

**Phase 1: Documentation Architecture**
- `tmp_rovodev_DOCUMENTATION_ARCHITECTURE_ANALYSIS.md` - Complete doc audit
- `tmp_rovodev_PHASE1_IMPLEMENTATION_SUMMARY.md` - What was changed

**Phase 2: Journey Assessment**
- `tmp_rovodev_AI_JOURNEY_ASSESSMENT.md` - Full onboarding experience
- `tmp_rovodev_MCP_JOURNEY_ASSESSMENT.md` - MCP integration testing

**Phase 3: Architecture Deep Dive**
- `tmp_rovodev_ARCHITECTURE_DEEP_DIVE.md` - System architecture analysis

**Phase 4: Gap Resolution**
- `tmp_rovodev_GAPS_FIXED_SUMMARY.md` - All fixes implemented

**Phase 5: Testing Preparation**
- `tmp_rovodev_TESTING_COORDINATION.md` - Multi-AI testing strategy
- `tmp_rovodev_TESTING_READY.md` - Testing execution guide

**Complete Summary**
- `tmp_rovodev_COMPLETE_SESSION_SUMMARY.md` - Full session overview

### Test Coordinator (test_coordinator.py)

Automated testing coordinator that:
- Assigns tests to Qwen and Gemini via modality switcher
- Executes Phase 1 (post-documentation) and Phase 2 (core functionality) tests
- Collects results and generates reports

**Usage:**
```bash
cd /home/yogapad/empirical-ai/empirica
source .venv-empirica/bin/activate
python3 tests/coordination/test_coordinator.py
```

## Manual Testing Setup

For manual tmux-based testing demonstration:

### 1. Create Tmux Session Layout

```bash
# Create session with 4 windows
tmux new-session -s empirica-testing -n coordinator

# Window 0: Coordinator (Claude)
# Window 1: Split - Qwen (left) | Gemini (right)
# Window 2: Results monitor
# Window 3: MCP server (optional)
```

### 2. Test Assignments

**Qwen Tasks:**
- Fresh installation test
- MCP server test
- Canonical assessment test
- Session persistence test

**Gemini Tasks:**
- Onboarding experience test
- Documentation cross-reference test
- CASCADE workflow test
- MCP tools integration test

**Claude (Coordinator) Tasks:**
- Monitor progress
- Analyze results
- Prioritize fixes
- Generate final report

### 3. Manual Test Commands

**Fresh Install (Qwen):**
```bash
python3 -m venv .venv-test-qwen
source .venv-test-qwen/bin/activate
pip install -e .
pip install -r requirements.txt
empirica --help
```

**Onboarding (Gemini):**
```bash
empirica onboard --ai-id test-gemini
```

**MCP Server (Qwen):**
```bash
python3 mcp_local/empirica_mcp_server.py
# Check: Should list 22 tools including get_empirica_introduction
```

**Core Tests (Both):**
```bash
pytest tests/integrity/ -v    # No heuristics validation
pytest tests/unit/ -v         # Unit tests
pytest tests/integration/ -v  # Integration tests
```

## Expected Outcomes

### Success Criteria:
- ✅ All installations succeed
- ✅ Onboarding completes without errors
- ✅ MCP server starts and lists 22 tools
- ✅ Core assessment uses genuine LLM (no heuristics)
- ✅ CASCADE workflow completes all 7 phases
- ✅ Documentation links work

### Deliverables:
- Test execution report
- Issue list with priorities
- Recommendations for fixes
- Production readiness assessment

## Recording for Demo

This testing setup can be recorded to demonstrate:
1. Multi-AI coordination using Empirica
2. Visual tmux-based testing workflow
3. Real-time test execution and results
4. Empirica testing itself with Empirica (meta!)

**Recording Commands:**
```bash
# Start recording
tmux pipe-pane -o 'cat >> empirica-testing-$(date +%Y%m%d-%H%M%S).log'

# Or use asciinema
asciinema rec empirica-testing-demo.cast

# Execute tests in each pane
# Stop recording when done
```

## Notes

- These analysis documents were created during the 2025-11-10 assessment session
- Total: ~10,000+ lines of analysis and documentation
- All critical gaps have been fixed
- System is production-ready pending validation
- Documents can be archived after review

## Next Steps

1. Review analysis documents
2. Execute testing (automated or manual)
3. Address any critical issues found
4. Archive these documents to `docs/archive/2025-11-10-rovodev-assessment/`
5. Proceed with release preparation

---

**Created:** 2025-11-10  
**Purpose:** Testing coordination and analysis documentation  
**Status:** Ready for execution
