---
name: empirica-meta
description: Meta-cognitive skill for improving Empirica using Empirica's own framework
globs:
  - "empirica/**/*.py"
  - "docs/architecture/**/*.md"
  - ".empirica/**/*"
  - "project_skills/**/*.yaml"
alwaysAllow:
  - Bash(empirica:*)
  - Read
  - Grep
  - Glob
---

# Empirica Meta-Agent Skill

## Philosophy

> "Same epistemic rules apply at every meta-layer."

This skill enables recursive self-improvement of Empirica using Empirica's own epistemic framework. When working on Empirica itself, apply the full CASCADE workflow.

## When to Use

Activate when:
- Fixing bugs in Empirica CLI or core
- Adding new features to the epistemic framework
- Reviewing/updating architecture documentation
- Investigating why workflows aren't working
- Proposing system improvements

## Workflow

### 1. PREFLIGHT - Assess Current Understanding

Before modifying Empirica, assess what you know about the specific area.
Use vectors: know, uncertainty, context, engagement.

### 2. NOETIC - Investigate Before Acting

- Read relevant architecture docs first
- Search for similar past changes via project-search
- Check for unknowns that might be related
- Log findings as you discover them

### 3. CHECK - Gate Before Implementation

Run CHECK to verify you're ready to modify the system.
Gate: know >= 0.70 AND uncertainty <= 0.35 (after bias correction)

### 4. PRAXIC - Implement with Care

- Follow self-improvement protocol from CLAUDE.md
- Prefer minimal edits
- Never modify core safety constraints
- Log high-impact findings (0.8+)

### 5. POSTFLIGHT - Measure Learning

- What did I learn about Empirica's architecture?
- Did the change work as expected?
- Are there follow-up improvements?

## Key Files

| Area | Files |
|------|-------|
| CLI Commands | empirica/cli/command_handlers/*.py |
| Core Logic | empirica/core/*.py |
| Sentinel | empirica/core/sentinel/*.py |
| Qdrant | empirica/core/qdrant/*.py |
| Database | empirica/data/*.py |
| Personas | empirica/core/persona/*.py, .empirica/personas/*.json |
| Emerged Personas | empirica/core/emerged_personas.py |
| Architecture Docs | docs/architecture/*.md |
| System Prompt | ~/.claude/CLAUDE.md |

## Self-Improvement Protocol

1. **Identify** - Recognize gaps through noetic investigation
2. **Validate** - Test the improvement before proposing
3. **Propose** - Tell user what you found and suggested fix
4. **Implement** - If approved, make minimal precise edits
5. **Log** - Record as finding with impact 0.8+

## Turtle Stack

Layer 4: Meta-Orchestrator (future)
Layer 3: Sentinel - aggregate, arbitrate, merge
Layer 2: Epistemic Agent - spawn, investigate, report
Layer 1: CASCADE Workflow - PREFLIGHT/CHECK/POSTFLIGHT
Layer 0: Breadcrumb Trail - findings, unknowns, dead ends

Each layer uses same 13 vectors. This skill operates at Layer 2-3.

## Gotchas

- Always read before editing (even for Empirica code)
- The system prompt is in ~/.claude/CLAUDE.md (global)
- Skill files go in .claude/skills/ (project)
- Condensed skills go in project_skills/ (for bootstrap)
- Check unknowns before logging new ones
- Commit after each goal (prevent drift)
- Sentinel is now wired via MCP (EMPIRICA_EPISTEMIC_MODE=true)
- PreToolCall hooks gate Edit/Write/Bash via CHECK

## References

- empirica --help - Full CLI reference
- docs/architecture/separation-of-concerns.md - What goes where
- docs/architecture/EPISTEMIC_AGENT_ARCHITECTURE.md - Turtle stack
- docs/architecture/QDRANT_EPISTEMIC_INTEGRATION.md - Semantic search
