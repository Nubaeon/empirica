# Workspace Management API Reference

**Version:** 1.5.0
**Database:** `~/.empirica/workspace/workspace.db`
**Purpose:** Cross-project portfolio management and trajectory tracking

---

## Overview

The workspace system provides a **global registry** that tracks all Empirica projects. It enables:

- Portfolio-level views across projects
- Cross-project pattern discovery
- Project switching and instance binding
- Trajectory health monitoring

---

## Commands

### `workspace-init`

Initialize workspace database and structure.

```bash
# Initialize in current directory
empirica workspace-init

# Initialize specific path
empirica workspace-init --path ~/projects

# Non-interactive mode
empirica workspace-init --non-interactive --output json
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--path` | No | CWD | Workspace path |
| `--output` | No | `human` | Output format: `human` or `json` |
| `--non-interactive` | No | `false` | Skip prompts, use defaults |

**Creates:**
- `~/.empirica/workspace/workspace.db` — Global registry
- `~/.empirica/workspace/` directory structure

---

### `workspace-list`

List all registered projects with filtering options.

```bash
# List all projects
empirica workspace-list

# Filter by type
empirica workspace-list --type research

# Filter by tags
empirica workspace-list --tags "ai,ml"

# Tree view (hierarchical)
empirica workspace-list --tree

# Show children of specific project
empirica workspace-list --parent abc123
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--type` | No | all | Filter by project type |
| `--tags` | No | - | Filter by tags (comma-separated) |
| `--parent` | No | - | Show children of project ID |
| `--tree` | No | `false` | Hierarchical tree view |
| `--output` | No | `human` | Output format |

**Project Types:**
- `product` — Product/application projects
- `application` — Standalone applications
- `feature` — Feature branches/modules
- `research` — Research and exploration
- `documentation` — Documentation projects
- `infrastructure` — Infrastructure/tooling
- `operations` — Operations and DevOps

**Output (human):**
```
📦 WORKSPACE: 5 projects
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  empirica          product     active   ⚡82%  🎯12  📝45
  empirica-crm      product     active   ⚡75%  🎯3   📝12
  empirica-mcp      feature     active   ⚡90%  🎯1   📝8
  research-ml       research    dormant  💫45%  🎯5   📝23
  docs              documentation active ⚡88%  🎯2   📝15
```

**Output (JSON):**
```json
{
  "ok": true,
  "projects": [
    {
      "id": "748a81a2-...",
      "name": "empirica",
      "trajectory_path": "/home/user/empirica",
      "project_type": "product",
      "status": "active",
      "total_transactions": 156,
      "total_findings": 45,
      "total_goals": 12,
      "last_transaction_timestamp": 1707318600.0
    }
  ],
  "count": 5
}
```

---

### `workspace-overview`

Portfolio view with aggregated stats across all projects.

```bash
# Full overview
empirica workspace-overview

# Sort by activity
empirica workspace-overview --sort-by activity

# Filter by status
empirica workspace-overview --filter active

# JSON output
empirica workspace-overview --output json
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--sort-by` | No | `activity` | Sort: `activity`, `knowledge`, `uncertainty`, `name` |
| `--filter` | No | all | Filter: `active`, `inactive`, `complete` |
| `--output` | No | `human` | Output format |

**Output (human):**
```
╔════════════════════════════════════════════════════════════╗
║                    WORKSPACE OVERVIEW                       ║
╠════════════════════════════════════════════════════════════╣
║  Active Projects:     5                                     ║
║  Total Transactions:  487                                   ║
║  Total Findings:      234                                   ║
║  Total Dead-ends:     45                                    ║
║  Total Goals:         67 (23 active)                        ║
╠════════════════════════════════════════════════════════════╣
║  📊 KNOWLEDGE DISTRIBUTION                                  ║
║  ████████████████████░░░░░░░░░░  68% avg know               ║
║  ░░░░░░░░████░░░░░░░░░░░░░░░░░░  22% avg uncertainty        ║
╠════════════════════════════════════════════════════════════╣
║  🔥 MOST ACTIVE (7d)                                        ║
║  1. empirica         42 transactions   +15 findings         ║
║  2. empirica-crm     12 transactions   +8 findings          ║
║  3. docs              5 transactions   +3 findings          ║
╚════════════════════════════════════════════════════════════╝
```

---

### `workspace-map`

Project dependency and relationship map.

```bash
# Show project map
empirica workspace-map

# JSON for visualization tools
empirica workspace-map --output json
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--output` | No | `human` | Output format |

**Output (human):**
```
🗺️ WORKSPACE MAP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

empirica (core)
├── empirica-mcp [depends_on]
├── empirica-crm [extends]
└── docs [documents]

empirica-crm
└── (standalone)

research-ml
├── empirica [shared_learning]
└── ml-models [derived]
```

**Output (JSON):**
```json
{
  "ok": true,
  "nodes": [
    {"id": "748a81a2-...", "name": "empirica", "type": "product"}
  ],
  "edges": [
    {
      "source": "empirica-mcp-id",
      "target": "748a81a2-...",
      "link_type": "depends_on",
      "relevance": 0.9
    }
  ]
}
```

---

## Related Commands

### `project-list`

List projects (queries workspace.db).

```bash
empirica project-list
```

### `project-switch`

Switch active project for current instance.

```bash
empirica project-switch empirica
empirica project-switch --project-id 748a81a2-...
```

### `ecosystem-check`

Validate workspace health.

```bash
empirica ecosystem-check
```

---

## Python API

```python
from empirica.data.workspace_database import WorkspaceDatabase

db = WorkspaceDatabase()

# List projects
projects = db.list_projects(status='active')

# Get project
project = db.get_project(project_id)

# Update project stats
db.update_project_stats(project_id, {
    'total_transactions': 100,
    'total_findings': 50
})

# Add trajectory link
db.add_trajectory_link(
    source_project_id=source_id,
    target_project_id=target_id,
    link_type='shared_learning',
    artifact_type='finding',
    artifact_id=finding_id
)

db.close()
```

---

## Database Schema

See [WORKSPACE_DATABASE_SCHEMA.md](../WORKSPACE_DATABASE_SCHEMA.md) for full schema details.

**Key tables:**
- `global_projects` — Project registry
- `global_sessions` — Cross-project session tracking
- `trajectory_patterns` — Cross-project learning patterns
- `trajectory_links` — Project relationships

---

## Statusline Integration

The statusline shows workspace status:

```
WS:5  — 5 active projects in workspace
```

Configure via `EMPIRICA_STATUS_MODE` environment variable.

---

## Related Documentation

- [WORKSPACE_DATABASE_SCHEMA.md](../WORKSPACE_DATABASE_SCHEMA.md) — Database schema
- [PROJECT_SWITCHING_FOR_AIS.md](../../guides/PROJECT_SWITCHING_FOR_AIS.md) — Project switching guide
- [TMUX_MULTI_PANE_GUIDE.md](../../guides/TMUX_MULTI_PANE_GUIDE.md) — Multi-instance setup
