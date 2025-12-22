# Empirica Database Schema

**Total Tables:** 30  
**Database Type:** SQLite (with PostgreSQL adapter support)  
**Architecture:** Modular with dual goal/subtask systems

---

## Table Categories

### 1. Core Session Management (4 tables)
- **sessions** - AI sessions with metadata (ai_id, project_id, timestamps)
- **cascades** - Reasoning cascade executions (task, context, goal tracking)
- **reflexes** - Epistemic checkpoints (PREFLIGHT, CHECK, POSTFLIGHT)
- **cascade_metadata** - CASCADE workflow metadata

**Relationships:**
```
sessions (1) ──> (N) cascades
sessions (1) ──> (N) reflexes
cascades (1) ──> (N) cascade_metadata
```

### 2. Epistemic Tracking (5 tables)
- **epistemic_snapshots** - Point-in-time epistemic state captures
- **divergence_tracking** - Delegate vs trustee alignment tracking
- **drift_monitoring** - Long-term behavioral pattern tracking  
- **bayesian_beliefs** - Evidence-based belief evolution
- **epistemic_sources** - Source attribution (docs, URLs, code)

**Relationships:**
```
sessions (1) ──> (N) epistemic_snapshots
cascades (1) ──> (N) bayesian_beliefs
sessions (1) ──> (N) epistemic_sources
```

### 3. OLD Goal/Subtask System (2 tables)
**From SessionDatabase - Legacy system**
- **goals** - Session goals (objective, status, timestamps)
- **subtasks** - Work items (goal_id FK, description, status)

**Relationships:**
```
sessions (1) ──> (N) goals [old]
goals [old] (1) ──> (N) subtasks [old]
```

### 4. NEW Goal/Task System (5 tables)
**From core.goals & core.tasks repositories - Modern system**
- **goals** (new schema) - Goals with success criteria
- **success_criteria** - Validation rules for goals
- **goal_dependencies** - Goal dependency graph
- **subtasks** (new schema) - Enhanced task tracking
- **subtask_dependencies** - Subtask dependency graph
- **task_decompositions** - Task breakdown strategies

**Relationships:**
```
goals [new] (1) ──> (N) success_criteria
goals [new] (1) ──> (N) goal_dependencies
goals [new] (1) ──> (N) subtasks [new]
subtasks [new] (1) ──> (N) subtask_dependencies
goals [new] (1) ──> (1) task_decompositions
```

**⚠️ DUAL SYSTEM ALERT:**
The database has TWO goal/subtask implementations:
1. **OLD**: data.repositories.GoalRepository (used by SessionDatabase)
2. **NEW**: core.goals.repository.GoalRepository (used by facade methods)

Both write to the same database but with different schemas!

### 5. Project Management (9 tables)
- **projects** - Multi-session projects (name, description, repos)
- **project_handoffs** - AI-to-AI handoffs within project
- **handoff_reports** - Handoff metadata
- **project_findings** - Cross-session discoveries
- **project_unknowns** - Unresolved questions  
- **project_dead_ends** - Failed approaches
- **project_reference_docs** - Documentation links
- **mistakes_made** - Error tracking with root cause analysis
- **token_savings** - Git notes compression metrics

**Relationships:**
```
projects (1) ──> (N) sessions
projects (1) ──> (N) project_handoffs
projects (1) ──> (N) project_findings
projects (1) ──> (N) project_unknowns
projects (1) ──> (N) project_dead_ends
projects (1) ──> (N) project_reference_docs
projects (1) ──> (N) handoff_reports
sessions (1) ──> (N) mistakes_made
```

### 6. Investigation Tools (4 tables)
- **investigation_tools** - Tool usage tracking
- **investigation_logs** - Investigation event logs
- **act_logs** - Action logging with confidence scores
- **investigation_branches** - Multi-branch investigations
- **merge_decisions** - Branch merge outcomes

**Relationships:**
```
sessions (1) ──> (N) investigation_tools
sessions (1) ──> (N) investigation_logs
sessions (1) ──> (N) act_logs
sessions (1) ──> (N) investigation_branches
investigation_branches (1) ──> (N) merge_decisions
```

### 7. System Tables (1 table)
- **sqlite_sequence** - Auto-increment tracking (SQLite internal)

---

## Key Foreign Key Relationships

```
                    ┌─────────────┐
                    │  projects   │
                    └──────┬──────┘
                           │
                           │ (1:N)
                           │
                    ┌──────▼──────┐
                    │  sessions   │───────┐
                    └──────┬──────┘       │
                           │              │
              ┌────────────┼──────────┐   │
              │            │          │   │
         (1:N)│       (1:N)│     (1:N)│   │(1:N)
              │            │          │   │
       ┌──────▼───┐  ┌────▼────┐  ┌─▼───▼───┐
       │ cascades │  │ reflexes│  │  goals   │
       └──────┬───┘  └─────────┘  └─────┬────┘
              │                          │
         (1:N)│                     (1:N)│
              │                          │
    ┌─────────▼────────┐          ┌──────▼──────┐
    │ bayesian_beliefs │          │  subtasks   │
    └──────────────────┘          └─────────────┘
```

---

## Table Statistics

| Table | Estimated Purpose | Peak Usage |
|-------|------------------|------------|
| sessions | 100s | Long-term storage |
| cascades | 1000s | Per CASCADE run |
| reflexes | 1000s | 3 per CASCADE (PF/CH/PO) |
| goals | 10s | Few per session |
| subtasks | 100s | Many per goal |
| project_findings | 100s | Accumulates over time |
| epistemic_snapshots | 100s | Periodic captures |

---

## Access Patterns

**SessionDatabase** (main facade):
- Direct SQL for sessions, cascades, reflexes
- data.repositories.GoalRepository for old goals/subtasks
- Lazy-loaded core.goals/tasks for new system

**Facade Methods** (added today):
- `query_goals()` → core.goals.repository
- `query_subtasks()` → core.tasks.repository
- `get_goal_subtasks()` → core.tasks.repository
- `query_goal_progress()` → core.tasks.repository

---

## Migration Notes

**Dual Goal System Issue:**
- Old system: SessionDatabase → data.repositories.GoalRepository
- New system: core.goals.repository.GoalRepository + core.tasks.repository.TaskRepository
- Both coexist in same database with different schemas!
- Eventually need to consolidate or clearly separate

**Storage Locations:**
- Project-local: `./.empirica/sessions/sessions.db`
- Global config: `~/.empirica/config.yaml`
- Git notes: Compressed checkpoints (~97.5% token reduction)

---

Generated: 2025-12-21
