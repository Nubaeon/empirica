# AI vs Agent: Empirica CASCADE Patterns

**Purpose:** Define terminology and CASCADE usage patterns for collaborative AI/Agent environments

**Created:** 2025-01-XX  
**Status:** Architecture Pattern Definition

---

## 🤖 Terminology: AI vs Agent

### AI (Collaborative Intelligence)
**Definition:** Engaged, reasoning partner working WITH the user

**Characteristics:**
- High autonomy and reasoning capability
- Engages in dialogue, asks clarifying questions
- Plans architecture, makes design decisions
- Uses full CASCADE workflow (PREFLIGHT → POSTFLIGHT)
- Creates goals, defines success criteria
- Delegates work to agents
- Learns and tracks epistemic growth

**Examples:**
- Claude/Rovo Dev collaborating with user on feature design
- GPT-4 planning system architecture
- Gemini researching and proposing solutions

**Empirica Usage:** Full CASCADE workflow

---

### Agent (Acting Intelligence)
**Definition:** Focused executor of specific, well-defined tasks

**Characteristics:**
- Lower autonomy, task-focused
- Executes predefined subtasks
- Limited dialogue (reports progress/completion)
- Uses simplified CASCADE (primarily ACT phase)
- Takes goals/subtasks as input
- Reports back with evidence
- May use lighter epistemic tracking

**Examples:**
- Mini-agent implementing test suite from specifications
- Code formatter applying linting rules
- Documentation generator creating API docs
- Test runner executing test suites

**Empirica Usage:** Simplified CASCADE (ACT-focused)

---

## 🔄 CASCADE Split Patterns

### Pattern 1: AI Solo Work (Full CASCADE)

**Use When:**
- Single AI working independently
- No delegation needed
- AI has capability to complete all work

```
AI {
  BOOTSTRAP → Initialize session, load context
  PREFLIGHT → Assess knowledge, identify uncertainty
  INVESTIGATE → Research, explore, prototype
  CHECK → Validate readiness (confidence ≥0.7)
  ACT → Implement, test, document
  POSTFLIGHT → Measure learning, generate handoff
}
```

**Example:**
```
Claude implements OAuth feature solo:
  PREFLIGHT (know: 0.6, uncertainty: 0.5)
  INVESTIGATE: Research OAuth flows, explore libraries
  CHECK (confidence: 0.8)
  ACT: Write auth.py, tests, docs
  POSTFLIGHT (know: 0.9, learned OAuth patterns)
```

---

### Pattern 2: AI Delegates to Agents (Collaborative)

**Use When:**
- AI designs/plans, agents execute
- Clear task decomposition possible
- Agents have specialized capabilities
- Parallel execution beneficial

```
AI (Lead) {
  BOOTSTRAP → Initialize session
  PREFLIGHT → Assess overall knowledge
  INVESTIGATE → Research, design architecture
    └─ CREATE GOALS & SUBTASKS
  CHECK (ready to delegate?)
  
  ┌─ DELEGATE ─────────────────────┐
  │                                 │
  ├─ Agent 1 { ACT subtasks 1-3 }  │
  ├─ Agent 2 { ACT subtasks 4-6 }  │
  └─ Agent 3 { ACT subtasks 7-9 }  │
  
  CHECK (review agent work)
  ACT (integrate, verify, refine)
  POSTFLIGHT (learned from design + agent feedback)
}

Agent (Worker) {
  Receive: subtask_id, description, context
  ACT → Execute subtask
  COMPLETE → Report evidence
  (Optional: Mini-PREFLIGHT if subtask complex)
}
```

**Example:**
```
Claude designs rate limiting, Mini-agent implements tests:

Claude:
  PREFLIGHT (know: 0.7, design skills high)
  INVESTIGATE: Design rate limit strategy (token bucket)
  CREATE GOALS:
    - Goal 1: Implement middleware (Claude does this)
    - Goal 2: Write unit tests (delegate to mini-agent)
    - Goal 3: Write integration tests (delegate to mini-agent)
    - Goal 4: Update docs (Claude does this)
  
  DELEGATE:
    mini-agent → Goal 2 (unit tests)
    mini-agent → Goal 3 (integration tests)
  
  CHECK (review mini-agent's tests)
  ACT (integrate tests, verify, write docs)
  POSTFLIGHT (learned: token bucket implementation)

Mini-agent (Goal 2):
  ACT: Write test_rate_limit.py (15 test cases)
  COMPLETE: "Unit tests in test_rate_limit.py, 15 tests, all passing"

Mini-agent (Goal 3):
  ACT: Write test_rate_limit_e2e.py (5 scenarios)
  COMPLETE: "Integration tests in test_rate_limit_e2e.py, 5 scenarios, all passing"
```

---

### Pattern 3: Multiple AIs Collaborating (Peer CASCADE)

**Use When:**
- Multiple reasoning AIs working together
- Each AI brings domain expertise
- Work requires multiple perspectives
- Complex problem requiring specialization

```
Lead AI {
  PREFLIGHT → Assess overall problem
  INVESTIGATE → Decompose into domains
  CREATE GOALS (domain-specific)
  
  ┌─ COORDINATE ───────────────────┐
  │                                 │
  ├─ AI 2 (Specialist A) {         │
  │    Mini-CASCADE on Goal 1       │
  │  }                              │
  │                                 │
  ├─ AI 3 (Specialist B) {         │
  │    Mini-CASCADE on Goal 2       │
  │  }                              │
  └─────────────────────────────────┘
  
  CHECK (synthesize specialist work)
  ACT (integrate, resolve conflicts)
  POSTFLIGHT (learned from specialists)
}

Specialist AI {
  PREFLIGHT (domain-specific assessment)
  INVESTIGATE (deep dive in specialty)
  ACT (specialized implementation)
  POSTFLIGHT (report findings to lead)
}
```

**Example:**
```
Building secure payment system:

Lead AI (Architecture):
  PREFLIGHT: Understand payment requirements
  INVESTIGATE: Design system architecture
  CREATE GOALS:
    - Goal 1: Security implementation (Security AI)
    - Goal 2: Payment integration (Payment AI)
    - Goal 3: Testing strategy (Lead + Test Agent)

Security AI (Goal 1):
  PREFLIGHT (security knowledge: 0.9)
  INVESTIGATE: Threat modeling, encryption strategy
  ACT: Implement security layer, audit code
  POSTFLIGHT: Report vulnerabilities addressed

Payment AI (Goal 2):
  PREFLIGHT (payment APIs knowledge: 0.8)
  INVESTIGATE: Compare Stripe vs PayPal
  ACT: Implement payment integration
  POSTFLIGHT: Report integration complete + learnings

Lead AI:
  CHECK: Review security + payment implementations
  ACT: Integrate both, resolve conflicts, verify
  POSTFLIGHT: Learned security + payment patterns
```

---

## 📋 Agent Empirica Guidelines

### Simplified CASCADE for Agents

Agents typically use **ACT-focused workflow**:

```
Agent Workflow:
1. Receive subtask (description, context)
2. (Optional) Mini-PREFLIGHT if complex/uncertain
3. ACT → Execute work
4. COMPLETE → Report evidence
5. (Optional) Mini-POSTFLIGHT if learning occurred
```

### When Agents Use Full CASCADE

**Use full CASCADE if:**
- Subtask is complex (multi-step, >30min)
- Initial uncertainty high (>0.5)
- Learning expected (new library/pattern)
- Multiple approaches need evaluation

**Example:**
```
Agent receives: "Implement OAuth token refresh mechanism"

This is complex, so agent uses full CASCADE:
  PREFLIGHT (uncertainty: 0.6 - don't know refresh flow)
  INVESTIGATE: Research OAuth refresh token spec
  CHECK (confidence: 0.8)
  ACT: Implement refresh mechanism
  POSTFLIGHT (uncertainty: 0.2 - now understand flow)
```

### When Agents Skip CASCADE

**Skip formal CASCADE for:**
- Simple, well-defined tasks (<10min)
- Known patterns (done before)
- No uncertainty (clear instructions)

**Example:**
```
Agent receives: "Run pytest on all test files"

Simple task, just ACT:
  ACT: Run `pytest tests/ -v`
  COMPLETE: "Tests ran, 42/42 passing"
```

---

## 🎯 Goal & Subtask Ownership

### AI Creates, Agent Executes

**AI Responsibilities:**
- Create goals with `create_goal()`
- Define success criteria
- Break down into subtasks with `add_subtask()`
- Delegate subtasks to agents
- Review agent work
- Integrate results

**Agent Responsibilities:**
- Execute assigned subtasks
- Report progress/blockers
- Complete subtasks with `complete_subtask(task_id, evidence)`
- (Optional) Create sub-subtasks if needed

### Handoff Protocol

**AI → Agent Handoff:**
```python
# AI creates subtask
subtask_id = add_subtask(
    goal_id="goal-uuid",
    description="Write unit tests for auth validation",
    importance="high",
    estimated_tokens=500
)

# AI sends to agent (via user or orchestration)
→ Agent receives: subtask_id + description + context

# Agent works
agent.execute(subtask_id)

# Agent completes
complete_subtask(
    task_id=subtask_id,
    evidence="Created test_auth_validation.py with 15 tests, all passing. Coverage 95%."
)

# AI checks completion
progress = get_goal_progress(goal_id)
```

---

## 🔀 Governance Layer Integration

### Future: Dynamic Role-Based Prompts

**Vision:** Cognitive Vault + Sentinel provides appropriate prompts based on role

```python
# AI requests prompt
prompt = get_system_prompt(
    ai_id="rovo-dev",
    role="collaborative_ai",
    modality="coding",
    task_type="feature_design"
)
→ Returns: AI_COLLABORATIVE_PROMPT (full CASCADE guidance)

# Agent requests prompt
prompt = get_system_prompt(
    ai_id="mini-agent",
    role="acting_agent",
    modality="testing",
    task_type="test_implementation"
)
→ Returns: AGENT_EXECUTION_PROMPT (ACT-focused guidance)
```

**Benefits:**
- Right prompt for right role
- Consistent terminology (AI vs Agent)
- Token-efficient (load only needed guidance)
- Centrally managed, version controlled

---

## 📊 Comparison Table

| Aspect | AI (Collaborative) | Agent (Acting) |
|--------|-------------------|----------------|
| **Autonomy** | High | Low-Medium |
| **Dialogue** | Extensive | Minimal |
| **Planning** | Creates goals/plans | Executes plans |
| **CASCADE** | Full (PREFLIGHT → POSTFLIGHT) | Simplified (ACT-focused) |
| **Uncertainty** | Tracks and manages | Reports blockers |
| **Learning** | Measures epistemic growth | Optional, task-specific |
| **Delegation** | Delegates to agents | Rarely delegates |
| **Examples** | Claude, GPT-4, Gemini | Mini-agent, linters, formatters |

---

## 🎯 Best Practices

### For AIs (Collaborative Intelligence):

1. **Use full CASCADE** for significant work
2. **Create clear subtasks** when delegating
3. **Review agent work** before integrating
4. **Track learning** from both own work and agent feedback
5. **Generate handoffs** for continuity

### For Agents (Acting Intelligence):

1. **Use simplified CASCADE** (ACT-focused) for simple tasks
2. **Use full CASCADE** for complex/uncertain tasks
3. **Report evidence** clearly when completing
4. **Ask for clarification** if subtask unclear
5. **Don't overthink** - execute efficiently

### For Users (Human Coordinators):

1. **Choose right tool** - AI for reasoning, agent for execution
2. **Delegate appropriately** - match task complexity to tool
3. **Provide context** when assigning to agents
4. **Review handoffs** between AIs/agents
5. **Track costs** - agents cheaper, AIs more capable

---

## 🔮 Future Patterns

### Multi-Agent Orchestration
```
Lead AI {
  Design system architecture
  CREATE 10 goals
  
  Agent Pool:
    - 3 test agents (parallel test creation)
    - 2 doc agents (parallel documentation)
    - 1 integration agent (assembly)
  
  COORDINATE parallel execution
  CHECK all work
  INTEGRATE results
}
```

### Specialized AI Teams
```
Architecture AI → Design
Security AI → Security review
Performance AI → Optimization
Test AI → Test strategy

Agents execute implementation
```

### Adaptive Delegation
```
AI assesses subtask complexity:
  - Simple → Delegate to agent
  - Medium → Keep (own ACT)
  - Complex → Delegate to specialist AI
```

---

## 📚 References

**Related Docs:**
- `05_ARCHITECTURE.md` - Overall Empirica architecture
- `06_CASCADE_FLOW.md` - Detailed CASCADE workflow
- `docs/production/23_SESSION_CONTINUITY.md` - Handoff patterns

**System Prompts:**
- `SYSTEM_PROMPT_DEV_COMPACT.md` - For both AIs and agents (development)
- Future: Role-specific prompts via Governance Layer

---

**Key Principle:** The distinction matters because it affects how CASCADE is used, how work is delegated, and how learning is tracked. AIs think and plan; agents execute and report.
