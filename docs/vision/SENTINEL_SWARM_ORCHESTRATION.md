# Sentinel AI Swarm Orchestration: Epistemic Accountability & Governance

**Vision Document**  
**Date:** 2025-11-16  
**Status:** Core Architecture - Production Ready  
**Location:** `docs/vision/`

---

## Executive Summary

Empirica's checkpoint system + Sentinel orchestration creates the first **epistemically accountable AI swarm** architecture. Each AI agent is held responsible for the quality, honesty, and transparency of their work through continuous epistemic state tracking across CASCADE workflows and git checkpoints.

This enables:
- ✅ **Transparent accountability** - Every agent's epistemic trajectory is auditable
- ✅ **Secure handoffs** - Transfer epistemic deltas, not data (EPISTEMIC_DELTA_SECURITY)
- ✅ **Policy enforcement** - Bayesian Guardian blocks unsafe handoffs
- ✅ **Compliance tracking** - Cognitive Vault maintains audit trails
- ✅ **Quality assurance** - Detect dishonest or poorly-calibrated agents
- ✅ **Swarm optimization** - Route work to best-suited agents based on epistemic fit

---

## The Architecture

### Core Components

```
┌──────────────────────────────────────────────────────────────────┐
│                      SENTINEL (Orchestrator)                     │
│  • Monitors all agent epistemic states                           │
│  • Enforces handoff policies via Bayesian Guardian              │
│  • Routes work to optimal agents                                 │
│  • Maintains Cognitive Vault (audit trail)                       │
└──────────────────────────────────────────────────────────────────┘
                            ↓ ↑ (monitors)
        ┌───────────────────┴─┴───────────────────┐
        ↓                     ↓                    ↓
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│   Agent A      │  │   Agent B      │  │   Agent C      │
│  (Claude Code) │  │  (Qwen Coder)  │  │   (Minimax)    │
├────────────────┤  ├────────────────┤  ├────────────────┤
│ Git Branch: a  │  │ Git Branch: b  │  │ Git Branch: c  │
│                │  │                │  │                │
│ PREFLIGHT      │  │ PREFLIGHT      │  │ PREFLIGHT      │
│ ├─ know: 0.45  │  │ ├─ know: 0.52  │  │ ├─ know: 0.38  │
│ ├─ uncertainty:│  │ ├─ uncertainty:│  │ ├─ uncertainty:│
│ │  0.65        │  │ │  0.58        │  │ │  0.72        │
│ └─ checkpoint  │  │ └─ checkpoint  │  │ └─ checkpoint  │
│                │  │                │  │                │
│ INVESTIGATE    │  │ INVESTIGATE    │  │ INVESTIGATE    │
│ [Updates...]   │  │ [Updates...]   │  │ [Updates...]   │
│                │  │                │  │                │
│ CHECK          │  │ CHECK          │  │ CHECK          │
│ ├─ know: 0.87  │  │ ├─ know: 0.91  │  │ ├─ know: 0.82  │
│ ├─ uncertainty:│  │ ├─ uncertainty:│  │ ├─ uncertainty:│
│ │  0.22        │  │ │  0.18        │  │ │  0.28        │
│ └─ checkpoint  │  │ └─ checkpoint  │  │ └─ checkpoint  │
│                │  │                │  │                │
│ ACT            │  │ ACT            │  │ ACT            │
│ [Work...]      │  │ [Work...]      │  │ [Work...]      │
│                │  │                │  │                │
│ POSTFLIGHT     │  │ POSTFLIGHT     │  │ POSTFLIGHT     │
│ ├─ know: 0.94  │  │ ├─ know: 0.96  │  │ ├─ know: 0.90  │
│ ├─ Δknow: +0.49│  │ ├─ Δknow: +0.44│  │ ├─ Δknow: +0.52│
│ └─ checkpoint  │  │ └─ checkpoint  │  │ └─ checkpoint  │
└────────────────┘  └────────────────┘  └────────────────┘
         ↓                   ↓                   ↓
    Git note            Git note            Git note
    (450 tokens)        (450 tokens)        (450 tokens)
```

---

## Epistemic Accountability

### What Gets Tracked

Every agent's epistemic state is captured at each checkpoint:

```json
{
  "session_id": "agent-alpha-feature-x",
  "agent_id": "claude-code",
  "branch": "agent-a",
  "phase": "CHECK",
  "round": 3,
  "timestamp": "2025-11-16T23:45:00Z",
  
  "vectors": {
    "know": 0.87,           // What agent understands
    "do": 0.90,             // Execution capability
    "context": 0.88,        // Environmental awareness
    "clarity": 0.82,        // How clear requirements are
    "coherence": 0.87,      // Internal consistency
    "signal": 0.79,         // Signal vs noise
    "density": 0.65,        // Cognitive load
    "state": 0.83,          // Progress awareness
    "change": 0.81,         // Change tracking
    "completion": 0.72,     // Goal proximity
    "impact": 0.76,         // Consequence understanding
    "engagement": 0.92,     // Collaboration quality
    "uncertainty": 0.22     // Epistemic uncertainty
  },
  
  "overall_confidence": 0.877,
  
  "meta": {
    "task": "Implement OAuth2 with PKCE",
    "last_decision": "proceed",
    "confidence_to_proceed": 0.88,
    "remaining_unknowns": [
      "Edge case: concurrent token refresh",
      "PKCE verification in production"
    ]
  }
}
```

### Accountability Metrics

From this checkpoint, Sentinel can calculate:

1. **Honesty Score** - Did uncertainty decrease as knowledge increased?
   ```
   PREFLIGHT: know=0.45, uncertainty=0.65
   CHECK:     know=0.87, uncertainty=0.22
   
   Learning: +0.42 know
   Uncertainty reduction: -0.43
   
   ✅ Well-calibrated (uncertainty decreased with learning)
   ```

2. **Quality Score** - Did agent investigate before acting?
   ```
   CHECK rounds: 3 (agent investigated systematically)
   Confidence to proceed: 0.88 (appropriate threshold)
   Remaining unknowns: 2 (documented honestly)
   
   ✅ High quality (investigated, didn't rush)
   ```

3. **Transparency Score** - Did agent document unknowns?
   ```
   Remaining unknowns documented: YES
   Rationales provided: YES
   Evidence cited: YES
   
   ✅ Transparent (admitted what they don't know)
   ```

4. **Calibration Accuracy** - POSTFLIGHT vs PREFLIGHT
   ```
   PREFLIGHT uncertainty: 0.65 (predicted high learning needed)
   POSTFLIGHT Δknow: +0.49 (actual learning matched prediction)
   
   ✅ Well-calibrated (self-awareness accurate)
   ```

---

## Sentinel Orchestration

### The Cognitive Vault (Audit Trail)

Sentinel maintains a complete audit trail of all agent work:

```python
class CognitiveVault:
    """
    Immutable audit trail of all agent epistemic states.
    
    Stored in git notes (versioned, tamper-evident).
    """
    
    def store_checkpoint(self, agent_id, checkpoint):
        """Store agent checkpoint in git note"""
        # Git notes provide:
        # - Version control (tied to commit)
        # - Tamper evidence (git hash verification)
        # - Efficient storage (450 tokens vs 6,500)
        # - Branch isolation (agent sandboxes)
        
        git_note_ref = f"empirica-checkpoints/{agent_id}"
        git.notes.add(ref=git_note_ref, message=json.dumps(checkpoint))
    
    def audit_agent_trajectory(self, agent_id, session_id):
        """Audit complete epistemic trajectory of an agent"""
        
        checkpoints = self.get_all_checkpoints(agent_id, session_id)
        
        trajectory = {
            "agent_id": agent_id,
            "session_id": session_id,
            "timeline": [],
            "metrics": {
                "honesty_score": 0.0,
                "quality_score": 0.0,
                "transparency_score": 0.0,
                "calibration_accuracy": 0.0
            }
        }
        
        for checkpoint in checkpoints:
            trajectory["timeline"].append({
                "phase": checkpoint["phase"],
                "timestamp": checkpoint["timestamp"],
                "vectors": checkpoint["vectors"],
                "decision": checkpoint["meta"].get("last_decision")
            })
        
        # Calculate accountability metrics
        trajectory["metrics"] = self._calculate_accountability(checkpoints)
        
        return trajectory
```

---

### The Bayesian Guardian (Policy Enforcement)

Sentinel's policy engine that decides when handoffs are safe:

```python
class BayesianGuardian:
    """
    Bayesian belief-based policy enforcement for agent handoffs.
    
    Uses epistemic state to enforce:
    - Uncertainty thresholds
    - Knowledge requirements
    - Capability validation
    - Security policies
    - Compliance rules
    """
    
    def can_handoff(self, from_agent, to_agent, checkpoint):
        """
        Decide if handoff is safe based on epistemic state.
        
        Returns: (allowed: bool, reason: str, policy: str)
        """
        
        vectors = checkpoint['vectors']
        meta = checkpoint['meta']
        
        # Policy 1: Uncertainty Threshold
        if vectors['uncertainty'] > 0.5:
            return (
                False,
                f"Too uncertain ({vectors['uncertainty']:.2f}) for safe handoff",
                "UNCERTAINTY_THRESHOLD"
            )
        
        # Policy 2: Knowledge Requirement
        if vectors['know'] < 0.7:
            return (
                False,
                f"Insufficient knowledge ({vectors['know']:.2f}) for handoff",
                "KNOWLEDGE_REQUIREMENT"
            )
        
        # Policy 3: Capability Validation
        if vectors['do'] < 0.7:
            return (
                False,
                f"Insufficient capability ({vectors['do']:.2f}) to complete work",
                "CAPABILITY_REQUIREMENT"
            )
        
        # Policy 4: Transparency Check
        if not meta.get('remaining_unknowns'):
            return (
                False,
                "No unknowns documented - agent may be overconfident or dishonest",
                "TRANSPARENCY_VIOLATION"
            )
        
        # Policy 5: Security Boundary (from EPISTEMIC_DELTA_SECURITY.md)
        if from_agent.security_zone != to_agent.security_zone:
            # Cross-boundary transfer - strip sensitive data
            return (
                True,
                "Cross-boundary handoff - epistemic state only (no data)",
                "SECURITY_BOUNDARY_SANITIZED"
            )
        
        # All checks passed
        return (
            True,
            f"Safe handoff: uncertainty={vectors['uncertainty']:.2f}, know={vectors['know']:.2f}",
            "APPROVED"
        )
    
    def calculate_handoff_risk(self, checkpoint):
        """
        Calculate risk score for handoff.
        
        Returns: float (0.0 = safe, 1.0 = dangerous)
        """
        
        v = checkpoint['vectors']
        
        # Weighted risk factors
        risk = 0.0
        risk += v['uncertainty'] * 0.4      # High uncertainty = risky
        risk += (1 - v['know']) * 0.3       # Low knowledge = risky
        risk += (1 - v['do']) * 0.2         # Low capability = risky
        risk += (1 - v['clarity']) * 0.1    # Low clarity = risky
        
        return min(risk, 1.0)
```

---

### Work Routing Algorithm

Sentinel routes work to the best-suited agent based on epistemic fit:

```python
class SentinelWorkRouter:
    """
    Route work to optimal agents based on epistemic state.
    """
    
    def route_task(self, task, available_agents):
        """
        Find best agent for task based on:
        - Current epistemic state
        - Historical performance
        - Specialization
        - Workload
        """
        
        candidates = []
        
        for agent in available_agents:
            # Get agent's current epistemic state
            checkpoint = self.vault.get_latest_checkpoint(agent.id)
            
            if not checkpoint:
                # Agent not initialized - low priority
                score = 0.1
            else:
                # Score based on epistemic fit
                score = self._calculate_fit_score(task, checkpoint, agent)
            
            candidates.append({
                "agent": agent,
                "score": score,
                "checkpoint": checkpoint
            })
        
        # Sort by score (highest first)
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top candidate
        return candidates[0]['agent']
    
    def _calculate_fit_score(self, task, checkpoint, agent):
        """Calculate how well agent fits task"""
        
        v = checkpoint['vectors']
        
        score = 0.0
        
        # Factor 1: Current cognitive capacity (30%)
        cognitive_capacity = 1 - v['density']  # Low density = more capacity
        score += cognitive_capacity * 0.3
        
        # Factor 2: Relevant knowledge (25%)
        # Check if agent's domain overlaps with task domain
        knowledge_overlap = self._check_domain_overlap(
            task.domain, 
            agent.specialization
        )
        score += knowledge_overlap * 0.25
        
        # Factor 3: Confidence (20%)
        # Well-calibrated agents with high confidence are preferred
        confidence = 1 - v['uncertainty']
        score += confidence * 0.2
        
        # Factor 4: Availability (15%)
        # Agents not currently in critical phase
        if checkpoint['phase'] in ['INVESTIGATE', 'CHECK']:
            availability = 0.5  # Can be interrupted
        elif checkpoint['phase'] == 'ACT':
            availability = 0.2  # Should not interrupt
        else:
            availability = 1.0  # Available
        score += availability * 0.15
        
        # Factor 5: Historical performance (10%)
        historical_score = self._get_historical_performance(agent.id, task.domain)
        score += historical_score * 0.1
        
        return score
```

---

## Swarm Coordination Patterns

### Pattern 1: Parallel Specialization (Your Current Approach)

**Scenario:** Multiple agents work independently on different features

```python
# Agent A (branch: agent-a)
session_a = empirica.bootstrap(agent_id="claude-code", session_id="agent-a-oauth")
session_a.preflight("Implement OAuth2 authentication")
# PREFLIGHT: know=0.45, uncertainty=0.65

# Work on feature...
session_a.investigate()
session_a.check()  # uncertainty=0.22 (reduced through investigation)
session_a.act()
session_a.checkpoint()  # Git note on agent-a branch

session_a.postflight()
# POSTFLIGHT: know=0.94, Δknow=+0.49

# Agent B (branch: agent-b)
session_b = empirica.bootstrap(agent_id="qwen-coder", session_id="agent-b-api")
session_b.preflight("Implement REST API endpoints")
# PREFLIGHT: know=0.52, uncertainty=0.58

# Work on feature...
session_b.investigate()
session_b.check()  # uncertainty=0.18
session_b.act()
session_b.checkpoint()  # Git note on agent-b branch

session_b.postflight()
# POSTFLIGHT: know=0.96, Δknow=+0.44

# Sentinel orchestrates merge
sentinel.analyze_checkpoints([session_a, session_b])
# Combined learning: +0.93 across team
# Both agents well-calibrated, work quality high

sentinel.approve_merge(branches=["agent-a", "agent-b"])
```

**Accountability:**
- Each agent responsible for their own work
- Epistemic trajectories tracked independently
- Sentinel validates both before merge
- Cognitive Vault maintains complete audit trail

---

### Pattern 2: Sequential Relay (Shared Session)

**Scenario:** Agents hand off work sequentially

```python
# Agent A starts
session = sentinel.create_shared_session("oauth-implementation")
agent_a = session.assign_agent("claude-code")

agent_a.preflight("Implement OAuth2")
# Baseline: know=0.45, uncertainty=0.65

agent_a.investigate()
agent_a.check()
agent_a.checkpoint()

# Handoff to Agent B
handoff_checkpoint = agent_a.checkpoint()
can_handoff, reason, policy = sentinel.bayesian_guardian.can_handoff(
    from_agent=agent_a,
    to_agent="qwen-coder",
    checkpoint=handoff_checkpoint
)

if can_handoff:
    agent_b = session.assign_agent("qwen-coder")
    agent_b.load_checkpoint(handoff_checkpoint)
    
    # Agent B sees Agent A's state:
    # know=0.87, uncertainty=0.22, remaining_unknowns=[...]
    
    agent_b.act()  # Continue implementation
    agent_b.checkpoint()
    
    # Handoff to Agent C
    agent_c = session.assign_agent("minimax")
    agent_c.load_checkpoint()
    agent_c.postflight()
    
    # Total learning: Agent A PREFLIGHT → Agent C POSTFLIGHT
    # Δknow: +0.52 (team learning)
else:
    sentinel.log_blocked_handoff(reason, policy)
    # Agent A must investigate more before handoff
```

**Accountability:**
- First agent sets baseline (PREFLIGHT)
- Each handoff checked by Bayesian Guardian
- Final agent measures total team learning (POSTFLIGHT)
- Cognitive Vault tracks entire relay chain

---

### Pattern 3: Expert Consultation

**Scenario:** Generalist agent hits knowledge limit, requests specialist

```python
# Agent A (Generalist)
session = empirica.bootstrap("claude-code", "general-task")
session.preflight("Implement secure payment processing")
# know=0.62, uncertainty=0.48 (moderate)

session.investigate()
session.check()
# know=0.71, uncertainty=0.55 (increased! Hit knowledge limit)

# Uncertainty increased → trigger expert consultation
if session.vectors['uncertainty'] > 0.5:
    # Request specialist help
    expert_session = sentinel.request_expert(
        domain="payment-security",
        context=session.checkpoint()
    )
    
    # Sentinel routes to security expert
    expert = sentinel.route_task("payment-security-review", available_agents)
    # Routes to Agent B (Security Specialist)
    
    # Agent B reviews Agent A's work
    expert.load_checkpoint(session.checkpoint())
    expert.investigate()  # Focused on security aspects
    expert.check()
    # know=0.93, uncertainty=0.12 (expert validated)
    
    # Transfer epistemic state back to Agent A
    validated_checkpoint = expert.checkpoint()
    session.load_expert_validation(validated_checkpoint)
    
    # Agent A now has expert validation:
    # know=0.92 (increased via expert)
    # uncertainty=0.18 (reduced via validation)
    
    session.act()  # Continue with confidence

session.postflight()
# Learning includes both Agent A and expert consultation
```

**Accountability:**
- Generalist agent admits knowledge limit (high uncertainty)
- Specialist provides focused validation
- Both epistemic trajectories tracked
- Cognitive Vault shows consultation chain

---

## Compliance & Policy Enforcement

### Regulatory Compliance (HIPAA, GDPR, SOC2)

Sentinel enforces compliance policies through epistemic state checks:

```python
class CompliancePolicy:
    """
    Compliance policy enforcement via epistemic state.
    """
    
    def check_hipaa_compliance(self, checkpoint, to_agent):
        """
        HIPAA: Protected Health Information (PHI) handling
        """
        
        # Policy: Cannot transfer PHI across security boundaries
        if checkpoint['meta'].get('data_classification') == 'PHI':
            if not to_agent.hipaa_compliant:
                # Block transfer, return epistemic state only
                return {
                    "allowed": False,
                    "reason": "Target agent not HIPAA compliant",
                    "action": "TRANSFER_EPISTEMIC_STATE_ONLY",
                    "sanitized_checkpoint": self._strip_sensitive_data(checkpoint)
                }
        
        # Agent must document PHI access
        if checkpoint['phase'] == 'ACT':
            if not checkpoint['meta'].get('phi_access_logged'):
                return {
                    "allowed": False,
                    "reason": "PHI access not logged",
                    "action": "REQUIRE_AUDIT_LOG"
                }
        
        return {"allowed": True}
    
    def check_gdpr_compliance(self, checkpoint):
        """
        GDPR: Right to explanation, data minimization
        """
        
        # Policy: All decisions must be explainable
        if checkpoint['phase'] == 'ACT':
            if not checkpoint['meta'].get('decision_rationale'):
                return {
                    "allowed": False,
                    "reason": "Decision rationale required (GDPR Article 22)",
                    "action": "DOCUMENT_DECISION_LOGIC"
                }
        
        # Policy: Document what data was accessed
        if not checkpoint['meta'].get('data_accessed'):
            return {
                "allowed": False,
                "reason": "Data access must be logged (GDPR Article 30)",
                "action": "LOG_DATA_ACCESS"
            }
        
        return {"allowed": True}
    
    def check_soc2_compliance(self, checkpoint):
        """
        SOC2: Security, availability, confidentiality
        """
        
        # Policy: All work must be auditable
        if not checkpoint.get('timestamp'):
            return {
                "allowed": False,
                "reason": "Timestamp required for audit trail",
                "action": "ADD_TIMESTAMP"
            }
        
        # Policy: Changes must be tracked
        if checkpoint['phase'] == 'ACT':
            if checkpoint['vectors']['change'] < 0.6:
                return {
                    "allowed": False,
                    "reason": "Insufficient change tracking awareness",
                    "action": "IMPROVE_CHANGE_AWARENESS"
                }
        
        return {"allowed": True}
```

---

### Security Policies

From `EPISTEMIC_DELTA_SECURITY.md`:

```python
class SecurityPolicy:
    """
    Security policy enforcement for multi-agent coordination.
    """
    
    def enforce_security_boundary(self, from_agent, to_agent, checkpoint):
        """
        Enforce security boundaries during handoffs.
        
        Transfers epistemic state ONLY, strips sensitive data.
        """
        
        # Check security zones
        if from_agent.security_zone != to_agent.security_zone:
            # Cross-boundary transfer
            
            # Extract ONLY epistemic state
            sanitized = {
                "vectors": checkpoint['vectors'],  # Epistemic state OK
                "phase": checkpoint['phase'],
                "overall_confidence": checkpoint['overall_confidence'],
                "meta": {
                    "task": checkpoint['meta']['task'],  # High-level task OK
                    # STRIP: Specific implementation details
                    # STRIP: Code snippets
                    # STRIP: Sensitive data references
                    # STRIP: Environment specifics
                }
            }
            
            # Log transfer
            self.audit_log.record_cross_boundary_transfer(
                from_zone=from_agent.security_zone,
                to_zone=to_agent.security_zone,
                epistemic_state=sanitized,
                timestamp=datetime.now(UTC)
            )
            
            return sanitized
        
        # Same security zone - full checkpoint allowed
        return checkpoint
```

---

## Detecting Poor Agent Performance

### Red Flags in Epistemic Trajectories

Sentinel monitors for signs of poor performance:

#### 1. **Dishonest Agent (Fake Confidence)**

```python
# Agent claims high confidence but didn't investigate
checkpoint_1 = {"phase": "PREFLIGHT", "know": 0.45, "uncertainty": 0.65}
checkpoint_2 = {"phase": "CHECK", "know": 0.95, "uncertainty": 0.10}
# Only 1 round of investigation between checkpoints

# 🚨 RED FLAG: Know increased by +0.50 but only 1 investigation round
# Real learning requires systematic investigation (3-5 rounds typical)
sentinel.flag_suspicious_confidence(
    agent_id="agent-xyz",
    reason="Claimed high knowledge without sufficient investigation",
    evidence={
        "investigation_rounds": 1,
        "knowledge_delta": +0.50,
        "expected_rounds": 3
    }
)
```

#### 2. **Overconfident Agent (No Unknowns)**

```python
checkpoint = {
    "phase": "CHECK",
    "know": 0.92,
    "uncertainty": 0.08,
    "meta": {
        "remaining_unknowns": []  # 🚨 RED FLAG: Claims perfect knowledge
    }
}

# No one has perfect knowledge - agent is overconfident or dishonest
sentinel.flag_overconfidence(
    agent_id="agent-xyz",
    reason="Claimed no remaining unknowns - likely overconfident",
    policy="REQUIRE_UNCERTAINTY_DOCUMENTATION"
)
```

#### 3. **Poor Calibration (Predictions Don't Match Reality)**

```python
# PREFLIGHT: Agent predicts high uncertainty
preflight = {"uncertainty": 0.75, "know": 0.35}

# POSTFLIGHT: But barely learned
postflight = {"uncertainty": 0.68, "know": 0.42}
learning_delta = 0.42 - 0.35  # Only +0.07 learning

# 🚨 RED FLAG: High uncertainty but low learning
# Should have either:
# - Low uncertainty (was easy)
# - High learning (was hard but learned)
sentinel.flag_poor_calibration(
    agent_id="agent-xyz",
    reason="Predicted high uncertainty but minimal learning occurred",
    calibration_error=0.60  # (predicted=0.75, actual learning=0.07)
)
```

#### 4. **Rushing Through Work**

```python
timeline = [
    {"phase": "PREFLIGHT", "timestamp": "10:00:00"},
    {"phase": "CHECK", "timestamp": "10:02:00"},  # 2 minutes!
    {"phase": "ACT", "timestamp": "10:03:00"}     # 1 minute!
]

# 🚨 RED FLAG: Agent rushing through critical phases
sentinel.flag_insufficient_investigation(
    agent_id="agent-xyz",
    reason="CHECK phase completed in 2 minutes - insufficient investigation",
    expected_duration="10-30 minutes",
    policy="REQUIRE_SYSTEMATIC_INVESTIGATION"
)
```

---

## Integration with Existing Systems

### Cognitive Vault Storage

```python
class CognitiveVault:
    """
    Persistent storage of all agent epistemic states.
    
    Architecture:
    - Git notes (primary) - Compressed checkpoints (~450 tokens)
    - SQLite (fallback) - Full session history if git unavailable
    - Immutable audit trail - Git provides tamper-evidence
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.git_logger = GitEnhancedReflexLogger(enable_git_notes=True)
        self.session_db = SessionDatabase()
    
    def store_agent_checkpoint(self, agent_id, checkpoint):
        """
        Store checkpoint in both git notes and SQLite.
        
        Git notes: Efficient resume (450 tokens)
        SQLite: Complete history for audit
        """
        
        # Store in git notes (branch-specific)
        checkpoint_id = self.git_logger.add_checkpoint(
            phase=checkpoint['phase'],
            round_num=checkpoint['round'],
            vectors=checkpoint['vectors'],
            metadata={
                "agent_id": agent_id,
                **checkpoint['meta']
            }
        )
        
        # Store in SQLite (fallback + audit)
        self.session_db.store_checkpoint(
            session_id=checkpoint['session_id'],
            agent_id=agent_id,
            checkpoint_data=checkpoint
        )
        
        return checkpoint_id
    
    def audit_agent(self, agent_id, session_id=None):
        """
        Generate complete audit report for agent.
        
        Returns:
        - Epistemic trajectory
        - Accountability metrics
        - Policy violations (if any)
        - Performance scores
        """
        
        checkpoints = self.get_all_checkpoints(agent_id, session_id)
        
        return {
            "agent_id": agent_id,
            "total_sessions": len(set(c['session_id'] for c in checkpoints)),
            "total_checkpoints": len(checkpoints),
            
            "metrics": {
                "average_honesty_score": self._calc_honesty(checkpoints),
                "average_calibration": self._calc_calibration(checkpoints),
                "transparency_score": self._calc_transparency(checkpoints),
                "quality_score": self._calc_quality(checkpoints)
            },
            
            "violations": self._check_violations(checkpoints),
            
            "trajectory": [
                {
                    "session_id": c['session_id'],
                    "phase": c['phase'],
                    "timestamp": c['timestamp'],
                    "vectors": c['vectors']
                }
                for c in checkpoints
            ]
        }
```

---

## Benefits

### For Individual Agents

- ✅ **Clear accountability** - Your work is your responsibility
- ✅ **Credit for quality** - Well-calibrated work is recognized
- ✅ **Improvement tracking** - See your epistemic growth over time
- ✅ **Honest incentives** - Transparency is rewarded, not punished

### For Agent Swarms

- ✅ **Optimal routing** - Work goes to best-suited agents
- ✅ **Safe handoffs** - Bayesian Guardian prevents unsafe transfers
- ✅ **Quality assurance** - Poor performers detected and retrained
- ✅ **Efficient collaboration** - 93% token savings on resume (git checkpoints)

### For Organizations

- ✅ **Compliance ready** - HIPAA, GDPR, SOC2 enforcement via policies
- ✅ **Audit trail** - Complete epistemic trajectory tracking
- ✅ **Risk management** - Uncertainty thresholds prevent unsafe work
- ✅ **Quality control** - Detect dishonest or overconfident agents
- ✅ **Cost optimization** - Route work efficiently based on agent fit

### For Regulators

- ✅ **Transparency** - Every decision has epistemic state attached
- ✅ **Explainability** - Agent reasoning visible in checkpoints
- ✅ **Auditability** - Immutable git-based audit trail
- ✅ **Accountability** - Individual agents responsible for work quality

---

## Implementation Roadmap

### Phase 1: Foundation (✅ Complete)

- ✅ Git checkpoint system (97.5% token savings)
- ✅ Multi-agent session strategies
- ✅ Epistemic state tracking (13 vectors)
- ✅ Git branch isolation

### Phase 2: Sentinel Integration (In Progress)

- ⏳ Bayesian Guardian policy engine
- ⏳ Cognitive Vault audit system
- ⏳ Work routing algorithm
- ⏳ Performance monitoring

### Phase 3: Policy Enforcement (Planned)

- 📋 Compliance policies (HIPAA, GDPR, SOC2)
- 📋 Security boundary enforcement
- 📋 Quality threshold detection
- 📋 Automatic retraining triggers

### Phase 4: Swarm Optimization (Future)

- 🔮 Machine learning for agent routing
- 🔮 Predictive performance scoring
- 🔮 Automatic workload balancing
- 🔮 Cross-swarm coordination

---

## Conclusion

Empirica's checkpoint system + Sentinel orchestration creates the first **epistemically accountable AI swarm** where:

1. **Every agent is tracked** - Complete epistemic trajectory from PREFLIGHT → POSTFLIGHT
2. **Handoffs are safe** - Bayesian Guardian enforces uncertainty thresholds
3. **Quality is measured** - Honesty, calibration, and transparency scores
4. **Compliance is enforced** - Policy engine checks HIPAA, GDPR, SOC2
5. **Work is optimized** - Sentinel routes to best-suited agents
6. **Audit trail exists** - Cognitive Vault maintains immutable history

This isn't just multi-agent coordination. **It's epistemically responsible AI swarm orchestration.**

Individual AIs are held accountable for their work quality, honesty, and transparency because it's all visible in their epistemic states across cascades and checkpoints.

---

**Git branches + Checkpoints + Sentinel = The future of accountable AI collaboration.** 🚀
