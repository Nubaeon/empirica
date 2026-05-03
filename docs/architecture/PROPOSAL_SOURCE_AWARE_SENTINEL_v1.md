# Proposal: source-aware Sentinel routing rule (v1)

> v0 (PROMPT_FOR_EMPIRICA_CLAUDE_source_aware_sentinel.md) shipped the
> data primitive — `epistemic_source` field on artifacts, per-transaction
> `epistemic_provenance` ratio in `calibration_reflection`. Visibility
> only; no gate routing.
>
> v1 turns that data into a **conditional gate**: opt-in per-domain,
> work-mode-aware, with anti-gaming cross-checks. The goal is to catch
> the rubber-stamp CHECK pattern in domains that genuinely need a floor
> (security, customer-data, greenfield infra) **without** burdening
> projects where intuition-tagged work is legitimate (small follow-ons,
> docs polish, refactors of code the AI just wrote).

---

## What v0 already gives us

After the v0 substrate (commits cde0bb381, 4d4b5c5b0, d5459dfef,
a6f64b2f8), every POSTFLIGHT response now carries:

```jsonc
"calibration_reflection": {
  "epistemic_provenance": {
    "intuition_artifacts": 1,
    "search_artifacts": 2,
    "mixed_artifacts": 2,
    "untagged_artifacts": 0,
    "total_artifacts": 5,
    "ratio": "mixed"   // all_intuition | all_search | mixed | untagged | no_data
  }
}
```

The AI sees its own per-transaction ratio and is expected to self-correct
on next PREFLIGHT. The brittle assumption: AIs will read it. v1 closes
that gap with an enforced floor in the domains that need one.

---

## Three primitives

### 1. `min_search_ratio` knob in domain config

Domain configs already live at `empirica/config/domains/<name>.yaml`
and carry per-criticality thresholds (`coverage_min`, `check_pass_ratio`,
etc.). Add a parallel knob:

```yaml
# empirica/config/domains/cybersec.yaml (illustrative)
domain: cybersec
criticalities:
  high:
    description: "Public-facing services, authenticated user data"
    required_checks: [tests, lint, complexity, dep_audit]
    thresholds:
      coverage_min: 0.5
      check_pass_ratio: 1.0
      min_search_ratio: 0.5      # ← NEW. ≥50% of tagged artifacts must be search/mixed.
      min_search_artifacts: 1    # ← NEW. At least 1 search-or-mixed artifact required.
    max_iterations: 5
```

**Defaults:** Both new keys default to `None` everywhere. Most projects
feel zero change. `default.yaml` ships with both unset — the floor is
opt-in, not opt-out.

**Loader:** `DomainProfile.from_dict` (`empirica/core/sentinel/orchestrator.py:262`)
already handles the YAML→dataclass mapping. Two new optional fields on
the criticality threshold dict.

### 2. `work_mode` field on goals

Per ecodex's brief: "Per-goal honesty cannot be a generic rule. A small
follow-on with deep loaded plan context legitimately starts at high
vectors via intuition. Greenfield work in unfamiliar code does not."

The AI declares intent at goal-create. New optional field on `goals`:

```sql
-- migration 041_goal_work_mode
ALTER TABLE goals ADD COLUMN work_mode TEXT;  -- nullable, default NULL
```

Values:

| `work_mode` | Meaning | Floor enforcement |
|---|---|---|
| `polish`        | Cosmetic / docs / rename — already-internalized content      | Floor **bypassed** |
| `iteration`     | Small follow-on to recently-shipped work                     | Floor **bypassed** |
| `investigation` | Pure noetic — explicitly looking, not building              | Floor **bypassed** (search expected by definition) |
| `greenfield`    | New module, new code, no prior loaded context                | Floor **enforced** |
| `spec_impl`     | Implementing from a spec/doc/RFC                             | Floor **enforced** |
| `refactor`      | Restructuring code the AI hasn't read yet                    | Floor **enforced** |
| `NULL`          | Unspecified (back-compat, also acts as "default to enforced" for opt-in domains) | Floor **enforced** if domain has one |

**CLI:**

```bash
empirica goals-create --objective "Add OAuth flow" --work-mode greenfield
empirica goals-create --objective "Polish error message" --work-mode polish
```

**No prompt-side change required** — the AI just learns to add the flag
when relevant. If they don't, the conservative default (NULL → enforce)
catches the case the floor is designed to catch.

### 3. Sentinel tool-call cross-check (anti-gaming)

The risk: AI tags every artifact `search` to clear the floor. Counter:
the Sentinel already counts tool calls per phase via `tool_call_count`
on the active_work file (and per-phase splits via Sentinel's existing
phase-aware tracking). Use that as the anti-gaming check.

**Rule:**

```python
# Pseudocode in sentinel-gate.py CHECK gate
def evaluate_source_floor(transaction_id, goal_id, domain_threshold):
    prov = compute_epistemic_provenance(db, transaction_id)
    tagged_search = prov['search_artifacts'] + prov['mixed_artifacts']
    tagged_total  = prov['total_artifacts'] - prov['untagged_artifacts']

    # Anti-gaming: tagged search artifacts should be plausible given
    # the actual noetic tool calls observed. If the AI tagged 5
    # artifacts as search but Sentinel saw 0 reads/greps/web/MCP,
    # something is wrong.
    noetic_calls = get_phase_tool_count(transaction_id, phase='noetic')
    if tagged_search > noetic_calls + GRACE:   # GRACE=2 for cross-transaction context
        return GateResult(
            decision='investigate',
            reason=(
                f"Source-tag mismatch: {tagged_search} search-tagged "
                f"artifacts but only {noetic_calls} noetic tool calls "
                f"this transaction. Honest re-tag or do real noetic work."
            ),
        )

    # Floor check (only fires if domain opted in AND goal is enforced)
    if domain_threshold is None or not is_enforced_work_mode(goal_id):
        return GateResult(decision='proceed')

    if tagged_total == 0:
        return GateResult(decision='investigate', reason='No tagged artifacts yet.')

    ratio = tagged_search / tagged_total
    if ratio < domain_threshold['min_search_ratio']:
        return GateResult(
            decision='investigate',
            reason=(
                f"Search ratio {ratio:.0%} below floor "
                f"{domain_threshold['min_search_ratio']:.0%} for "
                f"{domain_threshold['domain']}/{domain_threshold['criticality']}. "
                f"Need ≥{domain_threshold['min_search_artifacts']} "
                f"search-or-mixed artifact(s) before proceeding."
            ),
        )
    return GateResult(decision='proceed')
```

**Where it hooks in:** `sentinel-gate.py` already has `_get_dynamic_thresholds()`
(see finding `B1 gate integration points identified` from the earlier
domain registry work). The source-floor check sits in the same auto-proceed
path, evaluated only when `domain` and `criticality` were declared in PREFLIGHT.

---

## Escape hatches

The floor must not become a wall. Three escape paths:

1. **`work_mode`** at goal-create — already covered above. The honest
   "this is polish, no search needed" override.

2. **Per-AI calibration history** — if an AI has historically shipped
   intuition-only work AND those POSTFLIGHTs had low grounded divergence,
   the per-AI calibration profile can soften the floor. (Reuses the
   existing Bayesian per-AI bias tracking that already informs Brier-
   based threshold inflation.)

3. **Explicit re-CHECK** — if the AI thinks the floor misfired, they
   can submit CHECK with `--justify` text and the gate logs a calibration
   dispute (`calibration_disputes` table from migration 032 already
   exists). Doesn't auto-bypass, but creates the audit trail for
   reviewing whether the floor needs tuning.

---

## Failure modes considered

| Mode | What goes wrong | Mitigation |
|---|---|---|
| **False positive** | AI legitimately knows from prior context, gets routed | `work_mode` declaration + per-AI calibration history |
| **Gaming via mistagging** | AI tags everything as `search` | Tool-call cross-check ratio (search artifacts ≤ noetic tool calls + grace) |
| **Floor too aggressive** | Slows legitimate small-iteration work | Opt-in per-domain only; default has no floor; enforced work modes are a closed set |
| **Floor too lax** | Caught nothing, no behavior change | Per-domain tuning over months; the dispute table records every override and feeds threshold review |
| **AI burnout / micro-management** | AI feels the gate is in the way | Floor never trips on `polish` / `iteration` / `investigation` modes — those are the everyday operating modes |
| **Cross-transaction context** | AI did the search work in T1, applies it in T2 | The GRACE constant in the cross-check + recognition that T2's "intuition" can legitimately be T1's "search" cached forward |

---

## Migration path: v0 → v1

| Step | Change | Backward compat |
|---|---|---|
| Migration 041 | `goals.work_mode TEXT NULL` | Existing goals: NULL (treated as "default") |
| `goals-create --work-mode` flag | Optional CLI arg | Existing scripts: unaffected |
| Domain config `min_search_ratio` / `min_search_artifacts` keys | Optional YAML keys | Existing domains: no enforcement |
| `default.yaml` ships **without** the floor | No surprise enforcement | Projects that haven't opted into a stricter domain see zero change |
| `cybersec.yaml`, future `customer-data.yaml`, `compliance.yaml` ship with sensible floors | Opt-in by setting `domain: cybersec` in PREFLIGHT | Domains without a floor ignore the new keys |
| Sentinel gate floor evaluator | New code path in `sentinel-gate.py` `_get_dynamic_thresholds` consumer | Activates only when `domain` + `criticality` declared AND that domain has the keys set |
| Calibration_reflection still surfaces visibility ratio | v0 behavior preserved | AIs in non-floored domains still see the data, can self-correct |

**No data migration risk** — additive only. v0 DBs upgrade cleanly. Old
artifacts stay untagged (`epistemic_source = NULL`) and contribute to
`untagged_artifacts` count but not to the floor numerator/denominator.

---

## Open questions for review

1. **Cross-transaction grace.** The GRACE constant in the anti-gaming
   check needs empirical tuning. Start at 2; revisit after a month of
   real data.

2. **Where does `work_mode` get auto-suggested?** Should `goals-create`
   without `--work-mode` print a hint like "tip: declare --work-mode for
   gate-aware routing" once per session? Risk: noise. Benefit: discovery.
   Default: silent for now; revisit if adoption is low.

3. **Should the calibration history feedback loop be explicit?** i.e.
   "this AI floor-overrode 5 times in the last 20 transactions and
   POSTFLIGHT divergence was below threshold each time → relax floor
   for them by 0.1." Mechanism is feasible but adds surface area. Defer
   to v2.

4. **Compliance domain coverage.** v1 ships floors only on `cybersec`
   in the bundled domains. Should `consulting`, `operations`,
   `marketing` get domain-specific thresholds too? Likely yes for
   `consulting` (deliverables to clients), no for the rest. Confirm
   per domain before adding keys.

5. **MCP/cockpit surface.** This proposal only addresses the CLI
   gate. MCP tool calls (e.g. `mcp__empirica__check_submit`) hit the
   same gate code path so should inherit automatically. Cockpit TUI
   may want to show the floor status as a visible badge — separate UX
   work, not blocking for v1.

---

## Out of scope for v1

- **Auto-classifying turn `epistemic_source`** from tool-use events.
  Phase 14 in the chat surface does this; the substrate hook would be
  Sentinel deriving artifact source from "did Read/Grep/Glob/WebFetch/
  MCP fire between PREFLIGHT and the artifact log." Useful but separable.
- **Cross-AI calibration normalization.** If different AIs have
  systematically different intuition/search ratios, that's interesting
  data but not a v1 problem.
- **A public dashboard of source ratios.** Telemetry surfacing — defer.

---

## Implementation sequence (post-approval)

1. Migration 041 + `goals-create --work-mode` flag + tests
2. Domain config schema extension (`min_search_ratio` /
   `min_search_artifacts` keys) + loader updates + tests
3. `_compute_floor_decision()` helper extending the existing
   `_compute_epistemic_provenance()` from v0
4. Sentinel gate integration in `_get_dynamic_thresholds` consumer
5. Anti-gaming cross-check (`get_phase_tool_count` integration)
6. CLI override / dispute path
7. Update `cybersec.yaml` with sensible floor; document in
   constitution + lean prompt
8. End-to-end tests (gate fires, gate bypasses on polish, gate
   doesn't fire when domain has no floor, dispute records override)

Estimate: 4-6 commits, ~600 LOC across DB/CLI/Sentinel/docs/tests.
Not a release-blocker — ship after v0 has accumulated 2-4 weeks of
real `epistemic_source` data so the threshold defaults are
empirically grounded.

---

*v0: David asked, ecodex wrote the brief, empirica-claude shipped the
substrate. v1: David asked the routing question, empirica-claude
scoped the design. Same pattern.*
