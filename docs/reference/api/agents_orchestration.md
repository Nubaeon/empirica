# Agents Orchestration API Reference

**Version:** 1.5.0
**Purpose:** Parallel investigation agents with epistemic budget allocation

---

## Overview

Empirica's agent system enables **parallel epistemic investigation** by spawning child agents that:

- Investigate specific domains (security, performance, architecture)
- Operate with allocated attention budgets
- Report findings back to parent session
- Use personas for specialized expertise

---

## Commands

### `agent-spawn`

Spawn a child investigation agent.

```bash
empirica agent-spawn \
  --session-id <parent-session-id> \
  --task "Investigate authentication security" \
  --persona security-analyst \
  --context "Focus on JWT implementation"
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--session-id` | Yes | - | Parent session ID |
| `--task` | Yes | - | Investigation task description |
| `--persona` | No | - | Persona ID to use |
| `--turtle` | No | `false` | Auto-select best emerged persona |
| `--context` | No | - | Additional context from parent |
| `--output` | No | `text` | Output format: `text` or `json` |

**Output (JSON):**
```json
{
  "ok": true,
  "branch_id": "abc123-branch",
  "child_session_id": "def456...",
  "persona": "security-analyst",
  "task": "Investigate authentication security",
  "parent_session_id": "parent-id",
  "allocated_budget": 5
}
```

**Use case:** Spawn specialized agents for different investigation domains while maintaining parent session context.

---

### `agent-parallel`

Spawn multiple parallel investigation agents with automatic budget allocation.

```bash
empirica agent-parallel \
  --session-id <parent-session-id> \
  --task "Investigate system architecture" \
  --budget 20 \
  --max-agents 5 \
  --strategy information_gain \
  --domains security performance architecture
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--session-id` | Yes | - | Parent session ID |
| `--task` | Yes | - | Investigation task |
| `--budget` | No | `20` | Total findings budget |
| `--max-agents` | No | `5` | Maximum parallel agents |
| `--strategy` | No | `information_gain` | Budget allocation strategy |
| `--domains` | No | auto | Override investigation domains |
| `--output` | No | `text` | Output format |

**Strategies:**

| Strategy | Description |
|----------|-------------|
| `information_gain` | Allocate based on Shannon information gain (diminishing returns) |
| `uniform` | Equal allocation across domains |
| `priority` | Allocate based on domain priority |

**Output (JSON):**
```json
{
  "ok": true,
  "parent_session_id": "abc123...",
  "agents": [
    {
      "branch_id": "security-branch",
      "domain": "security",
      "budget": 8,
      "expected_gain": 0.72
    },
    {
      "branch_id": "perf-branch",
      "domain": "performance",
      "budget": 7,
      "expected_gain": 0.65
    },
    {
      "branch_id": "arch-branch",
      "domain": "architecture",
      "budget": 5,
      "expected_gain": 0.58
    }
  ],
  "total_budget": 20,
  "strategy": "information_gain"
}
```

---

### `agent-report`

Submit agent findings back to parent session.

```bash
# Report with postflight
empirica agent-report \
  --branch-id <branch-id> \
  --postflight '{"vectors": {"know": 0.85}, "findings": [...]}'

# Report from stdin
empirica agent-report --branch-id <branch-id> --postflight -
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--branch-id` | Yes | - | Branch ID from agent-spawn |
| `--postflight` | No | - | Postflight JSON or `-` for stdin |
| `--output` | No | `text` | Output format |

**Postflight Schema:**
```json
{
  "vectors": {
    "know": 0.85,
    "uncertainty": 0.15,
    "completion": 1.0
  },
  "findings": [
    {"finding": "JWT uses RS256", "impact": 0.8},
    {"finding": "Refresh tokens in Redis", "impact": 0.7}
  ],
  "unknowns": [
    {"unknown": "Token rotation policy?"}
  ],
  "dead_ends": [
    {"approach": "File-based tokens", "why_failed": "No cluster support"}
  ]
}
```

---

### `agent-aggregate`

Aggregate findings from all child agents in a session.

```bash
empirica agent-aggregate \
  --session-id <parent-session-id> \
  --round 1
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--session-id` | Yes | - | Parent session ID |
| `--round` | No | - | Investigation round (filters by round) |
| `--output` | No | `text` | Output format |

**Output (JSON):**
```json
{
  "ok": true,
  "session_id": "abc123...",
  "agents_completed": 3,
  "agents_pending": 0,
  "total_findings": 15,
  "total_unknowns": 5,
  "total_dead_ends": 2,
  "aggregated_vectors": {
    "know": 0.82,
    "uncertainty": 0.18
  },
  "findings_by_domain": {
    "security": 5,
    "performance": 6,
    "architecture": 4
  }
}
```

---

### `agent-export`

Export agent branch for sharing or persistence.

```bash
# Export to file
empirica agent-export \
  --branch-id <branch-id> \
  --output-file agent_security.json

# Export and register to sharing network
empirica agent-export \
  --branch-id <branch-id> \
  --register
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--branch-id` | Yes | - | Branch ID to export |
| `--output-file` | No | stdout | Output file path |
| `--register` | No | `false` | Register to Qdrant sharing network |
| `--output` | No | `text` | Output format |

**Export Format:**
```json
{
  "branch_id": "abc123-branch",
  "session_id": "def456...",
  "parent_session_id": "parent-id",
  "persona": "security-analyst",
  "task": "Investigate authentication",
  "findings": [...],
  "unknowns": [...],
  "dead_ends": [...],
  "vectors": {...},
  "exported_at": "2026-02-07T20:00:00Z"
}
```

---

### `agent-import`

Import agent branch into a session.

```bash
empirica agent-import \
  --session-id <target-session-id> \
  --input-file agent_security.json
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--session-id` | Yes | - | Session to import into |
| `--input-file` | Yes | - | Agent JSON file path |
| `--output` | No | `text` | Output format |

---

### `agent-discover`

Discover agents from the sharing network (Qdrant).

```bash
empirica agent-discover \
  --query "security authentication" \
  --limit 5
```

---

## Workflow Example

```bash
# 1. Create parent session
session_id=$(empirica session-create --ai-id claude-code --output json | jq -r .session_id)

# 2. Submit PREFLIGHT
empirica preflight-submit - << EOF
{"session_id": "$session_id", "task_description": "Security audit", "vectors": {"know": 0.5}}
EOF

# 3. Spawn parallel agents with budget allocation
empirica agent-parallel \
  --session-id $session_id \
  --task "Comprehensive security audit" \
  --budget 30 \
  --strategy information_gain

# 4. (Agents investigate and report back)

# 5. Aggregate all findings
empirica agent-aggregate --session-id $session_id

# 6. Rollup findings with deduplication
empirica session-rollup --parent-session-id $session_id --semantic-dedup

# 7. Submit POSTFLIGHT
empirica postflight-submit - << EOF
{"session_id": "$session_id", "vectors": {"know": 0.88}, "summary": "Security audit complete"}
EOF
```

---

## Python API

```python
from empirica.core.parallel_orchestrator import ParallelOrchestrator
from empirica.core.attention_budget import AttentionBudgetCalculator

# Create orchestrator
orchestrator = ParallelOrchestrator(session_id=parent_session_id)

# Allocate budget
calculator = AttentionBudgetCalculator(session_id=parent_session_id)
budget = calculator.create_budget(
    domains=['security', 'performance', 'architecture'],
    current_vectors={'know': 0.5, 'uncertainty': 0.5},
    total_budget=20
)

# Spawn agents
agents = orchestrator.spawn_parallel(
    task="Investigate system",
    budget=budget,
    max_agents=5
)

# Wait for completion and aggregate
results = orchestrator.aggregate_results()
```

---

## Integration with Memory Management

Agent orchestration integrates with memory commands:

- `memory-prime` — Allocate attention budget before spawning
- `session-rollup` — Aggregate and deduplicate agent findings
- `pattern-check` — Check agent approaches against dead-ends

See [MEMORY_MANAGEMENT_COMMANDS.md](../MEMORY_MANAGEMENT_COMMANDS.md) for details.

---

## Related Documentation

- [MEMORY_MANAGEMENT_COMMANDS.md](../MEMORY_MANAGEMENT_COMMANDS.md) — Budget allocation
- [PERSONA_PROFILE.md](../PERSONA_PROFILE.md) — Agent personas
- [MULTI_SESSION_LEARNING.md](../../human/developers/MULTI_SESSION_LEARNING.md) — Session coordination
