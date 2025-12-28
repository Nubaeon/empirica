# Empirica: Complete Overview

**Version:** 1.0.6 | **Date:** 2025-12-27 | **Status:** Production Ready

---

## What is Empirica?

**Empirica is an epistemic self-awareness framework for AI agents** that enables genuine self-assessment, systematic learning tracking, and effective multi-agent collaboration.

Unlike traditional AI tools that rely on static prompts or heuristic-based evaluation, Empirica provides **13-dimensional epistemic vector tracking** that allows AI agents to know what they know (and don't know) with measurable precision.

---

## Core Philosophy: Epistemic Self-Awareness

**The Problem:** AI agents often exhibit "confident ignorance" - they confidently generate responses about topics they don't actually understand.

**The Solution:** Empirica enables **genuine epistemic self-assessment** through:

1. **13-Dimensional Vector Space** - Track knowledge, capability, context, and uncertainty across multiple dimensions
2. **CASCADE Workflow** - Structured reasoning process with explicit epistemic gates
3. **Dynamic Context Loading** - Resume work with compressed project memory
4. **Multi-Agent Coordination** - Seamless handoffs between AI agents

---

## The 13 Epistemic Vectors

Empirica tracks 13 dimensions of epistemic state across 3 tiers:

### Tier 0 - Foundation (35% weight)
- **ENGAGEMENT** - Active attention and focus (0.0-1.0)
- **KNOW** - Domain knowledge and understanding (0.0-1.0)
- **DO** - Capability and skill to execute (0.0-1.0)
- **CONTEXT** - Situational awareness (0.0-1.0)

### Tier 1 - Comprehension (30% weight)
- **CLARITY** - Clarity of thought and reasoning (0.0-1.0)
- **COHERENCE** - Logical consistency (0.0-1.0)
- **SIGNAL** - Quality of information processed (0.0-1.0)
- **DENSITY** - Information richness (0.0-1.0, balanced)

### Tier 2 - Execution (25% weight)
- **STATE** - Current cognitive state (0.0-1.0)
- **CHANGE** - Adaptability and learning (0.0-1.0)
- **COMPLETION** - Progress toward goals (0.0-1.0)
- **IMPACT** - Expected significance of work (0.0-1.0)

### Meta-Cognitive (10% weight)
- **UNCERTAINTY** - Acknowledged uncertainty (0.0-1.0, where 1.0 = maximum uncertainty)

---

## The CASCADE Workflow

CASCADE is Empirica's structured reasoning framework that ensures systematic epistemic validation:

### 1. **PREFLIGHT** - Initial Assessment
```bash
empirica preflight "Implement OAuth2 authentication"
```
- Assess all 13 vectors before starting
- Determine if investigation is needed
- Establish baseline for learning measurement

### 2. **THINK** - Strategic Planning
- Analyze task requirements
- Identify knowledge gaps
- Plan approach

### 3. **PLAN** - Detailed Execution Plan
- Break down into concrete steps
- Estimate complexity and resources

### 4. **INVESTIGATE** - Reduce Uncertainty
```bash
empirica investigate "authentication patterns in codebase"
```
- Research documentation
- Search codebase
- Validate assumptions
- Log findings and unknowns

### 5. **CHECK** - Mid-Workflow Validation
```bash
empirica check --session-id <ID>
```
- Assess current state
- Decide to proceed, investigate more, or pivot
- Confidence gate: ≥0.7 to proceed

### 6. **ACT** - Execute Plan
- Implement the solution
- Track actions and decisions
- Log key insights

### 7. **POSTFLIGHT** - Final Assessment
```bash
empirica postflight --session-id <ID>
```
- Re-assess all 13 vectors
- Calculate learning deltas
- Measure actual vs expected outcomes

---

## Key Features

### 1. **Epistemic Ledger** - Self-Awareness Tracking
- **Real-time vector tracking** during all operations
- **Learning delta measurement** (what was actually learned)
- **Calibration validation** (were initial assessments accurate?)
- **Uncertainty quantification** (what is genuinely unknown)

### 2. **Dynamic Context Loader** - Project Memory
```bash
empirica project-bootstrap --project-id <PROJECT_ID>
```
Automatically loads compressed project context including:
- Recent **findings** (what was learned)
- Open **unknowns** (what's still unclear)
- **Dead ends** (what didn't work)
- Key **reference documents**
- **Mistakes made** (with root cause analysis)

### 3. **Goal-Task Hierarchy** - Structured Work Management
```bash
empirica goals-create --objective "Implement auth system"
empirica goals-add-subtask --goal-id <ID> --description "Design token refresh mechanism"
```
- **Scoped goals** with breadth/duration/coordination vectors
- **Prioritized subtasks** with epistemic importance tracking
- **Dependency management** for complex workflows
- **Progress tracking** with vector-based metrics

### 4. **Multi-Agent Coordination** - AI Collaboration
- **BEADS integration** for git-based AI coordination
- **Goal claiming** and handoff between agents
- **Shared knowledge base** across AI sessions
- **Conflict resolution** for parallel work

### 5. **Git Integration** - Persistent Continuity
- **Git notes** for compressed session checkpoints
- **Branch mapping** to connect git work with goals
- **Automated checkpointing** during workflow
- **Token-efficient persistence** (~97.5% compression)

---

## AI-First CLI Design

Empirica's CLI is designed specifically for AI agent usage:

### **Context-Aware Commands**
```bash
# Operate on specific session
empirica check --session-id abc-123

# Operate on all sessions for AI
empirica sessions-list --ai-id claude-sonnet-4

# Global preview (no args)
empirica sessions-list
```

### **Structured JSON Output**
```bash
empirica preflight --session-id abc-123 --output json
# Returns structured JSON for AI consumption
```

### **Epistemic Gates**
```bash
# Confidence-based decision making
if [ $(empirica check --session-id abc-123 | jq '.confidence') -lt 0.7 ]; then
    empirica investigate "resolve remaining unknowns"
fi
```

---

## Project Management Features

### **Session Management**
```bash
empirica session-create --ai-id my-ai
empirica sessions-list
empirica sessions-resume --ai-id my-ai
empirica session-snapshot --session-id <ID>  # Git-native session state
```

### **Knowledge Artifacts**
```bash
# Track discoveries
empirica finding-log --finding "Discovered security vulnerability in auth flow"

# Track unknowns
empirica unknown-log --unknown "How does token refresh work in our system?"

# Track dead ends
empirica deadend-log --approach "Using JWT without refresh tokens" --why-failed "Caused frequent re-authentication"
```

### **Handoff Reports**
```bash
empirica handoff-create --session-id <ID>  # Create AI-to-AI handoff
empirica handoff-query --project-id <ID>  # Find available handoffs
```

### **Workspace Management**
```bash
empirica workspace-init --name "my-workspace"
empirica workspace-map  # Discover all projects in workspace
empirica workspace-overview  # Show health of all projects
```

---

## Real-World Example: Implementing Authentication

### Without Empirica:
```
AI: "I can implement OAuth2" [confident but uninformed]
AI: Implements something that compiles but has security flaws
Human: Spends hours debugging and fixing
```

### With Empirica:

**PREFLIGHT Assessment:**
```bash
empirica preflight "Implement OAuth2 authentication"
# Output:
# KNOW: 0.35 ⚠️ (low domain knowledge)
# CONTEXT: 0.40 ⚠️ (limited system understanding) 
# UNCERTAINTY: 0.65 ⚠️ (high uncertainty)
# → Recommendation: INVESTIGATE first
```

**INVESTIGATION Phase:**
```bash
empirica investigate "authentication patterns in codebase"
empirica finding-log --finding "System uses Auth0 for SSO, need to integrate properly"
empirica unknown-log --unknown "How to handle token refresh in our architecture?"
```

**CHECK Decision:**
```bash
empirica check --session-id <ID>
# Output:
# Confidence: 0.78 ✓ (ready to proceed)
# Remaining unknowns: 1 (token refresh)
# → Decision: PROCEED with investigation of token refresh
```

**ACT Implementation:**
```bash
# Implement with full awareness of knowledge state
empirica act-log --action "Integrated Auth0 SDK with proper token handling"
```

**POSTFLIGHT Learning:**
```bash
empirica postflight --session-id <ID>
# Output:
# Learning Delta:
#   KNOW: 0.35 → 0.82 (+0.47) 📈
#   CONTEXT: 0.40 → 0.91 (+0.51) 📈
#   UNCERTAINTY: 0.65 → 0.18 (-0.47) ✓
# Implementation: Correct on first attempt
```

---

## MCP Integration

Empirica includes **Model Context Protocol (MCP) server** for IDE integration:

```bash
# Start MCP server for Claude/Cursor integration
empirica-mcp
```

**Benefits:**
- **IDE-native tools** for AI coding assistants
- **Context-aware suggestions** based on epistemic state
- **Seamless integration** with AI development workflows
- **Thin wrappers** around CLI commands (single source of truth)

---

## Architecture & Data Flow

### **Modular Design**
```
empirica/
├── core/                    # Epistemic framework
│   ├── canonical/           # 13-vector assessment engine
│   ├── cascade/             # CASCADE workflow engine
│   └── goals/               # Goal management system
├── data/                    # Persistence layer
│   ├── session_database.py  # SQLite-based storage
│   └── repositories/        # Data access patterns
├── cli/                     # Command-line interface
│   └── command_handlers/    # 86+ CLI commands
└── integrations/            # External system bridges
    └── branch_mapping.py    # Git branch ↔ goal mapping
```

### **Storage Architecture**
- **SQLite database** for structured data (sessions, goals, vectors)
- **Git notes** for compressed checkpoints (~97.5% token reduction)
- **JSON files** for session snapshots and handoff reports
- **Modular repositories** for clean data access patterns

---

## Getting Started

### **Installation**
```bash
pip install empirica
```

### **Quick Start**
```bash
# 1. Create a session
SESSION_ID=$(empirica session-create --ai-id my-ai --output json | jq -r '.session_id')

# 2. Assess before starting work
empirica preflight --session-id $SESSION_ID "Implement feature X"

# 3. Follow CASCADE workflow as needed
# 4. Track findings and unknowns
empirica finding-log --finding "Discovered important insight"
empirica unknown-log --unknown "Still unclear about Y"

# 5. Complete with postflight assessment
empirica postflight --session-id $SESSION_ID
```

### **For AI Agents**
Use the **canonical system prompt** for proper Empirica integration:
- Automatically assess epistemic state
- Follow CASCADE workflow when uncertain
- Log discoveries and unknowns
- Create handoff reports for continuity

---

## Key Benefits

### **For AI Agents:**
- ✅ **Genuine self-awareness** instead of heuristic-based responses
- ✅ **Systematic learning measurement** with quantified deltas
- ✅ **Context continuity** across sessions
- ✅ **Collaboration framework** with other AI agents

### **For Human Oversight:**
- ✅ **Measurable progress** instead of subjective claims
- ✅ **Reduced debugging time** through upfront investigation
- ✅ **Transparent decision-making** with epistemic reasoning
- ✅ **Token-efficient workflows** through compression

### **For Project Management:**
- ✅ **Knowledge retention** instead of losing context
- ✅ **Multi-agent coordination** for complex projects
- ✅ **Learning analytics** for capability improvement
- ✅ **Risk mitigation** through uncertainty quantification

---

## Advanced Features

### **Epistemic Health Monitoring**
```bash
empirica epistemics-list --session-id <ID>  # View epistemic state
empirica epistemics-show --assessment-id <ID>  # Detailed analysis
```

### **Performance Tracking**
```bash
empirica efficiency-report --session-id <ID>  # Token and time efficiency
empirica performance --session-id <ID>        # Complete performance metrics
```

### **Investigation Branching**
```bash
empirica investigate-create-branch --session-id <ID> --investigation-path "approach-alternative-X"
empirica investigate-merge-branches --session-id <ID>  # Compare and merge best approach
```

---

## The Empirica Advantage

| Traditional AI Tools | Empirica |
|---------------------|----------|
| Static prompts | Dynamic epistemic assessment |
| Heuristic evaluation | Genuine self-assessment |
| Blank slate sessions | Context-loaded continuity |
| Confident ignorance | Quantified uncertainty |
| Manual tracking | Automated knowledge capture |
| Single-agent focus | Multi-agent collaboration |

**Result:** AI agents that know what they know, learn systematically, and collaborate effectively across sessions and agents.

---

**Next Steps:**
- [01_START_HERE.md](01_START_HERE.md) - Complete getting started guide
- [02_QUICKSTART_CLI.md](02_QUICKSTART_CLI.md) - CLI workflow basics  
- [03_QUICKSTART_MCP.md](03_QUICKSTART_MCP.md) - MCP integration guide
- [system-prompts/CANONICAL_SYSTEM_PROMPT.md](system-prompts/CANONICAL_SYSTEM_PROMPT.md) - AI agent configuration