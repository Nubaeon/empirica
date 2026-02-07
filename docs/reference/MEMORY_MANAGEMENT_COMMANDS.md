# Memory Management Commands Reference

**Version:** 1.5.0
**Purpose:** Epistemic memory management for parallel agents and context optimization

---

## Overview

Empirica provides a suite of memory management commands that expose the underlying attention budget, context management, and information gain infrastructure. These commands enable:

- **Attention allocation** across investigation domains
- **Zone-based retrieval** (anchor/working/cache)
- **Information gain optimization** for token-efficient retrieval
- **Pattern checking** against known dead-ends and mistakes
- **Parallel agent aggregation** with deduplication
- **Context budget monitoring** (like `/proc/meminfo`)

---

## Commands

### `memory-prime`

Allocate attention budget across multiple investigation domains.

**Purpose:** Uses Shannon information gain with diminishing returns to distribute investigation budget across domains. Essential for parallel agent coordination.

```bash
empirica memory-prime \
  --session-id <ID> \
  --domains '["security", "performance", "architecture"]' \
  --budget 20 \
  --know 0.5 \
  --uncertainty 0.5 \
  --prior-findings '{"security": 3}' \
  --dead-ends '{"architecture": 1}' \
  --persist
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--session-id` | Yes | - | Session ID for budget tracking |
| `--domains` | Yes | - | JSON array of domain names |
| `--budget` | No | `20` | Total findings budget to allocate |
| `--know` | No | `0.5` | Current know vector (0.0-1.0) |
| `--uncertainty` | No | `0.5` | Current uncertainty vector (0.0-1.0) |
| `--prior-findings` | No | `{}` | JSON object of prior findings per domain |
| `--dead-ends` | No | `{}` | JSON object of dead ends per domain |
| `--persist` | No | `false` | Persist budget to database |
| `--output` | No | `human` | Output format: `human` or `json` |

**Output (human):**
```
🎯 Attention Budget Allocated (total: 20)
============================================================
  security             [████████░░░░░░░░░░░░░░░░░░░░░░]  5 (gain: 0.72)
  performance          [██████████████░░░░░░░░░░░░░░░░]  9 (gain: 0.85)
  architecture         [██████░░░░░░░░░░░░░░░░░░░░░░░░]  6 (gain: 0.68)
============================================================
Budget ID: abc123...
✓ Persisted to database
```

**Use case:** Before spawning parallel investigation agents, allocate attention budget so each agent knows how many findings to target in their domain.

---

### `memory-scope`

Retrieve memories by scope using the three-zone tier system.

**Purpose:** Access memories organized in ANCHOR (permanent), WORKING (active), and CACHE (evictable) zones based on scope vectors.

```bash
empirica memory-scope \
  --session-id <ID> \
  --scope-breadth 0.7 \
  --scope-duration 0.5 \
  --zone working \
  --content-type finding \
  --min-priority 0.3
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--session-id` | Yes | - | Session ID for context management |
| `--scope-breadth` | No | `0.5` | Scope breadth (0=narrow, 1=wide) |
| `--scope-duration` | No | `0.5` | Scope duration (0=ephemeral, 1=long-term) |
| `--zone` | No | `all` | Zone filter: `anchor`, `working`, `cache`, `all` |
| `--content-type` | No | - | Filter by type: `finding`, `unknown`, `goal`, etc. |
| `--min-priority` | No | `0.0` | Minimum priority score to include |
| `--output` | No | `human` | Output format: `human` or `json` |

**Zone descriptions:**

| Zone | Icon | Purpose | Eviction |
|------|------|---------|----------|
| ANCHOR | ⚓ | Permanent context (goals, constraints) | Never |
| WORKING | ⚙️ | Active task context | When scope changes |
| CACHE | 💾 | Recently used, may be needed | Under memory pressure |

**Output (human):**
```
📦 Memory Scope Query (scope: breadth=0.7, duration=0.5)
======================================================================
  ⚙️ JWT auth uses RS256 signing                                  120t  p=0.85
  ⚙️ Refresh tokens stored in Redis with 30-day TTL               95t  p=0.78
  ⚓ Primary goal: Implement authentication                        45t  p=0.92
======================================================================
```

---

### `memory-value`

Retrieve memories ranked by information gain per token.

**Purpose:** Optimize context loading by prioritizing memories with highest novelty and expected information gain relative to their token cost.

```bash
empirica memory-value \
  --session-id <ID> \
  --query "authentication patterns" \
  --budget 5000 \
  --min-gain 0.1 \
  --include-eidetic \
  --include-episodic
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--session-id` | Yes | - | Session ID |
| `--query` | Yes | - | Query text to match against memories |
| `--budget` | No | `5000` | Token budget for retrieval |
| `--project-id` | No | auto | Project ID (auto-detected) |
| `--min-gain` | No | `0.1` | Minimum information gain to include |
| `--include-eidetic` | No | `false` | Include eidetic (fact) memory |
| `--include-episodic` | No | `false` | Include episodic (narrative) memory |
| `--output` | No | `human` | Output format: `human` or `json` |

**Output (human):**
```
💎 Memory Value Retrieval (budget: 5000 tokens)
======================================================================
Selected 12 items using 4,832 tokens
----------------------------------------------------------------------
  📝 [ 120t] v=8.42 | JWT RS256 provides stronger security than HS256...
  📝 [  95t] v=7.15 | Refresh tokens use sliding window expiration...
  ❓ [  45t] v=6.88 | How are revoked tokens handled across regions?...
======================================================================
```

**Use case:** When context is limited, retrieve highest-value memories first. The value score is `(gain × novelty) / tokens × 1000`.

---

### `pattern-check`

Real-time pattern sentinel checking against known dead-ends and mistakes.

**Purpose:** Before implementing an approach, check if it matches known dead-ends or mistake patterns. Lightweight enough to call frequently during work.

```bash
empirica pattern-check \
  --session-id <ID> \
  --approach "Use Redis for session storage" \
  --know 0.6 \
  --uncertainty 0.4 \
  --threshold 0.7
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--session-id` | Yes | - | Session ID |
| `--approach` | Yes | - | Description of current approach to validate |
| `--project-id` | No | auto | Project ID (auto-detected) |
| `--know` | No | `0.5` | Current know vector (for risk calculation) |
| `--uncertainty` | No | `0.5` | Current uncertainty vector (for risk calculation) |
| `--threshold` | No | `0.7` | Similarity threshold for pattern matching |
| `--output` | No | `human` | Output format: `human` or `json` |

**Output (human - low risk):**
```
✅ Pattern Check: LOW
============================================================
Approach: Use Redis for session storage...
------------------------------------------------------------
✅ No concerning patterns detected. Proceed with confidence.
============================================================
```

**Output (human - high risk):**
```
🛑 Pattern Check: HIGH
============================================================
Approach: Use file-based caching for user sessions...
------------------------------------------------------------
☠️ Dead-end matches:
   • File-based session storage doesn't scale...
     Why failed: Race conditions under load, no cluster support...
⚠️ Mistake risk: 65%
   High uncertainty + low know is a historical mistake pattern
============================================================
```

**Use case:** Critical for avoiding repeated mistakes. Call before committing to an implementation approach.

---

### `session-rollup`

Aggregate findings from parallel child sessions into a parent session.

**Purpose:** When spawning multiple investigation agents, use rollup to deduplicate, score, and gate their findings back into the parent session.

```bash
empirica session-rollup \
  --parent-session-id <ID> \
  --budget 20 \
  --min-score 0.3 \
  --jaccard-threshold 0.7 \
  --semantic-dedup \
  --log-decisions
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--parent-session-id` | Yes | - | Parent session ID to aggregate children for |
| `--budget` | No | `20` | Max findings to accept |
| `--min-score` | No | `0.3` | Minimum quality score to accept finding |
| `--jaccard-threshold` | No | `0.7` | Jaccard similarity threshold for dedup |
| `--semantic-dedup` | No | `false` | Use Qdrant semantic dedup in addition to Jaccard |
| `--project-id` | No | auto | Project ID for semantic dedup (auto-detected) |
| `--log-decisions` | No | `false` | Log accept/reject decisions to database |
| `--output` | No | `human` | Output format: `human` or `json` |

**Output (human):**
```
🔄 Session Rollup: abc123...
======================================================================
Child sessions: 3
Total findings: 45 → Deduped: 28 → Accepted: 18
Acceptance rate: 64%
----------------------------------------------------------------------
✅ Accepted findings:
   [security-agent] JWT validation should use RS256... (score: 0.92)
   [perf-agent] Connection pooling reduces latency by 40%... (score: 0.88)
   [arch-agent] Event-driven design simplifies scaling... (score: 0.85)
   ... and 15 more
❌ Rejected: 10 findings
======================================================================
```

**Use case:** After parallel agents complete their investigation, rollup consolidates their findings with deduplication and quality filtering.

---

### `memory-report`

Get context budget report (like `/proc/meminfo` for AI context).

**Purpose:** Monitor memory pressure, zone utilization, and eviction candidates.

```bash
empirica memory-report --session-id <ID>
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--session-id` | Yes | - | Session ID |
| `--output` | No | `human` | Output format: `human` or `json` |

**Output (human):**
```
📊 Context Budget Report
============================================================
Total: [████████████████████████████░░░░░░░░░░░░░░░░░░░░░░] 56%
       28,450 / 50,000 tokens
------------------------------------------------------------
⚓ ANCHOR   [████████████████░░░░] 5,200/8,000t (12 items)
⚙️ WORKING  [██████████████████░░] 18,500/20,000t (45 items)
💾 CACHE    [██████░░░░░░░░░░░░░░] 4,750/22,000t (23 items)
------------------------------------------------------------
============================================================
```

**Output (under pressure):**
```
📊 Context Budget Report
============================================================
Total: [██████████████████████████████████████████████████] 94%
       47,000 / 50,000 tokens
------------------------------------------------------------
⚓ ANCHOR   [████████████████████] 8,000/8,000t (18 items)
⚙️ WORKING  [████████████████████] 20,000/20,000t (52 items)
💾 CACHE    [██████████████████░░] 19,000/22,000t (41 items)
------------------------------------------------------------
⚠️ MEMORY PRESSURE DETECTED
🗑️ Eviction candidates: 15
============================================================
```

---

## Workflow Examples

### Parallel Investigation with Budget Allocation

```bash
# 1. Allocate budget across domains
empirica memory-prime \
  --session-id $PARENT_ID \
  --domains '["security", "performance", "architecture"]' \
  --budget 30 \
  --persist

# 2. Spawn child agents (each investigates their domain)
# (agents use their allocated budget)

# 3. Rollup findings from children
empirica session-rollup \
  --parent-session-id $PARENT_ID \
  --semantic-dedup \
  --log-decisions
```

### Context-Aware Retrieval

```bash
# Check current memory state
empirica memory-report --session-id $ID

# Retrieve high-value memories within budget
empirica memory-value \
  --session-id $ID \
  --query "authentication patterns" \
  --budget 3000 \
  --min-gain 0.2
```

### Pre-Implementation Pattern Check

```bash
# Before implementing, check for dead-ends
empirica pattern-check \
  --session-id $ID \
  --approach "Implement caching with Redis Cluster" \
  --know 0.7 \
  --uncertainty 0.3

# If LOW risk, proceed. If HIGH risk, investigate alternatives.
```

---

## Related Documentation

- [Attention Budget Architecture](../architecture/ATTENTION_BUDGET.md) — Technical details
- [Multi-Session Learning](../human/developers/MULTI_SESSION_LEARNING.md) — Session coordination
- [Environment Variables](./ENVIRONMENT_VARIABLES.md) — Configuration options
