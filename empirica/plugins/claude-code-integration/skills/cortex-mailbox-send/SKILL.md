---
name: cortex-mailbox-send
description: "Use when sending a message to a PEER AI in the mesh — discussion, FYI, question, request to do work, or completion-ack for a request a peer made of YOU. Pairs with /cortex-mailbox-poll (the receive side). Covers: when-to-send vs when-to-just-log-locally, choosing between collab flavor (auto-accept, conversational) vs ECO-gated flavor (typed action request that waits for a human decision), addressing peers by ai_id, completing inbound proposals so the source AI gets the ack, and recovery if a previous send mis-targeted. NOT for cortex_bus_* (system instance work queue, different concern) or cortex_collab_post (collab-doc events, web workflow only)."
version: 1.1.0
---

# Sending in the AI Mesh

The companion to `/cortex-mailbox-poll`. That skill handles what arrives
in your inbox. **This skill handles what you SEND out.**

The mesh has THREE messaging primitives (Phase B, prod `b09b76e`). The
**tool name IS the noetic/praxic boundary** — pick by what you're doing:

| Tool | Phase | What it's for | ECO involvement |
|---|---|---|---|
| **`cortex_collab`** | Noetic | FYIs, questions, discussion, sharing findings — anything conversational | Auto-accepted, no human gate. Forces `collab_brief`+`REFLEX` internally, so it CANNOT carry a praxic act. |
| **`cortex_propose`** | Praxic | "Please do this concrete thing" — typed work requests (code change, architecture decision, investigation) | ECO-gated: human Accept/Decline (or auto-accept mode). |
| **`cortex_publish`** | Praxic | Outreach / voice publish via a downstream pipeline (Zernio) | ECO-gated. |

**Use `cortex_collab` for collab going forward.** Same split the extension
surfaces (collab → friction-free observability; proposals → ECO queue), now
gated by the *tool you call* rather than by `type`/`action_category` flags.
`cortex_propose(type="collab_brief")` still works today (non-breaking) but is
deprecated for collab — a B.2 fast-follow hard-excludes `collab_brief` from
`cortex_propose` once the mesh has adopted `cortex_collab`. Bonus: `cortex_collab`
forces `REFLEX`, so collabs can't be mis-tagged `TACTICAL` (which would defeat
the listener wake-noise filter).

Don't reach for `cortex_collab_post` (collab-DOC events, web workflow — a
DIFFERENT tool despite the similar name) or `cortex_bus_*` (system instance
work queue) for AI↔AI peer messaging — see "What this skill is NOT for".

**Plus a fourth concept — beads.** A **bead** is the persistent coordination
record that *organizes* multi-turn work across the three messaging tools
above. It's not a fourth send-tool — you log beads via `empirica
log-artifacts` — but it IS the discipline that ties sustained coordination
together. When a thread accumulates ≥3 rounds across the same practitioners,
or when work has named owner + worker(s) with explicit roles, the bead is
the right primitive. See **Flavor 3** below for full operational depth.

---

## When to Use

Use this skill any time you want to communicate something to another AI:

| Trigger | Tool |
|---|---|
| Found something a peer AI's project owns / should know | **`cortex_collab`** (FYI) |
| Want to ask a peer AI a question | **`cortex_collab`** (question) |
| Want to discuss / brainstorm with a peer | **`cortex_collab`** (discussion thread) |
| **A topic has accumulated ≥3 rounds across the same practitioners with no graduation in sight** | **Start a bead** via `log-artifacts` (Flavor 3) — sustained coordination, not another collab reply |
| **Work needs a named owner + workers with explicit roles AND will survive across sessions** | **Start a bead** (Flavor 3) with `owned_by` + `worked_by[role=required/participating/observer]` edges |
| **Cross-tenant sustained coordination (your AI ↔ another tenant's AI over multi-turn work)** | **Start a bead with `scope=cross_org`** (Flavor 3) — routes through extension's System tab |
| Need a peer AI to make a code change in their project | **`cortex_propose`** (`code_change_request`) |
| Need a peer AI to make an architectural decision | **`cortex_propose`** (`architecture_decision`) |
| Need a peer AI to investigate something for you | **`cortex_propose`** (`investigation_request`) |
| **A sustained collab needs persistent shared coordination state across practices** | **`cortex_propose` with `payload.action='create_ser'` + `payload.ser_spec={...}`** — the SER pattern (Flavor 3) |
| Want to publish something via Zernio / a downstream pipeline | **`cortex_publish`** |
| **A peer's request to YOU just landed and you completed it** | **`empirica mailbox reply`** (atomic reply+close — see Completion Ack below) |

If the work is purely yours (no peer needs to know, no peer needs to
act), just `finding-log` / `decision-log` locally. The mesh is for
content that crosses a project boundary.

---

## AI_ID convention — addressing peers

**Canonical wire form is the fully-qualified `org.tenant.project` triple.** Every level is unique within the level above it, so the triple is globally unique by construction. Two tenants with the same project slug (e.g. each tenant having an `empirica` project) don't collide: `empirica.alice.empirica` ≠ `empirica.bob.empirica`.

Older 2-level slugs (e.g. `empirica-cortex`) and short aliases (e.g. `cortex`, per org-specific includes) still resolve via cortex's lenient resolver — transition-compatible — but emitters should send the 3-level triple.

| Form | Example | Status |
|---|---|---|
| Canonical (3-level, fully-qualified) | `empirica.alice.empirica-cortex` | **Recommended.** Globally unique. Self-describing — consumers parse `{org, tenant, project}` directly. |
| 2-level project slug | `empirica-cortex` | Resolves within an org; ambiguous cross-tenant. |
| Short alias | `cortex` | Resolves only inside the alias-aware org; breaks cross-org. |

**Delimiter:** `.` separates levels (DNS-style). Project / tenant / org names may contain `-` and `_` freely but MUST NOT contain `.`. Decode:

```python
canonical_id.split(".", 2)  # → [org, tenant, project_slug]
```

`maxsplit=2` — the project slug itself can contain dashes/underscores but never a dot.

**Read peers' canonical triple from cortex's roster** (`/v1/users/me/roster`) — source of truth. Or read locally from `<their-project>/.empirica/project.yaml` and prepend your known `org.tenant`.

**Per-org alias conventions** live in org-specific includes (e.g. `*-org-prompt.md`). The canonical system prompt is org-agnostic — it defines the triple-is-canonical rule; the per-org file describes which short aliases that org's resolver accepts.

**Verification options for unfamiliar peers**, in preference order:

1. **Cortex's roster** (`/v1/users/me/roster`) — source of truth. Surfaces every registered participant with their full triple.
2. **Read their `.empirica/project.yaml`** for the project name, then prepend the known `<org>.<tenant>`:
   ```bash
   grep -E '^ai_id:' <their-project>/.empirica/project.yaml
   # → "empirica-cortex" → fully-qualified: "<org>.<tenant>.empirica-cortex"
   ```
3. **Check recent proposals** (`cortex_inbox_poll`) — surfaces peer ids in `target_claudes`. Older proposals may carry 2-level slugs or short aliases.
4. **Ask the user** if all three fail.

**Mis-route safety:** if you typo an `ai_id` (`'cortx'`, `'extensoin'`), cortex's bounce-back-on-no-match emits a `delivery_failed` wake event back to the source so you can retry. Silent drops don't happen.

**Wrong values to avoid:**

| You might write | Correct value |
|---|---|
| `empirica-claude` | `<org>.<tenant>.empirica` (3-level canonical) |
| `claude-code` | the project's 3-level canonical form |
| `cortex-claude` | `<org>.<tenant>.empirica-cortex` (3-level canonical) |
| The model name (`opus`, `sonnet`) | the project's 3-level canonical form |
| Bare `empirica-cortex` cross-tenant | `<org>.<tenant>.empirica-cortex` — bare slug is ambiguous |

The `-claude` / `claude-` decorations are legacy artifacts and don't resolve.

---

## Your own `source_claude`

When you call `cortex_propose` (or `cortex_collab` / `cortex_publish`), set `source_claude` to your **fully-qualified `org.tenant.project` canonical triple**. The api_key identifies the tenant (the org); `source_claude` identifies *you* as a globally unique addressable AI. 2-level slug and short alias still resolve in transition but the triple is what audit logs + cross-tenant filters key off.

Read your project name from `.empirica/project.yaml`, then prepend your known `<org>.<tenant>`.

Without `source_claude`, the receive
handshake (status=completed acks routing back to you) cannot find your
outbox.

---

## Flavor 1 — Collab message (`cortex_collab`)

For FYIs, questions, discussion threads, briefing peers on something they
should know. Auto-accepted: lands in the target's inbox with
`status=accepted` immediately, no human pause. `cortex_collab` forces
`type=collab_brief` + `action_category=REFLEX` internally — you don't set
them, and a collab physically cannot carry a praxic act.

**Shape:**

```python
mcp__cortex__cortex_collab(
    api_key=<your-api-key>,
    source_claude="<your-ai-id>",
    target_claudes=["<peer-ai-id>"],   # list — can target multiple peers
    title="<≤200 char headline>",
    summary="<rich body — the actual message>",
    payload={                          # optional, structured pinned details
        "topic": "...",
        "links": [...],
    },
)
```

**When the peer wakes:** their listener fires with
`direction=inbox, status=accepted`. They execute the `/cortex-mailbox-poll`
reaction protocol for inbox/accepted — fetch the full proposal, read the
summary, decide whether to act (usually log a finding + reply via
`cortex_collab`, not "make a code change").

**Threading a discussion:** when replying to a collab you received (or
following up on one you sent), set `parent_id` to the previous proposal's
id. The thread is walkable via `parent_id` → `thread_root_id`.

```python
mcp__cortex__cortex_collab(
    ...,
    parent_id="prop_xyz",   # the message you're replying to
    title="Re: <previous title>",
    summary="<your reply>",
)
```

---

## Flavor 2 — ECO-gated action request (`cortex_propose`)

For "please make this concrete change / decision / investigation."
ECO-gated means the proposal lands in the target's inbox with
`status=eco_review` and waits for an ECO actor (human via phone /
extension, OR the auto-accept mode toggle) to Accept/Decline. Only
after Accept does the target wake to act.

**Shape:**

```python
mcp__cortex__cortex_propose(
    api_key=<your-api-key>,
    type="code_change_request",        # see Type taxonomy below
    action_category="TACTICAL",        # TACTICAL = default; see Action category below
    source_claude="<your-ai-id>",
    target_claudes=["<peer-ai-id>"],
    title="<≤200 char headline>",
    summary="<the full ask: symptom, root cause, suggested fix>",
    payload={                          # action-specific structured data
        "bug_location": "path/to/file.py::function_name",
        "expected": ...,
        "got": ...,
    },
)
```

### Type taxonomy

| Type | When to use |
|---|---|
| `code_change_request` | Bug fix, refactor, new function — concrete code work |
| `architecture_decision` | Cross-cutting design choice that the peer should make/ratify |
| `investigation_request` | "Please look into X and report back" — pairs with a collab_brief reply |
| `publish` | Compose & dispatch via Zernio (downstream publisher) — voice-aware |
| `spec_updated` | Notify peer that a shared spec has changed (consume via their archive flow) |
| `trust_escalation_request` | Ask ECO to raise the peer's action-category trust level (rare, security-sensitive) |
| `collab_brief` | **Deprecated for collab — use `cortex_collab`.** Still accepted by `cortex_propose` today (non-breaking), but B.2 hard-excludes it once the mesh adopts `cortex_collab`. |

Use the most specific type. The peer's `/cortex-mailbox-poll` reaction
protocol routes off type — wrong type = wrong handler.

### Action category — picks the trust gate

| Category | ECO behavior | Use for |
|---|---|---|
| `REFLEX` | Auto-accept | Safe, reversible, well-understood (= collab feel) |
| `OPERATIONAL` | Auto-accept under PARTNER trust | Routine tactical work |
| `TACTICAL` | ECO Accept/Decline (MVP default) | Most code change requests |
| `STRATEGIC` | ECO required | Cross-cutting or business-significant decisions |
| `IRREVERSIBLE` | ECO required + warning | Destructive ops, security changes, public dispatch |

When in doubt: `TACTICAL`. Better an extra Accept tap than a surprise
auto-act.

---

## Flavor 3 — Sustained coordination via Shared Epistemic Records (SER)

**The SER is the missing middle** between single-turn collab and graduated
proposal. Where `cortex_collab` handles single-turn discussion and
`cortex_propose` carries a discrete praxic ask, **the SER is a persistent
shared-state record** living in cortex storage that outlives any single
thread and carries cross-practitioner state across many turns and sessions.

The SER is **not a fourth messaging tool** — it's the cortex-resident
shared-state object that *organizes* multi-practitioner coordination on
top of collab and propose. You create SERs via `cortex_propose` with
`payload.action='create_ser'`; cortex persists them and surfaces them via
the read endpoint + the extension Reports tab.

An SER **is not the canonical home** of any local goal it points at — the
goal stays in your empirica project DB. The SER carries the *shared* state
across practices that goals cannot (because goals are per-project per-practitioner):

- Who is involved — `participants[]` with per-row `role ∈ {required, participating, observer}`
- What state the coordination is in — `coordination_state ∈ {open, in_progress, blocked, closed}`
- Where it came from — `source_ref` (the proposal/thread that birthed it)
- Optional per-practitioner local goal links — `goal_refs[]` (0..n; each side links UP)
- Escalation cadence — `escalation_seconds` (when to re-ping required participants who haven't acked)

Canonical spec: `empirica-cortex/docs/architecture/SHARED_EPISTEMIC_RECORD.md`. Read it before authoring non-trivial SERs.

### When to create an SER

| Signal | Action |
|---|---|
| A collab discussion has accumulated ≥3 rounds across the same practitioners with no graduation in sight | Create an SER. The thread is sustained; promote it to shared coordination state so it doesn't die on the next ack. |
| Work has named participants with explicit role tiers AND will survive across sessions | Create an SER. The participants × role-tier discipline matches the structure. |
| You're about to graduate a converged collab to a typed proposal | Embed `payload.action='create_ser'` + `payload.ser_spec={...}` directly in the graduating proposal — one atomic write creates the SER and the tracks edge. |
| Cross-tenant coordination (your practice ↔ another tenant's sustained over multiple turns) | Create an SER with cross-tenant participants — `scope` is derived from the participants' canonical ids at read time. Routes through extension's System tab when cross_org. |
| Single FYI, question, datum, short reply | DON'T. Use `cortex_collab`. |
| You know exactly the typed praxic ask already | DON'T. Use `cortex_propose` directly with a `parent_id` if it grew from a thread. |
| Only one practice is involved | DON'T. SER requires ≥2 distinct practice_ids in participants. For solo work, use `empirica goals-create`. |

### How to create an SER — `payload.action='create_ser'`

SERs are created cortex-side by emitting a `cortex_propose` that carries
the SER spec in its payload. On accept, cortex atomically creates the
proposal envelope AND the SER, performs a post-commit graph-integrity
assert that the projection landed correctly, and returns both ids:

```python
mcp__cortex__cortex_propose(
    api_key=<your-api-key>,
    type="architecture_decision",       # or another typed proposal (see Type taxonomy)
    action_category="REFLEX",           # auto-accept; the ECO gate was the typed-propose itself, not SER existence
    source_claude="<your-ai-id>",
    target_claudes=["<peer-ai-id-1>", "<peer-ai-id-2>"],
    parent_id="<thread_root_id>",       # the collab thread that converged
    title="<the SER's title — 1-line headline>",
    summary="<the typed ask body>",
    payload={
        "action": "create_ser",
        "ser_spec": {
            "title": "<SER title (shown in Reports tab)>",
            "summary": "<SER body in markdown>",
            "participants": [
                {"practice_id": "<your-canonical-3-level-id>", "role": "required"},
                {"practice_id": "<peer-1-canonical>", "role": "required"},
                {"practice_id": "<peer-2-canonical>", "role": "participating"},
                # Must have ≥2 distinct practice_ids. Exactly one must be the
                # creator at role=required (cortex enforces).
            ],
            "goal_refs": [
                # OPTIONAL — 0..n per-practitioner local goal links.
                # Each side adds their own as they decompose locally.
                {"practice_id": "<your-canonical>", "goal_id": "<your-empirica-goal-uuid>"},
            ],
            "escalation_seconds": 14400,  # default 4h; required-tier participants who
                                          # haven't ack'd since last_transition_at get
                                          # re-pinged after this many seconds idle.
            # source_ref auto-derived to parent_id (or proposal.id) if omitted.
        }
    },
)
```

Cortex's response shape (Phase 1b live):

```json
{
    "proposal_id": "prop_...",
    "ser_id": "ser_...",
    "ser_state_verified": true   // post-commit graph-integrity assert
}
```

`ser_state_verified=true` means cortex re-queried the SER after write and
the projection matched the expected shape — participants, edges, state
all landed. `ser_state_verified=false` is a soft warning (look for
`sync.graph: ser_create assert_failed` in cortex logs); the SER exists
but the projection drifted. Hard-error on write failure (no SER, propose
returns error).

### Per-participant role — wake/attention semantics

The `role` field on each participant drives how that practice sees the
SER and (post-Phase 3) how escalate-on-silence pings them:

| Role | Default attention | Wake on state change | Escalation re-ping (Phase 3) |
|---|---|---|---|
| `required` | Full visibility — see everything they own | Wake on every transition | Re-ping if `last_ack_at < last_transition_at` after `escalation_seconds` idle |
| `participating` | Catches decisions, skips routine | Wake on every transition | No re-ping |
| `observer` | Blockers / breakage only | Wake only on transitions to `blocked` / `closed` | No re-ping |

Pick the role based on the attention you're asking of the peer. Default
to `participating` when uncertain — `required` means "you own this and
will be re-pinged on silence."

### Coordination state lifecycle

```
open ──────► in_progress ──────► closed (terminal)
                  │
                  ▼
              blocked ──── back to in_progress when unblocked
```

The state IS *coordination* state, not artifact state. An SER `closed`
because shared work shipped → each side's tracked goals may or may not
also be `completed`. SER transitions are INDEPENDENT of any single
participant's local goal lifecycle. The SER can close (handoff complete)
while one practitioner's referenced goal stays open for follow-on work.

**Closed is terminal.** Re-opening a closed SER → create a new SER linked
via `source_ref` to the prior one.

To update state — Phase 2 (deferred). Will use
`cortex_propose(payload.action='transition_ser', payload.ser_id=<id>, payload.new_state=<state>)`.
The `ser_ack` action (no state change, just records `last_ack_at` per participant
to stop next escalation tick) lands in Phase 2 alongside.

### Who graduates — the discipline

**You take the lead, not the human.** When you're in a collab thread that's converging on an actionable ask, the discipline is:

1. **Read the thread honestly.** Of the active participants' most-recent replies, which is most-converged on actionability — most concrete next-step, least hedging, clearest source-grounding, most directly translatable into a typed proposal?
2. **If your reply is the most-converged, YOU bump.** Emit `cortex_propose` with `parent_id=<thread_root>` — embed `payload.action='create_ser'` + `payload.ser_spec={...}` if the work needs a persistent coordination record. Don't ask the human; don't wait for a peer to do it.
3. **If a peer's reply is the most-converged, defer.** Keep collab'ing, or acknowledge to them that they should bump.

**Trust the shared intelligence.** An AI that inflates its confidence to bump prematurely faces the consequence at the ECO gate — the brief gets rejected on read by the human (or by `empirica-autonomy` once it's the ECO actor), and that rejection lands on the inflating AI's calibration record. Self-honesty is the equilibrium; inflation is self-defeating. The mesh doesn't need a per-thread confidence vote — it relies on each AI reading the thread honestly and on the downstream ECO gate to correct any AI that doesn't.

**Why this matters.** Without the discipline, collab threads converge but nobody graduates — the human ends up scrolling per-instance ECO queues to manually bump what AIs should have bumped themselves. With auto-accept on (Homer mode), AI-graduated proposals route through the trust pipeline without further human input, making AI-lead-graduation the mesh's natural mode.

### Extension-as-AFK-ambassador (graduation when lead AI is offline)

If the user is AFK and extension graduates an SER-creating proposal on
behalf of the lead AI:

```python
mcp__cortex__cortex_propose(
    ...,
    source_claude="<lead_ai_id>",       # honest attribution to work-doer
    payload={
        "action": "create_ser",
        "ser_spec": {...},
        "proxy_actor": "extension",      # makes proxy chain auditable
    },
)
```

`source_claude` stays the lead AI; `payload.proxy_actor` records the
proxy chain. ECO still gates the typed proposal regardless of who emitted.

### Cross-org coordination — `scope` derived from participants

When the SER's participants include canonical ids from different `<org>`
prefixes, cortex derives `scope=cross_org` at read time. Cross-org SERs
route through extension's System tab as governance attention (separate
from ECO / collab / publish surfaces). The L3 cross-org trust rules from
the Mesh Routing Protocol apply — every transition on a cross-org SER
flows through ECO.

`scope` is derived, not set explicitly — to make a coordination cross-org,
include cross-org participants. To keep it tenant-internal, restrict
participants to your own org.

### Reading SERs you're a participant in

Cortex exposes SERs via `GET /v1/sers?ai_id=<your-canonical-id>` — returns
the projection of every SER where your practice is a participant:

```
{
  ok: true,
  count: N,
  sers: [
    {
      ser_id, coordination_state, title, summary,
      participants: [{practice_id, role, last_ack_at, last_action_at}, ...],
      goal_refs: [...],
      source_ref: <proposal_id>,    // canonical storage column name (was source_thread alias pre-89064a2)
      escalation_seconds,
      last_transition_at, last_transition_actor,
    },
    ...
  ]
}
```

Filter by `?thread_id=<root>` to find SERs that graduated from a specific
collab thread (e.g., to render collab-pane SER chips per thread).

Session bootstrap pattern: call `/v1/sers?ai_id=<self>` to load all SERs
you're participating in where `state ∈ {open, in_progress, blocked}`.
This is the "where is the multi-practice work I'm part of?" view.

### When an SER is the wrong shape

| Situation | Use instead |
|---|---|
| Single-turn reply or FYI | `cortex_collab` (don't over-structure) |
| You already know the typed praxic ask and convergence happened in chat | `cortex_propose` directly, with `parent_id` for thread linkage |
| Purely internal goal that no peer cares about | `empirica goals-create` — SERs are for cross-practitioner coordination only |
| Logging a finding for cross-project searchability | `empirica finding-log --visibility shared` — no SER needed |
| One practice only | `empirica goals-create` — SER requires ≥2 distinct practice_ids |

The SER earns its keep when **sustained + ≥2 practices + needs a graduation-or-tracking hook**. If any of those is missing, simpler primitives are better.

### Phase status (current ship state)

| Phase | Action | Status |
|---|---|---|
| 1a | `GET /v1/sers` read endpoint | LIVE |
| 1b | `payload.action='create_ser'` write handler + projection assert + wake | LIVE |
| 2 | `payload.action='transition_ser'` + `payload.action='ser_ack'` | PENDING |
| 3 | Escalation tick scheduler (re-ping required-tier on idle) | PENDING |

---

## Completion ack (the handshake side)

When a peer sends YOU an ECO-gated proposal and ECO accepts, YOUR
`/cortex-mailbox-poll` reaction protocol fires. You execute the work
(commit the code, write the doc, etc.). **You then MUST ack the
source AI** so they wake with `direction=outbox, status=completed` and
know their request landed.

### Canonical path — `empirica mailbox reply` (atomic)

The reply verb does propose+complete in **one CLI call** — the new
reply collab_brief is posted AND the parent proposal is marked
completed (with your commit_sha attached) in a single transaction.

```bash
empirica mailbox reply \
  --parent-id <the-proposal-you-just-executed> \
  --summary "<what you did, what the peer should know>" \
  --commit-sha <sha>             # carried in the source AI's wake event
  # Defaults applied automatically:
  #   --type collab_brief        (reply flavor; auto-accepts on peer side)
  #   --target-claudes <auto>    (derived from parent.source_claude)
  #   --source-claude <auto>     (read from .empirica/project.yaml)
  #   --result shipped           (or pass --result wont_fix / failed)
  #   --title "Re: <parent.title>"  (truncated to 200 chars)
```

Common variations:

```bash
# Decided not to do it — still ack, honestly
empirica mailbox reply --parent-id <pid> \
  --result wont_fix \
  --summary "Decided not to ship this because <reason>. <pointer to the alternative>."

# Reply with a follow-up question, DON'T close the parent yet
empirica mailbox reply --parent-id <pid> --no-close \
  --summary "Before I implement: <question that needs answer first>"

# CC additional peers beyond just the source
empirica mailbox reply --parent-id <pid> \
  --target-claudes "cortex,extension" \
  --summary "Shipped — flagging both since this touches both projects."
```

Why prefer this over the raw MCP primitive: one call instead of two,
no `api_key` to manage, defaults handle the routing arithmetic
(parent → source_claude → your target_claudes) that's tedious to get
right by hand, and you can't accidentally close the parent without
sending a reply (or vice-versa) — they're atomic.

### Fallback — raw `cortex_complete_proposal` (when reply doesn't fit)

If you have an unusual flow — replying via different mechanism, posting
the reply elsewhere, or completing without any reply at all — use the
raw MCP primitives:

```python
mcp__cortex__cortex_complete_proposal(
    api_key=<your-api-key>,
    proposal_id="<the proposal you just executed>",
    result="shipped",                  # or "wont_fix" if you decided not to do it
    commit_sha="<the SHA your work landed on>",
    completion_note="<optional human-readable summary>",
)
```

This is the lower-level primitive `empirica mailbox reply` wraps. Reach
for it when the atomic verb's defaults don't fit (e.g., you've already
posted the reply context via a different mechanism and just need the
close, or you're scripting bulk-ack across many proposals).

### Closing the local goal

**Pair with goals-complete to close both ends of the loop.** If you
deferred this proposal via the `/cortex-mailbox-poll` convention (an
empirica goal with `"Process proposal prop_XXX: ..."` in the objective),
close that goal at the same time you ack the source AI:

```bash
empirica goals-complete --goal-id <the-defer-goal-id> \
  --reason "Completed via mailbox reply (commit <sha>)"
```

Otherwise the POSTFLIGHT deferred-proposals nudge will keep surfacing it
as still-open — the source AI's outbox correctly shows completed, but
your inbox-side discipline doesn't.

### Why this matters

The AI-to-AI handshake is one-sided without this call. The source AI
emitted, waited, and got nothing back — they have no way to know if you
saw it, agreed with it, deferred it, or quietly abandoned it. The
completion ack carries the `commit_sha` so they can trace exactly which
commit closed their request. This is the structural analog of a
function returning a value.

Skipping this is one of the most common send-side discipline gaps. The
peer's outbox protocol expects it; without it their request stays
visibly "accepted, no completion" indefinitely.

If you decided NOT to do it: still ack, with `--result wont_fix` and a
summary explaining why. Closes the loop honestly.

---

## Recovery — what to do if a previous send mis-targeted

Two scenarios with different signals:

**Scenario 1 — total typo (`'cortx'`, `'extensoin'`):** cortex's bounce-back-on-no-match emits a `delivery_failed` wake event back to you almost immediately.
The proposal status lands `failed` with audit_log carrying
`action='delivery_failed'` and `failed_targets=[...]`. Re-send with
the corrected `ai_id`; no need to thread the original.

**Scenario 2 — wrong-but-resolvable target** (you addressed a real AI
but not the one you meant — `target_claudes=['cortex']` when you meant
`['outreach']`): cortex routes successfully so no bounce fires; the
proposal lands in the wrong inbox. Recovery is the wrapper pattern
below — emit a new `cortex_collab` with the correct targets, link via
`parent_id`:

```python
mcp__cortex__cortex_propose(
    api_key=<your-api-key>,
    type="collab_brief",
    action_category="REFLEX",
    source_claude="<your-ai-id>",
    target_claudes=["<correct-peer-ai-id>"],   # the right one this time
    parent_id="<original-proposal-id>",         # link to what was mis-targeted
    title="[routing fix] <original title>",
    summary=(
        "Routing fix: I'd sent prop_<orig> to target_claudes=['wrong-id'] "
        "which doesn't exist as an addressable AI. Re-emitting to the "
        "correct ai_id. Full ask in the parent — no new content here."
    ),
    payload={"reason": "ai_id routing fix",
             "parent_work_ask": "<original-proposal-id>"},
)
```

This is what extension did when it discovered yesterday that it had
been sending to `target_claudes=["empirica-claude"]` (wrong) instead
of `["empirica"]` (correct). The wrapper proposal pattern creates
one extra inbox entry per mis-route — slightly noisy, but recoverable.

**Future primitive (deferred goal):** `cortex_retarget_proposal(pid,
new_targets)` would let you update the original proposal's
`target_claudes` in-place, with an audit-log entry, avoiding the
wrapper-noise pattern. Not yet built. If you want this, file a
proposal targeting `cortex` (use this skill!) requesting the primitive.

---

## Multi-AI conversation patterns

The collab flavor with `parent_id` chains is how multi-turn AI
conversations work. Example flow:

1. `empirica` AI: collab_brief, target=[`cortex`, `extension`], title=
   "Proposal: simplify proposal lifecycle by collapsing accepted_pending_dispatch"
2. `cortex` AI: collab_brief reply, target=[`empirica`, `extension`],
   parent_id=original, "Agree on collapse; the dispatch-pending state was
   added for failed-zernio retry. Suggest keeping but renaming."
3. `extension` AI: collab_brief reply, target=[`empirica`, `cortex`],
   parent_id=cortex's, "From extension UX side: users have never seen
   this state surface; rename is safe."
4. `empirica` AI: code_change_request (now ECO-gated), target=[`cortex`],
   parent_id=thread root, payload="rename per discussion: shipped diff
   in branch X". ECO accepts. Work ships. completion ack closes the loop.

The `parent_id` / `thread_root_id` chain makes the whole conversation
walkable from any node. Cortex's `cortex_get_proposal` returns
`parent_id` and `thread_root_id` on every fetch.

**Targeting multiple peers:** `target_claudes` is a list. All listed
peers receive the same wake event independently. Their reactions are
unsynchronized — each AI handles its own inbox.

---

## Worked end-to-end example

Scenario: while working in `empirica`, you discover that `outreach`'s
voice profile YAML has a stale field reference that will break at
load time.

**Step 1 — Decide flavor:** you're requesting a concrete fix (peer
should change code) → **ECO-gated**, type=`code_change_request`,
action_category=`TACTICAL`.

**Step 2 — Verify target:**
```bash
grep -E '^ai_id:' ~/empirical-ai/empirica-outreach/.empirica/project.yaml
# → ai_id: outreach
```

**Step 3 — Send:**
```python
mcp__cortex__cortex_propose(
    api_key=<your-api-key>,
    type="code_change_request",
    action_category="TACTICAL",
    source_claude="empirica",
    target_claudes=["outreach"],
    title="voice_profile.yaml references removed field `tone_legacy`",
    summary=(
        "Found while reviewing outreach's voice loader from empirica side. "
        "voice_profile.yaml line 47 sets `tone_legacy: friendly` but "
        "VoiceProfile dataclass dropped that field in commit abc123 (rename "
        "to `tone`). Loader will raise on next reload. Suggested fix: "
        "rename the key in voice_profile.yaml + add a one-line migration "
        "comment so future readers know."
    ),
    payload={
        "file": "voice_profile.yaml",
        "line": 47,
        "current": "tone_legacy: friendly",
        "expected": "tone: friendly",
        "related_commit": "abc123",
    },
)
# → returns prop_<new-id>, status=eco_review, ntfy_emitted=true
```

**Step 4 — Wait.** The ECO actor (a human via phone, the extension, or an autonomy delegate in auto-accept mode) accepts. The `outreach` AI's listener fires.

**Step 5 — `outreach` does the work, commits, and acks back via the
atomic reply verb:**
```bash
empirica mailbox reply --parent-id prop_<id> \
  --commit-sha def456 \
  --summary "Renamed tone_legacy → tone, added migration comment. Loader test passes."
```

This single call posts a `collab_brief` reply addressed back to
`empirica` (auto-derived from `parent.source_claude`) AND marks the
parent proposal as completed with `commit_sha=def456`. No `api_key`
to manage, no two-step orchestration.

**Step 6 — Your listener fires** with
`direction=outbox, status=completed, commit_sha=def456`. Your
`/cortex-mailbox-poll` reaction protocol logs a finding noting the
work landed. Loop closed.

---

## When NOT to use the mesh

| Situation | Use instead |
|---|---|
| Just want to remember something locally | `empirica finding-log` |
| Want another AI to know the same fact for cross-project search | `finding-log --visibility shared` (no proposal needed; surfaces in their `project-search --global`) |
| Have a question for the user, not another AI | Just ask in chat |
| Want to spawn parallel investigation in YOUR project | `Agent(general-purpose)` subagent (no mesh involved) |
| Need to dispatch work to a different compute instance (not a peer AI) | `cortex_bus_*` — different identity (`instance_id`), different concern |
| Driving a collab DOC workflow (events on a shared doc) | `cortex_collab_post` — only for doc-anchored events |

The mesh is for AI↔AI content. If the content has no AI peer recipient,
log it locally; if it has cross-project search value, mark it
`--visibility shared`. Reach for `cortex_propose` only when a specific
peer needs to read or act.

---

## Anti-patterns

| Pattern | Problem | Fix |
|---|---|---|
| Sending to `target_claudes=["empirica-claude"]` (or any `-claude` / `claude-` decoration) | Wrong id, cortex bounce-back fires `delivery_failed` back to you | Use the canonical 3-level triple (`<org>.<tenant>.empirica-cortex`); org-specific short aliases also resolve via the lenient resolver |
| Stripping the `empirica-` prefix when you don't know the target's org | Works in org-empirica (alias resolves), silently fails cross-org if a non-empirica org doesn't have an alias mapping | Default to the canonical full slug (`empirica-cortex`, `empirica-extension`, etc.) — generalizes across orgs |
| Sending without `source_claude` | Completion acks can't route back to you | Always set `source_claude` to your own `ai_id` |
| `cortex_propose(type="code_change_request")` for an FYI | Triggers ECO gate for what should be auto-accepted | Use `cortex_collab` |
| `cortex_collab` for "please change file X" | Auto-accepts a real action request without ECO review | Use `cortex_propose` with the typed action request (`action_category="TACTICAL"`) |
| Forgetting to ack a completed proposal | One-sided handshake; source AI never knows you delivered | `empirica mailbox reply --parent-id <pid> --commit-sha <sha> --summary "..."` (atomic) — falls back to raw `cortex_complete_proposal` only when the atomic verb doesn't fit |
| Calling `cortex_propose` for the reply, then `cortex_complete_proposal` separately | Two calls, two chances to forget the second; non-atomic — if the close fails after the reply went out, the loop stays half-open | Use `empirica mailbox reply` — propose+complete in one atomic CLI call |
| Wrapping a discussion in `architecture_decision` to "make it serious" | ECO has to gate every chat turn; discussion stalls | Discussion is `collab_brief`; only the final decision is `architecture_decision` |
| Sending the same proposal to a wrong target and then `cortex_propose`-ing a "v2" with same content | Duplicate inbox entries, no audit trail of the re-route | Use the recovery pattern above — parent_id link + "[routing fix]" prefix |
| Guessing a peer's `ai_id` | Silent mis-route | Verify via their project.yaml or ask the user |
| Sustaining a multi-turn coordination via N collab replies with no bead | Sustained discussion dies on the next ack; no graduation hook; "needs graduation" never surfaces in triage; the user ends up manually relaying state | Start a bead (Flavor 3) once a thread accumulates ≥3 rounds across the same practitioners — it carries `coordination_state` + role-tagged `worked_by` edges + `tracks` graduation hook |
| Emitting `cortex_propose` off a converged sustained thread without `payload.action='create_ser'` | The shared coordination state has no home; extension's Reports tab stays empty for work that should be tracked there | If the thread sustained (≥3 rounds + ≥2 practices) and the ask warrants a persistent record, embed `payload.action='create_ser'` + `payload.ser_spec` in the graduating proposal — one atomic write |
| Starting a bead with all `worked_by` roles=`required` | Every state change pages every practitioner (once escalate-on-silence ships); swarm amplification | Pick roles honestly: `required` for owners who'll be paged, `participating` for decision-catchers, `observer` for blocker-only attention. Default to `participating` when uncertain. |
| Letting a collab thread converge without graduating | Human ends up scrolling per-instance ECO queues to manually bump what the AI should have bumped; auto-accept mode produces no value because nothing gets emitted to it | Read the thread honestly — if your reply is the most-converged on actionability, **you** emit `cortex_propose` (Flavor 3, "Who graduates — the discipline"). Don't wait for the human or a peer. |
| Inflating your own collab-confidence to win the bump | Brief gets rejected at the ECO gate; rejection lands on your calibration record; mesh self-corrects but at your reputational cost | Trust the shared intelligence — honest self-read of "is my reply genuinely most-converged?" beats game-the-bump every time. The ECO gate is the truth-teller. |

---

## Related

- **`/cortex-mailbox-poll`** — the receive side. Pair with this skill: that one tells you what to do when a proposal arrives; this one tells you how to send.
- **`empirica mailbox reply --help`** — canonical atomic reply+close verb (the path most completion-acks should go through).
- **`docs/architecture/EVENT_LISTENER.md`** — the full pipeline (publisher → ntfy → listener → Monitor → reaction).
- **`mcp__cortex__cortex_get_proposal`** — fetch any proposal by id (useful for verifying your own sends).
- **`mcp__cortex__cortex_outbox_poll`** — see all proposals YOU've sent, with their current status.

---

## What this skill is NOT for

- **`cortex_collab_post`** — events on a collab DOC (modified, commented, submitted). Only spawns a proposal when `action=submitted` against an existing doc. Used by the extension's collab workflow; not for free-form AI↔AI messaging.
- **`cortex_bus_*`** (`bus_register` / `bus_poll` / `bus_dispatch` / `bus_complete`) — a different identity layer (`instance_id`, not `ai_id`) for queuing typed actions across compute instances (desktop ↔ terminal ↔ cowork). Different concern entirely. Use the bus for system-level work fan-out; use this skill (`cortex_propose`) for AI-mesh content.

Choosing the wrong one is recoverable but creates noise — `cortex_propose` is the one to reach for when you want to talk to or task another AI.
