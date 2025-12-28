# Empirica: Comprehensive System Architecture

**Version:** 3.0 (Consolidated)
**Date:** 2025-12-27
**Purpose:** The single source of truth for Empirica's system architecture, providing a complete orientation for developers and AI agents.

---

## What is Empirica?

**Empirica is a privacy-first, epistemic self-awareness framework that enables AI agents to function as a Cognitive Operating System.** It operates as **cognitive middleware** between the LLM and the interface, providing functional self-awareness, coordination, and continuous learning.

**Core Philosophy:**
> "Measure and validate genuine epistemic state without interfering with reasoning. Transfer metacognitive knowledge, not raw conversations. User controls their data."

---

## System Layers (Bottom-Up)

This visual overview describes the complete architecture of the Empirica system from the user/agent layer down to the persistent storage and future Cognitive Vault.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER / AI AGENT LAYER                            │
│  (LLM Engine: Claude, GPT-4, Qwen, etc. - uses Empirica for epistemic  │
│   self-awareness via MCP or Python API)                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    INTERFACE LAYER (How to use Empirica)                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │
│  │   MCP Tools      │  │   Empirica CLI   │  │  Python API      │    │
│  │                  │  │                  │  │                  │    │
│  │ • session_create │  │ • session-create │  │ from empirica... │    │
│  │ • preflight      │  │ • preflight      │  │ db = Session...  │    │
│  │ • check          │  │ • check          │  │ db.create_...    │    │
│  │ • finding_log    │  │ • finding-log    │  │ db.log_finding() │    │
│  │ • goals_create   │  │ • goals-create   │  │                  │    │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                CASCADE WORKFLOW (Epistemic Process)                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PREFLIGHT → [CHECK]* → POSTFLIGHT → Δ (Deltas)                       │
│     ↓            ↓           ↓           ↓                             │
│  Assess      Decision    Measure    Calculate                          │
│  baseline    gates       learning    epistemic                         │
│  state       (0-N)       outcome     change                            │
│                                                                         │
│  Each phase uses 13 EPISTEMIC VECTORS:                                 │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │ TIER 0: engagement (gate)                                     │    │
│  │ TIER 1: know, do, context                                     │    │
│  │ TIER 2: clarity, coherence, signal, density                   │    │
│  │ TIER 3: state, change, completion, impact                     │    │
│  │ META:   uncertainty (explicit tracking)                       │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    CORE PROCESSING LAYER                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ EPISTEMIC ASSESSMENT                                            │  │
│  │ • Compute 13-vector state                                       │  │
│  │ • Calculate confidence scores                                   │  │
│  │ • Track uncertainty explicitly                                  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ DELTA COMPUTATION                                               │  │
│  │ • PREFLIGHT vs POSTFLIGHT deltas                                │  │
│  │ • Learning velocity (change per minute)                         │  │
│  │ • Git correlation (epistemic state → code changes)              │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ GOAL ORCHESTRATION                                              │  │
│  │ • Break complex work into subtasks                              │  │
│  │ • Track findings/unknowns/deadends per subtask                  │  │
│  │ • Scope tracking (breadth/duration/coordination)                │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ SENTINEL ORCHESTRATOR (Oversight Layer)                         │  │
│  │ • Multi-persona coordination                                    │  │
│  │ • Arbitration strategies                                        │  │
│  │ • Compliance monitoring                                         │  │
│  │ • SLM trained on Empirica deltas (future)                       │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                   STORAGE LAYER (3-Layer Atomic Write)                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │
│  │   SQLite DB      │  │   Git Notes      │  │   JSON Logs      │    │
│  │                  │  │                  │  │                  │    │
│  │ • sessions       │  │ • Compressed     │  │ • Full reflex    │    │
│  │ • reflexes       │  │   checkpoints    │  │   logs           │    │
│  │ • findings       │  │ • Immutable      │  │ • Human-readable │    │
│  │ • unknowns       │  │   history        │  │ • Backup         │    │
│  │ • deadends       │  │ • Distributed    │  │                  │    │
│  │ • goals          │  │                  │  │                  │    │
│  │ • subtasks       │  │                  │  │                  │    │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘    │
│                                                                         │
│  Atomic Write: SQLite → Git Notes → JSON (graceful degradation)        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      DATA PRODUCTS (What You Get)                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  • Epistemic Deltas (learning measurement)                              │
│  • Git-Epistemic Correlation (commit → epistemic context)               │
│  • Session Handoffs (continuity across sessions)                        │
│  • Calibration Reports (predicted vs actual confidence)                 │
│  • Project Breadcrumbs (findings/unknowns/deadends aggregated)          │
│  • Delta Packages (training data for Sentinel SLM - future)             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Key Concepts Explained

### 1. Privacy-First Data Storage (Local, User-Controlled)
Empirica is designed with privacy as a core principle. All data generated during a session is stored locally on the user's machine, with no cloud dependencies.

*   **SQLite Session DB (`.empirica/sessions/sessions.db`):** The primary source of truth for structured, queryable data like sessions, cascades, assessments, and epistemic vectors.
*   **Reflex Logs (`.empirica_reflex_logs/`):** A human-readable, temporal audit trail of phase-specific reasoning chains in JSON format. This separation prevents recursive analysis.
*   **JSON Exports (`.empirica/exports/`):** Portable, shareable, privacy-preserving summaries and epistemic snapshots.
*   **Qdrant Vector DB (Optional, Local):** A self-hosted vector database for semantic search over documentation and learning experiences.

### 2. The CASCADE Workflow (Epistemic Process)
The core process for ensuring epistemic rigor.
*   **PREFLIGHT (Baseline Assessment):** The AI assesses its 13 epistemic vectors *before* starting work to establish a baseline.
*   **THINK (Initial Reasoning):** The AI analyzes task requirements and constraints.
*   **PLAN (Investigation Strategy):** For complex tasks, the AI creates a systematic investigation plan.
*   **INVESTIGATE (Knowledge Gathering):** The AI uses tools to address unknowns and fill knowledge gaps.
*   **CHECK (Readiness Assessment):** The AI self-assesses if remaining unknowns are acceptable before proceeding. A confidence score of >= 0.70 is typically required.
*   **ACT (Execute Task):** The AI performs the work, documenting decisions and reasoning.
*   **POSTFLIGHT (Final Assessment):** The AI re-assesses its 13 vectors *after* work to measure the "epistemic delta" (learning).

### 3. Distributed Coordination via Git
Empirica uses Git as a "cognitive substrate" for multi-agent coordination.
*   **Branches:** Represent different reasoning paths or explorations.
*   **Commits:** Act as epistemic snapshots of what the AI knew at a decision point.
*   **Merges:** Represent the integration of knowledge from different reasoning paths.
*   **Git Notes:** Store compressed, portable state for handoffs between sessions or agents, enabling massive token reduction (e.g., 97%).

### 4. Privacy-Preserving Knowledge Transfer
Instead of transferring full, sensitive conversation histories, Empirica uses **Epistemic Snapshots**.
*   **Size:** ~500 tokens (95%+ compression).
*   **Content:** Contains the 13 epistemic vectors, an abstracted context summary, semantic tags, and a reasoning brief.
*   **Excludes:** Raw conversation text, sensitive data (keys, PII), full code snippets.
This allows knowledge about confidence, uncertainty, and what was learned to be transferred without violating privacy.

### 5. Sentinel Orchestrator & The Cognitive Vault (Future Vision)
The long-term vision includes a **Cognitive Vault**—a secure, Git-native storage system—governed by a **Sentinel** (a small, open-weights language model).
*   **Sentinel's Role:** The Sentinel will be trained on the "delta packages" (learning trajectories) produced by other AIs. It will monitor all AI activity, validate epistemic commits, manage handoffs, and enforce governance policies.
*   **Self-Improving System:** This creates a feedback loop where the system gets smarter over time by learning from its own operational data.

---

## Why This Architecture Matters

*   **Provider Agnostic:** Any LLM can be an "AI Ambassador." The epistemic layer is separate.
*   **Git-Native:** Leverages a battle-tested distributed system for coordination and versioning.
*   **Self-Improving:** The training data (delta packages) is a natural byproduct of real-world usage.
*   **Secure & Private by Design:** Local-first storage and a security-focused `Bayesian Guardian` layer provide robust protection.
*   **Scalable:** The architecture supports adding more AIs without fundamental changes, as Git handles coordination.

This architecture provides the necessary infrastructure for building truly robust, auditable, and trustworthy AI systems.
