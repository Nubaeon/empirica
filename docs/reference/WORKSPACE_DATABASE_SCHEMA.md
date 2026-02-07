# Workspace Database Schema Reference

**Location:** `~/.empirica/workspace/workspace.db`
**Version:** 1.5.0
**Purpose:** Cross-project portfolio management and trajectory tracking

---

## Overview

The workspace database is a **global registry** that tracks all Empirica projects. It enables:
- Portfolio-level views across projects
- Cross-project pattern discovery
- Project switching and instance binding
- Trajectory health monitoring

---

## Tables

### `global_projects`

Primary table tracking all registered projects.

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `id` | TEXT | (required) | Project UUID (primary key) |
| `name` | TEXT | (required) | Human-readable project name |
| `description` | TEXT | NULL | Project description |
| `trajectory_path` | TEXT | (required) | Path to project's `.empirica/` directory |
| `git_remote_url` | TEXT | NULL | Git remote URL for sync/discovery |
| `git_branch` | TEXT | `'main'` | Current git branch |
| `total_transactions` | INTEGER | `0` | Cached transaction count |
| `total_findings` | INTEGER | `0` | Cached findings count |
| `total_unknowns` | INTEGER | `0` | Cached unknowns count |
| `total_dead_ends` | INTEGER | `0` | Cached dead-ends count |
| `total_goals` | INTEGER | `0` | Cached active goals count |
| `last_transaction_id` | TEXT | NULL | Most recent transaction UUID |
| `last_transaction_timestamp` | REAL | NULL | Unix timestamp of last transaction |
| `last_sync_timestamp` | REAL | NULL | When stats were last refreshed |
| `status` | TEXT | `'active'` | `'active'`, `'dormant'`, `'archived'` |
| `project_type` | TEXT | `'product'` | `'product'`, `'research'`, `'outreach'` |
| `project_tags` | TEXT | NULL | JSON array of tags |
| `created_timestamp` | REAL | (required) | Unix timestamp of creation |
| `updated_timestamp` | REAL | (required) | Unix timestamp of last update |
| `metadata` | TEXT | NULL | JSON for extensibility |

**Indexes:**
- `idx_global_projects_status` — Fast filtering by status
- `idx_global_projects_type` — Fast filtering by project type
- `idx_global_projects_last_tx` — Sort by recent activity

**Status Values:**
| Value | Description |
|-------|-------------|
| `active` | Actively worked on, shown by default |
| `dormant` | Not recently active, still tracked |
| `archived` | Hidden from default views |

---

### `trajectory_patterns`

Cross-project learning patterns (mistakes, successes, dead-ends).

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `id` | TEXT | (required) | Pattern UUID |
| `pattern_type` | TEXT | (required) | `'learning'`, `'mistake'`, `'dead_end'`, `'success'` |
| `pattern_description` | TEXT | (required) | Human-readable description |
| `source_project_ids` | TEXT | (required) | JSON array of project UUIDs |
| `occurrence_count` | INTEGER | `1` | How many times observed |
| `avg_impact` | REAL | NULL | Average impact across occurrences |
| `confidence` | REAL | NULL | Pattern reliability score (0-1) |
| `domain` | TEXT | NULL | `'caching'`, `'auth'`, `'performance'`, etc. |
| `tech_stack` | TEXT | NULL | JSON array: `['Python', 'Redis']` |
| `first_observed` | REAL | (required) | Unix timestamp |
| `last_observed` | REAL | (required) | Unix timestamp |
| `pattern_data` | TEXT | (required) | Full pattern details as JSON |

**Indexes:**
- `idx_trajectory_patterns_type` — Filter by pattern type
- `idx_trajectory_patterns_domain` — Filter by domain

---

### `trajectory_links`

Cross-project artifact connections.

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `id` | TEXT | (required) | Link UUID |
| `source_project_id` | TEXT | (required) | Origin project UUID |
| `target_project_id` | TEXT | (required) | Destination project UUID |
| `link_type` | TEXT | (required) | `'shared_learning'`, `'dependency'`, `'related'`, `'derived'` |
| `artifact_type` | TEXT | NULL | `'finding'`, `'unknown'`, `'dead_end'`, `'pattern'` |
| `artifact_id` | TEXT | NULL | UUID of linked artifact |
| `relevance` | REAL | `1.0` | Link relevance score (0-1) |
| `notes` | TEXT | NULL | Human-readable notes |
| `created_timestamp` | REAL | (required) | Unix timestamp |
| `created_by_ai_id` | TEXT | NULL | AI that created the link |

**Indexes:**
- `idx_trajectory_links_source` — Query by source project
- `idx_trajectory_links_target` — Query by target project

**Constraints:**
- Foreign keys to `global_projects(id)`
- Unique on `(source_project_id, target_project_id, artifact_type, artifact_id)`

---

### `instance_bindings`

Maps AI instances (tmux panes) to projects.

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `instance_id` | TEXT | (required) | Instance ID (`tmux_0`, `pts-5`) |
| `project_id` | TEXT | (required) | Bound project UUID |
| `project_name` | TEXT | NULL | Cached project name |
| `bound_at` | REAL | (required) | Unix timestamp of binding |
| `bound_by` | TEXT | NULL | AI ID that created binding |
| `notes` | TEXT | NULL | Binding notes |

**Indexes:**
- `idx_instance_bindings_project` — Query by project

---

## CLI Commands

```bash
# List all projects in workspace
empirica workspace-list

# Overview with stats
empirica workspace-overview

# Project dependency map
empirica workspace-map

# Initialize workspace (creates database)
empirica workspace-init
```

---

## Query Examples

```sql
-- Get all active projects sorted by recent activity
SELECT name, trajectory_path, last_transaction_timestamp
FROM global_projects
WHERE status = 'active'
ORDER BY last_transaction_timestamp DESC;

-- Find projects with many dead-ends (potential learning opportunities)
SELECT name, total_dead_ends, total_findings
FROM global_projects
WHERE total_dead_ends > 5
ORDER BY total_dead_ends DESC;

-- Get cross-project patterns in a domain
SELECT pattern_description, occurrence_count, confidence
FROM trajectory_patterns
WHERE domain = 'authentication'
ORDER BY confidence DESC;

-- Find linked projects
SELECT gp.name, tl.link_type, tl.relevance
FROM trajectory_links tl
JOIN global_projects gp ON tl.target_project_id = gp.id
WHERE tl.source_project_id = '<your-project-id>';
```

---

## Related Documentation

- [Instance Isolation](../architecture/INSTANCE_ISOLATION.md) — How instances bind to projects
- [Database Schema (Project-Level)](./DATABASE_SCHEMA_UNIFIED.md) — Per-project sessions.db
- [Project Switching](../guides/PROJECT_SWITCHING_FOR_AIS.md) — How projects are selected
