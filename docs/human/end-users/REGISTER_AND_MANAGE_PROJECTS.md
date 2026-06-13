# Register & manage Empirica projects — copy-paste set

Drop-in command blocks for the Empirica extension's copy-prompt UX (and for
humans/AIs at a terminal). Every block is copy-pastable as-is. Built against
real CLI behavior; verified for the v1.12 registration model.

**The one rule that makes this simple:** a project's id is **git-intrinsic** —
it's minted once by `project-init`, committed in `.empirica/project.yaml`, and
travels with the repo. `project-register` then **adopts** that id (it never
mints a second one). Sharing a project across machines or with Cortex never
changes its identity.

---

## Register a project

Pick the block that matches your situation.

### 1. Brand-new project (no `.empirica/` yet)

`project-init` mints the id and commits it to `.empirica/project.yaml`;
`project-register` adopts it and shares to Cortex.

```bash
empirica project-init && empirica project-register .
```

Scripted / non-interactive (extension copy-prompt):

```bash
empirica project-init --non-interactive && empirica project-register .
```

> `project-register .` on a folder that was never init'd will stop and point
> you back to `project-init` — that's why init comes first. It does **not**
> silently mint.

### 2. Already an Empirica project (id rides in the cloned repo)

The committed `.empirica/project.yaml` already carries the id — just register
this machine to it.

```bash
git clone <url> <name> && cd <name> && empirica project-register .
```

Local-only (skip Cortex — offline, or Cortex down):

```bash
empirica project-register . --no-cortex
```

### 3. No local Empirica (pure Cloud / Cowork)

When there's no repo on the machine (Desktop/Cowork seats, bursty practices),
register directly in Cortex via the MCP tool — no CLI install needed:

```
cortex_project_register(name="<display name>", slug="<tenant-scoped slug>")
```

Cortex mints the id and returns it prominently. **If that project later gains a
local repo, write the returned id into `.empirica/project.yaml`** (downward
adoption) rather than re-initialising — keeps the one-id-per-project guarantee.

> Availability: the `cortex_project_register` tool ships with Cortex's
> registration-model slice (SER `ser_c10ae794`). Blocks 1 and 2 are live today.

---

## Manage projects

### See what's registered

```bash
empirica projects-list --output table      # or json / yaml
```

### Add / sync many at once (the "add many" power-tool)

`projects-sync` walks the filesystem, upserts the local registry, and POSTs each
project to Cortex — one verb for the whole pipeline. Keep it separate in your
head from "register one project" above; this is bulk lifecycle.

```bash
empirica projects-sync --dry-run                 # preview — no writes
empirica projects-sync                            # full sync
empirica projects-sync --include <regex>          # only matching projects
empirica projects-sync --prune                    # drop stale local registry entries
```

`--include` / `--exclude` take regexes and compose; `--prune` only touches the
local registry, never Cortex.

### Update a project's metadata

```bash
empirica project-update --project-description "..."   # edit committed project.yaml fields
```

---

## Addressing a project / practice on the mesh

Peers and proposals address a practice by its **canonical 3-form**:
`<org>.<tenant>.<project-slug>`. Tenant-scoped slugs mean the same slug under
two tenants are distinct by construction — `david.empirica-outreach` and
`philipp.empirica-outreach` never collide (enforced by `UNIQUE(slug,
owner_user_id)` + adopt-id).

**Watch the "doubled empirica".** Repos slugged `empirica-*` produce a 3-form
where `empirica` appears twice — once as the org, once as the project-slug
prefix. This is correct; do not strip the second one:

| Practice | Canonical 3-form |
|---|---|
| David's outreach | `empirica.david.empirica-outreach` |
| Philipp's outreach | `empirica.philipp.empirica-outreach` |
| Philipp's mesh-support | `empirica.philipp.empirica-mesh-support` |
| (no-prefix exception) | `empirica.philipp.usw` |

When unsure of the exact form, `empirica practice-context --ai-id <slug>` prints
the canonical `ai_id_mesh` to emit — no guessing.

---

## What changes with the v1.12 registration model

- `project-register` **adopts** the committed id (already true today); on a
  within-tenant slug collision Cortex returns a clear "slug taken" error instead
  of silently creating a suffixed duplicate.
- Dedup/reconcile is a one-time migration concern, not part of normal use — in
  steady state, registering a project creates no duplicates.
