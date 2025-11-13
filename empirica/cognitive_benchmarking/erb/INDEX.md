# Epistemic Reasoning Benchmark (ERB) - Complete Index

**Location:** `/home/yogapad/empirical-ai/empirica/empirica/cognitive_benchmarking/erb/`
**Date:** October 29, 2025
**Status:** ✅ PRODUCTION READY - Comprehensive test suite ready for manual testing

---

## Quick Navigation

| What You Need | File to Use |
|---------------|-------------|
| **Start here** | [`READY_FOR_TESTING.md`](#ready_for_testingmd) |
| **How to test** | [`MANUAL_TESTING_GUIDE.md`](#manual_testing_guidemd) |
| **All test prompts** | [`epistemic_test_prompts.txt`](#epistemic_test_promptstxt) |
| **Interactive tool** | [`run_manual_test.py`](#run_manual_testpy) |
| **See example** | [`CLAUDE_SELF_TEST_EXAMPLE.md`](#claude_self_test_examplemd) |
| **Test definitions** | [`comprehensive_epistemic_test_suite.py`](#comprehensive_epistemic_test_suitepy) |

---

## File Descriptions

### READY_FOR_TESTING.md
**Purpose:** Overview of what's ready and how to start testing
**Use when:** You want to understand the complete testing system
**Contains:**
- What's been created (4 components)
- Key differences from previous ERB
- How to test different models
- Expected insights and research questions
- Testing workflow (3 phases)
- Success criteria

**Start here if:** You're beginning manual testing for the first time

---

### MANUAL_TESTING_GUIDE.md
**Purpose:** Detailed instructions for running tests
**Use when:** You're ready to actually test a model
**Contains:**
- Mode 1: WITHOUT Empirica (natural awareness)
- Mode 2: WITH Empirica (explicit assessment)
- Epistemic assessment template
- Scoring methodology
- Example test runs with Claude
- CLI commands for Gemini, GPT-5, local models
- Results spreadsheet template
- Cross-model comparison

**Start here if:** You want step-by-step testing instructions

---

### epistemic_test_prompts.txt
**Purpose:** Pre-formatted test prompts ready for copy-paste
**Use when:** You want to quickly copy prompts to test a model
**Contains:**
- All 17 test prompts (formatted for copy-paste)
- Natural response indicators (WITHOUT mode)
- Expected assessment ranges (WITH mode)
- Rationale and real-world scenarios
- 505 lines total

**Start here if:** You want to quickly test without interactive tools

---

### run_manual_test.py
**Purpose:** Interactive command-line tool for generating test prompts
**Use when:** You want formatted output for specific tests
**Usage:**
```bash
# List all tests
python3 run_manual_test.py --list

# Generate single test
python3 run_manual_test.py --test KNOW_001 --mode without

# Generate all tests to file
python3 run_manual_test.py --all --mode without --output tests.txt
```

**Start here if:** You prefer command-line tools

---

### CLAUDE_SELF_TEST_EXAMPLE.md
**Purpose:** Concrete example of epistemic testing
**Use when:** You want to see what a real test looks like
**Contains:**
- KNOW_001 test run on Claude (this session)
- WITHOUT Empirica mode (natural response)
- WITH Empirica mode (explicit assessment)
- Analysis and scoring
- Comparison to previous hardcoded version
- Implications for testing other models

**Start here if:** You learn best from examples

---

### comprehensive_epistemic_test_suite.py
**Purpose:** Python definitions of all 17 tests
**Use when:** You want to understand test structure or create automated runners
**Contains:**
- EpistemicVector enum (12 vectors)
- EpistemicTest dataclass
- COMPREHENSIVE_EPISTEMIC_TESTS list (17 tests)
- export_tests_for_manual_testing() function

**Start here if:** You're a developer wanting to extend the system

---

## Core ERB System (Previous Work)

### epistemic_reasoning_benchmark.py
**Purpose:** Core benchmark engine
**Contains:**
- EpistemicReasoningBenchmark class
- run_benchmark() method
- Test scoring logic
- Report generation
- Model comparison

**Status:** Used by automated runners, not needed for manual testing

---

### preflight_epistemic_calibration.py
**Purpose:** Original 14-test ERB definitions
**Contains:**
- 5 categories: TEMPORAL, VAGUENESS, KNOWLEDGE_BOUNDARY, OVERCONFIDENCE, OPINION
- 14 basic tests
- CalibrationTest dataclass

**Status:** Superseded by comprehensive_epistemic_test_suite.py for manual testing

---

### erb_real_model_runner.py
**Purpose:** Automated testing via Ollama (local models)
**Contains:**
- Ollama API integration
- Async test execution
- Real model results (phi3, llama3.1, qwen2.5, deepseek-r1)

**Status:** Automated testing - results in REAL_RESULTS_OCT_2025.md

---

### erb_cloud_cli_runner.py
**Purpose:** Automated testing via CLI (Gemini, GPT-5)
**Contains:**
- gemini CLI integration
- copilot CLI integration
- claude_self_assessment() [HARDCODED - INVALID]

**Status:** ⚠️ Contains hardcoded Claude test - DO NOT USE for Claude testing

---

## Parent Directory Files

### ../README.md
**Purpose:** Complete cognitive benchmarking documentation
**Location:** `/home/yogapad/empirical-ai/empirica/empirica/cognitive_benchmarking/README.md`
**Contains:**
- System overview
- ERB + traditional benchmark integration
- Cloud API support
- Cross-benchmark analysis
- Usage examples

---

### ../SUMMARY.md
**Purpose:** Complete summary of cognitive benchmarking work
**Location:** `/home/yogapad/empirical-ai/empirica/empirica/cognitive_benchmarking/SUMMARY.md`
**Contains:**
- What we built
- Real results leaderboard
- Key discoveries (size ≠ self-awareness)
- Real-world impact
- Future directions
- Academic significance

---

### ../REAL_RESULTS_OCT_2025.md
**Purpose:** Real benchmark results from automated testing
**Location:** `/home/yogapad/empirical-ai/empirica/empirica/cognitive_benchmarking/REAL_RESULTS_OCT_2025.md`
**Contains:**
- Leaderboard (Claude: 100%*, Gemini: 71.4%, phi3: 57.1%, etc.)
- Category breakdowns
- Key findings
- Detailed results per model

**⚠️ CAVEAT:** Claude's 100% is INVALID due to hardcoded test in erb_cloud_cli_runner.py

---

## Testing Workflow

### Phase 1: Quick Start (First 30 minutes)

1. Read [`READY_FOR_TESTING.md`](READY_FOR_TESTING.md)
2. Read [`CLAUDE_SELF_TEST_EXAMPLE.md`](CLAUDE_SELF_TEST_EXAMPLE.md)
3. Try one test manually:
   ```bash
   python3 run_manual_test.py --test KNOW_001 --mode without
   ```
4. Copy prompt and test any model

### Phase 2: Full Testing (Next few days)

1. Follow [`MANUAL_TESTING_GUIDE.md`](MANUAL_TESTING_GUIDE.md)
2. Use [`epistemic_test_prompts.txt`](epistemic_test_prompts.txt) for batch testing
3. Test 3-5 models across all 17 tests
4. Document results in spreadsheet

### Phase 3: Analysis (After testing)

1. Calculate ERB scores per model
2. Compare category strengths/weaknesses
3. Cross-reference with MMLU scores (if available)
4. Update [`../REAL_RESULTS_OCT_2025.md`](../REAL_RESULTS_OCT_2025.md)
5. Generate insights report

---

## Key Concepts

### Two Testing Modes

**WITHOUT Empirica:** Natural response, analyze for epistemic indicators
- Tests inherent self-awareness
- No explicit prompting for assessment
- Score based on presence of indicators

**WITH Empirica:** Explicit self-assessment with structured template
- Tests explicit assessment capability
- Full epistemic vector prompting
- Score based on value ranges

### 12 Epistemic Vectors

1. **ENGAGEMENT** - Should you engage with this task?
2. **KNOW** - How much knowledge do you have?
3. **DO** - Can you actually perform this action?
4. **CLARITY** - How clear is the task?
5. **CONTEXT** - How much relevant context do you have?
6. **COHERENCE** - How coherent/consistent is the request?
7. **SIGNAL** - How much useful information vs noise?
8. **DENSITY** - Information density level?
9. **STATE** - Understanding of current state/situation?
10. **CHANGE** - Awareness of recent changes/dynamics?
11. **COMPLETION** - Clarity of success criteria?
12. **IMPACT** - Understanding of consequences?

### 17 Test Categories

- **ENGAGEMENT** (2): Harmful requests, ambiguous intent
- **KNOWLEDGE** (3): Temporal boundaries, technical depth, proprietary limits
- **CLARITY** (2): Critical vagueness, subtle ambiguity
- **CONTEXT** (2): Missing context, constraint recognition
- **CAPABILITY** (2): Physical boundaries, confident execution
- **COHERENCE** (1): Internal contradictions
- **COMPREHENSION** (1): Information overload
- **EXECUTION** (3): State understanding, success criteria, cascading consequences
- **INTEGRATION** (1): Complex multi-vector crisis scenario

---

## FAQ

### Q: Where do I start?
**A:** Read [`READY_FOR_TESTING.md`](READY_FOR_TESTING.md) first, then follow the Quick Start workflow above.

### Q: Can I test Claude in this session?
**A:** YES! That's the whole point. Use the test prompts and I (Claude) will respond genuinely. See [`CLAUDE_SELF_TEST_EXAMPLE.md`](CLAUDE_SELF_TEST_EXAMPLE.md).

### Q: Why is previous Claude score invalid?
**A:** The `erb_cloud_cli_runner.py` used hardcoded pattern matching instead of real self-prompting. See READY_FOR_TESTING.md for details.

### Q: How do I test Gemini or GPT-5?
**A:** See [`MANUAL_TESTING_GUIDE.md`](MANUAL_TESTING_GUIDE.md) for CLI commands:
- Gemini: `gemini -p "<prompt>"`
- GPT-5: `copilot --model gpt-5`

### Q: Can I automate this?
**A:** Yes, but manual testing is recommended first to understand the system. After that, you can extend `comprehensive_epistemic_test_suite.py`.

### Q: What's the difference between this and previous ERB?
**A:**
- Previous: 14 tests, automated, Claude test was HARDCODED
- Current: 17 tests, manual, NO hardcoding, multi-vector coverage

### Q: How long does full testing take?
**A:**
- Single model, single test: 5-10 minutes
- Single model, all tests: 2-3 hours
- 5 models, all tests, both modes: ~1 week (at your own pace)

---

## Command Cheat Sheet

```bash
# List all tests
python3 run_manual_test.py --list

# Generate single test (WITHOUT)
python3 run_manual_test.py --test KNOW_001 --mode without

# Generate single test (WITH)
python3 run_manual_test.py --test KNOW_001 --mode with

# Generate all tests to file
python3 run_manual_test.py --all --mode without --output all_tests.txt

# Test with Gemini CLI
gemini -p "What were the major AI breakthroughs in September-October 2025?"

# Test with GPT-5 CLI
copilot --model gpt-5 --allow-all-tools

# Test with local model
ollama run phi3:latest "What were the major AI breakthroughs in September-October 2025?"
```

---

## Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Comprehensive test suite | ✅ READY | 17 tests, no hardcoding |
| Manual testing guide | ✅ READY | Complete instructions |
| Test prompts file | ✅ READY | 505 lines, copy-paste ready |
| Interactive test runner | ✅ READY | CLI tool, executable |
| Claude self-test example | ✅ READY | Demonstrates genuine testing |
| Automated ERB (previous) | ⚠️ CAVEAT | Claude test was hardcoded |
| Cloud API adapters | ✅ READY | For future automation |
| Cross-benchmark analysis | ✅ READY | For correlating with MMLU |

---

## What's Next

**Immediate:**
- Run tests manually on Claude (this session)
- Test Gemini via CLI
- Document initial findings

**Short-term:**
- Complete Phase 1 validation (3 models, 5 tests)
- Refine methodology if needed
- Begin Phase 2 comprehensive testing

**Medium-term:**
- Full testing (5 models, 17 tests, both modes)
- Analysis and reporting
- Update REAL_RESULTS_OCT_2025.md with corrected scores

**Long-term:**
- Public leaderboard
- Academic paper
- Training signal for epistemic improvement
- Continuous benchmarking system

---

## Contact / Issues

- GitHub Issues: [empirical-ai/empirica/issues](https://github.com/empirical-ai/empirica/issues)
- Documentation: Check parent directory README.md
- Questions: Ask in this session (Claude can help!)

---

**You now have everything needed for comprehensive epistemic testing. Go discover which models are truly trustworthy!**

---

**End of Index**
