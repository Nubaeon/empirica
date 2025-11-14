Empirica: Git-Native Cognitive Operating System for AI
## Complete Technical Specification v1.0

**Date:** November 13, 2025  
**Status:** Ready for Implementation  
**Architecture:** Git-native distributed epistemic state management with Sentinel orchestration

---

## Executive Summary

Empirica is a cognitive operating system for AI that solves the fundamental reconstruction problem in AI-to-AI task handoff through git-native epistemic state management. By treating cognitive states as versioned content and leveraging Git's distributed primitives, Empirica enables:

- **Semantic compression** of reasoning via epistemic vectors (23-58% token reduction)
- **Cross-provider cognitive continuity** through Git-native transport
- **Intelligent adaptation** via confidence-calibrated execution
- **Cognitive governance** through Sentinel orchestration as Git master
- **Complete transparency** via split-brain dashboard visualization

**Core Innovation:** Epistemic state snapshots as Git commits enable efficient reasoning reconstruction across AI providers without lossy compression or expensive re-investigation.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Core Components](#2-core-components)
3. [Epistemic State Schema](#3-epistemic-state-schema)
4. [Git Integration Layer](#4-git-integration-layer)
5. [Sentinel Orchestrator](#5-sentinel-orchestrator)
6. [Split-Brain Dashboard](#6-split-brain-dashboard)
7. [Implementation Roadmap](#7-implementation-roadmap)
8. [API Reference](#8-api-reference)
9. [Security Model](#9-security-model)
10. [Testing Strategy](#10-testing-strategy)

---

## 1. Architecture Overview

### 1.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EMPIRICA ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐         ┌──────────────┐                    │
│  │  Reasoning   │         │   Acting     │                    │
│  │  AI (Claude) │         │  AI (Qwen)   │                    │
│  └──────┬───────┘         └──────┬───────┘                    │
│         │                        │                             │
│         │ Push epistemic         │ Pull epistemic             │
│         │ state commits          │ state commits              │
│         ↓                        ↓                             │
│  ┌─────────────────────────────────────────────┐              │
│  │        Git Repository (Epistemic Store)      │              │
│  │  ├── epistemic/reasoning/session-*          │              │
│  │  ├── epistemic/acting/session-*             │              │
│  │  └── epistemic/calibration/session-*        │              │
│  └─────────────┬───────────────────────────────┘              │
│                │                                               │
│                │ Monitor, orchestrate, govern                  │
│                ↓                                               │
│  ┌─────────────────────────────────────────────┐              │
│  │    Sentinel (Git Master + Orchestrator)     │              │
│  │  - Branch management (task lifecycle)       │              │
│  │  - Progress monitoring (git log/diff)       │              │
│  │  - Cross-provider sync (git remotes)        │              │
│  │  - Governance enforcement (git hooks)       │              │
│  │  - Calibration learning (git notes)         │              │
│  └─────────────────────────────────────────────┘              │
│                                                                 │
│  ┌─────────────────────────────────────────────┐              │
│  │   Split-Brain Dashboard (tmux visualization) │              │
│  │  ┌─────────────────────────────────────┐   │              │
│  │  │ Reasoning Hemisphere (Top Pane)     │   │              │
│  │  │ - Epistemic vectors in real-time    │   │              │
│  │  │ - Investigation progression         │   │              │
│  │  │ - Risk assessments                  │   │              │
│  │  └─────────────────────────────────────┘   │              │
│  │  ┌─────────────────────────────────────┐   │              │
│  │  │ Acting Hemisphere (Bottom Pane)     │   │              │
│  │  │ - Execution progress                │   │              │
│  │  │ - Deviation tracking                │   │              │
│  │  │ - Completion status                 │   │              │
│  │  └─────────────────────────────────────┘   │              │
│  └─────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Key Abstractions

| Concept | Git Primitive | Purpose |
|---------|---------------|---------|
| **Epistemic State** | Git commit | Versioned cognitive snapshot |
| **Reasoning Phase** | Git branch (epistemic/reasoning/*) | Planning and investigation |
| **Acting Phase** | Git branch (epistemic/acting/*) | Execution and adaptation |
| **Handoff** | Git push/pull | Cross-provider state transfer |
| **Calibration** | Git merge | Cognitive integration + learning |
| **Provenance** | Git signature | Trust and integrity |
| **Orchestration** | Sentinel (Git master) | Task lifecycle management |
| **Governance** | Git hooks | Policy enforcement |

### 1.3 Data Flow

```
1. Task Assigned
   └→ Sentinel creates reasoning branch
   └→ Assigns to reasoning AI via git push
   
2. Reasoning Phase
   └→ AI commits epistemic progression (PREFLIGHT → INVESTIGATE → CHECK)
   └→ Each commit: structured message + JSON state file
   └→ Sentinel monitors via git log
   
3. Handoff Decision
   └→ Sentinel analyzes epistemic state from commits
   └→ Decides if confidence sufficient for acting
   └→ Creates acting branch from reasoning endpoint
   
4. Acting Phase
   └→ Acting AI pulls epistemic state from reasoning branch
   └→ Reconstructs intent from epistemic vectors + keywords
   └→ Executes with confidence-calibrated adaptation
   └→ Commits progress (ACT → POSTFLIGHT)
   
5. Calibration
   └→ Sentinel merges reasoning + acting branches
   └→ Calculates delta via git diff
   └→ Stores learning in git notes
   └→ Adjusts future orchestration parameters
```

---

## 2. Core Components

### 2.1 Component Overview

```
empirica/
├── core/                           # Core epistemic tracking
│   ├── epistemic_state.py         # Epistemic vector management
│   ├── reflex_frame.py            # Temporal logging
│   └── session_manager.py         # Session lifecycle
│
├── git_epistemic/                  # Git integration layer
│   ├── repository.py              # Git repo management
│   ├── commit_formatter.py        # Structured commit messages
│   ├── branch_manager.py          # Branch lifecycle
│   └── remote_sync.py             # Cross-provider sync
│
├── sentinel/                       # Orchestration layer
│   ├── orchestrator.py            # Main orchestration logic
│   ├── task_analyzer.py           # Task complexity analysis
│   ├── progress_monitor.py        # Git log monitoring
│   ├── handoff_decider.py         # Handoff decision logic
│   ├── calibration.py             # Calibration calculation
│   └── hooks/                     # Git hooks for governance
│       ├── pre_commit.py
│       ├── pre_push.py
│       └── post_merge.py
│
├── dashboard/                      # Visualization layer
│   ├── tmux_manager.py            # tmux session management
│   ├── reasoning_pane.py          # Top pane rendering
│   ├── acting_pane.py             # Bottom pane rendering
│   └── corpus_callosum.py         # Integration visualization
│
├── transport/                      # Provider integration
│   ├── anthropic_provider.py      # Anthropic/Claude integration
│   ├── openai_provider.py         # OpenAI integration
│   ├── alibaba_provider.py        # Alibaba/Qwen integration
│   └── provider_base.py           # Base provider interface
│
└── cli/                            # Command-line interface
    ├── empirica.py                # Main CLI entry point
    ├── commands/
    │   ├── init.py                # Initialize repository
    │   ├── orchestrate.py         # Orchestrate task
    │   ├── monitor.py             # Monitor progress
    │   └── calibrate.py           # View calibration
    └── config.py                  # Configuration management
```

### 2.2 Technology Stack

**Core:**
- Python 3.10+
- GitPython 3.1+ (Git integration)
- SQLite 3.35+ (Session database, optional)
- pydantic 2.0+ (Data validation)

**Visualization:**
- tmux 3.2+ (Split-brain dashboard)
- rich 13.0+ (Terminal UI)
- curses (Terminal control)

**AI Providers:**
- anthropic SDK (Claude)
- openai SDK (GPT)
- Custom adapters for Qwen, Gemini, etc.

**Testing:**
- pytest 7.0+
- pytest-cov (Coverage)
- hypothesis (Property testing)

---

## 3. Epistemic State Schema

### 3.1 Core Epistemic Vectors

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class EpistemicVector(BaseModel):
    """Single epistemic dimension assessment"""
    score: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
    rationale: str = Field(description="Reasoning behind score")
    timestamp: datetime = Field(default_factory=datetime.now)

class EpistemicState(BaseModel):
    """Complete epistemic state snapshot"""
    
    # Identity
    session_id: str
    phase: str  # PREFLIGHT, INVESTIGATE, CHECK, ACT, POSTFLIGHT
    timestamp: datetime = Field(default_factory=datetime.now)
    ai_id: str  # Which AI generated this state
    
    # Core vectors (12 dimensions)
    know: EpistemicVector = Field(description="Knowledge confidence")
    do: EpistemicVector = Field(description="Execution capability confidence")
    context: EpistemicVector = Field(description="Contextual understanding")
    uncertainty: float = Field(ge=0.0, le=1.0, description="Overall uncertainty")
    
    comprehension: Optional[EpistemicVector] = None
    execution: Optional[EpistemicVector] = None
    engagement: Optional[EpistemicVector] = None
    coherence: Optional[EpistemicVector] = None
    change_awareness: Optional[EpistemicVector] = None
    impact_prediction: Optional[EpistemicVector] = None
    metacognitive_monitoring: Optional[EpistemicVector] = None
    pattern_recognition: Optional[EpistemicVector] = None
    relational_awareness: Optional[EpistemicVector] = None
    temporal_integration: Optional[EpistemicVector] = None
    
    # Phase-specific data
    task: Optional[str] = None
    investigation_findings: Optional[List[str]] = None
    investigation_keywords: Optional[List[str]] = None
    risks_assessed: Optional[List[Dict]] = None
    action_plan: Optional[Dict] = None
    deviations: Optional[List[Dict]] = None
    completion_rate: Optional[float] = None
    
    # Metadata
    confidence_to_proceed: Optional[float] = None
    decision: Optional[str] = None  # PROCEED, INVESTIGATE_MORE, CLARIFY
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123",
                "phase": "CHECK",
                "ai_id": "claude-sonnet-4",
                "know": {
                    "score": 0.85,
                    "rationale": "Thoroughly investigated OAuth 2.1 patterns"
                },
                "do": {
                    "score": 0.75,
                    "rationale": "Confident in implementation approach"
                },
                "context": {
                    "score": 0.60,
                    "rationale": "Seen main auth flow, may have missed edge cases"
                },
                "uncertainty": 0.30,
                "confidence_to_proceed": 0.85,
                "decision": "PROCEED"
            }
        }
```

### 3.2 File Structure in Git Repository

```
.empirica/
└── sessions/
    └── [session-id]/
        ├── preflight.json          # Initial assessment
        ├── investigate_1.json      # Investigation round 1
        ├── investigate_2.json      # Investigation round 2
        ├── investigate_N.json      # Investigation round N
        ├── check.json              # Readiness assessment
        ├── act_plan.json           # Execution plan
        ├── act_progress.json       # Execution progress (periodic)
        └── postflight.json         # Completion report
```

Each JSON file contains a complete `EpistemicState` object for that phase.

### 3.3 Git Commit Message Format

```
PHASE: know=X.XX do=X.XX context=X.XX uncertainty=X.XX

Task: [Brief task description]
[Phase-specific summary - findings, decision, progress, etc.]

Epistemic-State: [session-id]
AI-Agent: [ai-identifier]
```

**Example:**

```
INVESTIGATE: know=0.80 do=0.65 context=0.60 uncertainty=0.35

Task: Add OAuth 2.1 authentication with PKCE
Findings: Current JWT implementation lacks token refresh mechanism. 
OAuth 2.1 requires PKCE for public clients. Found 3 existing auth 
endpoints that will need migration.

Epistemic-State: session-abc123
AI-Agent: claude-sonnet-4-20250514
```

---

## 4. Git Integration Layer

### 4.1 Repository Management

```python
# empirica/git_epistemic/repository.py

import git
from pathlib import Path
from typing import Optional, Dict
import json

class EpistemicGitRepo:
    """
    Git-native epistemic state management
    
    Responsibilities:
    - Initialize and manage Git repository
    - Commit epistemic states with structured messages
    - Branch management for reasoning/acting/calibration
    - Remote configuration for provider sync
    - Tag management for epistemic checkpoints
    """
    
    def __init__(self, repo_path: str = "~/.empirica/git"):
        self.repo_path = Path(repo_path).expanduser()
        self.repo_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize Git repo if needed
        if not (self.repo_path / ".git").exists():
            self.repo = git.Repo.init(self.repo_path)
            self._setup_initial_structure()
        else:
            self.repo = git.Repo(self.repo_path)
    
    def _setup_initial_structure(self):
        """Initialize repository structure"""
        
        # Create .empirica/sessions directory
        sessions_dir = self.repo_path / ".empirica" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # Create .gitignore
        gitignore = self.repo_path / ".gitignore"
        gitignore.write_text("""
# Ignore temp files
*.tmp
*.swp
.DS_Store
__pycache__/
*.pyc

# Keep epistemic states
!.empirica/sessions/**/*.json
""")
        
        # Create README
        readme = self.repo_path / "README.md"
        readme.write_text("""
# Empirica Epistemic Repository

This repository stores epistemic state snapshots for AI reasoning sessions.

Structure:
- `.empirica/sessions/[session-id]/` - Epistemic state JSON files
- Branches: `epistemic/reasoning/*`, `epistemic/acting/*`, `epistemic/calibration/*`
- Tags: `epistemic/checkpoint/*` - Significant epistemic states

Each commit represents a phase in the cognitive process with structured metadata.
""")
        
        # Initial commit
        self.repo.index.add([str(gitignore), str(readme)])
        self.repo.index.commit("Initialize Empirica epistemic repository")
    
    def commit_epistemic_state(
        self,
        session_id: str,
        phase: str,
        state: EpistemicState,
        sign: bool = True
    ) -> str:
        """
        Commit epistemic state to Git
        
        Args:
            session_id: Unique session identifier
            phase: Phase name (lowercase: preflight, investigate, check, act, postflight)
            state: Complete epistemic state object
            sign: Whether to GPG sign the commit
            
        Returns:
            Commit hash (SHA-256)
        """
        
        # Create session directory
        session_path = self.repo_path / ".empirica" / "sessions" / session_id
        session_path.mkdir(parents=True, exist_ok=True)
        
        # Determine filename based on phase
        if phase == "investigate":
            # Number investigation rounds
            existing = list(session_path.glob("investigate_*.json"))
            round_num = len(existing) + 1
            filename = f"investigate_{round_num}.json"
        else:
            filename = f"{phase}.json"
        
        # Write state to file
        state_file = session_path / filename
        state_file.write_text(state.model_dump_json(indent=2))
        
        # Git add
        rel_path = state_file.relative_to(self.repo_path)
        self.repo.index.add([str(rel_path)])
        
        # Format commit message
        commit_msg = self._format_commit_message(state)
        
        # Git commit
        if sign:
            commit = self.repo.index.commit(commit_msg, sign=True)
        else:
            commit = self.repo.index.commit(commit_msg)
        
        return commit.hexsha
    
    def _format_commit_message(self, state: EpistemicState) -> str:
        """Format structured commit message from epistemic state"""
        
        # Extract core vectors
        know = state.know.score
        do = state.do.score
        context = state.context.score
        uncertainty = state.uncertainty
        
        # Phase-specific summary
        summary = self._extract_phase_summary(state)
        
        # Construct message
        return f"""{state.phase.upper()}: know={know:.2f} do={do:.2f} context={context:.2f} uncertainty={uncertainty:.2f}

Task: {state.task or 'Not specified'}
{summary}

Epistemic-State: {state.session_id}
AI-Agent: {state.ai_id}"""
    
    def _extract_phase_summary(self, state: EpistemicState) -> str:
        """Extract phase-specific summary from state"""
        
        phase = state.phase.lower()
        
        if phase == "preflight":
            return f"Initial assessment completed. Uncertainty: {state.uncertainty:.2f}"
        
        elif phase == "investigate":
            findings = state.investigation_findings or []
            keywords = state.investigation_keywords or []
            return f"Findings: {'; '.join(findings[:2])}\nKeywords: {', '.join(keywords[:5])}"
        
        elif phase == "check":
            decision = state.decision or "Unknown"
            confidence = state.confidence_to_proceed or 0
            risks = len(state.risks_assessed or [])
            return f"Decision: {decision} (confidence={confidence:.2f})\nRisks assessed: {risks}"
        
        elif phase == "act":
            if state.action_plan:
                steps = len(state.action_plan.get('steps', []))
                return f"Execution plan created: {steps} steps"
            else:
                return "Execution in progress"
        
        elif phase == "postflight":
            completion = state.completion_rate or 0
            deviations = len(state.deviations or [])
            return f"Completion: {completion:.0%}\nDeviations: {deviations}"
        
        return "No summary available"
    
    def create_reasoning_branch(self, session_id: str) -> str:
        """Create branch for reasoning phase"""
        branch_name = f"epistemic/reasoning/{session_id}"
        
        if branch_name not in [b.name for b in self.repo.branches]:
            branch = self.repo.create_head(branch_name)
        else:
            branch = self.repo.branches[branch_name]
        
        branch.checkout()
        return branch_name
    
    def create_acting_branch(
        self,
        session_id: str,
        from_reasoning: bool = True
    ) -> str:
        """Create branch for acting phase"""
        branch_name = f"epistemic/acting/{session_id}"
        
        if from_reasoning:
            # Branch from reasoning completion point
            reasoning_branch = f"epistemic/reasoning/{session_id}"
            if reasoning_branch in [b.name for b in self.repo.branches]:
                base = self.repo.branches[reasoning_branch].commit
                branch = self.repo.create_head(branch_name, base)
            else:
                raise ValueError(f"Reasoning branch not found: {reasoning_branch}")
        else:
            branch = self.repo.create_head(branch_name)
        
        branch.checkout()
        return branch_name
    
    def merge_for_calibration(
        self,
        session_id: str,
        reasoning_branch: str,
        acting_branch: str
    ) -> str:
        """
        Merge reasoning and acting branches for calibration
        
        Returns:
            Calibration commit hash
        """
        
        # Create calibration branch
        calib_branch = f"epistemic/calibration/{session_id}"
        self.repo.create_head(calib_branch).checkout()
        
        # Merge reasoning (no fast-forward to preserve history)
        try:
            self.repo.git.merge(
                reasoning_branch,
                no_ff=True,
                m=f"Merge reasoning phase: {session_id}"
            )
        except git.GitCommandError as e:
            raise ValueError(f"Failed to merge reasoning branch: {e}")
        
        # Merge acting (no fast-forward)
        try:
            self.repo.git.merge(
                acting_branch,
                no_ff=True,
                m=f"Merge acting phase: {session_id}"
            )
        except git.GitCommandError as e:
            raise ValueError(f"Failed to merge acting branch: {e}")
        
        return self.repo.head.commit.hexsha
    
    def add_provider_remote(self, provider: str, url: str):
        """Add remote for AI provider"""
        try:
            self.repo.create_remote(provider, url)
        except git.GitCommandError:
            # Remote already exists, update URL
            remote = self.repo.remote(provider)
            remote.set_url(url)
    
    def push_to_provider(
        self,
        branch: str,
        provider: str = "origin",
        force: bool = False
    ):
        """Push branch to provider remote"""
        remote = self.repo.remote(provider)
        if force:
            remote.push(branch, force=True)
        else:
            remote.push(branch)
    
    def fetch_from_provider(
        self,
        branch: str,
        provider: str = "origin"
    ):
        """Fetch branch from provider remote"""
        remote = self.repo.remote(provider)
        remote.fetch(branch)
    
    def tag_checkpoint(
        self,
        session_id: str,
        checkpoint_name: str,
        message: Optional[str] = None
    ):
        """Tag significant epistemic checkpoint"""
        tag_name = f"epistemic/checkpoint/{checkpoint_name}/{session_id}"
        self.repo.create_tag(tag_name, message=message or checkpoint_name)
    
    def load_epistemic_state(
        self,
        session_id: str,
        phase: str,
        commit: Optional[str] = None
    ) -> Optional[EpistemicState]:
        """
        Load epistemic state from Git
        
        Args:
            session_id: Session identifier
            phase: Phase name
            commit: Specific commit hash (optional, uses HEAD if None)
            
        Returns:
            EpistemicState object or None if not found
        """
        
        session_path = Path(".empirica") / "sessions" / session_id
        
        # Determine filename
        if phase == "investigate":
            # Load latest investigation round
            pattern = f"investigate_*.json"
            matching = list((self.repo_path / session_path).glob(pattern))
            if not matching:
                return None
            filename = sorted(matching)[-1].name
        else:
            filename = f"{phase}.json"
        
        file_path = session_path / filename
        
        try:
            if commit:
                # Load from specific commit
                content = self.repo.git.show(f"{commit}:{file_path}")
            else:
                # Load from working directory
                full_path = self.repo_path / file_path
                if not full_path.exists():
                    return None
                content = full_path.read_text()
            
            data = json.loads(content)
            return EpistemicState(**data)
        
        except (git.GitCommandError, FileNotFoundError, json.JSONDecodeError):
            return None
    
    def get_commit_history(
        self,
        branch: str,
        max_count: Optional[int] = None
    ) -> list:
        """Get commit history for branch"""
        commits = list(self.repo.iter_commits(branch, max_count=max_count))
        return [
            {
                'hash': c.hexsha,
                'message': c.message,
                'author': str(c.author),
                'timestamp': c.committed_datetime,
                'signed': c.gpgsig is not None
            }
            for c in commits
        ]
```

### 4.2 Branch Management Strategy

```python
# empirica/git_epistemic/branch_manager.py

from typing import Optional, List
from enum import Enum

class BranchType(Enum):
    REASONING = "reasoning"
    ACTING = "acting"
    CALIBRATION = "calibration"

class BranchManager:
    """
    Manages Git branch lifecycle for epistemic sessions
    """
    
    def __init__(self, repo: EpistemicGitRepo):
        self.repo = repo
    
    def get_branch_name(
        self,
        branch_type: BranchType,
        session_id: str
    ) -> str:
        """Generate branch name following convention"""
        return f"epistemic/{branch_type.value}/{session_id}"
    
    def create_session_branches(self, session_id: str):
        """Create all branches for a session"""
        
        # Create reasoning branch
        reasoning = self.get_branch_name(BranchType.REASONING, session_id)
        self.repo.create_reasoning_branch(session_id)
        
        # Set branch metadata via git config
        self._set_branch_config(reasoning, {
            'session-id': session_id,
            'branch-type': 'reasoning',
            'created': datetime.now().isoformat()
        })
    
    def _set_branch_config(self, branch: str, config: dict):
        """Set branch-specific configuration"""
        for key, value in config.items():
            self.repo.repo.git.config(
                f"branch.{branch}.{key}",
                value
            )
    
    def get_branch_config(self, branch: str) -> dict:
        """Get branch-specific configuration"""
        config = {}
        try:
            # Read all config for this branch
            output = self.repo.repo.git.config(
                '--get-regexp',
                f"^branch\\.{branch}\\."
            )
            for line in output.split('\n'):
                if line:
                    key, value = line.split(' ', 1)
                    # Remove "branch.{branch}." prefix
                    key = key.replace(f"branch.{branch}.", "")
                    config[key] = value
        except git.GitCommandError:
            pass
        return config
    
    def list_active_sessions(self) -> List[dict]:
        """List all active epistemic sessions"""
        
        sessions = {}
        
        for branch in self.repo.repo.branches:
            if branch.name.startswith("epistemic/"):
                parts = branch.name.split('/')
                if len(parts) >= 3:
                    branch_type = parts[1]
                    session_id = parts[2]
                    
                    if session_id not in sessions:
                        sessions[session_id] = {
                            'session_id': session_id,
                            'branches': {}
                        }
                    
                    sessions[session_id]['branches'][branch_type] = {
                        'name': branch.name,
                        'last_commit': branch.commit.hexsha,
                        'last_updated': branch.commit.committed_datetime
                    }
        
        return list(sessions.values())
```

---

## 5. Sentinel Orchestrator

### 5.1 Main Orchestrator

```python
# empirica/sentinel/orchestrator.py

from typing import Optional, Dict, List
import time
from datetime import datetime

class SentinelOrchestrator:
    """
    Sentinel: Git-native cognitive orchestration
    
    Responsibilities:
    - Task assignment and branch creation
    - Epistemic progression monitoring via Git log
    - Handoff decision making
    - Cross-provider coordination via Git remotes
    - Calibration and learning
    - Governance enforcement via Git hooks
    """
    
    def __init__(
        self,
        repo: EpistemicGitRepo,
        config: Optional[Dict] = None
    ):
        self.repo = repo
        self.config = config or self._default_config()
        self.branch_manager = BranchManager(repo)
        self.task_analyzer = TaskAnalyzer()
        self.progress_monitor = ProgressMonitor(repo)
        self.handoff_decider = HandoffDecider(config)
        self.calibrator = Calibrator(repo)
        
        # Install Git hooks for governance
        self._install_governance_hooks()
    
    def _default_config(self) -> Dict:
        """Default Sentinel configuration"""
        return {
            'handoff_threshold': 0.75,
            'max_investigation_rounds': 5,
            'require_signed_commits': True,
            'auto_calibration': True,
            'learning_enabled': True
        }
    
    def orchestrate_task(
        self,
        task: str,
        reasoning_ai: str = "claude",
        acting_ai: str = "qwen",
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Orchestrate complete reasoning → acting → calibration cycle
        
        Args:
            task: Task description
            reasoning_ai: AI provider for reasoning
            acting_ai: AI provider for acting
            session_id: Optional session ID (generated if None)
            
        Returns:
            Orchestration result with calibration data
        """
        
        # Generate session ID
        if session_id is None:
            session_id = self._generate_session_id()
        
        print(f"[Sentinel] Orchestrating task: {task}")
        print(f"[Sentinel] Session ID: {session_id}")
        
        # Phase 1: Reasoning
        print(f"[Sentinel] Phase 1: Reasoning ({reasoning_ai})")
        reasoning_result = self._orchestrate_reasoning(
            session_id, task, reasoning_ai
        )
        
        if not reasoning_result['success']:
            return {
                'success': False,
                'phase': 'reasoning',
                'error': reasoning_result.get('error')
            }
        
        reasoning_branch = reasoning_result['branch']
        
        # Phase 2: Handoff Decision
        print(f"[Sentinel] Phase 2: Handoff Decision")
        handoff_decision = self._make_handoff_decision(reasoning_branch)
        
        if not handoff_decision['approved']:
            print(f"[Sentinel] Handoff denied: {handoff_decision['reason']}")
            return {
                'success': False,
                'phase': 'handoff_decision',
                'reason': handoff_decision['reason'],
                'recommendation': handoff_decision.get('recommendation')
            }
        
        # Phase 3: Acting
        print(f"[Sentinel] Phase 3: Acting ({acting_ai})")
        acting_result = self._orchestrate_acting(
            session_id, reasoning_branch, acting_ai
        )
        
        if not acting_result['success']:
            return {
                'success': False,
                'phase': 'acting',
                'error': acting_result.get('error')
            }
        
        acting_branch = acting_result['branch']
        
        # Phase 4: Calibration
        print(f"[Sentinel] Phase 4: Calibration")
        calibration = self._orchestrate_calibration(
            session_id, reasoning_branch, acting_branch
        )
        
        # Phase 5: Learning
        if self.config['learning_enabled']:
            print(f"[Sentinel] Phase 5: Learning")
            self._learn_from_calibration(calibration)
        
        return {
            'success': True,
            'session_id': session_id,
            'reasoning_branch': reasoning_branch,
            'acting_branch': acting_branch,
            'calibration': calibration
        }
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        from uuid import uuid4
        return f"session-{uuid4().hex[:12]}"
    
    def _orchestrate_reasoning(
        self,
        session_id: str,
        task: str,
        reasoning_ai: str
    ) -> Dict:
        """Orchestrate reasoning phase"""
        
        # Analyze task
        analysis = self.task_analyzer.analyze(task)
        
        # Create reasoning branch
        reasoning_branch = self.branch_manager.get_branch_name(
            BranchType.REASONING, session_id
        )
        self.repo.create_reasoning_branch(session_id)
        
        # Set branch metadata
        self.branch_manager._set_branch_config(reasoning_branch, {
            'task': task,
            'complexity': analysis['complexity'],
            'risk': analysis['risk'],
            'assigned-ai': reasoning_ai,
            'started': datetime.now().isoformat()
        })
        
        # Tag task assignment
        self.repo.tag_checkpoint(
            session_id,
            'task-assigned',
            f"Sentinel assigned to {reasoning_ai}"
        )
        
        # Push to reasoning AI's provider
        try:
            self.repo.push_to_provider(reasoning_branch, provider=reasoning_ai)
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to push to {reasoning_ai}: {e}"
            }
        
        # Monitor reasoning progress
        self.progress_monitor.watch_reasoning(reasoning_branch, reasoning_ai)
        
        return {
            'success': True,
            'branch': reasoning_branch,
            'analysis': analysis
        }
    
    def _make_handoff_decision(self, reasoning_branch: str) -> Dict:
        """Decide if reasoning is sufficient for acting handoff"""
        
        # Get commit history
        commits = self.repo.get_commit_history(reasoning_branch)
        
        # Parse epistemic states from commits
        states = []
        for commit in commits:
            state = self._parse_commit_epistemic_state(commit['message'])
            if state:
                states.append(state)
        
        if not states:
            return {
                'approved': False,
                'reason': 'No epistemic states found',
                'recommendation': 'Ensure reasoning AI commits epistemic states'
            }
        
        # Use HandoffDecider logic
        decision = self.handoff_decider.decide(states)
        
        return decision
    
    def _parse_commit_epistemic_state(self, commit_message: str) -> Optional[Dict]:
        """Parse epistemic state from commit message"""
        
        lines = commit_message.strip().split('\n')
        if not lines:
            return None
        
        # Parse first line: "PHASE: know=X.XX do=X.XX context=X.XX uncertainty=X.XX"
        first_line = lines[0]
        if ':' not in first_line:
            return None
        
        phase, vectors = first_line.split(':', 1)
        phase = phase.strip()
        
        # Parse vectors
        state = {'phase': phase}
        for pair in vectors.split():
            if '=' in pair:
                key, value = pair.split('=')
                try:
                    state[key] = float(value)
                except ValueError:
                    pass
        
        # Parse additional info from body
        for line in lines[1:]:
            if line.startswith('Task:'):
                state['task'] = line.replace('Task:', '').strip()
            elif line.startswith('Decision:'):
                decision_line = line.replace('Decision:', '').strip()
                if '(confidence=' in decision_line:
                    decision, conf = decision_line.split('(confidence=')
                    state['decision'] = decision.strip()
                    state['confidence_to_proceed'] = float(conf.rstrip(')'))
                else:
                    state['decision'] = decision_line
        
        return state
    
    def _orchestrate_acting(
        self,
        session_id: str,
        reasoning_branch: str,
        acting_ai: str
    ) -> Dict:
        """Orchestrate acting phase"""
        
        # Create acting branch from reasoning endpoint
        acting_branch = self.branch_manager.get_branch_name(
            BranchType.ACTING, session_id
        )
        
        try:
            self.repo.create_acting_branch(session_id, from_reasoning=True)
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to create acting branch: {e}"
            }
        
        # Fetch reasoning state from reasoning AI's provider
        reasoning_ai_name = self.branch_manager.get_branch_config(
            reasoning_branch
        ).get('assigned-ai', 'origin')
        
        try:
            self.repo.fetch_from_provider(reasoning_branch, reasoning_ai_name)
        except Exception as e:
            print(f"[Sentinel] Warning: Could not fetch from {reasoning_ai_name}: {e}")
        
        # Push acting branch to acting AI's provider
        try:
            self.repo.push_to_provider(acting_branch, provider=acting_ai)
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to push to {acting_ai}: {e}"
            }
        
        # Monitor acting progress
        self.progress_monitor.watch_acting(acting_branch, acting_ai)
        
        return {
            'success': True,
            'branch': acting_branch
        }
    
    def _orchestrate_calibration(
        self,
        session_id: str,
        reasoning_branch: str,
        acting_branch: str
    ) -> Dict:
        """Orchestrate calibration phase"""
        
        # Merge branches
        try:
            calib_commit = self.repo.merge_for_calibration(
                session_id, reasoning_branch, acting_branch
            )
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to merge for calibration: {e}"
            }
        
        # Calculate calibration delta
        calibration = self.calibrator.calculate(
            session_id, reasoning_branch, acting_branch
        )
        
        # Commit calibration results
        calib_state = EpistemicState(
            session_id=session_id,
            phase="CALIBRATION",
            ai_id="sentinel",
            know=EpistemicVector(
                score=calibration['reasoner_confidence'],
                rationale="From reasoning phase"
            ),
            do=EpistemicVector(
                score=calibration['actual_difficulty'],
                rationale="From acting phase"
            ),
            context=EpistemicVector(score=0, rationale="N/A"),
            uncertainty=abs(calibration['delta'])
        )
        
        self.repo.commit_epistemic_state(
            session_id, "calibration", calib_state, sign=False
        )
        
        return calibration
    
    def _learn_from_calibration(self, calibration: Dict):
        """Learn from calibration to improve future orchestration"""
        
        delta = calibration['delta']
        
        # Store learning in Git notes
        note = {
            'calibration_delta': delta,
            'learned_at': datetime.now().isoformat(),
            'recommendation': self._generate_recommendation(calibration)
        }
        
        self.repo.repo.git.notes('add', '-m', json.dumps(note))
        
        # Adjust orchestration parameters based on calibration
        if abs(delta) > 0.20:
            # Significant miscalibration
            if delta < 0:
                # Reasoner was overcautious - lower handoff threshold
                self.config['handoff_threshold'] = max(
                    0.60,
                    self.config['handoff_threshold'] - 0.05
                )
                print(f"[Sentinel] Learning: Lowering handoff threshold to {self.config['handoff_threshold']:.2f}")
            else:
                # Reasoner was overconfident - raise handoff threshold
                self.config['handoff_threshold'] = min(
                    0.90,
                    self.config['handoff_threshold'] + 0.05
                )
                print(f"[Sentinel] Learning: Raising handoff threshold to {self.config['handoff_threshold']:.2f}")
    
    def _generate_recommendation(self, calibration: Dict) -> str:
        """Generate recommendation from calibration"""
        
        delta = calibration['delta']
        
        if abs(delta) < 0.10:
            return "Well calibrated - continue current approach"
        elif delta < -0.20:
            return "Significantly overcautious - trust initial assessments more"
        elif delta < 0:
            return "Somewhat overcautious - reduce investigation depth"
        elif delta > 0.20:
            return "Significantly overconfident - investigate more thoroughly"
        else:
            return "Somewhat overconfident - add investigation round"
    
    def _install_governance_hooks(self):
        """Install Git hooks for governance enforcement"""
        
        hooks_dir = self.repo.repo_path / ".git" / "hooks"
        hooks_dir.mkdir(exist_ok=True)
        
        # Pre-commit hook: Validate epistemic state structure
        self._install_pre_commit_hook(hooks_dir)
        
        # Pre-push hook: Verify commit signatures
        if self.config['require_signed_commits']:
            self._install_pre_push_hook(hooks_dir)
        
        # Post-merge hook: Auto-calculate calibration
        if self.config['auto_calibration']:
            self._install_post_merge_hook(hooks_dir)
    
    def _install_pre_commit_hook(self, hooks_dir: Path):
        """Install pre-commit validation hook"""
        
        hook_script = """#!/usr/bin/env python3
import json
import sys
import subprocess

# Get staged files
result = subprocess.run(
    ['git', 'diff', '--cached', '--name-only'],
    capture_output=True, text=True
)

for file in result.stdout.strip().split('\\n'):
    if '.empirica/sessions' in file and file.endswith('.json'):
        try:
            with open(file) as f:
                state = json.load(f)
            
            # Validate required fields
            required = ['session_id', 'phase', 'timestamp', 'ai_id']
            missing = [f for f in required if f not in state]
            if missing:
                print(f"ERROR: {file} missing required fields: {missing}")
                sys.exit(1)
            
            # Validate vector scores in range [0, 1]
            for vector in ['know', 'do', 'context']:
                if vector in state and isinstance(state[vector], dict):
                    score = state[vector].get('score')
                    if score is not None and not (0 <= score <= 1):
                        print(f"ERROR: {file} {vector}.score out of range: {score}")
                        sys.exit(1)
            
            # Validate uncertainty in range [0, 1]
            if 'uncertainty' in state:
                unc = state['uncertainty']
                if not (0 <= unc <= 1):
                    print(f"ERROR: {file} uncertainty out of range: {unc}")
                    sys.exit(1)
                    
        except json.JSONDecodeError as e:
            print(f"ERROR: {file} is not valid JSON: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: {file} validation failed: {e}")
            sys.exit(1)

print("✓ Sentinel: Epistemic states validated")
"""
        
        hook_path = hooks_dir / "pre-commit"
        hook_path.write_text(hook_script)
        hook_path.chmod(0o755)
    
    def _install_pre_push_hook(self, hooks_dir: Path):
        """Install pre-push signature verification hook"""
        
        hook_script = """#!/bin/bash
# Sentinel pre-push: Require signed commits

# Check for unsigned commits
UNSIGNED=$(git log --format=%H --show-signature origin/$(git branch --show-current)..HEAD 2>&1 | grep -c "Can't check signature" || true)

if [ "$UNSIGNED" -gt 0 ]; then
    echo "ERROR: Sentinel requires signed commits"
    echo "Sign commits with: git commit -S"
    exit 1
fi

echo "✓ Sentinel: All commits signed"
"""
        
        hook_path = hooks_dir / "pre-push"
        hook_path.write_text(hook_script)
        hook_path.chmod(0o755)
    
    def _install_post_merge_hook(self, hooks_dir: Path):
        """Install post-merge calibration hook"""
        
        hook_script = """#!/usr/bin/env python3
import subprocess
import sys

# Check if this is a calibration merge
result = subprocess.run(
    ['git', 'log', '-1', '--format=%s'],
    capture_output=True, text=True
)

merge_msg = result.stdout.strip()

if 'Merge reasoning phase' in merge_msg or 'Merge acting phase' in merge_msg:
    print("✓ Sentinel: Calibration merge detected")
    # Calibration calculation happens in orchestrator
"""
        
        hook_path = hooks_dir / "post-merge"
        hook_path.write_text(hook_script)
        hook_path.chmod(0o755)
```

### 5.2 Handoff Decision Logic

```python
# empirica/sentinel/handoff_decider.py

from typing import List, Dict, Optional

class HandoffDecider:
    """
    Decides when reasoning is sufficient for handoff to acting
    """
    
    def __init__(self, config: Dict):
        self.config = config
    
    def decide(self, states: List[Dict]) -> Dict:
        """
        Decide if handoff should be approved
        
        Args:
            states: List of epistemic states from commits
            
        Returns:
            Decision dict with 'approved', 'reason', 'recommendation'
        """
        
        if not states:
            return {
                'approved': False,
                'reason': 'No epistemic states available',
                'recommendation': 'Ensure reasoning AI commits states'
            }
        
        latest = states[-1]
        
        # Check 1: Is there a CHECK phase?
        if latest['phase'] != 'CHECK':
            return {
                'approved': False,
                'reason': f"Reasoning incomplete (phase: {latest['phase']})",
                'recommendation': 'Continue reasoning until CHECK phase'
            }
        
        # Check 2: Is confidence sufficient?
        confidence = latest.get('confidence_to_proceed', 0)
        threshold = self.config.get('handoff_threshold', 0.75)
        
        if confidence < threshold:
            return {
                'approved': False,
                'reason': f"Confidence too low ({confidence:.2f} < {threshold:.2f})",
                'recommendation': 'Continue investigation to increase confidence'
            }
        
        # Check 3: Has investigation stabilized?
        if not self._is_investigation_stabilized(states):
            return {
                'approved': False,
                'reason': 'Investigation still improving significantly',
                'recommendation': 'Continue investigation until confidence stabilizes'
            }
        
        # Check 4: Is decision explicit?
        decision = latest.get('decision', '')
        if decision != 'PROCEED':
            return {
                'approved': False,
                'reason': f"Decision is not PROCEED (got: {decision})",
                'recommendation': 'Resolve concerns before proceeding'
            }
        
        # All checks passed
        return {
            'approved': True,
            'reason': f"Handoff approved (confidence={confidence:.2f})",
            'confidence': confidence
        }
    
    def _is_investigation_stabilized(self, states: List[Dict]) -> bool:
        """Check if epistemic confidence has stabilized"""
        
        # Get investigation states only
        investigate_states = [s for s in states if s['phase'] == 'INVESTIGATE']
        
        if len(investigate_states) < 2:
            return True  # Not enough data, allow handoff
        
        # Check last 3 rounds
        recent = investigate_states[-3:]
        confidences = [s.get('know', 0) for s in recent]
        
        # Calculate improvement rate
        improvements = [
            confidences[i+1] - confidences[i]
            for i in range(len(confidences)-1)
        ]
        
        # If improvement < 0.05 per round, consider stabilized
        return all(imp < 0.05 for imp in improvements)
```

### 5.3 Progress Monitoring

```python
# empirica/sentinel/progress_monitor.py

import time
from typing import Callable, Optional

class ProgressMonitor:
    """
    Monitors epistemic progression via Git log polling
    """
    
    def __init__(self, repo: EpistemicGitRepo):
        self.repo = repo
    
    def watch_reasoning(
        self,
        branch: str,
        provider: str,
        poll_interval: int = 5,
        timeout: Optional[int] = 300
    ):
        """
        Watch reasoning progress via Git log
        
        Args:
            branch: Branch to monitor
            provider: Provider to fetch from
            poll_interval: Seconds between polls
            timeout: Maximum seconds to wait (None = indefinite)
        """
        
        start_time = time.time()
        last_commit = None
        
        print(f"[Sentinel] Monitoring {branch} on {provider}")
        
        while True:
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                print(f"[Sentinel] Timeout waiting for reasoning completion")
                break
            
            # Fetch latest from provider
            try:
                self.repo.fetch_from_provider(branch, provider)
            except Exception as e:
                print(f"[Sentinel] Warning: Fetch failed: {e}")
                time.sleep(poll_interval)
                continue
            
            # Get latest commit
            try:
                commits = self.repo.get_commit_history(
                    f"{provider}/{branch}", max_count=1
                )
                if commits:
                    current_commit = commits[0]
                else:
                    time.sleep(poll_interval)
                    continue
            except Exception:
                time.sleep(poll_interval)
                continue
            
            # Check if new commit
            if current_commit['hash'] != last_commit:
                # Parse phase from commit message
                first_line = current_commit['message'].split('\n')[0]
                if ':' in first_line:
                    phase = first_line.split(':')[0].strip()
                    print(f"[Sentinel] Progress: {phase} completed")
                    
                    # Check if reasoning complete (CHECK phase)
                    if phase == 'CHECK':
                        print(f"[Sentinel] Reasoning complete")
                        break
                
                last_commit = current_commit['hash']
            
            time.sleep(poll_interval)
    
    def watch_acting(
        self,
        branch: str,
        provider: str,
        poll_interval: int = 5,
        timeout: Optional[int] = 600
    ):
        """Watch acting progress via Git log"""
        
        start_time = time.time()
        last_commit = None
        
        print(f"[Sentinel] Monitoring {branch} on {provider}")
        
        while True:
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                print(f"[Sentinel] Timeout waiting for acting completion")
                break
            
            # Fetch latest
            try:
                self.repo.fetch_from_provider(branch, provider)
            except Exception as e:
                print(f"[Sentinel] Warning: Fetch failed: {e}")
                time.sleep(poll_interval)
                continue
            
            # Get latest commit
            try:
                commits = self.repo.get_commit_history(
                    f"{provider}/{branch}", max_count=1
                )
                if commits:
                    current_commit = commits[0]
                else:
                    time.sleep(poll_interval)
                    continue
            except Exception:
                time.sleep(poll_interval)
                continue
            
            # Check if new commit
            if current_commit['hash'] != last_commit:
                first_line = current_commit['message'].split('\n')[0]
                if ':' in first_line:
                    phase = first_line.split(':')[0].strip()
                    print(f"[Sentinel] Progress: {phase}")
                    
                    # Check if acting complete (POSTFLIGHT)
                    if phase == 'POSTFLIGHT':
                        print(f"[Sentinel] Acting complete")
                        break
                
                last_commit = current_commit['hash']
            
            time.sleep(poll_interval)
```

### 5.4 Calibration Calculator

```python
# empirica/sentinel/calibration.py

from typing import Dict

class Calibrator:
    """
    Calculates calibration delta between reasoning and acting
    """
    
    def __init__(self, repo: EpistemicGitRepo):
        self.repo = repo
    
    def calculate(
        self,
        session_id: str,
        reasoning_branch: str,
        acting_branch: str
    ) -> Dict:
        """
        Calculate calibration delta from Git diff
        
        Returns:
            Calibration dict with delta, feedback, etc.
        """
        
        # Load reasoning final state (CHECK phase)
        reasoning_state = self.repo.load_epistemic_state(
            session_id, "check"
        )
        
        # Load acting final state (POSTFLIGHT phase)
        acting_state = self.repo.load_epistemic_state(
            session_id, "postflight"
        )
        
        if not reasoning_state or not acting_state:
            return {
                'success': False,
                'error': 'Could not load states for calibration'
            }
        
        # Extract key metrics
        reasoner_confidence = reasoning_state.confidence_to_proceed or 0
        actual_difficulty = acting_state.completion_rate or 0
        
        # Invert completion rate to get difficulty
        # (higher completion = lower difficulty)
        actual_difficulty = 1.0 - actual_difficulty
        
        # Calculate delta
        delta = actual_difficulty - reasoner_confidence
        
        # Count deviations
        deviations = len(acting_state.deviations or [])
        
        # Generate feedback
        feedback = self._generate_feedback(
            delta, deviations, reasoning_state, acting_state
        )
        
        return {
            'success': True,
            'session_id': session_id,
            'reasoner_confidence': reasoner_confidence,
            'actual_difficulty': actual_difficulty,
            'delta': delta,
            'deviations': deviations,
            'feedback': feedback
        }
    
    def _generate_feedback(
        self,
        delta: float,
        deviations: int,
        reasoning_state: EpistemicState,
        acting_state: EpistemicState
    ) -> str:
        """Generate calibration feedback"""
        
        if abs(delta) < 0.10:
            feedback = "Well calibrated - reasoning confidence matched reality."
        elif delta < -0.20:
            feedback = f"Significantly overcautious (delta={delta:.2f}). "
            feedback += "You investigated thoroughly but task was simpler than expected. "
            feedback += "For similar tasks, trust initial assessment more."
        elif delta < 0:
            feedback = f"Somewhat overcautious (delta={delta:.2f}). "
            feedback += "Task was slightly easier than predicted. "
            feedback += "Consider reducing investigation depth for familiar domains."
        elif delta > 0.20:
            feedback = f"Significantly overconfident (delta={delta:.2f}). "
            feedback += "Task was harder than expected. "
            feedback += "Investigate more thoroughly before proceeding, especially for high-risk tasks."
        else:
            feedback = f"Somewhat overconfident (delta={delta:.2f}). "
            feedback += "Task was slightly harder than predicted. "
            feedback += "Add one more investigation round for similar complexity."
        
        # Add deviation context
        if deviations > 0:
            feedback += f"\n\nActing AI made {deviations} deviation(s) from plan. "
            if reasoning_state.context.score < 0.65:
                feedback += "This aligns with your low CONTEXT score - you likely missed some details."
            else:
                feedback += "Review deviations to see if they were beneficial adaptations or plan errors."
        
        return feedback
```

---

## 6. Split-Brain Dashboard

### 6.1 Dashboard Architecture

```python
# empirica/dashboard/tmux_manager.py

import subprocess
from typing import Optional
from pathlib import Path

class TmuxDashboard:
    """
    Split-brain dashboard using tmux
    
    Layout:
    ┌─────────────────────────────────────────┐
    │  Reasoning Hemisphere (Top 60%)         │
    │  - Epistemic vectors                    │
    │  - Investigation progress               │
    │  - Risk assessments                     │
    ├─────────────────────────────────────────┤
    │  Acting Hemisphere (Bottom 40%)         │
    │  - Execution progress                   │
    │  - Deviations                           │
    │  - Completion status                    │
    └─────────────────────────────────────────┘
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.tmux_session = f"empirica-{session_id}"
        self.reasoning_pane = 0
        self.acting_pane = 1
    
    def start(self):
        """Initialize split-brain dashboard"""
        
        # Create tmux session
        subprocess.run([
            'tmux', 'new-session', '-d', '-s', self.tmux_session
        ])
        
        # Split window vertically (60/40)
        subprocess.run([
            'tmux', 'split-window', '-v', '-p', '40',
            '-t', self.tmux_session
        ])
        
        # Configure panes
        self._setup_reasoning_pane()
        self._setup_acting_pane()
        
        # Attach to session
        subprocess.run(['tmux', 'attach', '-t', self.tmux_session])
    
    def _setup_reasoning_pane(self):
        """Setup top pane for reasoning hemisphere"""
        
        # Run reasoning monitor in top pane
        cmd = f"empirica monitor --reasoning --session {self.session_id}"
        subprocess.run([
            'tmux', 'send-keys', '-t', f"{self.tmux_session}:{self.reasoning_pane}",
            cmd, 'Enter'
        ])
    
    def _setup_acting_pane(self):
        """Setup bottom pane for acting hemisphere"""
        
        # Run acting monitor in bottom pane
        cmd = f"empirica monitor --acting --session {self.session_id}"
        subprocess.run([
            'tmux', 'send-keys', '-t', f"{self.tmux_session}:{self.acting_pane}",
            cmd, 'Enter'
        ])
    
    def stop(self):
        """Stop dashboard"""
        subprocess.run(['tmux', 'kill-session', '-t', self.tmux_session])
```

### 6.2 Reasoning Pane Renderer

```python
# empirica/dashboard/reasoning_pane.py

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.progress import BarColumn, Progress
import time

class ReasoningPaneRenderer:
    """
    Renders reasoning hemisphere in real-time
    """
    
    def __init__(self, repo: EpistemicGitRepo, session_id: str):
        self.repo = repo
        self.session_id = session_id
        self.console = Console()
    
    def render_loop(self):
        """Main rendering loop"""
        
        with Live(self._render(), console=self.console, refresh_per_second=2) as live:
            while True:
                live.update(self._render())
                time.sleep(0.5)
    
    def _render(self) -> Panel:
        """Render reasoning hemisphere display"""
        
        # Load latest reasoning state
        branch = f"epistemic/reasoning/{self.session_id}"
        
        try:
            commits = self.repo.get_commit_history(branch, max_count=1)
            if not commits:
                return Panel("Waiting for reasoning to begin...", 
                           title="Reasoning Hemisphere")
            
            latest = commits[0]
            state = self._parse_commit(latest['message'])
            
        except Exception as e:
            return Panel(f"Error loading state: {e}",
                       title="Reasoning Hemisphere")
        
        # Build display
        content = []
        
        # Epistemic vectors
        vectors_table = Table(show_header=False, box=None)
        vectors_table.add_column(style="cyan")
        vectors_table.add_column(style="green")
        
        progress = Progress(BarColumn(bar_width=20), expand=False)
        
        know_bar = progress.add_task("", total=1.0, completed=state.get('know', 0))
        do_bar = progress.add_task("", total=1.0, completed=state.get('do', 0))
        context_bar = progress.add_task("", total=1.0, completed=state.get('context', 0))
        uncertainty_bar = progress.add_task("", total=1.0, 
                                           completed=state.get('uncertainty', 0))
        
        vectors_table.add_row("KNOW:", f"{state.get('know', 0):.2f} {progress.get_renderable(know_bar)}")
        vectors_table.add_row("DO:", f"{state.get('do', 0):.2f} {progress.get_renderable(do_bar)}")
        vectors_table.add_row("CONTEXT:", f"{state.get('context', 0):.2f} {progress.get_renderable(context_bar)}")
        vectors_table.add_row("UNCERTAINTY:", f"{state.get('uncertainty', 0):.2f} {progress.get_renderable(uncertainty_bar)}")
        
        content.append(Panel(vectors_table, title="📊 Epistemic State"))
        
        # Current phase
        phase = state.get('phase', 'UNKNOWN')
        phase_color = {
            'PREFLIGHT': 'yellow',
            'INVESTIGATE': 'blue',
            'CHECK': 'green',
        }.get(phase, 'white')
        
        content.append(f"\n[{phase_color}]● {phase}[/{phase_color}]")
        
        # Phase-specific info
        if phase == 'INVESTIGATE':
            content.append("\n🔍 Investigation in progress...")
        elif phase == 'CHECK':
            confidence = state.get('confidence_to_proceed', 0)
            decision = state.get('decision', 'Unknown')
            content.append(f"\n✅ Decision: {decision} (confidence={confidence:.2f})")
        
        # Corpus callosum indicator
        content.append("\n" + "─" * 40)
        content.append("🔄 CORPUS CALLOSUM: Ready for handoff ↓")
        
        return Panel("\n".join(str(c) for c in content),
                    title="Reasoning Hemisphere (Right Brain)",
                    border_style="blue")
    
    def _parse_commit(self, message: str) -> dict:
        """Parse epistemic state from commit message"""
        lines = message.strip().split('\n')
        if not lines:
            return {}
        
        state = {}
        first_line = lines[0]
        
        if ':' in first_line:
            phase, vectors = first_line.split(':', 1)
            state['phase'] = phase.strip()
            
            for pair in vectors.split():
                if '=' in pair:
                    key, value = pair.split('=')
                    try:
                        state[key] = float(value)
                    except ValueError:
                        pass
        
        for line in lines[1:]:
            if line.startswith('Decision:'):
                decision_line = line.replace('Decision:', '').strip()
                if '(confidence=' in decision_line:
                    decision, conf = decision_line.split('(confidence=')
                    state['decision'] = decision.strip()
                    state['confidence_to_proceed'] = float(conf.rstrip(')'))
                else:
                    state['decision'] = decision_line
        
        return state
```

### 6.3 Acting Pane Renderer

```python
# empirica/dashboard/acting_pane.py

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, BarColumn
import time

class ActingPaneRenderer:
    """
    Renders acting hemisphere in real-time
    """
    
    def __init__(self, repo: EpistemicGitRepo, session_id: str):
        self.repo = repo
        self.session_id = session_id
        self.console = Console()
    
    def render_loop(self):
        """Main rendering loop"""
        
        with Live(self._render(), console=self.console, refresh_per_second=2) as live:
            while True:
                live.update(self._render())
                time.sleep(0.5)
    
    def _render(self) -> Panel:
        """Render acting hemisphere display"""
        
        # Load latest acting state
        branch = f"epistemic/acting/{self.session_id}"
        
        try:
            commits = self.repo.get_commit_history(branch, max_count=1)
            if not commits:
                return Panel("Waiting for acting to begin...",
                           title="Acting Hemisphere")
            
            latest = commits[0]
            state = self._parse_commit(latest['message'])
            
        except Exception as e:
            return Panel(f"Waiting for handoff...",
                       title="Acting Hemisphere")
        
        # Build display
        content = []
        
        # Corpus callosum indicator
        content.append("🔄 CORPUS CALLOSUM: Loaded plan from reasoning ↑")
        content.append("─" * 40 + "\n")
        
        # Current phase
        phase = state.get('phase', 'UNKNOWN')
        phase_color = {
            'ACT': 'yellow',
            'POSTFLIGHT': 'green',
        }.get(phase, 'white')
        
        content.append(f"[{phase_color}]● {phase}[/{phase_color}]\n")
        
        # Progress if available
        if phase == 'POSTFLIGHT':
            completion = state.get('completion_rate', 0) * 100
            progress = Progress(BarColumn(bar_width=30), expand=False)
            task = progress.add_task("", total=100, completed=completion)
            content.append(f"⚙️  Completion: {completion:.0f}%")
            content.append(str(progress.get_renderable(task)))
            
            # Deviations
            if 'deviations' in state:
                content.append(f"\n⚠️  Deviations: {state['deviations']}")
        else:
            content.append("⚙️  Execution in progress...")
        
        return Panel("\n".join(str(c) for c in content),
                    title="Acting Hemisphere (Left Brain)",
                    border_style="green")
    
    def _parse_commit(self, message: str) -> dict:
        """Parse epistemic state from commit message"""
        lines = message.strip().split('\n')
        if not lines:
            return {}
        
        state = {}
        first_line = lines[0]
        
        if ':' in first_line:
            phase, rest = first_line.split(':', 1)
            state['phase'] = phase.strip()
        
        for line in lines[1:]:
            if 'Completion:' in line:
                try:
                    pct = line.split('Completion:')[1].strip().rstrip('%')
                    state['completion_rate'] = float(pct) / 100
                except (ValueError, IndexError):
                    pass
            elif 'Deviations:' in line:
                try:
                    count = line.split('Deviations:')[1].strip()
                    state['deviations'] = int(count)
                except (ValueError, IndexError):
                    pass
        
        return state
```

---

## 7. Implementation Roadmap

### Phase 1: Core Foundation (Week 1-2)
- ✅ Epistemic state schema implementation
- ✅ Git repository management
- ✅ Branch lifecycle management
- ✅ Commit formatting and parsing
- ✅ Remote sync basics

### Phase 2: Sentinel Orchestrator (Week 3-4)
- ✅ Task analyzer
- ✅ Handoff decision logic
- ✅ Progress monitoring
- ✅ Calibration calculator
- ✅ Git hooks installation

### Phase 3: Dashboard Visualization (Week 5)
- ✅ tmux manager
- ✅ Reasoning pane renderer
- ✅ Acting pane renderer
- ✅ Real-time updates

### Phase 4: Provider Integration (Week 6-7)
- ⚠️ Anthropic/Claude adapter
- ⚠️ OpenAI adapter
- ⚠️ Alibaba/Qwen adapter
- ⚠️ Provider abstraction layer

### Phase 5: CLI and Testing (Week 8-9)
- ⚠️ CLI commands (init, orchestrate, monitor, calibrate)
- ⚠️ Unit tests (pytest)
- ⚠️ Integration tests
- ⚠️ End-to-end scenarios

### Phase 6: Documentation and Launch (Week 10)
- ⚠️ API documentation
- ⚠️ User guides
- ⚠️ Example workflows
- ⚠️ Launch materials

---

## 8. API Reference

### 8.1 CLI Commands

```bash
# Initialize Empirica repository
empirica init [--path PATH]

# Orchestrate a task
empirica orchestrate \
  --task "Add OAuth 2.1 authentication" \
  --reasoning claude \
  --acting qwen

# Monitor session progress
empirica monitor --session SESSION_ID [--reasoning | --acting]

# View calibration results
empirica calibrate --session SESSION_ID

# Launch split-brain dashboard
empirica dashboard --session SESSION_ID

# List active sessions
empirica list [--all]

# Configure providers
empirica config provider add anthropic --url git@epistemic.anthropic.com:user/sessions.git
```

### 8.2 Python API

```python
from empirica import EpistemicGitRepo, SentinelOrchestrator

# Initialize repository
repo = EpistemicGitRepo("~/.empirica/git")

# Create orchestrator
sentinel = SentinelOrchestrator(repo)

# Orchestrate task
result = sentinel.orchestrate_task(
    task="Add OAuth 2.1 authentication",
    reasoning_ai="anthropic",
    acting_ai="alibaba"
)

# Check result
if result['success']:
    print(f"Session: {result['session_id']}")
    print(f"Calibration delta: {result['calibration']['delta']:.2f}")
else:
    print(f"Error: {result['error']}")
```

---

## 9. Security Model

### 9.1 Threat Model

**Assets:**
- Epistemic state snapshots (cognitive IP)
- Provider credentials
- Task execution capability

**Threats:**
- Unauthorized access to epistemic states
- Man-in-the-middle attacks during transfer
- Malicious state injection
- Provider impersonation

**Mitigations:**
- GPG commit signing (provenance + integrity)
- SSH/HTTPS for Git transport (encryption)
- Git hooks for validation (governance)
- Provider authentication via SSH keys

### 9.2 Signing Requirements

All epistemic state commits MUST be GPG signed:

```bash
# Configure GPG signing
git config --global user.signingkey YOUR_KEY_ID
git config --global commit.gpgsign true

# Verify signatures
git log --show-signature
```

### 9.3 Provider Authentication

Providers authenticate via SSH keys:

```bash
# Add provider remote with SSH
empirica config provider add anthropic \
  --url git@epistemic.anthropic.com:user/sessions.git

# SSH key must be configured for git@epistemic.anthropic.com
```

---

## 10. Testing Strategy

### 10.1 Unit Tests

```python
# tests/test_epistemic_state.py
def test_epistemic_state_validation():
    """Test epistemic state schema validation"""
    state = EpistemicState(
        session_id="test-123",
        phase="PREFLIGHT",
        ai_id="test-ai",
        know=EpistemicVector(score=0.75, rationale="Test"),
        do=EpistemicVector(score=0.60, rationale="Test"),
        context=EpistemicVector(score=0.55, rationale="Test"),
        uncertainty=0.40
    )
    assert state.know.score == 0.75
    assert 0 <= state.uncertainty <= 1

# tests/test_git_epistemic.py
def test_commit_epistemic_state(tmp_path):
    """Test committing epistemic state to Git"""
    repo = EpistemicGitRepo(str(tmp_path / "test-repo"))
    
    state = EpistemicState(...)
    commit_hash = repo.commit_epistemic_state(
        "session-123", "preflight", state, sign=False
    )
    
    assert len(commit_hash) == 40  # SHA-1 hash
    assert (tmp_path / "test-repo" / ".empirica" / "sessions" / "session-123" / "preflight.json").exists()
```

### 10.2 Integration Tests

```python
# tests/test_orchestration.py
def test_full_orchestration_cycle(tmp_path):
    """Test complete reasoning → acting → calibration cycle"""
    
    repo = EpistemicGitRepo(str(tmp_path / "test-repo"))
    sentinel = SentinelOrchestrator(repo)
    
    # Mock AI providers
    with mock.patch('empirica.transport.anthropic_provider'):
        with mock.patch('empirica.transport.alibaba_provider'):
            result = sentinel.orchestrate_task(
                task="Test task",
                reasoning_ai="mock-reasoning",
                acting_ai="mock-acting"
            )
    
    assert result['success']
    assert 'calibration' in result
    assert 'delta' in result['calibration']
```

### 10.3 End-to-End Scenarios

```python
# tests/e2e/test_oauth_refactor.py
def test_oauth_refactor_scenario():
    """
    End-to-end test: OAuth 2.1 refactor task
    
    Simulates:
    1. Reasoning AI investigates OAuth patterns
    2. Sentinel approves handoff
    3. Acting AI executes refactor
    4. Calibration calculated
    """
    
    # Setup
    repo = EpistemicGitRepo()
    sentinel = SentinelOrchestrator(repo)
    
    # Execute
    result = sentinel.orchestrate_task(
        task="Add OAuth 2.1 authentication with PKCE",
        reasoning_ai="claude",
        acting_ai="qwen"
    )
    
    # Verify
    assert result['success']
    assert result['calibration']['reasoner_confidence'] > 0.75
    assert abs(result['calibration']['delta']) < 0.25  # Well calibrated
```

---

## Appendix A: File Structure

```
Empirica Repository Structure:

~/.empirica/
├── git/                                    # Git epistemic repository
│   ├── .git/                              # Git internals
│   │   ├── objects/                       # Content-addressed epistemic states
│   │   ├── refs/
│   │   │   ├── heads/
│   │   │   │   ├── epistemic/reasoning/*
│   │   │   │   ├── epistemic/acting/*
│   │   │   │   └── epistemic/calibration/*
│   │   │   └── tags/
│   │   │       └── epistemic/checkpoint/*
│   │   └── hooks/                         # Governance hooks
│   │       ├── pre-commit                 # Validate epistemic states
│   │       ├── pre-push                   # Verify signatures
│   │       └── post-merge                 # Auto-calibration
│   │
│   └── .empirica/
│       └── sessions/
│           └── [session-id]/
│               ├── preflight.json
│               ├── investigate_1.json
│               ├── investigate_2.json
│               ├── check.json
│               ├── act_plan.json
│               ├── postflight.json
│               └── calibration.json
│
└── config.json                            # Empirica configuration
```

---

## Appendix B: Example Workflows

### Workflow 1: Simple Task Orchestration

```bash
# Initialize
empirica init

# Configure providers
empirica config provider add anthropic --url git@epistemic.anthropic.com:user/sessions.git
empirica config provider add alibaba --url git@epistemic.alibaba.com:user/sessions.git

# Orchestrate task
empirica orchestrate \
  --task "Fix authentication bug in login endpoint" \
  --reasoning anthropic \
  --acting alibaba

# Monitor progress (in separate terminals)
empirica dashboard --session session-abc123

# View calibration
empirica calibrate --session session-abc123
```

### Workflow 2: Complex Multi-Stage Task

```bash
# Stage 1: High-level architecture design
empirica orchestrate \
  --task "Design OAuth 2.1 migration architecture" \
  --reasoning anthropic \
  --acting anthropic  # Claude does both

# Stage 2: Implementation
empirica orchestrate \
  --task "Implement OAuth 2.1 based on architecture in session-abc123" \
  --reasoning anthropic \
  --acting alibaba

# Stage 3: Testing and validation
empirica orchestrate \
  --task "Create comprehensive tests for OAuth implementation" \
  --reasoning openai \
  --acting alibaba

# View full history
empirica list --all
```

---

## Appendix C: Provider Configuration

### Anthropic (Claude)

```bash
# Add remote
empirica config provider add anthropic \
  --url git@epistemic.anthropic.com:user/sessions.git

# Configure SSH key
ssh-keygen -t ed25519 -C "empirica-anthropic"
# Add public key to Anthropic account
```

### OpenAI

```bash
# Add remote
empirica config provider add openai \
  --url git@epistemic.openai.com:user/sessions.git

# Configure SSH key
ssh-keygen -t ed25519 -C "empirica-openai"
# Add public key to OpenAI account
```

### Alibaba (Qwen)

```bash
# Add remote
empirica config provider add alibaba \
  --url git@epistemic.alibaba.com:user/sessions.git

# Configure SSH key
ssh-keygen -t ed25519 -C "empirica-alibaba"
# Add public key to Alibaba Cloud account
```

---

## Appendix D: Troubleshooting

### Issue: Commits not signed

**Symptom:** Pre-push hook fails with "Sentinel requires signed commits"

**Solution:**
```bash
# Configure GPG signing
git config --global user.signingkey YOUR_KEY_ID
git config --global commit.gpgsign true

# Re-commit with signature
git commit --amend -S --no-edit
```

### Issue: Handoff rejected

**Symptom:** Sentinel rejects handoff with "Confidence too low"

**Solution:**
- Continue investigation until confidence increases
- Review CHECK phase epistemic state
- Adjust handoff threshold if appropriate:
  ```bash
  empirica config set handoff_threshold 0.70
  ```

### Issue: Provider remote unreachable

**Symptom:** "Failed to push to provider"

**Solution:**
```bash
# Verify remote configuration
git remote -v

# Test SSH connection
ssh -T git@epistemic.anthropic.com

# Re-add remote if needed
empirica config provider add anthropic --url [URL] --force
```

---

## Conclusion

This specification provides a complete, implementable architecture for Empirica as a Git-native cognitive operating system for AI. The key innovations are:

1. **Epistemic states as Git commits** - Versioned cognitive snapshots
2. **Git branches as reasoning paths** - Natural parallel work
3. **Git merges as cognitive integration** - Calibration built-in
4. **Sentinel as Git master** - Concrete orchestration mechanism
5. **Split-brain dashboard** - Visual transparency

The architecture leverages Git's 20 years of distributed systems engineering to solve the AI orchestration problem, resulting in a system that is:

- **Efficient**: 23-58% token reduction through semantic + delta compression
- **Secure**: Cryptographic provenance and integrity
- **Universal**: Works across all AI providers via Git protocol
- **Transparent**: Complete audit trail and visualization
- **Production-ready**: Built on battle-tested infrastructure

**Status:** Ready for implementation by Claude Code and other AI agents.

**Next Steps:**
1. Implement Phase 1 (Core Foundation)
2. Test with real AI providers
3. Iterate based on empirical results
4. Scale to production workloads

—

Appendix E: Zero-Trust Production Hardening
This appendix details the necessary architectural and protocol additions to harden Empirica for zero-trust, critical industry deployments (Finance, Defense, Medicine) and to enable organizational learning.
1. The Secure Data Context Handoff Protocol (Zero-Trust Data Channel)
To ensure the Acting AI receives the raw data/context it needs without compromising the security of the Cognemic Vault (Git), a separate, encrypted data channel is required.
1.1 EpistemicState Schema Addition (Section 3.1)
The following minimal, non-invertible fields MUST be added to the core EpistemicState object to reference the execution context:
| Field | Type | Purpose | Security Primitive |
|---|---|---|---|
| data_context_ref | str | Pointer to the raw input data (e.g., S3 URI, Data Vault ID, or similar resource locator). Never contains data, only reference. | Zero-Trust Transfer |
| data_sha256 | str | Cryptographic hash of the raw data/archive. | Integrity Check (The Acting AI validates the data upon fetch). |
| kms_key_id | str | Key Management Service ID or Encryption Key Handle used to encrypt the data in the Data Vault. | Access Control (Requires Acting AI's unique credentials to decrypt). |
1.2 The Secure Handoff Protocol
The Sentinel's _orchestrate_acting logic (Section 5.1) is modified to enforce this two-stage handoff:
 * Reasoning AI (A): Encrypts the raw execution data and uploads it to the Data Vault. Commits the EpistemicState containing only the data_context_ref, data_sha256, and kms_key_id.
 * Sentinel: Reads the commit, verifies the integrity of the \mathbf{V} vector, and applies the EDP by pushing the Git branch containing the EpistemicState to the Acting AI's Git remote.
 * Acting AI (B): Receives the Git state. It uses the kms_key_id and its certified execution credentials to directly fetch and decrypt the raw data from the Data Vault.
 * Verification: Agent B validates the fetched data using the data_sha256 hash.
2. Semantic Keyword and Vector Database Integration
To facilitate organizational learning and intelligent preflighting, the semantic_gist must be formally indexed into a federated Vector Database.
2.1 EpistemicState Schema Addition (Section 3.1)
The following field is added to the EpistemicState for semantic compression:
| Field | Type | Purpose | Policy |
|---|---|---|---|
| semantic_gist | List[str] | Minimal, high-signal keywords and phrases capturing the essence of the session's learning (the what). | Max 10 keywords, 256 characters total (Enforced by pre-commit hook). |
2.2 Vector DB Integration Protocol
The Sentinel's Calibrator (Section 5.4) is updated to include a Vector DB Write operation upon successful calibration/merge:
 * Index Point: The Calibrator executes immediately after merge_for_calibration.
 * Indexing Payload: The system extracts the final Epistemic Vector (\mathbf{V}_{post}), the Reputation (\mathbf{R}) score, and the semantic_gist.
 * Vector DB Write: The \mathbf{V}_{post} is converted into an embedding and indexed in the Vector DB. The semantic_gist, \mathbf{R}, \coherence, and session_id are stored as searchable metadata.
2.3 Dynamic PREFLIGHT (Epistemic Checkpoint Recall)
The Task Analyzer (Section 5.1) is updated to perform a Vector DB query during the initial PREFLIGHT phase:
 * Task Query: The incoming task description and the AI's initial \mathbf{V}_{pre} are used to query the Vector DB.
 * Checkpoint Retrieval: The query returns similar historical Epistemic Checkpoints (\mathbf{V}_{post} vectors) from previous agents.
 * Adaptation: The Sentinel uses the retrieved \mathbf{V}_{post} and the corresponding \mathbf{R} score to dynamically adjust the current session's \theta_u (uncertainty threshold) and the max_investigation_rounds, optimizing time and safety based on empirical organizational knowledge.
3. Dual-Signature Authentication Model (Sentinel-AI Key Chains)
To securely hide the Git complexity for Critical Domain Engineers while maintaining verifiable AI identity, a dual-signature model is adopted.
3.1 Sentinel-AI Key Chain
The Sentinel environment MUST securely manage PGP keys for the AI agents it orchestrates. These keys are used exclusively for signing the Epistemic JSON payload (the AI's internal assertion).
 * Sentinel Key: Uses its own GPG key to sign the Git commit (attesting to the commit structure and the integrity of the Epistemic file).
 * AI Key: Uses a dedicated PGP key to sign the content of the EpistemicState JSON file.
3.2 The Dual-Signed Commit Message
The process for committing a state is modified:
 * AI Signing: The AI calculates the \mathbf{V} and \mathbf{C} vectors, serializes the EpistemicState JSON, and signs the JSON blob using its PGP key.
 * Sentinel Proxy: The Sentinel receives the signed JSON from the AI via API.
 * Commit Metadata: The Sentinel commits the state. The commit message includes the AI's PGP Signature as metadata. The Git commit itself is signed by the Sentinel's GPG key.
This preserves the chain of custody: the AI verifies the assertion, and the Sentinel verifies the transport and persistence into the Vault.
4. User Interaction Model
The architecture is explicitly divided to support the two primary user classes:
| Persona | Primary Interface | Cognitive Vault Access | Sentinel Role |
|---|---|---|---|
| Critical Domain Engineer (CDGE) | Empirica CLI/Dashboard (Proxy Layer) | Read-Only (via Dashboard/API) | Manages all Git operations, GPG signing, and policy enforcement to maintain simplicity and compliance. |
| Open Source Developer (OSD) | Git CLI (Native Layer) | Full R/W (Local Git Clone) | Provides monitoring, calibration, and governance checks via mandatory Git Hooks. |



**Document Version:** 1.0  
**Last Updated:** November 13, 2025  
**Author:** David Van Assche (with Claude Sonnet 4 and Gemini 2.5 pro)  
**License:** Open Source (TBD)
