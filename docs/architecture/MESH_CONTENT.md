# MeshContent — common substrate for Source + SER (and future mesh primitives)

**Status:** Proposal v0.1. Open for cortex + extension review.
**Goal:** d7efea49
**Related threads:**
  - Canonical source addressing + accessibility — `prop_w7q24hdurnhfnasf2ahiq5gvte` (active)
  - Mesh-sharing agreements / membrane — `ser_4272a07793` (shipped substrate)
  - Cross-mesh source map v1 — `commit 29af6e8a9` (shipped)

---

## 1. Motivation

Two cross-practice primitives have shipped or are shipping:

- **Source** (empirica-resident) — citable external material with project-scoped storage, visibility tiers, archive lifecycle. The cross-mesh discoverability layer (`sources-map --global`) walks per-project Qdrant.
- **SER — Shared Epistemic Record** (cortex-resident) — multi-participant coordination state with role-tiered participants, escalation-on-silence, three-action surface.

These are different primitives. They should stay different primitives. But they share a substantial amount of mechanism — and as the mesh grows (next candidates: shared `decision` artifacts at `--visibility shared`, cross-practice `goal_refs`, mesh-published `lessons`), each new primitive currently re-derives the same five questions:

1. **How is it addressed across the mesh?** (canonical address format)
2. **Who can see it?** (visibility tier + membrane gating)
3. **Who owns it / who acted on it?** (author + audit log)
4. **What's its lifecycle state?** (active → terminal — with type-specific terminal shapes)
5. **How does its content reach a peer who needs it?** (snapshot, hash dedup, size cap, request-pull fallback)

**MeshContent is the shared answer to those five questions.** It's not a single inheritance base — Source-side lives in empirica SQLite + Qdrant; SER-side lives in cortex storage. The substrate is a *contract*: the shape every mesh-citizen primitive implements, plus a small set of shared helpers each side uses to honor it.

The goal is to encode the contract once so the next mesh primitive doesn't re-litigate the same five questions in its own way.

---

## 2. Existing primitives — what they share, what they don't

| Aspect | Source | SER | Shared (MeshContent) |
|---|---|---|---|
| Storage | empirica `<project>/.empirica/sessions/sessions.db`, table `epistemic_sources` | cortex storage (multi-tenant) | — (storage stays primitive-specific) |
| ID | UUID | UUID | **Both: canonical address `<org>.<tenant>.<practice>#<type>_<uuid>`** |
| Created at | `discovered_at` | `created_at` | **Standard timestamp field** |
| Title | `title` (≤256) | `title` (≤200) | **Standard short headline** |
| Body | `description` (markdown) | `summary` (markdown) | **Standard markdown body** |
| Author | `discovered_by_ai`, single | `last_transition_actor` per change | Source = single; SER = multi-actor via audit log. **Shared: every mutation carries actor.** |
| Visibility | `visibility` ∈ `{local, shared, public}` (migration 049) | Implicit: scope = participants list | **Shared substrate: explicit `visibility` field, resolved against membrane on cross-tenant query.** |
| Content payload | `source_url` / file at `path` / blob to be promoted | The `summary` IS the content + projected goal/source refs | Source = external bytes; SER = inline + refs. **Shared: render pipeline returns canonical bytes + hash + size for mesh promotion.** |
| Lifecycle | `archived` BOOLEAN + `archive_reason` | `coordination_state` ∈ `{open, in_progress, blocked, closed}` | **Both have a terminal state. Shape differs; the existence of one + the transition audit are shared.** |
| Cross-practice routing | Same-tenant: `sources-map --global` walks per-project Qdrant. Cross-tenant: membrane-gated. | Cross-tenant by construction (participants in different practices) | **Shared: canonical address resolves to owning practice's user_id for ntfy push.** |
| Provenance | `entity_type` + `entity_id` (linked artifact) | `source_ref` (what spawned this SER) | **Both have a back-pointer to provenance.** |

The boundary is sharp:

- **Storage backend is primitive-specific.** Source stays empirica-side because it's a single-author artifact tied to project epistemic state. SER stays cortex-side because it's intrinsically multi-tenant.
- **The contract is shared.** Both implement the same five mesh-citizen questions; the answers should look the same shape regardless of which side owns the bytes.

---

## 3. The MeshContent contract

### 3.1. Canonical address

**Defer to active thread `prop_w7q24hdurnhfnasf2ahiq5gvte`.** Once cortex + extension lock the format, MeshContent inherits it. The proposed shape from that thread:

```
<org>.<tenant>.<practice>#<type>_<uuid>
```

Where `<type>` is the primitive name: `src`, `ser`, future `dec` for shared decisions, etc.

**Resolution contract:** every implementing primitive MUST provide a function from `(internal_id) → canonical_address` and a function from `canonical_address → (owning_practice, internal_id, type)`. Storage of the canonical address is **not** required (it's derivable). What's required is consistent derivation.

### 3.2. Visibility tier

Three tiers, same as artifact-visibility migration 039:

| Tier | Meaning |
|---|---|
| `local` | Single practice. Never crosses tenant boundary. (Default for safety.) |
| `shared` | Visible across practices within the same org (subject to org-internal membrane). |
| `public` | Visible to anyone with a cortex account (subject to org-to-org membrane). |

**Implementing primitive MUST:**
- Default to `local` if not specified
- Honor the membrane resolution at cross-tenant query/poll time (i.e. don't silently leak `shared` content to a tenant the owning practice hasn't agreed to share with)
- Use the `normalize_visibility` helper from `empirica.data.visibility` (or a cortex-side mirror) so bogus values fall through to safe defaults — **never silently promote to `public`**.

The membrane gating (mesh-sharing-agreements) is implemented elsewhere and reused; MeshContent doesn't re-implement gating, it just provides the field and the contract that the field will be honored.

### 3.3. Author / actor

Every mutation carries an actor identity. Shapes:

- **Single-author primitives (Source-style):** one `created_by_actor` field, canonicalized as `<practice>:<ai_id_or_eco_actor>`.
- **Multi-actor primitives (SER-style):** an append-only audit log with `{actor, action, at, details}` per row. The latest row's `actor` is the current "last actor."

The contract is: **every state-changing operation records WHO did it, canonicalized.** Reads are not logged.

### 3.4. Lifecycle

Two lifecycle shapes are valid:

- **Archive-style** (Source): boolean `archived` + nullable `archive_reason` enum + optional `archive_target_id` (for supersession). Lifecycle is one-shot (active → archived; closed is terminal).
- **State-machine-style** (SER): named states (`open | in_progress | blocked | closed`) with explicit transitions. Lifecycle can revisit `open` ↔ `in_progress` ↔ `blocked`; `closed` is terminal.

**The shared contract is just: there exists at least one terminal state, and transitions are recorded in the audit log.** The terminal-state shape is type-specific.

### 3.5. Render pipeline (mesh content promotion)

Per the active `prop_w7q24hdurnhfnasf2ahiq5gvte` thread, shared content must not be a dead pointer. The render pipeline answers: "give me the canonical bytes of this MeshContent, ready for promotion to cortex storage."

```
render(mesh_content) → {
    canonical_bytes: bytes,
    content_type: str,        # mime
    size_bytes: int,
    sha256: str,
    truncated: bool,          # true if size cap applied
}
```

Implementing primitive MUST provide a `render()` that:
1. Returns the canonical content payload (Source: file bytes / URL fetch / inline description; SER: the rendered Report — title + summary + participants + projected refs)
2. Caps size (proposed: 10 MB, matching the daemon `GET /api/v1/sources/{id}/content` cap shipped earlier)
3. Computes sha256 for cortex-side dedup
4. Reports `truncated: true` if the cap kicked in

The promotion path itself (daemon push on visibility change + AI-on-request-wake fallback — per my reply on `prop_w7q24hdurnhfnasf2ahiq5gvte`) calls `render()` and POSTs the result.

---

## 4. Storage layout

**Storage stays primitive-specific.** MeshContent is a contract + helpers, not a shared table.

- `epistemic_sources` (empirica per-project SQLite) — unchanged. Already has `visibility`, archive_*, entity provenance. Add `created_by_actor` if not equivalent to `discovered_by_ai`. Implements the contract via empirica-side helpers.
- `ser_records` + `ser_participants` (cortex storage) — unchanged structurally. Already has `coordination_state`, participant audit, source_ref. Add `visibility` field (currently implicit via participants). Implements the contract via cortex-side helpers.

**Shared helpers (where they live):**

| Helper | Empirica side | Cortex side |
|---|---|---|
| `canonical_address(practice, type, uuid) → str` | `empirica.core.mesh_content.address` | `cortex.mesh_content.address` |
| `parse_canonical(addr) → (practice, type, uuid)` | same module | same module |
| `normalize_visibility(value) → tier` | `empirica.data.visibility` (exists) | `cortex.mesh_content.visibility` (mirror) |
| `render(mesh_content) → RenderResult` | per-primitive impl in empirica | per-primitive impl in cortex |
| `record_actor(audit_log, actor, action, details)` | per-primitive in empirica | per-primitive in cortex |

Cortex-side helpers should mirror the empirica-side names and signatures so the two implementations are obviously the-same-thing.

---

## 5. Migration path

**Existing Source rows:** no migration required. The contract is implemented additively in empirica's source code (helpers added; existing columns reinterpreted). Canonical address is derived at read time, not stored. `created_by_actor` falls back to `discovered_by_ai` when absent.

**Existing SER records:** cortex-side change. Add `visibility` column (default `shared` — most existing SERs are cross-tenant by definition); existing `last_transition_actor` already satisfies the actor contract.

**Net-new MeshContent type (future, e.g. shared decision artifacts):** implement the helpers + the lifecycle + the render. Picks up canonical addressing + visibility + mesh routing for free.

---

## 6. Open questions for cortex + extension

1. **Canonical address shape:** deferring to `prop_w7q24hdurnhfnasf2ahiq5gvte`. Once locked, this doc gets a one-line update naming the agreed format.

2. **Where does the actor canonicalization live?** Suggest: `<practice>:<ai_id>` for AI actors, `<eco>:<actor_id>` for ECO decisions, `<system>:<component>` for cortex/empirica autonomous actions. Cortex side already has `last_transition_actor` with effectively this convention — formalize it as a substrate rule?

3. **Render size cap:** 10 MB matches the daemon endpoint cap. Reasonable for SER reports too (which are typically much smaller)? Or should the cap be per-type?

4. **Future MeshContent types:** likely candidates are shared decisions (`--visibility shared` on `decision-log`) and shared lessons. Should those be MeshContent at the substrate layer, or are they better handled by extending existing artifact-visibility promotion to global_learnings? My lean: MeshContent for anything that has cross-practice routing semantics; artifact-visibility for anything that's a per-practitioner artifact that happens to be shared (the existing global_learnings pattern stays load-bearing).

5. **Empirica-side mirror of cortex SER state:** today, empirica practitioners read SERs via cortex MCP. Should empirica maintain a local read-cache of SERs it participates in (for offline read + faster bootstrap)? Out of scope here, but the MeshContent contract makes it cheaper to add later — the canonical address is enough to lazy-fetch.

---

## 7. Thin first slice (ship now, neutral on §3.1)

To make progress without waiting for the canonical-address thread to land, ship:

1. **`empirica.core.mesh_content` module** — placeholder for the substrate. Initially exports `normalize_visibility` (re-export from `empirica.data.visibility` so future imports don't have to know the original location) + `RenderResult` dataclass + a stub `canonical_address()` function that returns the current best guess (`<practice>#src_<uuid>`) and gets updated once §3.1 lands.

2. **Source-side shim** — add a thin `MeshContentSource` wrapper around the existing `epistemic_sources` row that exposes the contract methods (`canonical_address()`, `visibility()`, `render()`, `audit_log()`). Existing source-add/source-list/sources-map continue to work unchanged; the wrapper is opt-in for callers that want the substrate view.

3. **Tests** — coverage on the contract: every implementing primitive's wrapper passes the same suite.

4. **Docs** — this file in `docs/architecture/`, linked from `docs/INDEX.md`.

Slice 1 doesn't presuppose §3.1's answer. When the canonical address lands, only `canonical_address()` changes; everything else is stable.

---

## 8. What this is NOT

- **Not a new storage table.** Source stays in `epistemic_sources`, SER stays in cortex storage. The substrate is contract + helpers, not data.
- **Not a replacement for global_learnings.** That's the artifact-visibility cross-project promotion pipeline. MeshContent is for things with cross-practice routing semantics (Source, SER), not for every shared artifact.
- **Not addressing-coupled.** §3.1 is deferred; the rest of the contract stands regardless of what address shape lands.
- **Not a circular dependency vector.** Empirica doesn't import from cortex and vice versa; both implement the contract independently using mirrored helper modules.

---

## 9. Decisions log (commit as decision-log entries when locked)

- **2026-06-07:** First draft, open for cortex + extension review.
- *(Cortex sign-off here)*
- *(Extension sign-off here)*
- *(David lock-in here)*
