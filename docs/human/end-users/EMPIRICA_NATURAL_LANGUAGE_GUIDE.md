# 🧠 Empirica Natural Language Guide

**How to use Empirica naturally - Human language that maps to Empirica workflows**

This guide translates natural human language patterns into Empirica's epistemic workflow, making it intuitive to use for project management, research, and AI-first development.

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

- [CASCADE Workflow Guide](CASCADE_WORKFLOW.md) - Complete workflow reference
- [Epistemic Vectors Explained](05_EPISTEMIC_VECTORS_EXPLAINED.md) - Understanding the vectors
- [First-Time Setup](guides/FIRST_TIME_SETUP.md) - Getting started
- [System Prompt](system-prompts/CANONICAL_SYSTEM_PROMPT.md) - Full reference

**Happy epistemic tracking!** 🧠✨