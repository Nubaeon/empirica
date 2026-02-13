# Phase-Aware Calibration: Noetic vs Praxic Grounding

**Status:** DESIGN SPEC
**Author:** David + Claude Code
**Date:** 2026-02-10
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

## Implementation Approach

### Phase 1: Split Evidence Collection

Modify `postflight-submit` grounded verification to:
1. Identify CHECK boundary timestamp(s) in the transaction
2. Partition evidence into pre-CHECK (noetic) and post-CHECK (praxic)
3. Compute separate divergence scores per phase
4. Store both tracks in `grounded_calibration` with phase labels

**Key change:** `calibration_score` becomes `noetic_calibration_score` + `praxic_calibration_score`.

### Phase 2: Noetic Evidence Sources

Add evidence collectors for the noetic phase:
- Query count from Qdrant (already logged in pattern_retrieval)
- File examination count from session (instrument via hooks)
- Unknowns/findings ratio (already in artifacts)
- Coverage metric: collections queried / collections available
- Dead-end avoidance: pattern-check calls during noetic phase

### Phase 3: Dynamic Thresholds

- Add `calibration_trajectory` per-phase tracking
- Sentinel reads phase-specific calibration history
- Threshold computation at PREFLIGHT (for CHECK gate) and CHECK (for action gate)
- Safety floors hardcoded, not adjustable by calibration

### Phase 4: Domain-Scoped Autonomy

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
