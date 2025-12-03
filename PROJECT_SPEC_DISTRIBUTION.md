# PROJECT SPECIFICATION: Empirica One-Click Distribution

**Status:** Ready for implementation
**Confidence Threshold:** 95% per phase
**Empirica Goal ID:** 09c478a1-3154-454f-92fe-aa2c4f956a02
**Session ID:** 5a6823e6-8f2a-4450-af9c-afd87ae73416

---

## Quick Start for Next Claude

1. **Read this file** (you are here)
2. **Read DISTRIBUTION_STRATEGY.md** (decisions & rationale)
3. **Read HANDOFF_DISTRIBUTION_IMPLEMENTATION.md** (detailed tasks)
4. **Execute Phase 0** (PyPI foundation)
5. **Validate at 95% confidence** before Phase 1
6. **Repeat for each phase**

---

## What You're Building

**Goal:** Make Empirica installable with one click on Windows, macOS, Linux, with full support for Claude, GPT-5, Gemini, Llama, and local models.

**Result users will see:**
```bash
# Install (any platform)
brew install empirica-cli  # macOS/Linux
choco install empirica-cli  # Windows
uv tool install empirica-cli  # Universal

# Use with any provider
empirica start --provider=claude
empirica start --provider=gpt5
empirica start --provider=gemini
empirica start --provider=local  # Ollama

# Works everywhere
$ empirica preflight --prompt "Debug auth system"
Epistemic State Assessment:
  KNOW: 0.3
  UNCERTAINTY: 0.8
  CLARITY: 0.5
  ...
```

---

## Five Implementation Phases

### Phase 0: PyPI Foundation ✅ CRITICAL PATH
**Status:** Blueprint complete, ready to execute
**Time:** 2-3 hours
**Owner:** Next Claude
**Success Metric:** Package published on TestPyPI, installable via `pip install`

**Key steps:**
1. Convert `requirements.txt` → `pyproject.toml`
2. Build distribution: `uv build`
3. Test locally: `pip install dist/*.whl`
4. Publish to TestPyPI: `uv publish --publish-url https://test.pypi.org/legacy/`
5. Validate installation works

**95% Confidence Criteria:**
- pyproject.toml is valid
- uv build succeeds without warnings
- Installation from wheel works
- `empirica --help` produces output
- Package appears on TestPyPI.org
- `pip install -i https://test.pypi.org/simple/ empirica-cli` works

**Risk:** None if you follow the template. This is standard Python packaging.

---

### Phase 1: Package Managers ✅ CRITICAL PATH
**Status:** Detailed instructions provided
**Time:** 4-6 hours
**Owner:** Next Claude
**Success Metric:** Users can install via `brew`, `choco`, `uv`, `pipx`

**Four sub-tasks:**

**1A: Publish to Real PyPI (15 min)**
- Create PyPI account, generate token
- `uv publish --token [token]`
- Verify at pypi.org/project/empirica-cli

**1B: Create Homebrew Tap (2-3 hours)**
- Create `homebrew-empirica` repo on GitHub
- Add formula for macOS/Linux
- Test: `brew install --build-from-source`
- Users: `brew install YOUR_USERNAME/empirica/empirica-cli`

**1C: Submit to Chocolatey (2-3 hours)**
- Create `.nuspec` manifest
- Submit to Chocolatey.org
- Wait 1-2 days for approval
- Users: `choco install empirica-cli`

**1D: GitHub Actions Auto-Publishing (1 hour)**
- Create `.github/workflows/publish.yml`
- Future releases auto-publish to PyPI/Homebrew

**95% Confidence Criteria:**
- PyPI: Package visible at pypi.org, `pip install` works on all 3 OS
- Homebrew: `brew install` works on macOS and Linux
- Chocolatey: Package approved, installable on Windows
- All three methods: `empirica --help` produces output
- Uninstall leaves no traces

**Risk:** Package manager moderation delays (mitigated by PyPI as primary)

---

### Phase 2: Docker Distribution (OPTIONAL)
**Status:** Template provided
**Time:** 1-2 hours
**Owner:** Next Claude (if proceeding; can defer)
**Success Metric:** Image published to Docker Hub, users can `docker run empirica-cli`

**Steps:**
1. Create `Dockerfile` with Python 3.11, empirica install
2. Build: `docker build -t YOUR_USERNAME/empirica-cli:0.1.0 .`
3. Push: `docker push YOUR_USERNAME/empirica-cli:0.1.0`
4. Test: `docker run YOUR_USERNAME/empirica-cli empirica --help`

**95% Confidence Criteria:**
- Image builds without errors
- Image size reasonable (~500MB-1GB)
- Works on Windows Docker Desktop, macOS Docker, Linux
- Volumes can be mounted: `docker run -v $PWD:/work`

**Note:** This is optional if not needed for target users

---

### Phase 3: Provider Integrations (OPTIONAL)
**Status:** Documented in INSTALLATION_GUIDE
**Time:** 2-4 hours per platform
**Owner:** Next Claude (if proceeding; can defer)
**Success Metric:** Users can access Empirica on Claude.ai, ChatGPT, Gemini, Ollama

**Integrations:**
- Claude Skill (Claude.ai)
- ChatGPT Custom GPT (OpenAI)
- Gemini Workspace (Google)
- Ollama Integration Docs (Local)

**Note:** These are complementary to CLI distribution. Not blocking.

---

### Phase 4: Validation & Testing (CRITICAL)
**Status:** Plan provided
**Time:** 2-4 hours
**Owner:** Next Claude
**Success Metric:** All platforms tested, 95%+ confidence, ready for release

**Testing dimensions:**

**Cross-Platform Testing:**
- [ ] Install on Windows (native or WSL2)
- [ ] Install on macOS (Intel and Apple Silicon)
- [ ] Install on Linux (Ubuntu, Fedora, others)
- [ ] Verify same commands work everywhere

**Provider Testing:**
- [ ] Run same goal with Claude + system prompt
- [ ] Run same goal with GPT-5 + system prompt
- [ ] Run same goal with Gemini + system prompt
- [ ] Compare epistemic deltas (should be similar patterns)

**Feature Testing:**
- [ ] `empirica bootstrap` works
- [ ] `empirica goals-create` works
- [ ] `empirica session-status` works
- [ ] `empirica preflight`, `investigate`, `act`, `postflight` work
- [ ] Checkpoints saved to git
- [ ] Handoffs generated correctly

**Documentation Testing:**
- [ ] Installation guide instructions verified
- [ ] System prompt loading verified
- [ ] Skill integration tested (Claude)
- [ ] Examples run without errors

**95% Confidence Criteria:**
- All cross-platform tests pass
- All provider tests show consistent epistemic patterns
- All features work on all platforms
- All documentation accurate
- No critical bugs found
- Users can follow docs and succeed

---

## Key Files & Resources

### Strategic Documents (Read First)
- **DISTRIBUTION_STRATEGY.md** - Why these decisions, what alternatives considered, risk analysis
- **EMPIRICA_INSTALLATION_GUIDE.md** - Complete setup for 9 platforms
- **HANDOFF_DISTRIBUTION_IMPLEMENTATION.md** - Detailed task-by-task instructions (long, reference as needed)

### Code Assets
- **pyproject.toml** - Created in Phase 0 (template in HANDOFF)
- **Dockerfile** - Created in Phase 3 (template in HANDOFF)
- **.github/workflows/publish.yml** - Created in Phase 1D (template in HANDOFF)
- **Formula/empirica-cli.rb** - Created in Phase 1B (template in HANDOFF)
- **empirica-cli.nuspec** - Created in Phase 1C (template in HANDOFF)

### Documentation Assets
- **docs/system-prompts/EMPIRICA_UNIVERSAL.md** - Phase 2A (template in HANDOFF)
- **docs/system-prompts/EMPIRICA_CLAUDE.md** - Phase 2B
- **docs/system-prompts/EMPIRICA_GPT5.md** - Phase 2C
- **docs/system-prompts/EMPIRICA_GEMINI.md** - Phase 2D

---

## Decision Framework: When to Proceed to Next Phase

**Only proceed to phase N+1 if phase N meets ALL 95% confidence criteria:**

```
Phase 0 Complete? (95% confidence)
  ├─ YES → Proceed to Phase 1
  └─ NO → Debug, fix, re-validate

Phase 1 Complete? (95% confidence)
  ├─ YES → Proceed to Phases 2-4 (can run in parallel)
  └─ NO → Debug, fix, re-validate

Phase 2 Complete? (95% confidence)
  ├─ YES → Mark as done (optional phase)
  └─ NO → Skip or defer (not critical path)

Phase 3 Complete? (95% confidence)
  ├─ YES → Mark as done (optional phase)
  └─ NO → Skip or defer (not critical path)

Phase 4 Complete? (95% confidence)
  ├─ YES → 🎉 RELEASE READY
  └─ NO → Go back to failing phase, fix, re-test
```

---

## Success Metrics (Overall)

You will know you've succeeded when:

1. ✅ Users can install via `uv tool install empirica-cli` on any OS
2. ✅ Users can install via `brew install` on macOS/Linux
3. ✅ Users can install via `choco install` on Windows
4. ✅ Users can use with Claude, GPT-5, Gemini, or local models
5. ✅ `empirica --help` works identically on all platforms
6. ✅ Epistemic framework works identically on all providers
7. ✅ System prompt (CANONICAL_SYSTEM_PROMPT.md) works with all providers
8. ✅ Documentation is comprehensive and accurate
9. ✅ No critical bugs reported by testers
10. ✅ Installation takes <5 minutes for new user

---

## What Not to Do

- ❌ Don't use npm to bundle Python (creates 180 MB bloat, bad maintenance)
- ❌ Don't assume one provider will work like another (test each)
- ❌ Don't skip validation (95% confidence is non-negotiable)
- ❌ Don't commit secrets to git (API keys, tokens)
- ❌ Don't publish until Phase 0 is 95% confident
- ❌ Don't assume pyproject.toml will work without testing
- ❌ Don't skip cross-platform testing (different OS, different issues)

---

## Critical Path (Must Complete)

**Must complete in order:**
1. Phase 0: PyPI Foundation
2. Phase 1: Package Managers
3. Phase 4: Validation

**Can run in parallel or defer:**
- Phase 2: Docker (nice-to-have)
- Phase 3: Skills (nice-to-have)

---

## Effort Estimate

- **Phase 0:** 2-3 hours (solo)
- **Phase 1:** 4-6 hours (solo)
- **Phase 2:** 1-2 hours (solo, optional Docker)
- **Phase 3:** 2-4 hours (solo per platform, optional Skills)
- **Phase 4:** 2-4 hours (solo)

**Total critical path:** 8-13 hours
**With optional phases:** 11-19 hours
**If parallelized with 2 AIs:** 5-10 hours

---

## Confidence Escalation

### PREFLIGHT (Assessment)
- Review this spec ✓
- Review DISTRIBUTION_STRATEGY.md ✓
- Verify you understand all 5 phases ✓
- Identify any blockers
- **Checkpoint:** Are you 95% confident you understand what to build?

### INVESTIGATE (Discovery)
- Set up development environment
- Review pyproject.toml template
- Check current code structure
- Identify where entry point is defined
- **Checkpoint:** Can you find and understand the entry point?

### ACT (Execution)
- Create pyproject.toml (Phase 0)
- Test locally (Phase 0)
- Publish to TestPyPI (Phase 0)
- Publish to real PyPI (Phase 1)
- Follow instructions for remaining phases
- **Checkpoint:** Does each phase meet 95% confidence criteria?

### POSTFLIGHT (Learning)
- Document what worked, what didn't
- Update this spec if anything changed
- Generate learnings for next distribution efforts
- Record time spent vs estimates
- **Checkpoint:** Is distribution now repeatable for future releases?

---

## Contact & Escalation

If you hit blockers:
1. Re-read DISTRIBUTION_STRATEGY.md (why this approach)
2. Re-read HANDOFF_DISTRIBUTION_IMPLEMENTATION.md (detailed steps)
3. Check the specific phase success criteria
4. If still blocked, note what's blocking and why (for next session)

---

## Next Claude: Your Starting Point

1. **Read this entire file** (30 minutes)
2. **Read DISTRIBUTION_STRATEGY.md** (60 minutes)
3. **Review HANDOFF_DISTRIBUTION_IMPLEMENTATION.md** for Phase 0 (30 minutes)
4. **Execute Phase 0** (2-3 hours)
5. **Validate at 95% confidence**
6. **Report back with results**

---

**Created:** 2025-12-03
**By:** Claude (previous session)
**For:** Next Claude (implementation)
**Status:** Ready to begin Phase 0
