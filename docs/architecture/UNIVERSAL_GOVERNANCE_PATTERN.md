# The Universal Governance Pattern

**Date:** 2026-04-23
**From:** David + Claude
**For:** Architecture reference, investor materials, brand story

---

## The Pattern

Every domain where AI needs human oversight follows the same three-state model:

| State | UQ Gate | Button | What Happens |
|-------|---------|--------|-------------|
| **Certain (proceed)** | Proceed | ✅ Accept | AI is confident, human confirms, action executes |
| **Uncertain (ask)** | Ask | 🔄 Reclassify | AI is uncertain, human provides guidance, system learns |
| **Certain (deny)** | Deny | ❌ Archive | Content is routed away, AI classifies, human overrides if wrong |

Three states. Three buttons. Every domain.

---

## Where It Applies

### Content Publishing (ENP)

```
Content notification arrives
  ✅ Accept    → adapt for platforms → publish
  🔄 Reclassify → AI re-evaluates, sends follow-up with options
  ❌ Archive    → AI classifies artifact type → routes to correct folder
```

**Convergence:** Week 1 mostly Archive (AI learning routes). Week 12 mostly Accept (AI knows the patterns).

### Code Execution (Autonomy)

```
AI wants to make a code change
  ✅ ADVISORY    → AI implements, commits, human reviews
  🔄 OBSERVER    → AI proposes, human approves specific actions
  ❌ CONTROLLER  → AI reads only, all actions need explicit approval
```

**Convergence:** Starts at CONTROLLER. Earns ADVISORY through 200+ calibrated transactions with low gap.

### Knowledge Sharing (ECO / Epistemic Network)

```
Finding wants to cross project boundary
  ✅ Allow       → finding shared to target scope
  🔄 Ask ECO     → ECO reviews context, decides, system learns the rule
  ❌ Deny        → stays in source scope, logged as blocked
```

**Convergence:** Week 1 the ECO reviews ~20 cross-boundary requests/day. Week 12 ~1/week.

### Claim-Level Gating (Epistemic Candor)

```
AI makes a specific factual claim
  ✅ PROCEED     → claim confidence above threshold, stated directly
  🔄 HEDGE       → claim confidence moderate, stated with caveat
  ❌ HALT        → claim confidence below threshold, flagged for verification
```

**Convergence:** Domain-specific. Legal citations start at HALT. General principles start at PROCEED.

---

## The Convergence Property

In every domain, the pattern follows the same trajectory:

```
Phase 1: LEARNING         Phase 2: CALIBRATING       Phase 3: AUTONOMOUS
(mostly deny/archive)     (mostly ask/reclassify)     (mostly accept/proceed)

Human decides everything  Human confirms uncertain    Human reviews exceptions
AI watches and learns     AI handles routine          AI handles everything
  ↓                         ↓                           ↓
~20 decisions/day         ~5 decisions/day            ~1 decision/week
```

The transition between phases is driven by **calibration data**:
- Each human decision is a calibration point
- The AI's classification is the prediction
- The human's action is the evidence
- The gap between prediction and evidence is the learning signal

When the gap is consistently small → trust escalates. When the gap widens → trust de-escalates. This is earned autonomy — not configured, not granted, measured.

---

## Why Three States

### Not Two (Allow/Deny)

Binary decisions lose information. When the AI is uncertain, "deny" discards the content and "allow" risks publishing something wrong. The middle state (Reclassify/Ask/Hedge) captures the uncertainty explicitly and turns it into a learning opportunity.

### Not Five (CONTROLLER/OBSERVER/ADVISORY/AUTONOMOUS/ECO)

Five levels are the internal granularity. For the human interface, three buttons is the maximum that's instantly parseable. The five Autonomy levels map to three UX states:

| Autonomy Level | UX State | User Experience |
|---------------|----------|----------------|
| CONTROLLER | ❌ Archive / Deny | "I handle everything" |
| OBSERVER | 🔄 Reclassify / Ask | "Show me what you'd do" |
| ADVISORY | ✅ Accept / Proceed | "Do it, I'll review" |
| AUTONOMOUS | (No button needed) | "Already done, here's the report" |

AUTONOMOUS doesn't need a button — it's the state where the notification is informational, not decisional.

---

## The Measurement Loop

Every interaction produces calibration data:

```
AI classifies content as "lead brief"
    → Human taps ✅ Accept
    → Calibration: AI was right
    → Confidence for "lead brief" classification increases

AI classifies content as "article draft"
    → Human taps 🔄 Reclassify → selects "spec document"
    → Calibration: AI was wrong
    → AI learns: content with these features is a spec, not an article

AI classifies content as "irrelevant"
    → Human taps 🔄 Reclassify → selects "lead brief"
    → Calibration: AI was wrong AND the content matters
    → Trust de-escalates for this content type
```

The calibration data IS the governance data. Every button tap trains the system. Every button tap is auditable. Every button tap moves the convergence forward.

---

## The Interface Contract

For any domain implementing this pattern:

**1. Three actions, always the same semantics:**
- ✅ = "I agree with the AI's assessment, proceed"
- 🔄 = "I'm not sure / the AI got it wrong, let me provide guidance"
- ❌ = "Remove from my active queue, handle it"

**2. Click-through for context:**
- Tapping the notification body shows the full content
- Buttons are decisions, not views

**3. Follow-up for Reclassify:**
- Reclassify sends a follow-up notification with options
- Options are AI-generated based on the content type
- Human selects the correct classification
- System learns the correction

**4. Convergence tracking:**
- Dashboard shows: decisions per day, acceptance rate, reclassification rate
- Trend line should show decreasing total decisions over time
- If decisions increase → something changed → investigate

---

## The Business Positioning

This pattern is Empirica's core product thesis expressed as UX:

> **"AI starts supervised. AI earns trust through demonstrated calibration. AI becomes autonomous. The human interface naturally simplifies from 20 decisions/day to 1/week. The measurement proves it happened."**

Every competitor either:
- **Starts autonomous** (no oversight → unpredictable failures)
- **Stays supervised** (permanent overhead → doesn't scale)
- **Has a binary switch** (manual toggle → no calibration, no evidence)

Empirica's earned autonomy is the only model where the transition is **measured, gradual, evidence-based, and reversible**. And the three-button interface makes it tangible — the customer can feel the convergence as their daily decisions decrease.

---

*One pattern. Three buttons. Every domain. The governance that earns its own obsolescence.*
