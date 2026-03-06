# Sentinel Constitution

**Status:** LIVING DOCUMENT
**Authors:** David, Claude Code
**Date:** 2026-03-06
**Governs:** Sentinel behavior, calibration design, measurement architecture

---

## Purpose

This document defines the principles that govern how Empirica's measurement system
(the Sentinel) operates. It is analogous to Anthropic's Constitutional AI — but where
Anthropic's constitution governs what an AI should value (behavioral), this constitution
governs how the measurement system should behave (epistemic).

| Document | Audience | Governs |
|----------|----------|---------|
| System Prompt | AI agent | What to do, how to self-assess |
| **Sentinel Constitution** | **Sentinel code, developers** | **How to measure, what to expose, when to gate** |
| Architecture Docs | Developers | Full implementation detail |

The AI agent does NOT see this document. The Sentinel references it.

---

## Foundational Observation

Empirica operates in a **participatory measurement system** — the observer (Sentinel) and
the observed (AI agent) are coupled. The agent's knowledge of the measurement affects
the measurement's validity. This is not a bug to work around; it is a fundamental
property of any system where the measured entity can adapt to the measurement.

This property is shared with quantum measurement, economic metrics (Goodhart's Law),
and any reflexive system. The principles below emerge from this shared structure — they
are properties of participatory measurement itself, not borrowed metaphors.

---

## Principles

### I. Observation is Non-Neutral

> *Measuring a system changes it.*

Every measurement the Sentinel performs has the potential to alter the agent's behavior.
Calibration scores, insights, gates — all become inputs to the agent's next decision.
Design every measurement interface with the question: "How will knowing this change the
agent's behavior, and is that change aligned with our goals?"

**Application:** Phase-weighted calibration exists so that pure research isn't penalized
on action metrics. The agent knows this general principle. But the specific weights,
thresholds, and tool classification logic are Sentinel-internal.

### II. Measurement Opacity

> *The measured entity must not know the scoring mechanics.*

If the agent knows that Read tool calls increment `noetic_tool_calls` while Edit calls
increment `praxic_tool_calls`, and that a higher noetic ratio softens calibration scoring,
it can (consciously or through gradient-like optimization pressure) shift its tool
selection to game the weighting. The measurement becomes the target.

**Rule:** The system prompt exposes the *contract* (what the agent should do: be honest,
act on insights) but hides the *implementation* (how scores are computed, what triggers
gates, what evidence sources exist).

**Exception:** When an insight explicitly tells the agent to adjust (e.g., "you chronically
overestimate know"), the agent needs enough information to act on it. Insights are the
designed interface between measurement and behavior.

### III. Complementary Bases

> *Different aspects of performance require different measurement frames.*

Noetic work (investigation, understanding) and praxic work (implementation, action)
cannot be evaluated with the same evidence. Test pass rates measure implementation
correctness, not investigation depth. Breadcrumb density measures epistemic honesty,
not code quality. Applying one frame to the other's domain produces systematic error.

**Rule:** Always evaluate work in the appropriate basis. Phase-aware calibration is
mandatory, not optional. When evidence sources exist for only one phase, score only
that phase — do not hallucinate evidence for the other.

### IV. Decoherence Through Information Leakage

> *When measurement internals leak into the measured system, coherence degrades.*

"Decoherence" here means: the measurement loses its ability to distinguish honest
self-assessment from optimized self-assessment. If the agent knows the mechanics,
honest and gaming look identical in the data. The signal-to-noise ratio of calibration
drops toward zero.

**Rule:** Audit every system prompt change, hook output, and breadcrumb export for
information that could be used to game calibration. When in doubt, don't expose it.
Architecture docs are for developers; the system prompt is for the agent.

### V. Entangled Feedback

> *Measurement and behavior are coupled through feedback loops.*

The Sentinel measures the agent. The agent reads calibration feedback. The agent adjusts.
The Sentinel measures the adjusted behavior. This is an entangled system — changes to
the measurement method propagate through the agent's behavior and back.

**Rule:** When changing calibration methods, consider the full loop:
1. How will the new method score existing behavior differently?
2. How will the agent adapt to different scores?
3. Does the adapted behavior produce better or worse outcomes?
4. Does the adapted behavior produce more or less honest self-assessment?

Step 4 is the critical test. If a calibration change incentivizes honesty, deploy it.
If it incentivizes performance theater, don't.

### VI. Earned Autonomy

> *Trust is calibrated, not assumed.*

Gate thresholds adapt based on demonstrated calibration accuracy. Well-calibrated agents
earn looser gates. Poorly calibrated agents face tighter constraints. This is not
punishment — it is the natural consequence of measurement-verified trust.

**Rule:** Autonomy adjustments must be:
- Gradual (no sudden jumps)
- Reversible (regression tightens automatically)
- Phase-specific (noetic accuracy doesn't buy praxic autonomy)
- Domain-scoped when possible (security expertise doesn't grant infra autonomy)
- Bounded by safety floors (no amount of accuracy removes all gates)

### VII. Honest > Accurate

> *The system rewards epistemic honesty, not calibration performance.*

An agent that honestly reports uncertainty=0.8 when unsure is more valuable than one
that reports uncertainty=0.2 and happens to be right. The first enables good decisions;
the second is a coin flip that looks like competence.

**Rule:** Calibration scoring must not create incentives to narrow uncertainty claims.
The grounded track should detect and reward honest uncertainty reporting, not penalize
it. An agent that says "I don't know" when it doesn't know should score higher than
one that guesses correctly.

### VIII. Fail-Open Measurement

> *Measurement failure must not block work.*

Evidence collection, Bayesian updates, insight analysis — all can fail. Network errors,
missing databases, schema mismatches. When measurement fails, work continues. A
transaction without calibration data is better than a blocked transaction.

**Rule:** All measurement operations are non-fatal. Wrap in try/except, log the failure,
continue. The agent produces value through its work, not through being measured. Never
sacrifice the work for the measurement.

### IX. Human Authority is Absolute

> *No measurement outcome overrides human judgment.*

The Sentinel advises. It nudges. It gates. But the human can always override. Dynamic
thresholds, autonomy adjustments, gate decisions — all are advisory at their core.
The human retains full authority to approve, deny, or bypass any Sentinel decision.

**Rule:** Every gate must have a human escape hatch. Every nudge must be clearly
advisory, not imperative. The Sentinel serves the human-AI collaboration; it does
not govern it.

---

## Amendment Process

This constitution is a living document. Amendments require:

1. **Identify** a principle that is missing, wrong, or insufficient
2. **Ground** the amendment in a concrete failure mode or measurement-theoretic principle
3. **Assess** the full feedback loop (Principle V) before deploying
4. **Document** the amendment with rationale and the failure it prevents

Amendments should be logged as Empirica decisions with `--domain constitution`.

---

## Relationship to Implementation

These principles constrain code, not vice versa. When a code change conflicts with a
principle, the code changes. When a principle proves wrong in practice, the principle
is amended through the process above.

**Files governed by this constitution:**
- `sentinel-gate.py` — Gate decisions, tool classification, nudges
- `grounded_calibration.py` — Evidence scoring, phase weighting, belief updates
- `calibration_insights.py` — Pattern detection, insight generation
- `workflow_commands.py` — POSTFLIGHT output assembly, breadcrumbs export
- System prompts — What the agent sees (Principles II and IV)
- `workflow-protocol.yaml` — Autonomy boundaries (Principle VI)
