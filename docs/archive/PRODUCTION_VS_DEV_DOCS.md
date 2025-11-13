# Production vs Development Documentation

**Question:** What docs to keep in production vs move to empirica-dev?  
**Analysis:** Current state and recommendations

---

## Current Documentation Inventory

**Total:** 399 .md files  
**Size:** ~1.16 MB total

### Breakdown by Directory:

1. **docs/production/** - 372 KB, 27 files
   - Complete production reference (21 guides)
   - API documentation
   - Architecture details
   - Configuration guides

2. **docs/guides/** - 392 KB
   - TRY_EMPIRICA_NOW.md
   - MCP config examples
   - Quick starts and tutorials

3. **docs/reference/** - 132 KB
   - Technical reference
   - API schemas
   - Quick references

4. **docs/architecture/** - 168 KB
   - EMPIRICA_SYSTEM_OVERVIEW.md
   - Component design
   - Data flows

5. **docs/phase_0/** - 64 KB
   - EMPIRICA_SINGLE_AI_FOCUS.md
   - Design decisions
   - Phase specifications

6. **docs/research/** - 32 KB
   - RECURSIVE_EPISTEMIC_REFINEMENT.md
   - Advanced topics

7. **docs/sessions/** - (new, session history)
   - Development session docs

---

## Recommendation: What to Keep vs Move

### ✅ KEEP in Production (Essential for Users)

**Main docs/ folder (9 files):**
- 00_START_HERE.md
- 02_INSTALLATION.md
- 03_CLI_QUICKSTART.md
- 04_MCP_QUICKSTART.md
- 05_ARCHITECTURE.md
- 06_TROUBLESHOOTING.md
- ONBOARDING_GUIDE.md
- PRODUCTION_READINESS_ASSESSMENT.md
- README.md

**docs/skills/** (1 file)
- SKILL.md - AI agent guide

**docs/production/** (ALL 21 guides - 372 KB)
- ✅ **KEEP** - Essential for production users
- Complete API reference
- Comprehensive system documentation
- Users need this for advanced features

**docs/guides/** (Essential tutorials)
- ✅ **KEEP** - TRY_EMPIRICA_NOW.md
- ✅ **KEEP** - examples/mcp_configs/
- Users need these for getting started

**docs/architecture/** (System overview)
- ✅ **KEEP** - EMPIRICA_SYSTEM_OVERVIEW.md
- Users/developers need architecture understanding

**docs/reference/** (API reference)
- ✅ **KEEP** - Technical reference docs
- API schemas and quick references

---

### 📦 MOVE to empirica-dev/ (Development Only)

**docs/sessions/** (ALL session history)
- 📦 **MOVE** - Internal development history
- Not needed by production users
- Useful for us to track decisions

**docs/phase_0/** (Design specifications)
- 📦 **MOVE** - Internal design docs
- Phase specifications are for development
- Users don't need this

**docs/research/** (Advanced research topics)
- 🤔 **OPTIONAL MOVE** - RECURSIVE_EPISTEMIC_REFINEMENT.md
- Very advanced, research-oriented
- Could stay for advanced users OR move to dev

**docs/_archive/** (Old archived docs)
- 📦 **MOVE** - Development artifacts
- Definitely not for production users

---

## Recommended Structure

### Production Repository (empirica/)

```
docs/
├── 00_START_HERE.md              ✅ Essential
├── 02_INSTALLATION.md             ✅ Essential
├── 03_CLI_QUICKSTART.md           ✅ Essential
├── 04_MCP_QUICKSTART.md           ✅ Essential
├── 05_ARCHITECTURE.md             ✅ Essential
├── 06_TROUBLESHOOTING.md          ✅ Essential
├── ONBOARDING_GUIDE.md            ✅ Essential
├── README.md                      ✅ Essential
├── skills/
│   └── SKILL.md                   ✅ Essential (AI agents)
├── production/                    ✅ Essential (21 guides, 372 KB)
│   ├── README.md
│   ├── 00_COMPLETE_SUMMARY.md
│   ├── 01_QUICK_START.md
│   └── ... (18 more comprehensive guides)
├── guides/                        ✅ Essential (tutorials)
│   ├── TRY_EMPIRICA_NOW.md
│   └── examples/mcp_configs/
├── architecture/                  ✅ Essential (system design)
│   └── EMPIRICA_SYSTEM_OVERVIEW.md
└── reference/                     ✅ Essential (API reference)
    └── [technical docs]
```

**Total for production:** ~9 main docs + ~50 subdirectory docs (~1 MB)

### Development Repository (empirica-dev/)

```
docs/
├── [All production docs above]    ✅ Keep for reference
├── sessions/                      📦 Development history
│   ├── 2025-11-08/               (Our session docs)
│   └── [future sessions]
├── phase_0/                       📦 Design specs
│   └── EMPIRICA_SINGLE_AI_FOCUS.md
├── research/                      📦 Research topics
│   └── RECURSIVE_EPISTEMIC_REFINEMENT.md
└── _archive/                      📦 Old artifacts
    └── [archived files]
```

---

## Rationale

### Why Keep production/ docs?

**Users need comprehensive reference:**
- API documentation (13_PYTHON_API.md)
- Epistemic vectors details (05_EPISTEMIC_VECTORS.md)
- CASCADE workflow (06_CASCADE_FLOW.md)
- Configuration tuning (16_TUNING_THRESHOLDS.md)
- Custom plugins (14_CUSTOM_PLUGINS.md)

**Without these:** Users can't:
- Use Python API effectively
- Understand 12-vector system deeply
- Configure advanced features
- Extend the system

**Size:** 372 KB is reasonable for comprehensive docs

### Why Move phase_0/ and sessions/?

**phase_0/ is internal design specs:**
- EMPIRICA_SINGLE_AI_FOCUS.md = design decisions
- Users don't need to know WHY we chose single-AI focus
- They just need to know HOW to use it

**sessions/ is development history:**
- Useful for us to track evolution
- Not relevant to production users
- Can confuse users ("what's this?")

---

## Action Plan

### Step 1: What to Move (When Creating empirica-dev/)

```bash
# After: cp -r empirica empirica-dev

# In empirica/ (production), move internal docs:
cd empirica
mkdir -p ../empirica-dev-docs-only
mv docs/sessions ../empirica-dev-docs-only/
mv docs/phase_0 ../empirica-dev-docs-only/
mv docs/_archive ../empirica-dev-docs-only/

# Optional: Move research
mv docs/research ../empirica-dev-docs-only/

# In empirica-dev/, restore them:
cd ../empirica-dev
mv ../empirica-dev-docs-only/* docs/
```

### Step 2: Update docs/README.md

Add note about what's included:

```markdown
## 📚 Documentation Included

This production documentation includes:
- ✅ Getting started guides (7 docs)
- ✅ Skills guide for AI agents
- ✅ Complete production reference (21 guides)
- ✅ Architecture overview
- ✅ Practical guides and examples

**Not included** (development-only docs):
- Design specifications (phase_0/)
- Development session history (sessions/)
- Research topics (may be published separately)
```

---

## Summary

### ✅ KEEP in Production (~1 MB, ~60 docs):
- All main docs/ files (9 essential guides)
- docs/skills/ (AI agent guide)
- docs/production/ (21 comprehensive guides) ⭐
- docs/guides/ (tutorials and examples)
- docs/architecture/ (system overview)
- docs/reference/ (API reference)

### 📦 MOVE to empirica-dev/ (~150 KB, ~10 docs):
- docs/sessions/ (development history)
- docs/phase_0/ (design specifications)
- docs/_archive/ (old artifacts)
- docs/research/ (optional - advanced research)

### Result:
- **Production:** Clean, user-focused, comprehensive
- **Dev:** Full history, design docs, research topics
- **Size:** Still under 1.5 MB (very reasonable)

---

**Recommendation:** Keep production/ docs - users need comprehensive reference!

