# Phase-Aware Calibration: Noetic vs Praxic Grounding

**Status:** IMPLEMENTED (Phases 1-2.8 complete + phase-weighted holistic score + calibration insights loop + actionable feedback)
**Author:** David + Claude Code
**Date:** 2026-02-10 (updated 2026-03-09)
**Depends on:** Grounded Calibration (v1.5.0), Sentinel Architecture, CHECK Gate

---

## Problem

Grounded calibration conflates epistemic gain with artifact production. Evidence sources
(tests, git metrics, artifact counts, goal completions) are **praxic proxies** — they
measure what was done, not what was understood.

A verification session that confirms "63/63 functions preserved, no circular deps"
produces high knowledge (uncertainty 0.25 -> 0.10) but near-zero artifacts. The grounding
system scores `know` at 0.5 when self-assessed 0.9 because it can't distinguish
"searched thoroughly, found nothing wrong" from "didn't search."

This is not a bug — it's a category error. The system applies action-based calibration
to investigation work. Humans make the same mistake: systematically overvaluing action
tasks over the arguably harder noetic investigation that makes good action possible.

---

## Design: CHECK as Phase Boundary

The CHECK gate already separates noetic (investigation) from praxic (action) phases.
Calibration should respect this boundary.

```
PREFLIGHT ─────────── CHECK ─────────── POSTFLIGHT ──── POST-TEST
    │                   │                    │               │
    │   NOETIC PHASE    │   PRAXIC PHASE     │               │
    │   (investigation) │   (action)         │               │
    │                   │                    │               │
    ├─ Noetic vectors ──┤─ Praxic vectors ───┤               │
    │                   │                    │               │
    │  Noetic evidence  │  Praxic evidence   │  Grounding    │
    │  (sources, coverage│  (tests, git,     │  (post-test)  │
    │   unknowns, dead- │   artifacts,       │               │
    │   ends avoided)   │   completions)     │               │
```

### Track A: Noetic Calibration (PREFLIGHT -> CHECK)

**Delta:** CHECK vectors minus PREFLIGHT vectors = noetic gain claimed.

**Evidence sources:**

| Source | What it measures | Quality |
|--------|-----------------|---------|
| Qdrant queries issued | Coverage breadth | OBJECTIVE |
| Files/modules examined | Investigation depth | OBJECTIVE |
| Unknowns surfaced | Uncertainty honesty | SEMI-OBJECTIVE |
| Assumptions tested | Critical thinking | SEMI-OBJECTIVE |
| Dead-ends identified (before hitting them) | Pattern recognition | SEMI-OBJECTIVE |
| Sentinel decision quality | CHECK outcome vs subsequent reality | OBJECTIVE (retroactive) |
| Sources consulted (ref-docs, bootstrap) | Preparation quality | OBJECTIVE |

**Calibration question:** "Did investigation actually reduce uncertainty proportional to claim?"

**Key insight:** Absence of findings IS evidence. "Searched 14 modules, found 0 circular
deps" is a high-value epistemic outcome. The evidence is the coverage, not the bug count.

### Track B: Praxic Calibration (CHECK -> POSTFLIGHT)

**Delta:** POSTFLIGHT vectors minus CHECK vectors = praxic gain claimed.

**Evidence sources:**

| Source | What it measures | Quality |
|--------|-----------------|---------|
| pytest results | Implementation correctness | OBJECTIVE |
| Git metrics (commits, files changed) | Action volume | OBJECTIVE |
| Goal/subtask completions | Delivery | SEMI-OBJECTIVE |
| Artifact counts (findings from implementation) | Discovery during action | SEMI-OBJECTIVE |
| Issue resolution | Problem solving | SEMI-OBJECTIVE |

**Calibration question:** "Did actions produce the outcomes predicted?"

### Pure-Phase Transactions

Not all transactions have both phases:

| Transaction Type | Phases | Calibration |
|-----------------|--------|-------------|
| Investigation only | PREFLIGHT -> CHECK (investigate) -> POSTFLIGHT | Track A only |
| Implementation with prep | PREFLIGHT -> CHECK (proceed) -> POSTFLIGHT | Track A + Track B |
| Quick fix | PREFLIGHT -> CHECK (proceed) -> POSTFLIGHT | Track B dominates |
| Multiple CHECKs | PREFLIGHT -> CHECK (investigate) -> CHECK (proceed) -> POSTFLIGHT | Track A until final proceed, then Track B |

For investigate-only sessions, praxic evidence is absent by design — no penalty.

### Multiple CHECKs

Transactions can have multiple CHECK gates (investigate loops). Each `investigate`
decision stays in noetic calibration. Only the final `proceed` CHECK starts the
praxic clock.

```
PREFLIGHT -> CHECK(investigate) -> CHECK(investigate) -> CHECK(proceed) -> POSTFLIGHT
             |--- noetic --------------------------------||- praxic ----|
```

---

## Dynamic Thresholds from Calibration History

The sentinel currently uses static thresholds from `workflow-protocol.yaml`.
Phase-aware calibration enables **earned autonomy** — thresholds that adapt based
on demonstrated calibration accuracy.

### Mechanism

```python
threshold = base_threshold - (calibration_accuracy * autonomy_factor)
threshold = clamp(threshold, safety_floor, base_threshold)
```

Where:
- `base_threshold` = conservative default (from workflow-protocol.yaml)
- `calibration_accuracy` = 1.0 - mean_divergence over last N transactions (per phase)
- `autonomy_factor` = max threshold reduction allowed (e.g., 0.2)
- `safety_floor` = absolute minimum threshold (never goes below this)

### Per-Phase Autonomy

| Phase | Calibration Track | Threshold Adjusted | Effect |
|-------|------------------|-------------------|--------|
| Noetic | Track A history | CHECK gate `proceed` threshold | Well-calibrated investigator -> looser CHECK, more autonomy to explore |
| Praxic | Track B history | POSTFLIGHT sentinel thresholds | Well-calibrated implementer -> wider latitude on action |

### Domain Scoping

Calibration accuracy is domain-scoped (via `subject` on findings/calibration records).
An AI can be:
- Well-calibrated on security investigation -> loose noetic gate for security
- Poorly calibrated on performance implementation -> tight praxic gate for performance

### Progression

```
New AI on project:     Conservative defaults (tight gates)
        |               calibration data accumulates
        v
~10 transactions:      Noetic divergence closing -> loosen CHECK
        |               praxic divergence still wide
        v
~20 transactions:      Praxic divergence closing -> loosen action gates
        |               both tracks stable
        v
Mature:                Earned autonomy based on demonstrated calibration
        |
        v (regression detected)
Auto-tighten:          Calibration accuracy drops -> gates tighten automatically
```

### Self-Correcting Properties

1. **Overconfidence** -> high divergence -> tighter gates -> forced investigation -> better calibration
2. **Underconfidence** -> low divergence -> gates stay conservative -> no harm (just slower)
3. **Domain regression** -> domain-specific tightening -> other domains unaffected
4. **Phase-specific** -> poor praxic calibration doesn't penalize noetic autonomy

---

## Implementation Status

### Phase 1: Split Evidence Collection -- COMPLETE (v1.5.1, updated v1.6.4)

- `detect_phase_boundary()` finds CHECK proceed timestamp
- `PostTestCollector(phase="noetic"|"praxic")` filters evidence by `check_timestamp`
- `EvidenceMapper.map_evidence(phase=...)` returns phase-tagged `GroundedAssessment`
- `grounded_beliefs` and `grounded_verifications` tables have `phase` column
- `run_grounded_verification()` runs separate noetic + praxic passes
- **Profile-specific collectors excluded from noetic phase** (v1.6.4): Code quality (ruff,
  radon, pyright), test results (pytest), git metrics, prose metrics, and web metrics only
  run during praxic or combined phases. Noetic grounding uses only epistemic process evidence
  (artifact counts, investigation thoroughness, sentinel decisions). This prevents
  deterministic output-quality metrics from conflating noetic calibration — a principle that
  applies across all domains, not just software engineering.

### Phase 2: Noetic Evidence Sources -- COMPLETE (v1.5.1)

Noetic-specific evidence collected pre-CHECK:
- Unknowns surfaced (epistemic honesty)
- Dead-ends identified (pattern recognition)
- Investigation findings (knowledge depth)
- CHECK iterations (investigate decisions counted)
- Source consultation quality

### Phase 2.5: Phase-Weighted Holistic Score -- COMPLETE (v1.5.9+)

The Sentinel now splits tool counts into `noetic_tool_calls` and `praxic_tool_calls`
based on existing tool classification (NOETIC_TOOLS set + safe bash detection).

At POSTFLIGHT, the holistic calibration score is computed as a weighted average:

```
holistic_score = noetic_weight * noetic_calibration + praxic_weight * praxic_calibration
```

Where weights are derived from tool call distribution:
- 95% noetic tools -> noetic_weight=0.9, praxic_weight=0.1 (floor applied)
- 50/50 split -> equal weights
- noetic_only transaction -> 100% noetic weight

Floor: any phase with evidence gets minimum 0.1 weight to prevent complete zeroing.

**POSTFLIGHT output now includes:**
```json
{
  "phase_weights": {"noetic": 0.92, "praxic": 0.08, "source": "tool_classification"},
  "holistic_calibration_score": 0.15,
  "holistic_gaps": {"know": 0.12, "signal": 0.08}
}
```

### Phase 2.6: Calibration Insights Loop -- COMPLETE (v1.5.9+)

New `CalibrationInsightsAnalyzer` detects systemic patterns across verification history:

| Pattern | Detection | Suggestion |
|---------|-----------|------------|
| **chronic_overestimate** | Same vector overestimated in >70% of records | Reduce self-assessment |
| **chronic_underestimate** | Same vector underestimated in >70% of records | Increase self-assessment |
| **evidence_gap** | Vector has evidence in <30% of verifications | Add evidence source |
| **phase_mismatch** | Gap >2x larger in one phase than the other | Phase evidence imbalance |
| **volatile** | Gap direction flips in >50% of consecutive pairs | Stabilize evidence |

Insights are:
- Stored in `calibration_insights` table (with `acted_on` flag for closing the loop)
- Exported to `.breadcrumbs.yaml` for session-start injection
- Included in POSTFLIGHT output as `insights[]`

This creates a feedback loop: each calibration cycle identifies where evidence
collection is weak, which informs improvements to the collection methods themselves.

### Phase 2.8: Actionable PREFLIGHT Feedback -- COMPLETE (v1.6.4)

PREFLIGHT now includes `suggested_ranges` in `previous_transaction_feedback`. For each
vector with a significant gap (|gap| > 0.1), the system computes a suggested range
from the grounded posterior mean ± 1 standard deviation:

```json
{
  "previous_transaction_feedback": {
    "significant_gaps": {"know": 0.348, "signal": -0.129},
    "suggested_ranges": {
      "know": {"grounded_mean": 0.77, "suggest_low": 0.75, "suggest_high": 0.78},
      "signal": {"grounded_mean": 0.85, "suggest_low": 0.83, "suggest_high": 0.87}
    },
    "note": "Use suggested_ranges to calibrate your next self-assessment."
  }
}
```

Requires >= 3 grounded observations per vector before suggesting ranges (avoids
premature suggestions from sparse data). Range narrows as evidence accumulates —
this is correct Bayesian behavior, not a bug.

### Phase 3: Dynamic Thresholds -- PENDING

- Add `calibration_trajectory` per-phase tracking
- Sentinel reads phase-specific calibration history
- Threshold computation at PREFLIGHT (for CHECK gate) and CHECK (for action gate)
- Safety floors hardcoded, not adjustable by calibration

### Phase 4: Domain-Scoped Autonomy -- PENDING

- Tag calibration records with domain (from finding subjects)
- Per-domain threshold computation
- Dashboard: `empirica calibration-report --by-domain --by-phase`

---

## Evidence That This Matters

From the session that motivated this spec:

| Metric | Self-assessed | Grounded | Reality |
|--------|--------------|----------|---------|
| know | 0.90 | 0.50 | Investigation confirmed 63/63 functions, clean DAG, no circular deps |
| signal | 0.80 | 1.00 | Findings about dead references were high-value |
| uncertainty | 0.10 | 0.18 | Uncertainty WAS genuinely low after thorough verification |

The grounded system undervalued `know` by 0.4 because no tests changed and no code
was committed. But the epistemic state genuinely improved — the uncertainty about
modularization quality was fully resolved.

With phase-aware calibration, this session would be evaluated as pure noetic work
against noetic evidence (coverage, queries, uncertainty reduction). The 0.4 gap
would not exist.

---

## Design Principles

1. **CHECK is the boundary** — not an arbitrary split, it's the gate that already exists
2. **Absence is evidence** — "searched and found nothing" is noetic signal, not silence
3. **Earned not given** — autonomy increases only with demonstrated calibration accuracy
4. **Self-correcting** — regression automatically tightens gates, no manual intervention
5. **Domain-scoped** — expertise in one area doesn't grant autonomy in another
6. **Phase-specific** — noetic and praxic competence are independent axes
7. **Safety floors** — no amount of calibration accuracy removes all gates
8. **Human retains override** — dynamic thresholds adjust AI autonomy, not human authority
