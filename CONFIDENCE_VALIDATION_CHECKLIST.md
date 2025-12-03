# 95% Confidence Validation Checklist

**For:** Distribution Implementation (Empirica Goal 09c478a1-3154-454f-92fe-aa2c4f956a02)
**Purpose:** Gate each phase with systematic validation before proceeding
**Use:** After completing each phase, verify ALL checkboxes before moving forward

---

## Phase 0: PyPI Foundation

**STOP.** Do not proceed to Phase 1 until ALL items are checked.

### Setup & Configuration
- [ ] **pyproject.toml created** - File exists at project root
- [ ] **TOML syntax valid** - Run: `python3 -m toml tests < pyproject.toml` (no errors)
- [ ] **Entry point defined** - `[project.scripts]` section points to actual function
- [ ] **Entry point exists** - Can import: `from empirica.cli.cli_core import main`
- [ ] **Dependencies listed** - All items from requirements.txt in `dependencies` array
- [ ] **Python version specified** - `requires-python = ">=3.9"` or similar

### Build Verification
- [ ] **uv installed** - `uv --version` produces output
- [ ] **Build succeeds** - `uv build` creates `dist/` directory with `.whl` and `.tar.gz`
- [ ] **No build warnings** - `uv build` output contains no "WARNING" lines
- [ ] **Wheel file exists** - `dist/empirica_cli-*.whl` is present and >1MB
- [ ] **Wheel is valid** - Can extract: `unzip -t dist/empirica_cli-*.whl`

### Local Installation Testing
- [ ] **Test venv created** - `uv venv /tmp/test-empirica` succeeds
- [ ] **Wheel installs** - `pip install dist/empirica_cli-*.whl` in test venv succeeds
- [ ] **CLI available** - `which empirica` returns path in test venv
- [ ] **Help works** - `empirica --help` produces output (not error)
- [ ] **Version detectable** - `empirica --version` returns version number
- [ ] **Key commands work** - `empirica bootstrap --help`, `empirica goals-create --help` (no errors)

### TestPyPI Publishing
- [ ] **TestPyPI account created** - Can log in at test.pypi.org
- [ ] **API token generated** - Have token from https://test.pypi.org/manage/account/tokens/
- [ ] **Upload succeeds** - `uv publish --publish-url https://test.pypi.org/legacy/ --token [token]` succeeds
- [ ] **Package visible** - Package appears at https://test.pypi.org/project/empirica-cli/
- [ ] **TestPyPI install works** - `pip install -i https://test.pypi.org/simple/ empirica-cli` succeeds
- [ ] **Fresh environment test** - In fresh venv: `empirica --help` works
- [ ] **Uninstall clean** - `pip uninstall empirica-cli` leaves no traces

### Confidence Assessment

**Ask yourself:**
- Do you understand what went into pyproject.toml? (must = YES)
- Could you explain it to someone else? (must = YES)
- Are there any warnings or errors? (must = NO)
- Did all tests pass on your platform? (must = YES)
- Is the package visible on TestPyPI? (must = YES)

**Your Confidence:**
```
Checkboxes passed: ____ / 23
If ≥22 (96%): Proceed to Phase 1 ✅
If <22: Fix issues, re-validate, recount
```

---

## Phase 1: Package Managers (PyPI + Homebrew + Chocolatey + GitHub Actions)

**STOP.** Do not proceed to Phase 2 until ALL items are checked.

### Task 1A: Publish to Real PyPI

- [ ] **PyPI account created** - Can log in at pypi.org
- [ ] **Real token generated** - Have token from https://pypi.org/manage/account/tokens/
- [ ] **Upload succeeds** - `uv publish --token [token]` succeeds without errors
- [ ] **Package visible** - Package appears at https://pypi.org/project/empirica-cli/
- [ ] **Installation works** - `pip install empirica-cli` succeeds (from real PyPI)
- [ ] **Fresh venv test** - In fresh venv: `empirica --help` works from real PyPI install
- [ ] **uv tool works** - `uv tool install empirica-cli` succeeds and adds to PATH
- [ ] **pipx works** - `pipx install empirica-cli` succeeds and adds to PATH
- [ ] **Verified on multiple OS** - Tested on at least 2 of: Windows, macOS, Linux

### Task 1B: Homebrew Tap

- [ ] **Tap repo created** - GitHub repo `homebrew-empirica` exists and is public
- [ ] **Formula file created** - `Formula/empirica-cli.rb` exists and is valid Ruby
- [ ] **SHA256 calculated** - Correct wheel SHA256 in formula (use: `shasum -a 256 *.whl`)
- [ ] **Audit passes** - `brew audit --strict --online Formula/empirica-cli.rb` passes
- [ ] **Local install works** - `brew install --build-from-source ./Formula/empirica-cli.rb` succeeds
- [ ] **Command works** - `empirica --help` produces output after brew install
- [ ] **Tap accessible** - Users can: `brew tap YOUR_USERNAME/empirica && brew install empirica-cli`
- [ ] **Tested on macOS/Linux** - Formula works on at least one of these

### Task 1C: Chocolatey

- [ ] **nuspec file created** - `.nuspec` file is valid XML
- [ ] **PowerShell script created** - `tools/chocolateyInstall.ps1` is valid (no syntax errors)
- [ ] **Package built** - `choco pack` creates `.nupkg` file
- [ ] **Chocolatey account created** - Can log in at chocolatey.org
- [ ] **API key generated** - Have Chocolatey API key
- [ ] **Submission succeeds** - `choco push *.nupkg --key=[key]` succeeds
- [ ] **Moderation in progress** - Package entered moderation queue (email confirmation received)
- [ ] **Approved status** - Package approved and appears in Chocolatey repo
- [ ] **Tested on Windows** - Installation via `choco install empirica-cli` works

### Task 1D: GitHub Actions Auto-Publishing

- [ ] **Workflow file created** - `.github/workflows/publish.yml` exists
- [ ] **YAML is valid** - No YAML syntax errors (use https://yamllint.com/)
- [ ] **Secrets configured** - `PYPI_TOKEN` set in GitHub Secrets
- [ ] **Test release created** - Created tag `v0.1.1` (test version)
- [ ] **Workflow triggered** - Workflow ran (check Actions tab)
- [ ] **Workflow succeeded** - No job failures
- [ ] **Package updated** - New version appears on PyPI automatically
- [ ] **Homebrew updated** - Formula auto-updated (if auto-update configured)

### Integration Testing

- [ ] **Uninstall tests** - `pip uninstall empirica-cli` leaves no traces
- [ ] **Uninstall Homebrew** - `brew uninstall empirica-cli` removes cleanly
- [ ] **Uninstall Chocolatey** - `choco uninstall empirica-cli` removes cleanly
- [ ] **Reinstall works** - Can reinstall without issues
- [ ] **All OS tested** - Windows, macOS, Linux all have working installs

### Confidence Assessment

**Ask yourself:**
- Is the package on real PyPI? (must = YES)
- Do all 3 package managers work? (must = YES on at least 1 each platform)
- Are there any critical bugs? (must = NO)
- Can you follow your own installation instructions? (must = YES)

**Your Confidence:**
```
Checkboxes passed: ____ / 36
If ≥34 (94%): Proceed to Phase 2 (Docker) ✅
If <34: Fix issues, re-validate, recount
```

---

## Phase 2: Docker Distribution (OPTIONAL)

Skip this section if not implementing Docker distribution.

### Dockerfile & Build

- [ ] **Dockerfile created** - File exists at project root
- [ ] **Dockerfile syntax valid** - No Docker syntax errors
- [ ] **Build succeeds** - `docker build -t empirica-cli:0.1.0 .` succeeds
- [ ] **Image size acceptable** - Image is <1GB (check with `docker images`)
- [ ] **No build warnings** - Build output has no warnings about deprecated commands

### Docker Functionality

- [ ] **Help command works** - `docker run empirica-cli:0.1.0 empirica --help` produces output
- [ ] **Version works** - `docker run empirica-cli:0.1.0 empirica --version` shows version
- [ ] **Volume mounting works** - `docker run -v $PWD:/work empirica-cli:0.1.0 ls /work` works
- [ ] **Works on Windows** - Docker Desktop for Windows runs it
- [ ] **Works on macOS** - Docker Desktop for macOS runs it
- [ ] **Works on Linux** - Docker runs it natively

### Docker Hub Publishing

- [ ] **Docker Hub account created** - Can log in at hub.docker.com
- [ ] **Image tagged for hub** - `docker tag empirica-cli:0.1.0 YOUR_USERNAME/empirica-cli:0.1.0`
- [ ] **Login succeeds** - `docker login` succeeds
- [ ] **Push succeeds** - `docker push YOUR_USERNAME/empirica-cli:0.1.0` completes
- [ ] **Image visible** - Image appears at https://hub.docker.com/r/YOUR_USERNAME/empirica-cli
- [ ] **Can pull from hub** - `docker pull YOUR_USERNAME/empirica-cli:0.1.0` works from clean machine

### Confidence Assessment

**Your Confidence:**
```
Checkboxes passed: ____ / 17
If ≥16 (94%): Mark Phase 2 done ✅
If <16: Fix issues, re-validate
```

---

## Phase 3: Provider Integrations (OPTIONAL)

Skip this section if not implementing skills/integrations.

Validate for each integration you implement:

### For Each Integration (Claude Skill, ChatGPT Custom GPT, Gemini Workspace, Ollama Docs)

- [ ] **Skill/integration file created** - SKILL.md or equivalent exists
- [ ] **Valid structure** - Follows respective provider's format
- [ ] **Tested with provider** - Actually tested, not assumed
- [ ] **Works as documented** - Can follow instructions and it works
- [ ] **Epistemic framework included** - Contains epistemic vector definitions
- [ ] **CASCADE workflow included** - Contains workflow phases

### Confidence Assessment

**Your Confidence:**
```
Checkboxes passed: ____ / (6 * number_of_integrations)
If ≥95%: Mark Phase 3 done ✅
If <95%: Fix failing integrations
```

---

## Phase 4: Validation & Testing (CRITICAL)

**FINAL GATE.** Do not release until ALL items are checked.

### Cross-Platform Installation

- [ ] **Windows installation** - Installed via `pip install` or `choco install` on Windows (or WSL2)
- [ ] **macOS installation** - Installed via `brew install` on macOS (Intel and/or Apple Silicon)
- [ ] **Linux installation** - Installed via `uv tool install` or native package on Linux
- [ ] **Same commands work everywhere** - `empirica --help`, `empirica --version` work identically
- [ ] **No platform-specific errors** - No errors like "command not found" or "module not found"

### Provider Testing (Same Goal, Different Providers)

- [ ] **Test goal selected** - Chose a non-trivial goal (e.g., "Debug a system component")
- [ ] **Claude test** - Ran goal with Claude + EMPIRICA_CLAUDE.md
- [ ] **GPT test** - Ran goal with GPT + EMPIRICA_GPT5.md
- [ ] **Gemini test** - Ran goal with Gemini + EMPIRICA_GEMINI.md
- [ ] **Local model test** - Ran goal with local model (Ollama) + EMPIRICA_UNIVERSAL.md
- [ ] **Results compared** - Reviewed outputs and epistemic deltas from all 4
- [ ] **Learning patterns consistent** - Different providers show similar epistemic delta patterns
- [ ] **No provider failures** - All 4 providers successfully completed goal

### Feature Testing

- [ ] **`empirica bootstrap` works** - Successfully creates new session
- [ ] **`empirica goals-create` works** - Can create goals with success criteria
- [ ] **`empirica session-status` works** - Returns current epistemic state
- [ ] **Epistemic phases work** - PREFLIGHT, INVESTIGATE, ACT, POSTFLIGHT all functional
- [ ] **Git integration works** - Checkpoints saved to git branches
- [ ] **Handoffs work** - Can generate epistemic handoff packages
- [ ] **Help is accurate** - `empirica --help` descriptions match actual behavior

### Documentation Testing

- [ ] **Installation guide accurate** - Can follow EMPIRICA_INSTALLATION_GUIDE.md and succeed
- [ ] **Prompts load correctly** - System prompts can be loaded and used by providers
- [ ] **All links work** - URLs in docs are valid and don't 404
- [ ] **Examples run** - Code examples in docs actually run without errors
- [ ] **Platform instructions work** - Each platform section (Cursor, Continue.dev, etc.) functions

### Bug & Error Testing

- [ ] **No critical bugs** - No showstoppers found during testing
- [ ] **Graceful error handling** - Errors produce helpful messages, not cryptic failures
- [ ] **Recoverable failures** - If something fails, can recover and try again
- [ ] **Data safety** - No data loss or corruption on failed operations
- [ ] **Clean uninstall** - Removing empirica leaves no stray files or environment pollution

### Final Verification

- [ ] **New user test** - Had someone unfamiliar follow installation steps (or you pretend to be new)
- [ ] **New user succeeded** - Installation and basic commands work on first try
- [ ] **Time to working install** - Setup takes <5 minutes from download
- [ ] **No prerequisite confusion** - User doesn't get stuck on "what's Python?" or "what's pip?"

### Confidence Assessment

**Ask yourself:**
- Can a new user install and use this? (must = YES)
- Does it work identically on all platforms? (must = YES)
- Does it work with all supported providers? (must = YES)
- Are there any bugs that would block users? (must = NO)
- Would you personally use this in production? (must = YES)

**Your Confidence:**
```
Checkboxes passed: ____ / 38
If ≥36 (95%): 🎉 RELEASE READY ✅
If <36: Fix issues, re-test, re-validate
```

---

## How to Use This Checklist

### For Each Phase:

1. **Complete the phase work** (refer to PROJECT_SPEC_DISTRIBUTION.md and HANDOFF_DISTRIBUTION_IMPLEMENTATION.md)

2. **Work through the checklist section** for that phase
   - Check off each item as you verify it
   - Mark items as N/A only with explicit justification
   - Don't skip items without good reason

3. **Count checkboxes:**
   - Total checkboxes in section
   - Checkboxes you checked (✓)
   - Calculate: (checked / total) × 100 = %

4. **Compare to threshold:**
   - If ≥95%: You have 95% confidence, proceed to next phase
   - If <95%: You have uncertainty, go back and fix/verify

5. **Document results:**
   - Note any items that were difficult
   - Note any items that revealed bugs
   - Note anything that surprised you

### Red Flags (Investigate Immediately):

- Fewer than 80% checkboxes passed → Major issues, don't proceed
- Items with caveats/exceptions → Investigate before trusting
- Skipped items → Validate why before proceeding
- Tests that "mostly worked" → Define "mostly" more rigorously

---

## What 95% Confidence Means

It means:
- ✅ You've verified the core functionality
- ✅ You've tested on representative platforms/providers
- ✅ You've found and fixed bugs during testing
- ✅ You understand what could still go wrong and why
- ✅ You would use this yourself

It does NOT mean:
- ❌ Everything is perfect (no software is)
- ❌ No edge cases exist (they always do)
- ❌ You've tested every possible scenario
- ❌ No future bugs will be found

It DOES mean:
- ✅ The core work is solid
- ✅ The foundation is stable
- ✅ You can defend your decisions
- ✅ You're ready to show others

---

**Use this checklist for each phase. Don't skip. Trust the process.**
