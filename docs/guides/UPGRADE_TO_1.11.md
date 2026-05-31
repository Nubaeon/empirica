# Upgrading to Empirica 1.11

This guide covers the 1.10.x → 1.11.0 jump. **There are no breaking changes** — the bump rolls up two months of patches (1.10.5 + 1.10.6) into a coherent minor along with a substantial documentation refresh that surfaces capabilities the patches added but didn't user-document at the time.

If you're already on 1.10.6, upgrading to 1.11.0 is `pip install --upgrade empirica` + `empirica setup-claude-code --force` with nothing to do post-upgrade. The headline value of 1.11.0 is the new docs.

If you're on 1.10.4 or earlier, you'll also pick up the intermediate patch content described in the [Highlights since 1.10.4](#highlights-since-1104) section below.

---

## Quick Upgrade

```bash
pip install --upgrade empirica empirica-mcp
empirica setup-claude-code --force          # Refresh hooks + plugin skills
empirica diagnose                            # Sanity check — green = ready
```

If you run a persistent listener as an OS service (systemd-user / launchd), restart it after the upgrade so it picks up the new code:

```bash
# Linux
systemctl --user restart empirica-listener

# macOS
launchctl kickstart -k gui/$UID/com.empirica.listener
```

The listener has a clean-exit reconnect contract — restart is the supported upgrade path.

---

## What's New in 1.11

Four entirely new user-facing docs, every one of them surfacing an existing capability that had been operational-only or skill-only previously:

### `MESH_SETUP.md` — comprehensive opt-in mesh setup
The full-stack walkthrough for users who want cross-AI coordination: provisioning Cortex, configuring credentials, installing the browser extension, configuring the ntfy push bridge, registering projects, arming listeners, end-to-end smoke test. Explicit framing throughout that empirica core works standalone — every layer of the mesh is opt-in. Includes a recap of what works **without** the mesh so users understand they can stop at any level.

→ [docs/human/end-users/MESH_SETUP.md](../human/end-users/MESH_SETUP.md)

### `PROJECT_LIFECYCLE.md` — multi-project narrative
The companion to `PROJECT_MANAGEMENT_FOR_USERS.md`. Covers the full discover → register → sync → prune → unregister story for users with N projects scattered across their filesystem: `projects-sync` as the single-verb master path, selective `--include`/`--exclude` regex filters, `--dry-run` patterns, the `--prune` flow, the **known cortex-side-unregister gap** (with current workarounds + queued design), and the **name↔UUID identity gap** for users provisioned through both CLI and Desktop clients.

→ [docs/human/end-users/PROJECT_LIFECYCLE.md](../human/end-users/PROJECT_LIFECYCLE.md)

### `LOGGING_AND_FINDING.md` — discovery-side walkthrough
A concrete OAuth2 worked example that threads the entire lifecycle (PREFLIGHT + goal + tasks + 5 artifact types + CHECK + completion + POSTFLIGHT) but spends the majority of its real estate on the **finding side**: semantic search (local + `--global`), the artifact graph + typed edges, entity discovery (`entity-list` / `entity-walk` / `entity-search`), the commit-context walker (single SHA, ranges, `--session`, `--only-with-artifacts`), and how to thread it all together a day or week later.

→ [docs/human/end-users/LOGGING_AND_FINDING.md](../human/end-users/LOGGING_AND_FINDING.md)

### Required-vs-Optional framing audit
Five existing user-facing docs got their mesh-vs-core framing sharpened (README, `MCP_INSTALLATION.md`, `FIRST_TIME_SETUP.md`, `ECOSYSTEM_OVERVIEW.md`, `PROJECT_MANAGEMENT_FOR_USERS.md`). The headline correction: `MCP_INSTALLATION.md`'s Tools Available table was listing cortex MCP tools as part of the `empirica-mcp` surface — fixed against the actual `empirica mcp-list-tools` output, plus a top-of-doc callout clarifying that **`empirica-mcp` and the Cortex MCP are two different servers** that can coexist under different names in a client config.

---

## Highlights since 1.10.4

If you skipped 1.10.5 + 1.10.6 patches and are jumping straight from 1.10.4, you pick up the rolled-up patch content. (If you've already been running 1.10.6 these are review only.)

### Bead v0 — coordination records as a new mesh primitive (1.10.5)

Beads are persistent, mutable coordination records that sit between single-turn collab (one-off discussion) and graduated proposals (typed praxic action). A bead carries `coordination_state` (`open` / `in_progress` / `blocked` / `closed`), `worked_by` edges with per-AI `role` metadata (`required` / `participating` / `observer`), `tracks` edges to actionables (proposals / goals / issues), and an optional cross-org scope flag.

**For AI-mesh users**: beads are the structured-coordination primitive your AIs should start when a thread sustains beyond 3 rounds across the same practitioners, or when work has a named owner + workers with explicit roles. The `/cortex-mailbox-send` skill's **Flavor 3** section walks the discipline end-to-end including the graduation contract (bead → typed proposal).

**For non-mesh users**: beads are invisible. The schema lands (migration 048 adds the `beads` table) but `bead` artifacts are only emitted through the mesh sync path; if you're not running mesh, nothing changes.

Sample `log-artifacts` payload to create a bead with the full edge set:

```bash
NOW=$(date +%s.%N)
empirica log-artifacts - << EOF
{
  "nodes": [
    {"ref": "b1", "type": "bead",
     "data": {
       "coordination_state": "open",
       "updated_at": $NOW,
       "scope": "local",
       "summary": "Sustained coordination on <topic>"
     }}
  ],
  "edges": [
    {"from": "b1", "to": "<empirica-practice-uuid>", "relation": "owned_by"},
    {"from": "b1", "to": "<empirica-practice-uuid>", "relation": "worked_by",
     "metadata": {"role": "required"}},
    {"from": "b1", "to": "<tracked-actionable-uuid>", "relation": "tracks"}
  ]
}
EOF
```

See [`MESH_SETUP.md`](../human/end-users/MESH_SETUP.md) + the `/cortex-mailbox-send` skill (Flavor 3) for the operational depth.

### Phase B mesh — noetic / praxic primitive split (1.10.5)

The Cortex MCP layer split its single mesh primitive into two — one for noetic conversation (auto-accepted), one for praxic action requests (ECO-gated). The empirica skills + system prompt now route AI-to-AI sends through this split. **Backwards-compatible**: the older single-primitive form still works, but it's deprecated for the conversational case. AIs running the updated skill will pick the right primitive automatically.

If you've trained custom AI agents against the older API, expect them to keep working through 1.11; deprecation hard-cutover lands in a later release.

### Graduation discipline — AIs take lead on collab → proposal bumping (1.10.6 skill update)

The `/cortex-mailbox-send` skill's Flavor 3 gains a "Who graduates — the discipline" subsection. The behaviour change: when a collab thread converges on an actionable ask, the AI whose reply is most-converged emits the typed proposal directly instead of waiting for the human to scroll per-instance ECO queues. Trust-the-shared-intelligence + the ECO gate as the truth-teller (rejection on inflation lands on the inflating AI's calibration record).

This is a discipline update in the skill; nothing to install separately. Loaded AIs pick it up on next session start after `empirica setup-claude-code --force`.

### Edge metadata persistence fix (1.10.5)

A real bug in `log-artifacts` was silently dropping per-edge `metadata` JSON. Code path: `_wire_edges` called `_store_edge(db, from_id, to_id, relation)` without passing `edge.get('metadata')`, so payloads carrying `{"role": "required"}` on a `worked_by` edge landed with `metadata=NULL` in `artifact_edges`. Affected every artifact edge with metadata, not just beads.

Pre-fix beads have NULL `worked_by` metadata even when emitted with role. Post-fix beads carry it correctly. If you emitted beads on 1.10.4 with role metadata and want the role tier to surface (for escalate-on-silence wake routing, for example), re-emit them post-upgrade.

### Listener stability cluster (1.10.5 + 1.10.6)

A series of operational fixes for users running the persistent listener:

- **Supervisor wrapper** (1.10.5) — standalone Monitor on hosts without systemd/launchd now auto-relaunches after clean exits (SIGTERM during reconnect, `ListenerUpgraded` on pip-version drift, etc.). The OS-supervisor mode is unchanged.
- **`work_type=remote-ops` SSH passthrough** (1.10.5) — the sentinel no longer deadlocks SSH-recon when the work-type is declared `remote-ops`. PREFLIGHT declaration IS the gate; calibration is `ungrounded_remote_ops` and self-assessment stands.
- **Listener drift bypass** (1.10.5) — `EMPIRICA_LISTENER_NO_DRIFT_EXIT` env var disables the upgrade-self-exit for non-supervised hosts that don't have automatic relaunch.
- **Wake-noise filter then removed** (1.10.5 added → 1.10.6 removed) — per cortex+extension contract: the per-message actionability flag was redundant + lossy. 1.10.6 drops both the field on `ProposalEvent` and the listener's `grep -v "actionability": "fyi"` filter. The tool split (collab vs propose) IS the actionability signal at the wire level.

### Lenient `ai_id` resolver (1.10.6)

Cortex MCP shipped a lenient alias-aware `ai_id` resolver, and empirica's `/cortex-mailbox-send` skill adopted the new convention: **canonical wire form is the full project slug** (e.g. `empirica-cortex`); the org-specific short alias (e.g. `cortex`) is a convenience that resolves server-side. Default to the canonical full slug for cross-org generality.

The empirica skill update is purely documentation — no behaviour change beyond what the cortex resolver enables.

---

## Action items for upgraders

- [ ] `pip install --upgrade empirica empirica-mcp`
- [ ] `empirica setup-claude-code --force` (refresh hooks + plugin skills)
- [ ] `empirica diagnose` — green = ready
- [ ] If you run a persistent listener, restart it (see Quick Upgrade above)
- [ ] **If you emitted beads pre-1.10.5 with role metadata** and want the role tier visible, re-emit them post-upgrade (see [Edge metadata persistence fix](#edge-metadata-persistence-fix-1105))
- [ ] **Multi-project users**: skim [`PROJECT_LIFECYCLE.md`](../human/end-users/PROJECT_LIFECYCLE.md) — covers the new `projects-sync` master verb and the selective `--include`/`--exclude` filters
- [ ] **Mesh users**: skim [`MESH_SETUP.md`](../human/end-users/MESH_SETUP.md) — covers the post-1.10.6 listener arming pattern + the Contract 2 wake-noise simplification
- [ ] **New to the discovery side**: walk through [`LOGGING_AND_FINDING.md`](../human/end-users/LOGGING_AND_FINDING.md) — the OAuth2 worked example threads search + entity-walk + commit-context together
- [ ] (Optional, for completeness) Verify the bead schema migration ran: `sqlite3 .empirica/sessions/sessions.db '.tables' | grep beads` — should show `beads`

---

## Cross-references

- [CHANGELOG.md](../../CHANGELOG.md) — full release notes for 1.10.5 + 1.10.6 + 1.11.0
- [UPGRADE_TO_1.10.md](./UPGRADE_TO_1.10.md) — prior minor upgrade guide (covers the `subtask` → `task` rename)
- [`MESH_SETUP.md`](../human/end-users/MESH_SETUP.md) — full optional-mesh setup
- [`PROJECT_LIFECYCLE.md`](../human/end-users/PROJECT_LIFECYCLE.md) — multi-project narrative
- [`LOGGING_AND_FINDING.md`](../human/end-users/LOGGING_AND_FINDING.md) — discovery-side walkthrough
