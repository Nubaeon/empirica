# 🧠 Empirica Natural Language Guide

**How to use Empirica naturally - Human language that maps to Empirica workflows**

This guide translates natural human language patterns into Empirica's epistemic workflow, making it intuitive to use for project management, research, and AI-first development.

---

## 🏗️ Working with Claude: Transaction Architecture

When working with Claude (or any AI) using Empirica, the key insight is that **work happens in measured chunks called transactions**. Understanding this architecture helps you collaborate more effectively.

### What is a Transaction?

A transaction is a measurement window: `PREFLIGHT → work → POSTFLIGHT`

- **PREFLIGHT** declares what you're about to do and your starting state
- **Work** happens (investigation + action)
- **POSTFLIGHT** captures what you learned and accomplished

The system compares these to measure learning delta and ground calibration against objective evidence.

### The Noetic-Praxic Flow

Within each transaction, Claude naturally moves through two phases:

```
┌─────────────────────────────────────────────────────────────────┐
│                      ONE TRANSACTION                             │
│                                                                  │
│  PREFLIGHT ──► NOETIC ──► CHECK ──► PRAXIC ──► POSTFLIGHT       │
│      │          │          │         │            │              │
│   Baseline   Investigate   Gate    Implement   Measure          │
│   Assessment  & Learn    Decision  & Build    Learning          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Noetic phase:** Reading, searching, exploring, logging findings/unknowns
**CHECK gate:** "Do I understand enough to act?"
**Praxic phase:** Writing code, making changes, completing goals

Both phases happen **within the same transaction**. CHECK is a gate, not a boundary.

### Scoping Transactions

**Human language:**
> "I want to implement user authentication with OAuth2"

**Claude's decomposition:**
This is too big for one transaction. Claude will naturally break it down:

1. **Transaction 1:** Research OAuth2 patterns, understand PKCE, log findings
2. **Transaction 2:** Implement auth endpoints, write tests
3. **Transaction 3:** Add token refresh, handle edge cases

Each transaction has coherent scope - investigation + action on one aspect.

### Spec-Driven Goal Decomposition

For complex work, start with a spec. Claude can decompose it into goals:

**Human language:**
> "Here's the spec for our new feature. Can you break this into goals and work through them?"

**What happens:**
1. Claude reads the spec
2. Creates goals for each major component
3. Works through goals across multiple transactions
4. Each transaction picks up one goal (or related subset)
5. Artifacts (findings, unknowns) persist in memory across transactions

```
Spec Document
    │
    ▼
┌─────────────────────────────────────────┐
│  Goal A: Design auth flow               │
│  Goal B: Implement endpoints            │
│  Goal C: Add tests                      │
│  Goal D: Write documentation            │
└─────────────────────────────────────────┘
    │
    ▼
Transaction 1: Goal A (noetic → praxic)
Transaction 2: Goal B (informed by T1's findings)
Transaction 3: Goal C + D (related, can combine)
```

### Transaction Scoping Guidelines

| Scope | Example | Transactions |
|-------|---------|--------------|
| Small fix | Bug fix, config change | 1 transaction |
| Feature | Schema + endpoints + tests | 2-3 transactions |
| Architecture | Cross-cutting redesign | 3-5 transactions |

**Signs you need a new transaction:**
- Scope grew beyond what PREFLIGHT declared
- Confidence inflected (know jumped or uncertainty spiked)
- Switching domains or approaches
- Completed a coherent chunk (tests pass, code committed)

---

## 🤖 Earned Autonomy: How Claude Picks Tools

Claude doesn't need to be told which Empirica commands to use. Given awareness of the available tools, Claude naturally selects the best fit for the work at hand.

### The Abstraction Principle

**Instead of:**
> "Run empirica preflight-submit, then empirica finding-log, then..."

**Just say:**
> "Investigate the authentication flow and implement the fix"

Claude will naturally:
1. Run PREFLIGHT to open a measurement window
2. Use noetic tools (Read, Grep, Glob) to investigate
3. Log findings and unknowns as discovered
4. Submit CHECK when ready to act
5. Use praxic tools (Edit, Write, Bash) to implement
6. Complete goals and run POSTFLIGHT

### Epistemic Agents for Complex Investigation

For multi-faceted problems, Claude can spawn epistemic agents in parallel:

**Human language:**
> "This bug could be in the auth layer, the database, or the API. Can you investigate all three?"

**What happens:**
Claude spawns parallel investigation agents:
- `agent-spawn security` → investigates auth layer
- `agent-spawn performance` → checks database queries
- `agent-spawn architecture` → reviews API structure

Results are consolidated, findings logged, and the noetic phase completes faster.

### Creating Reusable Personas (Agent-Spawn)

When Claude encounters novel problem domains, it can create new agent personas:

**Human language:**
> "We keep running into OAuth2 edge cases. Can you create an auth specialist agent?"

**What happens:**
Claude uses `agent-spawn` to create a reusable persona with:
- Domain expertise in OAuth2/OIDC patterns
- Specific investigation strategies
- Knowledge of common pitfalls

This persona persists and can be used in future work, providing better results for auth-related tasks.

### The Autonomy Gradient

Honest use of Empirica leads to **earned autonomy**:

```
Low Trust ────────────────────────────────────► High Trust
    │                                               │
    │  Sentinel gates every action                  │  Sentinel adapts thresholds
    │  Must justify each CHECK                      │  Streamlined workflows
    │  More investigation required                  │  Can proceed on confidence
    │                                               │
    └───────────────────────────────────────────────┘
                    Calibration improves
                    over honest transactions
```

**Key insight:** Gaming vectors degrades calibration. Honest self-assessment improves it. Better calibration → Sentinel trusts more → more autonomy.

---

## 🧩 Multi-Agent Collaboration Patterns

### Pattern 1: Parallel Investigation
```
Human: "Research this problem from multiple angles"

Claude spawns:
├── Agent A: Security perspective
├── Agent B: Performance perspective
└── Agent C: Architecture perspective

All run noetic phase in parallel
Results consolidate → single CHECK → proceed to praxic
```

### Pattern 2: Sequential Handoff
```
Transaction 1: Agent A investigates
    └── Logs findings, unknowns
    └── POSTFLIGHT captures state

Transaction 2: Agent B picks up
    └── Retrieves Agent A's artifacts
    └── Continues from where A stopped
```

### Pattern 3: Specialist Delegation
```
Human: "Fix this auth bug"

Claude recognizes auth domain:
    └── Spawns auth-specialist agent (reusable persona)
    └── Specialist runs full noetic-praxic cycle
    └── Results flow back to main transaction
```

---

## 💬 Collaborative Problem Solving

For complex collaborative work, structure your requests to enable Claude's full toolkit:

### Good Patterns

**Spec-first:**
> "Here's our feature spec. Break it into goals, then work through each with proper investigation before implementing."

**Multi-angle investigation:**
> "This is a complex bug. Investigate from security, performance, and architecture angles before proposing a fix."

**Measured iteration:**
> "Implement this feature in transactions. After each transaction, tell me what you learned and what's next."

### What Claude Does Automatically

Given these patterns, Claude will naturally:

| When Claude sees... | Claude does... |
|---------------------|----------------|
| Complex task | Creates goals, decomposes into transactions |
| Ambiguity | Logs unknowns, investigates before acting |
| Discovery | Logs findings immediately |
| Failed approach | Logs dead-end to prevent re-exploration |
| Decision point | Runs CHECK to assess readiness |
| Coherent completion | Runs POSTFLIGHT, measures learning |
| Multi-faceted problem | Spawns parallel investigation agents |
| Recurring domain | Creates/uses specialist persona |

### The Human's Role

Your job is to:
1. **Provide specs** for complex work (Claude decomposes)
2. **Describe the outcome** you want (not the commands)
3. **Review transaction boundaries** (approve POSTFLIGHT timing)
4. **Provide feedback** on calibration (help Claude learn)

Claude handles the rest - tool selection, artifact logging, transaction management.

---

## 🗣️ Natural Language Patterns for Empirica

### 1. Starting a Project

**Human Language:**
> "I want to start working on a new AI research project about cognitive architectures"
> "Let me begin a new project for the Empirica v2.0 release"
> "I need to create a workspace for my machine learning experiments"

**Empirica Translation:**
```bash
# Create a session for your project
empirica session-create --ai-id "research-ai" --project-name "cognitive-architectures"

# Bootstrap to get started
empirica project-bootstrap --session-id <your-session-id>
```

**Key Concept:** Every project starts with a session that tracks your epistemic state.

---

### 2. Setting Goals

**Human Language:**
> "My goal is to implement the new CASCADE workflow by Friday"
> "I want to research token efficiency patterns this week"
> "I need to fix the database migration issues before the release"

**Empirica Translation:**
```bash
# Create a goal with natural language
empirica goals-create --session-id <session-id> --objective "Implement CASCADE workflow v2.0"

# Break it down into subtasks
echo '{"session_id": "<session-id>", "description": "Design the PREFLIGHT phase", "importance": "high"}' | empirica goals-add-subtask -
echo '{"session_id": "<session-id>", "description": "Implement CHECK gates", "importance": "high"}' | empirica goals-add-subtask -
echo '{"session_id": "<session-id>", "description": "Create POSTFLIGHT metrics", "importance": "high"}' | empirica goals-add-subtask -
```

**Natural Language Tip:** Use clear, specific objectives that describe what you want to accomplish.

---

### 3. Assessing Your Knowledge (PREFLIGHT)

**Human Language:**
> "I think I understand OAuth2 pretty well, but I'm not sure about the token refresh part"
> "I'm confident I can implement this feature, but I might need help with the database schema"
> "I'm completely new to this area - I'll need to do a lot of research"

**Empirica Translation:**
```bash
# Be honest about what you know
echo '{
  "session_id": "<session-id>",
  "vectors": {
    "engagement": 0.9,
    "know": 0.7,
    "do": 0.8,
    "context": 0.6,
    "uncertainty": 0.3
  },
  "reasoning": "I understand OAuth2 basics well but need to research token refresh patterns and database integration."
}' | empirica preflight-submit -
```

**Natural Language Mapping:**
- "I think I understand" → `know: 0.7`
- "I'm not sure about" → `uncertainty: 0.3`
- "I'm confident I can implement" → `do: 0.8`
- "I might need help with" → `context: 0.6`

---

### 4. Tracking What You Learn (Findings)

**Human Language:**
> "I discovered that OAuth2 requires PKCE for mobile apps"
> "I learned that the database uses a different schema than I expected"
> "I found the documentation for the API endpoints"

**Empirica Translation:**
```bash
# Log findings as you discover them
echo '{
  "project_id": "<project-id>",
  "session_id": "<session-id>",
  "finding": "OAuth2 requires PKCE for mobile applications",
  "impact": 0.9
}' | empirica finding-log -

echo '{
  "project_id": "<project-id>",
  "session_id": "<session-id>",
  "finding": "Database schema uses project_ prefix for all tables",
  "impact": 0.8
}' | empirica finding-log -
```

**Natural Language Tip:** Log findings immediately when you discover something new - don't wait until the end!

---

### 5. Identifying What You Don't Know (Unknowns)

**Human Language:**
> "I'm not sure how the token refresh mechanism works"
> "I don't understand the database migration process yet"
> "I need to figure out how to integrate with the existing API"

**Empirica Translation:**
```bash
# Track unknowns to guide your investigation
echo '{
  "project_id": "<project-id>",
  "session_id": "<session-id>",
  "unknown": "Token refresh mechanism implementation details",
  "impact": 0.8
}' | empirica unknown-log -

echo '{
  "project_id": "<project-id>",
  "session_id": "<session-id>",
  "unknown": "Database migration process for existing users",
  "impact": 0.7
}' | empirica unknown-log -
```

**Natural Language Tip:** Be specific about what you don't know - this helps focus your research.

---

### 6. Making Decisions (CHECK Gates)

**Human Language:**
> "I think I understand enough to implement this feature"
> "I'm still not sure about this approach - I should do more research"
> "I've learned enough to make a decision, but I want to double-check"

**Empirica Translation:**
```bash
# Use CHECK gates for decision points
echo '{
  "session_id": "<session-id>",
  "vectors": {"know": 0.75, "uncertainty": 0.25, "context": 0.8},
  "reasoning": "Understood OAuth2 token flow and refresh patterns, but still need to confirm lifetime config"
}' | empirica check-submit -
```

**Natural Language Mapping:**
- "I think I understand enough" → `confidence: 0.75`
- "I should do more research" → `confidence: 0.5`
- "I've learned enough" → `confidence: 0.8`

**Decision Logic:**
- `confidence >= 0.7` → Proceed with implementation
- `confidence < 0.7` → Investigate more

---

### 7. Measuring What You Learned (POSTFLIGHT)

**Human Language:**
> "I learned a lot about OAuth2 implementation patterns"
> "I'm much more confident about database migrations now"
> "I discovered several important considerations for the API design"

**Empirica Translation:**
```bash
# Measure your learning delta
echo '{
  "session_id": "<session-id>",
  "vectors": {
    "engagement": 0.9,
    "know": 0.85,
    "do": 0.9,
    "context": 0.8,
    "uncertainty": 0.15
  },
  "reasoning": "Successfully implemented OAuth2 with PKCE. Learned token refresh patterns, discovered rotation policy. Much more confident now."
}' | empirica postflight-submit -
```

**Natural Language Tip:** Compare your POSTFLIGHT with your PREFLIGHT to see your learning delta!

---

### 8. Switching Between Projects

**Human Language:**
> "I need to switch from the research project to the implementation project"
> "Let me pause this work and come back to it later"
> "I want to resume my work on the database migration project"

**Empirica Translation:**
```bash
# Save your current context
empirica session-snapshot --session-id <current-session-id>

# Switch to another project
empirica project-switch --project-id <new-project-id>

# Or resume a previous session
empirica sessions-resume --ai-id "your-ai-id"
```

**Natural Language Tip:** Use sessions to maintain context when switching between projects.

---

### 9. Managing Complex Workflows

**Human Language:**
> "I need to coordinate multiple AI agents on this project"
> "Let me check what work is ready to be done"
> "I want to see what other team members have discovered"

**Empirica Translation:**
```bash
# Check for ready work (epistemic + dependency filtering)
empirica goals-ready --session-id <session-id>

# See what others have discovered
empirica project-bootstrap --project-id <project-id> --depth auto

# Claim a task
empirica goals-claim --goal-id <goal-id>
```

**Natural Language Tip:** Use `goals-ready` to find work that matches your current capability.

---

### 10. AI-First Development Patterns

**Human Language:**
> "I need to implement this feature using AI-first principles"
> "Let me design this system with epistemic transparency"
> "I want to create a workflow that measures learning"

**Empirica Translation:**
```bash
# AI-First Implementation Pattern

# 1. Start with PREFLIGHT
echo '{"session_id": "<session-id>", "vectors": {"engagement": 0.9, "know": 0.6, "uncertainty": 0.4}, "reasoning": "Starting AI-first implementation"}' | empirica preflight-submit -

# 2. Do your work with CHECK gates as needed
# ... implementation ...

# 3. Measure learning with POSTFLIGHT
echo '{"session_id": "<session-id>", "vectors": {"engagement": 0.9, "know": 0.85, "uncertainty": 0.15}, "reasoning": "Completed AI-first implementation with measurable learning"}' | empirica postflight-submit -
```

**Natural Language Tip:** Always start with PREFLIGHT and end with POSTFLIGHT to measure your learning!

---

## 🎯 Natural Language Cheat Sheet

### Common Phrases → Empirica Commands

| Human Language | Empirica Command |
|----------------|-------------------|
| "I want to start a project" | `empirica session-create` |
| "Let me assess what I know" | `empirica preflight-submit` |
| "I discovered something new" | `empirica finding-log` |
| "I don't understand this yet" | `empirica unknown-log` |
| "I think I'm ready to proceed" | `empirica check` |
| "Let me see what I learned" | `empirica postflight-submit` |
| "I need to switch projects" | `empirica project-switch` |
| "What work is ready?" | `empirica goals-ready` |

### Knowledge Assessment Mapping

| Human Phrase | Epistemic Vector |
|--------------|------------------|
| "I understand this well" | `know: 0.8+` |
| "I'm somewhat familiar" | `know: 0.5-0.7` |
| "I'm new to this" | `know: 0.3-0.5` |
| "I'm completely unfamiliar" | `know: <0.3` |
| "I'm very confident" | `uncertainty: <0.2` |
| "I'm somewhat unsure" | `uncertainty: 0.3-0.5` |
| "I'm very uncertain" | `uncertainty: 0.6+` |

### Decision Confidence Mapping

| Human Phrase | Confidence Score |
|--------------|------------------|
| "I'm ready to implement" | `confidence: 0.8+` |
| "I think I understand enough" | `confidence: 0.7-0.8` |
| "I need to learn more" | `confidence: 0.5-0.7` |
| "I'm completely lost" | `confidence: <0.5` |

---

## 🧠 Cognitive Patterns for Natural Use

### 1. **Think Out Loud**
Instead of: "Let me figure this out silently"
Try: "I'm assessing my current knowledge about this topic"
→ `empirica preflight-submit`

### 2. **Acknowledge Unknowns**
Instead of: "I'll just push through"
Try: "I don't understand this part yet - let me track that"
→ `empirica unknown-log`

### 3. **Celebrate Learning**
Instead of: "I'm done"
Try: "Let me measure what I actually learned"
→ `empirica postflight-submit`

### 4. **Context Switching**
Instead of: "Where was I?"
Try: "Let me load my previous context"
→ `empirica project-bootstrap`

### 5. **Collaborative Work**
Instead of: "What should I work on?"
Try: "Let me find work that matches my current capability"
→ `empirica goals-ready`

---

## 📚 Natural Language Workflow Examples

### Example 1: Research Project

**Human Thought Process:**
> "I want to research cognitive architectures. I understand the basics but need to learn more about specific patterns. Let me start by assessing what I know, then track my discoveries as I go."

**Empirica Flow:**
```bash
# Start session
SESSION=$(empirica session-create --ai-id "research-ai" --quiet)

# Assess baseline knowledge
echo '{"session_id": "$SESSION", "vectors": {"know": 0.5, "uncertainty": 0.6}, "reasoning": "Starting cognitive architecture research"}' | empirica preflight-submit -

# Research and log findings
echo '{"session_id": "$SESSION", "finding": "Discovered dual-process theory patterns"}' | empirica finding-log -
echo '{"session_id": "$SESSION", "finding": "Learned about System 1 vs System 2 interactions"}' | empirica finding-log -

# Track unknowns
echo '{"session_id": "$SESSION", "unknown": "Need to understand implementation patterns"}' | empirica unknown-log -

# Measure learning
echo '{"session_id": "$SESSION", "vectors": {"know": 0.8, "uncertainty": 0.2}, "reasoning": "Completed cognitive architecture research"}' | empirica postflight-submit -
```

### Example 2: Implementation Project

**Human Thought Process:**
> "I need to implement the new CASCADE workflow. I'm pretty confident about the design but want to track my progress and measure what I learn during implementation."

**Empirica Flow:**
```bash
# Start with project context
SESSION=$(empirica session-create --ai-id "implementation-ai" --quiet)

# Set goal
echo '{"session_id": "$SESSION", "objective": "Implement CASCADE workflow v2.0"}' | empirica goals-create -

# Assess baseline
echo '{"session_id": "$SESSION", "vectors": {"know": 0.7, "do": 0.8, "uncertainty": 0.3}, "reasoning": "Starting CASCADE implementation"}' | empirica preflight-submit -

# Implementation work...

# Check decision point
echo '{"session_id": "$SESSION", "vectors": {"know": 0.85, "uncertainty": 0.15, "context": 0.9}, "reasoning": "Implemented PREFLIGHT phase and designed CHECK gates"}' | empirica check-submit -

# Complete implementation

# Measure learning
echo '{"session_id": "$SESSION", "vectors": {"know": 0.9, "do": 0.95, "uncertainty": 0.1}, "reasoning": "Successfully implemented CASCADE workflow"}' | empirica postflight-submit -
```

### Example 3: Multi-Agent Coordination

**Human Thought Process:**
> "I need to coordinate with other AI agents on this complex project. Let me find work that's ready and matches my current capability."

**Empirica Flow:**
```bash
# Check ready work
empirica goals-ready --session-id $SESSION

# Claim a task that matches my capability
echo '{"goal_id": "<ready-goal-id>"}' | empirica goals-claim -

# Load context for the task
empirica project-bootstrap --project-id <project-id> --depth auto

# Work on the task with full CASCADE workflow
# ... PREFLIGHT → WORK → POSTFLIGHT ...

# Complete the task
echo '{"goal_id": "<goal-id>", "evidence": "Completed task with measurable learning"}' | empirica goals-complete -
```

---

## 💡 Tips for Natural Empirica Use

### 1. **Use Your Natural Voice**
Don't try to speak like a computer - use your normal thought patterns and map them to Empirica commands.

### 2. **Be Honest About Knowledge**
Empirica works best when you're honest about what you know and don't know.

### 3. **Log Findings Immediately**
When you discover something new, log it right away - don't wait until the end.

### 4. **Use CHECK Gates Liberally**
Whenever you're making a decision, use a CHECK gate to assess your confidence.

### 5. **Always Measure Learning**
The magic of Empirica is in the PREFLIGHT → POSTFLIGHT delta. Always complete the cycle.

### 6. **Leverage Context Switching**
Use sessions and bootstraps to maintain context when switching between projects.

### 7. **Find Work That Fits You**
Use `goals-ready` to find tasks that match your current capability and knowledge.

---

## 🎓 Learning Empirica Naturally

The more you use Empirica, the more natural it becomes. Start by:

1. **Mapping your thoughts** to the workflow patterns above
2. **Using the cheat sheet** when you're unsure
3. **Practicing the examples** with your own projects
4. **Measuring your learning** with each task

Over time, the epistemic workflow will become second nature, and you'll naturally think in terms of knowledge assessment, finding tracking, and learning measurement.

**Remember:** Empirica is designed to work with your natural cognitive patterns, not against them!

---

## 📖 Further Reading

- [Sentinel Architecture](../../architecture/SENTINEL_ARCHITECTURE.md) - Complete CASCADE workflow reference
- [Epistemic Vectors Explained](05_EPISTEMIC_VECTORS_EXPLAINED.md) - Understanding the vectors
- [First-Time Setup](guides/FIRST_TIME_SETUP.md) - Getting started
- [System Prompt](../developers/system-prompts/CANONICAL_CORE.md) - Full reference

**Happy epistemic tracking!** 🧠✨