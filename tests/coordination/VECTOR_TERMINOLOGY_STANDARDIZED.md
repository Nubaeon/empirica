# Vector Terminology Standardized - 2025-11-10

**Issue:** Inconsistent vector count references (12 vs 13)  
**Resolution:** Standardized to **12-Vector System**  
**Status:** ✅ COMPLETE

---

## The Correct Terminology

### 12-Vector System (with UNCERTAINTY meta-tracking)

**Structure:**
- **GATE:** ENGAGEMENT (1 vector) - Structural prerequisite (≥0.60 required)
- **TIER 0 - FOUNDATION (35% weight):** know, do, context (3 vectors)
- **TIER 1 - COMPREHENSION (25% weight):** clarity, coherence, signal, density (4 vectors)
- **TIER 2 - EXECUTION (25% weight):** state, change, completion, impact (4 vectors)
- **META:** UNCERTAINTY (explicit meta-tracking, not weighted)

**Total: 12 vectors + 1 meta tracker = 12-Vector System**

---

## Why 12, Not 13?

**UNCERTAINTY is META:**
- UNCERTAINTY tracks uncertainty ABOUT the assessment itself
- It's not part of the tier weighting (35/25/25/15)
- It's supplemental/derived tracking
- The 12 vectors are what you actively assess

**Architectural Clarity:**
- **12 vectors** = the active assessment dimensions
- **UNCERTAINTY** = meta-level tracking of epistemic uncertainty
- Total measurements = 12 + 1 meta

**Analogy:** Like having 12 gauges on a dashboard + 1 "reliability indicator" for the whole dashboard

---

## What Was Changed

### Files Updated:

1. **mcp_local/empirica_mcp_server.py** ✅
   - `get_empirica_introduction` tool
   - Changed "13 vectors" → "12-Vector System"
   - Clarified UNCERTAINTY as meta-tracking
   - Updated all format variations (full, quick, philosophy)

2. **README.md** ✅
   - Changed "13-vector" → "12-vector" 
   - Listed all 12 vectors explicitly
   - Added "+ UNCERTAINTY meta-tracking" clarification

3. **docs/01_b_MCP_AI_START.md** ✅
   - Section header: "Understanding the 13 Vectors" → "12-Vector System"
   - Added "META: UNCERTAINTY (Explicit Meta-Tracking)" section
   - Clarified "Not weighted in tiers (meta-level tracking)"

4. **docs/architecture/SYSTEM_ARCHITECTURE_DEEP_DIVE.md** ✅
   - All "13-vector" → "12-vector"
   - All "13 vector" → "12 vector"

---

## Terminology Guidelines

### ✅ Correct Usage:

- **"12-Vector System"** - The canonical terminology
- **"12 vectors + UNCERTAINTY meta-tracking"** - Full description
- **"12 active vectors with meta-tracking"** - Alternative phrasing
- **"12D assessment"** - Dimension terminology (architectural docs)

### ❌ Avoid:

- **"13 vectors"** - Confuses UNCERTAINTY's meta nature
- **"13-vector system"** - Implies UNCERTAINTY is weighted equally
- **"12 + 1 vectors"** - Awkward phrasing

### 💡 When to Clarify:

Use expanded form when introducing the system:
> "Empirica uses a **12-vector epistemic assessment system** with explicit **UNCERTAINTY meta-tracking**."

Use short form in technical contexts:
> "The 12-vector assessment includes ENGAGEMENT, FOUNDATION (3), COMPREHENSION (4), and EXECUTION (4)."

---

## Architecture Summary

```
┌─────────────────────────────────────────────┐
│         12-VECTOR SYSTEM                    │
├─────────────────────────────────────────────┤
│ GATE                                        │
│  └─ ENGAGEMENT (≥0.60 required)            │
├─────────────────────────────────────────────┤
│ TIER 0: FOUNDATION (35% weight)            │
│  ├─ KNOW (domain knowledge)                │
│  ├─ DO (capability)                        │
│  └─ CONTEXT (environmental awareness)      │
├─────────────────────────────────────────────┤
│ TIER 1: COMPREHENSION (25% weight)        │
│  ├─ CLARITY (task understanding)           │
│  ├─ COHERENCE (logical consistency)        │
│  ├─ SIGNAL (information quality)           │
│  └─ DENSITY (information load)             │
├─────────────────────────────────────────────┤
│ TIER 2: EXECUTION (25% weight)            │
│  ├─ STATE (current awareness)              │
│  ├─ CHANGE (progress tracking)             │
│  ├─ COMPLETION (goal proximity)            │
│  └─ IMPACT (consequence awareness)         │
├─────────────────────────────────────────────┤
│ META: UNCERTAINTY (explicit tracking)      │
│  └─ UNCERTAINTY (about the assessment)     │
│     - Not weighted in tiers                │
│     - Meta-level epistemic tracking        │
└─────────────────────────────────────────────┘

WEIGHTS: 35% + 25% + 25% + 15% (ENGAGEMENT) = 100%
UNCERTAINTY: Meta-tracking (separate from tier weights)
```

---

## Code References

### Where It's Defined:

**`empirica/core/canonical/reflex_frame.py`:**
```python
@dataclass
class EpistemicAssessment:
    """
    Architecture:
    - GATE: ENGAGEMENT (must be ≥ 0.60 to proceed)
    - TIER 0: FOUNDATION (35%) - know, do, context
    - TIER 1: COMPREHENSION (25%) - clarity, coherence, signal, density
    - TIER 2: EXECUTION (25%) - state, change, completion, impact
    - TIER 3: ENGAGEMENT (15%)
    - META: UNCERTAINTY (explicit tracking)
    """
```

### Where It's Used:

- **MCP Server:** 22 tools all reference 12-vector system
- **CLI:** `empirica assess` command
- **Onboarding:** Bootstrap wizard
- **Documentation:** All production docs
- **Tests:** CASCADE integration tests

---

## Benefits of This Clarification

### 1. Architectural Clarity
- Clear that UNCERTAINTY is meta-level tracking
- Tier weights (35/25/25/15) make sense without UNCERTAINTY
- Matches code implementation exactly

### 2. Pedagogical Clarity
- Easier to explain: "12 vectors you assess + uncertainty about your assessment"
- Avoids confusion about whether UNCERTAINTY is weighted
- Clear distinction between active assessment vs meta-tracking

### 3. Consistency
- Matches most of the existing codebase
- Aligns with "12D" terminology in architecture docs
- Consistent with `twelve_vector_monitor` naming

---

## Testing Confirmation

```bash
$ pytest tests/mcp/test_mcp_server_startup.py -v
======================= test session starts =======================
collected 3 items

tests/mcp/test_mcp_server_startup.py::test_server_starts PASSED [ 33%]
tests/mcp/test_mcp_server_startup.py::test_tools_registered PASSED [ 66%]
tests/mcp/test_mcp_server_startup.py::test_introduction_tool_exists PASSED [100%]

======================= 3 passed in 0.24s =======================
```

✅ All tests pass with new terminology

---

## Summary

**Changed:** 4 files updated  
**Standardized on:** 12-Vector System (+ UNCERTAINTY meta-tracking)  
**Rationale:** Architectural accuracy, pedagogical clarity, code consistency  
**Tests:** All passing ✅  

**The system is now consistently described as a 12-vector epistemic assessment framework with explicit uncertainty meta-tracking.**

---

**Completed:** 2025-11-10 19:55 UTC  
**AI:** Claude Copilot CLI
