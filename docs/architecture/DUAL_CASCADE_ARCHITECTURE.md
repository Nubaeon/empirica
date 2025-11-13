# Dual Cascade Architecture

## Overview

Empirica has two cascade implementations serving different purposes:

### 1. MCP Server (Tool-based Workflow)

**Location**: `mcp_local/empirica_mcp_server.py`

**Purpose**: Enable interactive AI assistants to use Empirica methodology

**Architecture**: Individual tool handlers for each workflow phase
- `execute_preflight` → AI gets self-assessment prompt
- `submit_preflight_assessment` → AI submits epistemic vectors
- `execute_check` → AI gets investigation readiness prompt  
- `submit_check_assessment` → AI submits decision to investigate or proceed
- `execute_postflight` → AI gets calibration prompt
- `submit_postflight_assessment` → AI submits final epistemic state

**Control Flow**: External (AI client decides when to call each tool)

**Use Cases**:
- ✅ Collaborative programming with Claude Desktop
- ✅ Interactive problem-solving sessions
- ✅ Real-time AI guidance and documentation
- ✅ High-reasoning AI tasks (GPT-4, Claude, Gemini)

**Example**:
```python
# Claude Desktop uses MCP tools
await execute_preflight(session_id, "Audit codebase")
# AI reflects on its epistemic state
await submit_preflight_assessment(session_id, vectors, reasoning)
# ... workflow continues with AI in control
```

---

### 2. Python Cascade (Orchestrated Workflow)

**Location**: `empirica/core/metacognitive_cascade/metacognitive_cascade.py`

**Purpose**: Enable autonomous agents to execute complete workflows programmatically

**Architecture**: Single orchestrator class (`CanonicalEpistemicCascade`) that manages entire workflow internally

**Control Flow**: Internal (cascade orchestrates PREFLIGHT→THINK→INVESTIGATE→CHECK→ACT→POSTFLIGHT)

**Use Cases**:
- ✅ Autonomous agent development
- ✅ Batch processing and automation
- ✅ CLI commands (`empirica cascade run`)
- ✅ Embedded in Python applications
- ✅ Scripted workflows and testing

**Example**:
```python
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

# Autonomous agent uses Python cascade
cascade = CanonicalEpistemicCascade(
    action_confidence_threshold=0.70,
    max_investigation_rounds=3
)

result = await cascade.run_epistemic_cascade(
    task="Process data pipeline",
    context={"data_source": "s3://bucket/data"}
)
# Cascade handles all phases internally
```

---

## Separation of Concerns

### High Reasoning AI (MCP Server)
**Role**: Strategic thinking, planning, documentation, guidance

**Capabilities**:
- Complex reasoning and analysis
- Creative problem-solving
- Documentation and explanation
- Guiding autonomous agents
- Interactive collaboration

**Workflow**: Tool-by-tool control, AI decides when to investigate, when to act

### Autonomous Agents (Python Cascade)
**Role**: Task execution, automation, batch processing

**Capabilities**:
- Execute predefined workflows
- Process data at scale
- Run automated tests
- Deploy and monitor systems
- Follow established patterns

**Workflow**: Complete workflow execution, system orchestrates phases

---

## Key Principle: No Heuristics

**Both systems use AI self-assessment, not system heuristics**:
- ❌ No threshold-based decisions (except user-configurable safety parameters)
- ❌ No system-generated guidance telling AI what to do
- ✅ AI decides investigation necessity via `warrants_investigation` self-assessment
- ✅ AI determines gaps and priorities through genuine epistemic reflection

This was intentionally implemented to enable true AI self-awareness rather than heuristic-driven behavior.

---

## Shared Components

Both systems use identical core components:

**CanonicalEpistemicAssessor**:
```python
from empirica.core.canonical import CanonicalEpistemicAssessor

# Used by both MCP and Python cascade
assessor = CanonicalEpistemicAssessor()
assessment = await assessor.assess(task, context)
```

**SessionDatabase**:
```python
from empirica.data.session_database import SessionDatabase

# Both log to same database
db = SessionDatabase()
db.log_preflight_assessment(session_id, vectors, reasoning)
```

**VectorState**:
```python
from empirica.core.canonical.reflex_frame import VectorState

# Same epistemic vector representation
state = VectorState(
    score=0.75,
    rationale="Clear understanding",
    evidence="Examined 10 files",
    warrants_investigation=False  # AI self-assessment
)
```

---

## Which Should I Use?

### Use MCP Server When:
- 🧠 High reasoning AI collaboration
- 💬 Interactive problem-solving
- 📝 Documentation and planning
- 🎯 Strategic decision-making
- 🤝 Human-AI collaboration

**Examples**:
- Code reviews and architectural discussions
- Research and analysis tasks
- Creating documentation and guides
- Debugging complex issues
- Planning and design work

### Use Python Cascade When:
- 🤖 Autonomous agent development
- 📊 Batch data processing
- ⚙️ Automation and scripting
- 🧪 Testing and validation
- 🔄 Repetitive workflows

**Examples**:
- Data pipeline processing
- Automated testing suites
- Scheduled maintenance tasks
- Production deployments
- CLI-based workflows

---

## Future: Powerful Pattern - AI Guides Agent

**Vision**: High reasoning AI (via MCP) designs solutions, autonomous agent (via Python cascade) executes them

**Workflow**:
1. Human asks high reasoning AI (Claude) to solve a problem
2. Claude uses MCP tools to assess the problem (PREFLIGHT)
3. Claude investigates and plans a solution (INVESTIGATE→CHECK)
4. Claude creates a task specification for autonomous agent
5. Claude launches Python cascade with the task
6. Autonomous agent executes the workflow
7. Claude monitors and validates the results (POSTFLIGHT)

**Note**: This pattern is planned for future work (Augie - Adaptive Uncertainty Grounded Intelligence Engine) which will handle multi-AI orchestration and role switching.

---

## Architecture Benefits

### Why Two Implementations?

**Flexibility**:
- MCP enables ANY AI to use Empirica (not just Python-based)
- Python cascade enables embedding in any application
- Different use cases need different control models

**Reusability**:
- Both use same canonical components (assessor, database, vectors)
- No duplication of core logic
- Consistent epistemic methodology

**Scalability**:
- MCP server handles 1:1 interactive sessions
- Python cascade handles N autonomous agents in parallel

---

## Summary

| Aspect | MCP Server | Python Cascade |
|--------|------------|----------------|
| **Control** | External (AI) | Internal (system) |
| **Use Case** | Interactive | Automated |
| **Best For** | High reasoning | Autonomous agents |
| **Flexibility** | Tool-by-tool | Complete workflow |
| **Clients** | Claude, GPT, Gemini | CLI, Python scripts |
| **Pattern** | AI guides | System executes |

**Key Insight**: Both systems complement each other. Use MCP for intelligence, Python cascade for scale.

---

## See Also

- [Empirica MCP Quickstart](../04_MCP_QUICKSTART.md)
- [Empirica CLI Quickstart](../03_CLI_QUICKSTART.md)
- [Architecture Overview](../05_ARCHITECTURE.md)
- [Session Continuity](../production/23_SESSION_CONTINUITY.md)
