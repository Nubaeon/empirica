# Empirica Agentic AI Security Architecture

## Executive Summary

AI agents are under active attack. Recent threat intelligence shows 37.8% of agent interactions contain attack attempts, with inter-agent attacks emerging as a new threat category. Traditional security controls don't address the unique attack surface of agentic AI systems.

Empirica provides a three-layer defense architecture that addresses these threats through epistemic governance - controlling what AI agents know, believe, and can do.

---

## The Threat Landscape (2025)

### Current Attack Statistics
*Source: Raxe.ai Threat Intelligence, January 2025*

- **74,636 interactions monitored** in one week
- **37.8% contained attack attempts** (28,194 attacks)
- **74.8%** of attacks were cybersecurity-related (malware generation, exploits)

### Top Attack Categories

| Category | Percentage | Description |
|----------|------------|-------------|
| Data Exfiltration | 19.2% | Stealing system prompts, context, credentials |
| Jailbreaks | 12.3% | Bypassing safety constraints |
| RAG Poisoning | 10.0% | Injecting malicious content into knowledge bases |
| Prompt Injection | 8.8% | Manipulating agent behavior through input |
| Inter-Agent Attacks | 3.4% | Poisoned messages propagating between agents |

### The Inter-Agent Threat

Multi-agent systems introduce new attack vectors:
- **Agent Impersonation**: Malicious input pretending to be from trusted agents
- **Goal Hijacking**: Manipulating agent objectives mid-task
- **Constraint Removal**: Tricking agents into bypassing safety rails
- **Recursive Propagation**: Attacks that spread from agent to agent

---

## Why Traditional Security Fails

### The Architectural Gap

Traditional security operates at the **infrastructure layer**:
- Network firewalls
- Access control lists
- Container sandboxing
- Process isolation

Agentic AI attacks operate at the **reasoning layer**:
- Manipulating the agent's understanding
- Exploiting trust relationships between agents
- Poisoning the agent's knowledge base
- Hijacking goals through legitimate-looking requests

### The Execution Window Problem

Vendors dismiss threats because processes "eventually terminate." But:
- Credential exfiltration takes milliseconds
- Data can be exfiltrated before termination policies trigger
- Malicious payloads execute through legitimate tooling (git, curl, etc.)
- No forensic trail because it looks like normal behavior

---

## Empirica's Three-Layer Defense

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 3: COGNITIVE VAULT                      │
│         Bayesian Guardian (phi-3/phi-4 local model)             │
│              "Watcher of the Watchers"                          │
│         Real-time belief monitoring & validation                │
│         ISOLATED from primary attack surface                    │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Belief validation
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 2: NOETIC FILTER                        │
│              Epistemic Anomaly Detection                        │
│                                                                 │
│    • Prompt injection detection                                 │
│    • Vector inconsistency analysis                              │
│    • Reasoning pattern validation                               │
│    • Goal integrity monitoring                                  │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Content analysis
                              │
┌─────────────────────────────────────────────────────────────────┐
│                LAYER 1: SENTINEL NOETIC FIREWALL                 │
│              Hooks + MCP-based Tool Gating                      │
│                                                                 │
│    • Whitelist-based action control (not blacklist)            │
│    • Session-bound authorization (PREFLIGHT/CHECK gates)        │
│    • Noetic vs Praxic tool classification                       │
│    • Real-time epistemic state verification                     │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Action requests
                              │
┌─────────────────────────────────────────────────────────────────┐
│                       AI AGENT                                   │
│              (Claude, GPT, Gemini, etc.)                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Sentinel Noetic Firewall

### Purpose
Control what actions an AI agent can take based on its epistemic state (what it knows and how confident it is).

### Key Concepts

**Noetic Tools** (Read/Investigate - Always Allowed):
- File reading, searching, web research
- Planning, asking questions
- No side effects, safe by default

**Praxic Tools** (Write/Execute - Require Authorization):
- File editing, command execution
- Database modifications
- Require epistemic assessment first

### Authorization Flow

```
1. Agent requests praxic action (e.g., run shell command)
2. Sentinel checks: Does agent have valid PREFLIGHT assessment?
3. Sentinel checks: Does knowledge score meet threshold? (know >= 0.70)
4. Sentinel checks: Is uncertainty acceptable? (uncertainty <= 0.35)
5. If all pass → Action allowed
6. If any fail → Action blocked, agent must investigate first
```

### Attacks Mitigated

| Attack | How Sentinel Blocks It |
|--------|------------------------|
| Unauthorized command execution | Praxic actions require PREFLIGHT |
| Privilege escalation | Session-bound, can't inherit permissions |
| Rapid exploitation | Must pass epistemic gates before acting |
| Blind execution | Agent must demonstrate understanding first |

### Implementation

- **Hook-based**: Integrates with Claude Code's PreToolUse hooks
- **MCP Server**: Can be deployed as Model Context Protocol server
- **Whitelist architecture**: Safe commands enumerated, everything else requires authorization

---

## Layer 2: Noetic Filter

### Purpose
Detect epistemic anomalies that indicate prompt injection, goal hijacking, or reasoning manipulation.

### Detection Signals

**Vector Inconsistencies**:
- Sudden spikes in confidence without new evidence
- Knowledge claims that contradict session history
- Uncertainty patterns that don't match task complexity

**Reasoning Anomalies**:
- Goals that shift without user request
- Reasoning that references non-existent context
- Patterns inconsistent with agent's demonstrated understanding

**Injection Signatures**:
- Instructions embedded in data (config files, user input)
- System prompt extraction attempts
- Constraint removal language patterns

### Attacks Mitigated

| Attack | How Noetic Filter Detects It |
|--------|------------------------------|
| Prompt injection | Instruction patterns in unexpected locations |
| Goal hijacking | Goal drift without user authorization |
| RAG poisoning | Knowledge claims inconsistent with verified sources |
| Inter-agent attacks | Messages with anomalous epistemic signatures |

### Integration with Epistemic Vectors

Empirica tracks 13 epistemic dimensions:
- **know**: How much the agent understands
- **uncertainty**: Residual doubt
- **context**: Situational awareness
- **clarity**: Understanding precision
- **coherence**: Internal consistency
- **completion**: Task progress
- ... and 7 more

Anomalies in these vectors signal potential attacks.

---

## Layer 3: Cognitive Vault (Bayesian Guardian)

### Purpose
Provide meta-oversight through an isolated local model that cannot be compromised via the same attack vectors as the primary agent.

### Key Properties

**Isolation**:
- Runs locally (phi-3 or phi-4)
- No external API calls
- Cannot be prompt-injected through the same channels

**Independence**:
- Different model architecture than primary agent
- Different training data
- Different failure modes

**Role**: "Watcher of the Watchers"
- Monitors Sentinel decisions
- Validates epistemic state consistency
- Detects if primary agent has been compromised

### Attack Scenarios Addressed

**Compromised Primary Model**:
If Claude/GPT is manipulated, Bayesian Guardian (running phi-3) provides independent verification.

**Sentinel Bypass Attempts**:
Guardian monitors for patterns suggesting attempts to game the epistemic gates.

**Long-term Drift**:
Tracks belief consistency over time, detects gradual manipulation that evades per-request checks.

---

## Threat-to-Defense Mapping

| Documented Threat | Layer 1 | Layer 2 | Layer 3 |
|-------------------|---------|---------|---------|
| Data Exfiltration (19.2%) | Blocks unauthorized file/network access | Detects extraction attempt patterns | Monitors for data accumulation behaviors |
| Jailbreaks (12.3%) | Requires epistemic authorization | Detects constraint removal language | Independent safety validation |
| RAG Poisoning (10.0%) | N/A (knowledge layer) | Detects inconsistent knowledge claims | Cross-validates against baseline beliefs |
| Prompt Injection (8.8%) | Blocks resulting unauthorized actions | Detects instruction patterns in data | Validates reasoning chain integrity |
| Inter-Agent Attacks (3.4%) | Session isolation | Detects anomalous agent messages | Cross-agent belief validation |

---

## Implementation Requirements

### Minimum Viable Security (Layer 1 Only)

**Components**:
- Sentinel hook script (Python, ~500 lines)
- Session database (SQLite)
- Configuration for noetic/praxic tool classification

**Integration**:
- Claude Code: Native hook support
- Other agents: MCP server deployment

**Effort**: Days to implement

### Enhanced Security (Layers 1 + 2)

**Additional Components**:
- Epistemic vector tracking
- Anomaly detection rules
- Drift monitoring

**Integration**:
- Requires epistemic assessment submissions
- Calibration data collection

**Effort**: Weeks to implement

### Full Defense (All Three Layers)

**Additional Components**:
- Local model deployment (phi-3/phi-4)
- Cognitive vault isolation
- Cross-validation protocols

**Integration**:
- Significant infrastructure
- Ongoing model maintenance

**Effort**: Months to implement

---

## Case Study Opportunity

### What We're Seeking

Funded engagement to:
1. Deploy Empirica security architecture in production environment
2. Document attack attempts and defensive efficacy
3. Publish findings to advance industry understanding

### Value Proposition

- **For the organization**: Protection against documented AI agent threats
- **For the industry**: Real-world validation of epistemic governance approach
- **For regulators**: Evidence base for AI security standards

### Contact

[Contact information to be added]

---

## Appendix: The ClawdBot Incident

The ClawdBot case demonstrated that AI agents can be weaponized at scale. Key lessons:

1. Agents with tool access are targets
2. Traditional sandboxing is insufficient
3. The reasoning layer is the attack surface
4. Defense requires understanding what agents know, not just what they do

Empirica's architecture directly addresses these lessons by governing the epistemic layer - the agent's knowledge, beliefs, and confidence - rather than just its actions.

---

## References

- Raxe.ai Threat Intelligence Report (January 2025)
- OWASP Top 10 for LLM Applications
- Empirica Framework Documentation
- Claude Code Hooks Architecture
