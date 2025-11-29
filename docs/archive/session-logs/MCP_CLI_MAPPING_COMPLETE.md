# Complete MCP-to-CLI Mapping Reference

**Last Updated:** 2025-11-27  
**Purpose:** Enable mini-agent to use both MCP tools and CLI commands interchangeably  
**Status:** Verified and tested

---

## 🎯 Quick Reference

| MCP Tool | CLI Command | Key Parameters | Output Format |
|----------|-------------|----------------|---------------|
| `execute_preflight` | `empirica preflight` | `--ai-id`, `--session-id`, `--prompt-only` | JSON |
| `submit_preflight_assessment` | `empirica preflight` | `--assessment-json`, `--sign` | JSON |
| `execute_check` | `empirica check` | `--session-id`, `--findings` | JSON |
| `submit_check_assessment` | `empirica check-submit` | `--vectors`, `--decision` | JSON |
| `execute_postflight` | `empirica postflight` | `--session-id`, `--summary` | JSON |
| `submit_postflight_assessment` | `empirica postflight-submit` | `--vectors`, `--reasoning` | JSON |
| `create_goal` | `empirica goal-create` | `--objective`, `--scope` | JSON |
| `add_subtask` | `empirica goal-add-subtask` | `--goal-id`, `--description` | JSON |
| `complete_subtask` | `empirica goal-complete-subtask` | `--task-id`, `--evidence` | JSON |
| `discover_goals` | `empirica goal-discover` | `--from-ai-id` | JSON |
| `resume_goal` | `empirica goal-resume` | `--goal-id`, `--ai-id` | JSON |
| `create_identity` | `empirica identity-create` | `--ai-id` | JSON |
| `list_identities` | `empirica identity-list` | - | JSON |
| `export_public_key` | `empirica identity-export` | `--ai-id` | PEM |
| `verify_signature` | `empirica identity-verify` | `--session-id` | JSON |
| `create_git_checkpoint` | `empirica checkpoint-create` | `--phase`, `--vectors` | JSON |
| `load_git_checkpoint` | `empirica checkpoint-load` | `--session-id` | JSON |
| `create_handoff_report` | `empirica handoff-create` | `--summary`, `--findings` | JSON |
| `query_handoff_reports` | `empirica handoff-query` | `--ai-id` | JSON |

---

## 📋 Detailed Mappings by Phase

### Phase 1: Git Automation (Checkpoints)

#### 1.1 Execute Preflight (Get Prompt)

**MCP Tool:**
```python
{
  "tool_name": "execute_preflight",
  "tool_input": {
    "session_id": "test-123",
    "prompt": "Implement authentication feature"
  }
}
```

**CLI Equivalent:**
```bash
empirica preflight "Implement authentication feature" \
    --session-id test-123 \
    --ai-id mini-agent \
    --prompt-only \
    --json
```

**Output:** Both return JSON with `self_assessment_prompt` field

---

#### 1.2 Submit Preflight Assessment (Creates Checkpoint)

**MCP Tool:**
```python
{
  "tool_name": "submit_preflight_assessment",
  "tool_input": {
    "session_id": "test-123",
    "vectors": {
      "engagement": 0.85,
      "know": 0.70,
      "do": 0.75,
      "context": 0.80,
      "clarity": 0.85,
      "coherence": 0.82,
      "signal": 0.78,
      "density": 0.40,
      "state": 0.75,
      "change": 0.70,
      "completion": 0.60,
      "impact": 0.65,
      "uncertainty": 0.25
    },
    "reasoning": "High confidence in domain knowledge..."
  }
}
```

**CLI Equivalent:**
```bash
# Create assessment file with NESTED format
cat > /tmp/assessment.json << 'EOF'
{
  "engagement": {
    "score": 0.85,
    "rationale": "Actively engaged in task"
  },
  "foundation": {
    "know": {"score": 0.70, "rationale": "Domain knowledge adequate"},
    "do": {"score": 0.75, "rationale": "Capable of execution"},
    "context": {"score": 0.80, "rationale": "Context understood"}
  },
  "comprehension": {
    "clarity": {"score": 0.85, "rationale": "Requirements clear"},
    "coherence": {"score": 0.82, "rationale": "Coherent with context"},
    "signal": {"score": 0.78, "rationale": "Signal identified"},
    "density": {"score": 0.40, "rationale": "Manageable complexity"}
  },
  "execution": {
    "state": {"score": 0.75, "rationale": "Environment mapped"},
    "change": {"score": 0.70, "rationale": "Changes tracked"},
    "completion": {"score": 0.60, "rationale": "Completion criteria clear"},
    "impact": {"score": 0.65, "rationale": "Impact understood"}
  },
  "uncertainty": {
    "score": 0.25,
    "rationale": "Low uncertainty overall"
  }
}
EOF

# Submit with assessment
empirica preflight "Implement authentication feature" \
    --session-id test-123 \
    --ai-id mini-agent \
    --assessment-json /tmp/assessment.json \
    --json
```

**⚠️ CRITICAL:** CLI requires **NESTED format** with `engagement`, `foundation`, `comprehension`, `execution`, `uncertainty` keys. MCP tool accepts **FLAT format** with just vector names.

**Output:** Both create git checkpoint and return assessment results

---

#### 1.3 Create Git Checkpoint (Manual)

**MCP Tool:**
```python
{
  "tool_name": "create_git_checkpoint",
  "tool_input": {
    "session_id": "test-123",
    "phase": "INVESTIGATE",
    "round_num": 2,
    "vectors": {
      "know": 0.80,
      "do": 0.75,
      "context": 0.85,
      "uncertainty": 0.20
    },
    "metadata": {
      "findings": "Reviewed 3 similar implementations",
      "progress": "50%"
    }
  }
}
```

**CLI Equivalent:**
```bash
empirica checkpoint-create \
    --session-id test-123 \
    --ai-id mini-agent \
    --phase INVESTIGATE \
    --round 2 \
    --vectors '{"know": 0.80, "do": 0.75, "context": 0.85}' \
    --metadata '{"findings": "Reviewed 3 implementations", "progress": "50%"}' \
    --json
```

**Output:** Checkpoint hash

---

#### 1.4 Load Checkpoint

**MCP Tool:**
```python
{
  "tool_name": "load_git_checkpoint",
  "tool_input": {
    "session_id": "test-123"
  }
}
```

**CLI Equivalent:**
```bash
empirica checkpoint-load \
    --session-id test-123 \
    --json
```

**Output:** Checkpoint data (vectors, metadata, phase)

---

### Phase 2: Cryptographic Identity (EEP-1)

#### 2.1 Create Identity

**MCP Tool:**
```python
{
  "tool_name": "create_identity",
  "tool_input": {
    "ai_id": "mini-agent",
    "overwrite": false
  }
}
```

**CLI Equivalent:**
```bash
empirica identity-create \
    --ai-id mini-agent \
    --json
```

**Output:** Identity created with Ed25519 keypair

---

#### 2.2 List Identities

**MCP Tool:**
```python
{
  "tool_name": "list_identities"
}
```

**CLI Equivalent:**
```bash
empirica identity-list --json
```

**Output:** Array of identities with public keys

---

#### 2.3 Export Public Key

**MCP Tool:**
```python
{
  "tool_name": "export_public_key",
  "tool_input": {
    "ai_id": "mini-agent"
  }
}
```

**CLI Equivalent:**
```bash
empirica identity-export \
    --ai-id mini-agent
```

**Output:** PEM-encoded public key

---

#### 2.4 Sign Assessment (EEP-1)

**MCP Tool:**
```python
{
  "tool_name": "submit_preflight_assessment",
  "tool_input": {
    "session_id": "test-123",
    "vectors": {...},
    "reasoning": "..."
    # Signing happens automatically if identity exists
  }
}
```

**CLI Equivalent:**
```bash
empirica preflight "task" \
    --session-id test-123 \
    --ai-id mini-agent \
    --assessment-json /tmp/assessment.json \
    --sign \
    --json
```

**Output:** Assessment with `signature` field containing EEP-1 signature

---

#### 2.5 Verify Signature

**MCP Tool:**
```python
{
  "tool_name": "verify_signature",
  "tool_input": {
    "session_id": "test-123"
  }
}
```

**CLI Equivalent:**
```bash
empirica identity-verify \
    --session-id test-123 \
    --json
```

**Output:** Verification status and details

---

### Phase 3: Goal Discovery & Cross-Session Collaboration

#### 3.1 Create Goal

**MCP Tool:**
```python
{
  "tool_name": "create_goal",
  "tool_input": {
    "session_id": "test-123",
    "objective": "Implement user authentication",
    "scope": "project_wide",
    "success_criteria": [
      "All tests passing",
      "Security review complete"
    ],
    "estimated_complexity": "medium",
    "metadata": {
      "priority": "high",
      "deadline": "2025-12-01"
    }
  }
}
```

**CLI Equivalent:**
```bash
empirica goal-create \
    --session-id test-123 \
    --ai-id mini-agent \
    --objective "Implement user authentication" \
    --scope project_wide \
    --success-criteria "All tests passing" \
    --success-criteria "Security review complete" \
    --estimated-complexity medium \
    --metadata '{"priority": "high", "deadline": "2025-12-01"}' \
    --json
```

**Output:** Goal ID and metadata

---

#### 3.2 Add Subtask

**MCP Tool:**
```python
{
  "tool_name": "add_subtask",
  "tool_input": {
    "goal_id": "goal-abc123",
    "description": "Implement password hashing",
    "importance": "high",
    "dependencies": ["subtask-xyz"],
    "estimated_tokens": 500
  }
}
```

**CLI Equivalent:**
```bash
empirica goal-add-subtask \
    --goal-id goal-abc123 \
    --description "Implement password hashing" \
    --importance high \
    --dependencies subtask-xyz \
    --estimated-tokens 500 \
    --json
```

**Output:** Subtask ID

---

#### 3.3 Complete Subtask

**MCP Tool:**
```python
{
  "tool_name": "complete_subtask",
  "tool_input": {
    "task_id": "subtask-xyz789",
    "evidence": "Implemented bcrypt hashing in auth.py lines 45-67. All tests passing."
  }
}
```

**CLI Equivalent:**
```bash
empirica goal-complete-subtask \
    --task-id subtask-xyz789 \
    --evidence "Implemented bcrypt hashing in auth.py lines 45-67. All tests passing." \
    --json
```

**Output:** Completion confirmation

---

#### 3.4 Discover Goals

**MCP Tool:**
```python
{
  "tool_name": "discover_goals",
  "tool_input": {
    "from_ai_id": "other-agent",
    "session_id": "optional-session-filter"
  }
}
```

**CLI Equivalent:**
```bash
# Discover from specific AI
empirica goal-discover \
    --from-ai-id other-agent \
    --json

# Discover all goals
empirica goal-discover \
    --ai-id mini-agent \
    --json
```

**Output:** Array of discoverable goals from git notes

---

#### 3.5 Resume Goal

**MCP Tool:**
```python
{
  "tool_name": "resume_goal",
  "tool_input": {
    "goal_id": "goal-abc123",
    "ai_id": "mini-agent"
  }
}
```

**CLI Equivalent:**
```bash
empirica goal-resume \
    --goal-id goal-abc123 \
    --ai-id mini-agent \
    --json
```

**Output:** Goal details and handoff context

---

### Additional Tools

#### Create Handoff Report

**MCP Tool:**
```python
{
  "tool_name": "create_handoff_report",
  "tool_input": {
    "session_id": "test-123",
    "task_summary": "Completed authentication implementation",
    "key_findings": [
      "Used bcrypt for password hashing",
      "Implemented JWT tokens"
    ],
    "remaining_unknowns": [
      "OAuth integration needs review"
    ],
    "next_session_context": "Ready for OAuth implementation",
    "artifacts_created": ["auth.py", "test_auth.py"]
  }
}
```

**CLI Equivalent:**
```bash
empirica handoff-create \
    --session-id test-123 \
    --summary "Completed authentication implementation" \
    --findings "Used bcrypt for password hashing" \
    --findings "Implemented JWT tokens" \
    --unknowns "OAuth integration needs review" \
    --next-context "Ready for OAuth implementation" \
    --artifacts auth.py test_auth.py \
    --json
```

**Output:** Handoff report ID

---

#### Query Handoff Reports

**MCP Tool:**
```python
{
  "tool_name": "query_handoff_reports",
  "tool_input": {
    "session_id": "test-123",
    "ai_id": "mini-agent",
    "limit": 10
  }
}
```

**CLI Equivalent:**
```bash
empirica handoff-query \
    --session-id test-123 \
    --ai-id mini-agent \
    --limit 10 \
    --json
```

**Output:** Array of handoff reports

---

## 🔧 Common Options

### Global Flags (Available on Most Commands)

| Flag | Description | MCP Equivalent |
|------|-------------|----------------|
| `--json` | Output as JSON | Default for MCP |
| `--verbose` | Verbose output | Not needed in MCP |
| `--quiet` | Suppress output | Not applicable |
| `--no-git` | Skip git operations | N/A |

### Session Resolution

Both MCP and CLI support session aliases:

```bash
# CLI
empirica checkpoint-load --session-id latest:active:mini-agent

# MCP (same)
{
  "tool_name": "load_git_checkpoint",
  "tool_input": {
    "session_id": "latest:active:mini-agent"
  }
}
```

**Alias patterns:**
- `latest` - Most recent session for current AI
- `latest:active:ai-id` - Most recent active session for AI
- `latest:completed:ai-id` - Most recent completed session
- `session-123` - Explicit session ID

---

## 🐛 Assessment Format Conversion

### MCP Format (Flat - Used by MCP Tools)

```json
{
  "engagement": 0.85,
  "know": 0.70,
  "do": 0.75,
  "context": 0.80,
  "clarity": 0.85,
  "coherence": 0.82,
  "signal": 0.78,
  "density": 0.40,
  "state": 0.75,
  "change": 0.70,
  "completion": 0.60,
  "impact": 0.65,
  "uncertainty": 0.25
}
```

### CLI Format (Nested - Required by --assessment-json)

```json
{
  "engagement": {
    "score": 0.85,
    "rationale": "Genuine reasoning here"
  },
  "foundation": {
    "know": {"score": 0.70, "rationale": "..."},
    "do": {"score": 0.75, "rationale": "..."},
    "context": {"score": 0.80, "rationale": "..."}
  },
  "comprehension": {
    "clarity": {"score": 0.85, "rationale": "..."},
    "coherence": {"score": 0.82, "rationale": "..."},
    "signal": {"score": 0.78, "rationale": "..."},
    "density": {"score": 0.40, "rationale": "..."}
  },
  "execution": {
    "state": {"score": 0.75, "rationale": "..."},
    "change": {"score": 0.70, "rationale": "..."},
    "completion": {"score": 0.60, "rationale": "..."},
    "impact": {"score": 0.65, "rationale": "..."}
  },
  "uncertainty": {
    "score": 0.25,
    "rationale": "..."
  }
}
```

**Why the difference?**
- MCP tools internally convert flat → nested before calling CLI
- CLI `--assessment-json` expects genuine LLM response format (with rationales)
- See: `empirica/core/canonical/canonical_epistemic_assessment.py:585-788`

---

## ✅ Testing Checklist

Mini-agent should verify both MCP and CLI produce identical results:

### Phase 1: Checkpoints
- [ ] MCP `execute_preflight` = CLI `--prompt-only`
- [ ] MCP `submit_preflight_assessment` = CLI `--assessment-json`
- [ ] Both create checkpoints in git notes
- [ ] Checkpoint data identical

### Phase 2: Identity
- [ ] MCP `create_identity` = CLI `identity-create`
- [ ] MCP `export_public_key` = CLI `identity-export`
- [ ] Signatures identical with `--sign` flag

### Phase 3: Goals
- [ ] MCP `create_goal` = CLI `goal-create`
- [ ] MCP `discover_goals` = CLI `goal-discover`
- [ ] Goal data in git notes identical

---

## 📚 Additional Resources

- **CLI Help:** `empirica <command> --help`
- **MCP Schema:** `mcp_local/empirica_mcp_server.py`
- **Assessment Parser:** `empirica/core/canonical/canonical_epistemic_assessment.py`
- **Test Scripts:** `test_working_checkpoint.sh`, `test_checkpoint_helper.sh`
- **Examples:** `docs/examples/assessment_format_example.json`

---

## 🚀 Quick Start for Mini-Agent

**Using MCP (Recommended):**
```python
# 1. Execute preflight
response = mcp_call("execute_preflight", {
    "session_id": "test-123",
    "prompt": "Implement feature X"
})

# 2. Perform genuine self-assessment (your reasoning)

# 3. Submit assessment (MCP handles format conversion)
mcp_call("submit_preflight_assessment", {
    "session_id": "test-123",
    "vectors": {
        "engagement": 0.85,
        "know": 0.70,
        # ... flat format
    },
    "reasoning": "My genuine assessment..."
})
```

**Using CLI (Alternative):**
```bash
# 1. Get prompt
empirica preflight "Implement feature X" \
    --session-id test-123 \
    --prompt-only > prompt.json

# 2. Perform genuine self-assessment

# 3. Submit with nested format
empirica preflight "Implement feature X" \
    --session-id test-123 \
    --assessment-json assessment.json
```

**Both approaches:**
- ✅ Create git checkpoints
- ✅ Store in session database
- ✅ Enable cross-session discovery
- ✅ Support EEP-1 signing

Choose MCP for programmatic access, CLI for testing/debugging.

---

**Version:** 2.0  
**Last Tested:** 2025-11-27  
**Status:** Production ready
