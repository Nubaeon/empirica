# Empirica Sync Architecture

**Version:** 1.0.0-draft
**Status:** Design Document
**Session:** 705cdec9-606a-49b6-9675-f4038871a9ff
**Date:** 2026-01-22

---

## Executive Summary

This document defines the sync architecture for Empirica epistemic data across devices and dependent projects. The core insight: **git notes are the canonical source** for all epistemic state; SQLite is a derived cache.

**Key Findings:**
1. `.empirica/` is gitignored - SQLite data (1431 findings, 226 unknowns) will be LOST on clone
2. Git notes infrastructure already exists (GitGoalStore, SessionSync)
3. Gap: Findings and unknowns need git notes equivalents

---

## Current State (Problem)

```
┌─────────────────────────────────────────────────────────────┐
│                    WHAT SURVIVES A CLONE                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ IN GIT NOTES (refs/notes/empirica/*)                    │
│  ├── goals/{goal_id}          254 goals                     │
│  ├── cascades/{session}/{id}  CASCADE checkpoints           │
│  ├── handoff/{handoff_id}     58 handoffs                   │
│  ├── checkpoints              Epistemic snapshots           │
│  └── breadcrumbs              Task context                  │
│                                                             │
│  ✅ GIT-TRACKED FILES                                       │
│  └── .breadcrumbs.yaml        Calibration (2316 obs)        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ❌ GITIGNORED (.empirica/)                                 │
│  ├── sessions/sessions.db     SQLite (55 tables!)           │
│  │   ├── project_findings     1431 findings (LOST!)         │
│  │   ├── session_findings     725 findings                  │
│  │   ├── project_unknowns     226 unknowns (LOST!)          │
│  │   ├── session_unknowns     141 unknowns                  │
│  │   ├── sessions             989 sessions                  │
│  │   ├── bayesian_beliefs     Computed                      │
│  │   ├── vector_trajectories  Computed                      │
│  │   └── ... (48 more tables)                               │
│  └── ref-docs/*.json          Pre-compact snapshots         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**The Problem:** Findings and unknowns are the most valuable breadcrumbs, and they're not in git!

---

## Proposed Architecture

### Principle: Git Notes as Canonical Source

```
┌─────────────────────────────────────────────────────────────┐
│                      GIT NOTES (Canonical)                  │
│                                                             │
│  refs/notes/empirica/                                       │
│  ├── goals/{goal_id}           ← Already implemented        │
│  ├── cascades/{session}/{id}   ← Already implemented        │
│  ├── handoffs/{handoff_id}     ← Already implemented        │
│  ├── findings/{finding_id}     ← NEW: Add GitFindingStore   │
│  ├── unknowns/{unknown_id}     ← NEW: Add GitUnknownStore   │
│  ├── dead_ends/{dead_end_id}   ← NEW: Add GitDeadEndStore   │
│  ├── sessions/{session_id}     ← NEW: Session metadata      │
│  └── checkpoints               ← Already implemented        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ empirica sync pull
                            │ empirica rebuild
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   SQLite (Derived Cache)                    │
│                                                             │
│  .empirica/sessions/sessions.db                             │
│  ├── Core tables (rebuilt from git notes)                   │
│  │   ├── sessions        ← from refs/notes/empirica/sessions│
│  │   ├── goals           ← from refs/notes/empirica/goals   │
│  │   ├── findings        ← from refs/notes/empirica/findings│
│  │   ├── unknowns        ← from refs/notes/empirica/unknowns│
│  │   └── dead_ends       ← from refs/notes/empirica/dead_ends│
│  │                                                          │
│  └── Computed tables (rebuilt from core)                    │
│      ├── bayesian_beliefs    ← computed from vectors        │
│      ├── vector_trajectories ← computed from assessments    │
│      └── concept_nodes/edges ← computed from findings       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
finding-log command
        │
        ▼
┌───────────────────┐
│ 1. Write to SQLite│ (immediate, for queries)
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ 2. Write to Git   │ (canonical, for sync)
│    Notes          │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ 3. Embed to Qdrant│ (semantic search)
└───────────────────┘
```

---

## CLI Commands

### Project-Level Sync

```bash
# Push epistemic state to remote
empirica sync push [--remote origin]
# Equivalent to: git push origin 'refs/notes/empirica/*:refs/notes/empirica/*'

# Pull epistemic state from remote
empirica sync pull [--remote origin] [--rebuild]
# Equivalent to: git fetch origin 'refs/notes/empirica/*:refs/notes/empirica/*'
# --rebuild: Also reconstruct SQLite from git notes

# Show sync status
empirica sync status
# Shows: local vs remote notes refs, pending changes, last sync time

# Force full rebuild of SQLite from git notes
empirica rebuild [--from-notes] [--qdrant]
# Reconstructs sessions.db from refs/notes/empirica/*
# --qdrant: Also rebuild Qdrant embeddings
```

### Workspace-Level Sync

```bash
# Sync all projects in workspace
empirica workspace sync [--push|--pull] [--filter "empirica-*"]
# Iterates through projects defined in .empirica-workspace

# Show workspace sync status
empirica workspace status
# Shows all projects, their sync state, dependencies
```

---

## Configuration

### Project Config (.empirica/config.yaml)

```yaml
version: '2.0'
root: /path/to/.empirica
paths:
  sessions: sessions/sessions.db
  identity: identity/

settings:
  auto_checkpoint: true
  git_integration: true
  log_level: info

# Sync Policy
sync:
  enabled: true
  remote: origin

  # What syncs via git notes
  layers:
    git_notes:
      enabled: true
      refs:
        - empirica/goals
        - empirica/cascades
        - empirica/handoffs
        - empirica/findings      # NEW
        - empirica/unknowns      # NEW
        - empirica/dead_ends     # NEW
        - empirica/sessions      # NEW
        - empirica/checkpoints
        - breadcrumbs
        - empirica-precompact
      push_on: [postflight, session_end, manual]

    # Calibration syncs via git-tracked file
    calibration:
      enabled: true
      source: .breadcrumbs.yaml
      method: git_tracked  # Already committed normally

    # Derived state - rebuild locally
    derived:
      sessions_db: rebuild_from_notes
      qdrant: rebuild_from_findings

  # Never sync (secrets via Doppler, identity is device-specific)
  exclude:
    - "*.token"
    - "*.key"
    - ".env*"
    - "identity/"
```

### Workspace Config (.empirica-workspace)

```yaml
workspace:
  name: "Empirical AI Development"

  scope:
    mode: selective
    include:
      - "empirica"
      - "empirica-*"
      - "cognitive_vault"
    exclude:
      - "*deprecated*"
      - "*backup*"

  # Project relationships
  projects:
    cognitive_vault:
      type: security
      depends_on: []
      sync:
        priority: 0           # Syncs FIRST (trust boundary)
        remote: private       # Different remote
        method: encrypted     # Always encrypted

    empirica:
      type: core
      depends_on: [cognitive_vault]
      sync:
        priority: 1
        remote: origin

    empirica-crm:
      type: application
      depends_on: [empirica]
      sync:
        priority: 2
        remote: origin
        shared_state:
          - calibration       # Reads from core
        isolated_state:
          - sessions
          - goals
          - findings

    "*":  # Default for auto-discovered
      type: application
      depends_on: [empirica]
      sync:
        priority: 3
        remote: origin

  # Sync orchestration
  sync:
    order: [cognitive_vault, empirica, "*"]
    on_conflict: ask
```

---

## Security Analysis

### What's Protected

| Data Type | Protection | Notes |
|-----------|------------|-------|
| Git notes | SSH/HTTPS | Standard git transport security |
| Calibration | Git-tracked | Visible in repo history |
| API keys | Doppler | Never in git |
| Identity keys | Device-local | Never synced |

### Threat Model

| Threat | Mitigation |
|--------|------------|
| Notes intercepted in transit | SSH/HTTPS encryption |
| Unauthorized access to remote | Git auth (SSH keys, tokens) |
| Secrets in git history | Doppler for secrets, git-crypt for sensitive configs |
| Cross-device key compromise | Identity keys are device-specific, never synced |
| Malicious note injection | Signed commits (optional), note signing (future) |

### Cognitive Vault Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    COGNITIVE VAULT                          │
│              (Trust Boundary - Syncs First)                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────┐  │
│  │   SECRETS    │   │  THRESHOLDS  │   │  CALIBRATION   │  │
│  │  (Doppler)   │   │   (Config)   │   │   AUTHORITY    │  │
│  └──────────────┘   └──────────────┘   └────────────────┘  │
│                                                             │
│  Syncs to: private remote (encrypted)                       │
│  Priority: 0 (before all other projects)                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Thresholds, calibration
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      EMPIRICA CORE                          │
│              (Framework - Syncs Second)                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Git notes: refs/notes/empirica/*                           │
│  Calibration: .breadcrumbs.yaml                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ CLI, calibration, lessons
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              DEPENDENT PROJECTS (empirica-crm, etc.)        │
│              (Applications - Sync Last)                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Own epistemic data (isolated)                              │
│  Shared calibration (from core)                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Roadmap

### Phase 1: Git Notes for Findings/Unknowns (Required)

1. Create `GitFindingStore` (mirror of GitGoalStore pattern)
2. Create `GitUnknownStore`
3. Create `GitDeadEndStore`
4. Modify `finding-log`, `unknown-log`, `deadend-log` to write to git notes
5. Update SessionSync to include new refs

**Files to modify:**
- `empirica/core/canonical/empirica_git/finding_store.py` (new)
- `empirica/core/canonical/empirica_git/unknown_store.py` (new)
- `empirica/cli/command_handlers/action_commands.py`
- `empirica/core/canonical/empirica_git/session_sync.py`

### Phase 2: CLI Sync Commands

1. `empirica sync push` - Push all notes refs
2. `empirica sync pull` - Fetch all notes refs
3. `empirica sync status` - Show diff between local/remote
4. `empirica rebuild` - Reconstruct SQLite from notes

**Files to create:**
- `empirica/cli/command_handlers/sync_commands.py`

### Phase 3: Workspace Orchestration

1. `empirica workspace sync` - Iterate projects
2. `empirica workspace status` - Show all projects
3. Dependency ordering (cognitive_vault first)

**Files to modify:**
- `empirica/cli/command_handlers/workspace_commands.py`
- Extend `.empirica-workspace` parser

### Phase 4: Conflict Resolution (Future)

1. Detect conflicting notes on pull
2. Strategy options: last-write-wins, manual merge, append-only
3. User prompt for resolution

---

## Unknowns / Future Work

1. **Conflict resolution strategy** - When same finding edited on two devices?
2. **Note signing** - Cryptographic verification of note authorship?
3. **Qdrant sync** - Should embeddings sync, or always rebuild?
4. **Multi-AI coordination** - When multiple AIs share same repo?
5. **Doppler integration specifics** - SDK, env var injection pattern?

---

## References

- `empirica/core/canonical/empirica_git/goal_store.py` - Existing pattern
- `empirica/core/canonical/empirica_git/session_sync.py` - Push/pull infrastructure
- `.empirica-workspace` - Workspace configuration
- Session 705cdec9 findings: ae078e3a, 26d3682a

---

**Document Status:** Ready for review. Pending unknowns logged for future investigation.
