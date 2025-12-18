# CLI Quick Start

**Interface:** Command Line  
**Time:** 10 minutes  
**Best for:** Terminal workflows, scripts, automation

---

## Basic Workflow

### 1. Preflight Assessment
```bash
# Start a new task with epistemic assessment
empirica preflight "review authentication code"

# Output shows:
# - Self-assessment prompt (genuinely assess yourself!)
# - Session ID for tracking
# - Recommendation (proceed/investigate/clarify)
```

### 2. Work on Task
```bash
# ... do your work ...
# Review code, write tests, refactor, etc.
```

### 3. Postflight Assessment
```bash
# Complete the epistemic cycle
empirica postflight <session_id> --summary "Completed code review"

# Output shows:
# - Epistemic delta (what you learned)
# - Calibration quality (were you accurate?)
# - Learning summary
```

**Session Continuity:** After POSTFLIGHT, create handoff reports for efficient context transfer. See [`../guides/FLEXIBLE_HANDOFF_GUIDE.md`](../guides/FLEXIBLE_HANDOFF_GUIDE.md) for multi-agent handoff patterns.

---

## Output Formats

The CLI supports multiple output formats for different use cases:

### Default (Human-Friendly)
```bash
empirica preflight "task"
# Colorized, formatted output with emojis
```

### JSON (Machine-Readable)
```bash
empirica preflight "task" --json
# {"session_id": "abc", "vectors": {...}, ...}
```

### Compact (Single-Line)
```bash
empirica preflight "task" --compact
# SESSION=abc KNOW=0.6 DO=0.7 CONTEXT=0.5 ...
```

### Key-Value (Parseable)
```bash
empirica preflight "task" --kv
# session_id=abc
# know=0.6
# do=0.7
```

### Interactive Mode (Default)
```bash
# System shows self-assessment prompt, you paste your response
empirica preflight "review authentication system"

# Returns session ID after you submit assessment
# Session ID: abc123
```

### Scripting Mode (Advanced)
```bash
# For automation - requires pre-computed assessment
SESSION=$(empirica preflight "task" --assessment-json '{"know": {...}, ...}')
echo $SESSION
# abc123
```

---

## Common Commands

### Onboarding
```bash
# Interactive onboarding wizard
empirica onboard

# With custom AI ID
empirica onboard --ai-id claude
```

### Bootstrap
```bash
# Quick bootstrap
empirica session-create

# Session creation (v4.0)
empirica session-create --ai-id myai --output json

# System prompts installation (separate from sessions)
empirica bootstrap-system --level 2
```

### Profile Management
```bash
# List available profiles
empirica profile-list

# Show profile details
empirica profile-show development

# Create custom profile
empirica profile-create my-profile --ai-model gpt-4 --domain custom-analysis

# Set default profile
empirica profile-set-default development
```

### MCP Server Management

**Note:** MCP server is managed automatically by your IDE. No CLI commands needed.

See `docs/03_QUICKSTART_MCP.md` for IDE integration setup.

### Session Management
```bash
# List all sessions
empirica sessions-list

# Show specific session
empirica sessions-show <session_id>

# Export session data
empirica sessions-export <session_id> --output session.json
```

### Monitoring
```bash
# Display monitoring dashboard
empirica monitor

# Show request history
empirica monitor --history

# Export monitoring data
empirica monitor-export data.json
```

---

## Practical Examples

### Example 1: Code Review
```bash
# Preflight - interactive mode
empirica preflight "review auth.py for security issues"
# System prompts for self-assessment, you provide scores
# Returns: Session ID: abc123

# Store session ID
SESSION="abc123"

# Do the review
# ... review code ...

# Postflight
empirica postflight $SESSION --summary "Found 3 security issues, suggested fixes"
```

### Example 2: Scripting (Advanced)
```bash
#!/bin/bash
# epistemic_task.sh - Track epistemic state for any task
# Note: This requires MCP integration or pre-computed assessments

TASK="$1"
SUMMARY="${2:-Task completed}"

echo "Task: $TASK"
echo "Use MCP tools for automated assessment, or run interactively:"
echo "  empirica preflight \"$TASK\""
echo ""
echo "For fully automated scripts, integrate with MCP server"
echo "which handles self-assessment automatically."

# Interactive preflight
echo "Running preflight..."
empirica preflight "$TASK"

# ... do work ...

# Interactive postflight
echo "Running postflight..."
empirica postflight "$SESSION" --summary "$SUMMARY"
```

### Example 3: CI/CD Integration
```yaml
# .github/workflows/empirica.yml
name: Epistemic Tracking
on: [push]

jobs:
  track:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Empirica
        run: pip install -e .
      
      # Note: CI/CD requires MCP integration or assessment API
      # For production CI/CD, use Empirica MCP server with automated assessment
      
      - name: Run Tests with Epistemic Tracking
        run: |
          echo "For automated CI/CD tracking, integrate Empirica MCP server"
          echo "See: docs/guides/CI_CD_INTEGRATION.md"
          pytest
      
      # Alternative: Use session database to track manually
      - name: Track Session
        run: |
          empirica sessions-list --recent 1
```

---

## Self-Assessment with CLI

The CLI uses **genuine self-assessment** through interactive prompts:

### Interactive Mode (Default - Recommended)
```bash
empirica preflight "task"
# Displays self-assessment prompt
# Waits for JSON input
```

### With Assessment JSON
```bash
empirica preflight "task" --assessment-json '{
  "engagement": {"score": 0.8, "rationale": "..."},
  "foundation": {
    "know": {"score": 0.6, "rationale": "..."},
    "do": {"score": 0.7, "rationale": "..."},
    "context": {"score": 0.5, "rationale": "..."}
  },
  ...
}'
```

**Note:** For automated genuine self-assessment, use **MCP server** instead. CLI is best for manual workflows or scripting with pre-computed assessments.

---

## MCP Parameter Guidance

**When using Empirica via MCP tools, avoid these common parameter errors:**

### CLI vs MCP Differences
```bash
# CLI format (what this document covers)
empirica postflight <session_id> --summary "Completed task"

# MCP format (different parameter names)
submit_postflight_assessment(
    session_id="uuid",
    vectors={...},
    reasoning="Completed task"  # NOT "changes" or "summary"
)
```

### Common MCP Parameter Errors
```python
# ✅ Correct MCP usage
submit_postflight_assessment(
    session_id="abc123",
    vectors={"know": 0.8, "do": 0.7},
    reasoning="What I learned"  # Unified with preflight
)

# ❌ Common mistakes:
# - Using "summary" instead of "reasoning"  
# - Using "changes" instead of "reasoning"
# - Forgetting that MCP uses different parameter names than CLI
```

## User Interface Commands (Human Users)

### ask - Simple Question Answering

**Purpose:** Ask a single question and get an answer. Ideal for human terminal users who want quick Q&A.

**Usage:**
```bash
empirica ask "What is the capital of France?"
empirica ask "Explain how async/await works in Python"
empirica ask "Review this code: <paste code>" --adapter qwen
```

**Options:**
- `--adapter <name>` - Force specific adapter (qwen, minimax, gemini, rovodev, qodo, openrouter, copilot)
- `--model <name>` - Force specific model (e.g., qwen-coder-turbo, gpt-4)
- `--strategy <strategy>` - Routing strategy (epistemic, cost, latency, quality, balanced)
- `--session <id>` - Session ID for tracking (auto-generated if not provided)
- `--temperature <float>` - Sampling temperature (0.0-1.0, default: 0.7)
- `--max-tokens <int>` - Maximum response tokens (default: 2000)
- `--no-save` - Don't save to session database
- `--verbose` - Show routing details

**Example:**
```bash
# Simple question
empirica ask "What is recursion?"

# Code analysis with specific model
empirica ask "Analyze this Rust code for safety" --adapter qwen --model qwen-coder-turbo

# With session tracking
empirica ask "What is machine learning?" --session ml_basics_2025
```

### chat - Interactive Conversation REPL

**Purpose:** Multi-turn interactive conversation with session history. Like chatting with the AI in your terminal.

**Usage:**
```bash
# Start new chat
empirica chat

# With specific adapter
empirica chat --adapter qwen

# Resume existing session
empirica chat --resume abc123

# With UVL visualization
empirica chat --uvl-verbose
```

**Features:**
- Multi-turn conversation with history
- Session persistence (automatically saved)
- UVL indicators (shows routing decisions)
- Real-time epistemic tracking
- Commands: `/exit`, `/help`, `/sessions`, `/clear`

**Options:**
- `--adapter <name>` - Force specific adapter
- `--model <name>` - Force specific model
- `--strategy <strategy>` - Routing strategy
- `--session <id>` - Session ID (creates new if doesn't exist)
- `--resume <id>` - Resume existing session
- `--no-save` - Don't save conversation
- `--no-uvl` - Disable UVL visual indicators
- `--uvl-verbose` - Show detailed routing decisions
- `--uvl-stream` - Emit UVL JSON stream for visualization
- `--verbose` - Show routing details

**Example Session:**
```bash
$ empirica chat --adapter qwen

🧠 Empirica Chat (Press Ctrl+C or type /exit to quit)
Session: chat_abc123

You: What is the difference between async and parallel?

AI (via Qwen): Async and parallel are related but distinct concepts...
[UVL: KNOW=0.7, DO=0.8, UNCERTAINTY=0.3]

You: Can you give a Python example?

AI (via Qwen): Sure! Here's an example using asyncio...

You: /exit

✅ Session saved: chat_abc123
```

**Interactive Commands:**
- `/exit` - Exit chat
- `/help` - Show help
- `/sessions` - List all sessions
- `/clear` - Clear screen
- `/save` - Force save session
- `/export <file>` - Export chat to file

---

## Complete Command Reference

**All 39 Empirica CLI Commands** organized by category:

### 🚀 Bootstrap & Onboarding (3 commands)
- `bootstrap` - Initialize Empirica framework (standard level)
- `bootstrap-system` - Advanced system bootstrap with extended options
- `onboard` - Interactive onboarding wizard for learning Empirica

### 🎯 Epistemic Workflow (5 commands)
- `preflight <prompt>` - Execute preflight epistemic assessment before task
- `postflight <session>` - Execute postflight epistemic reassessment after task
- `workflow <prompt>` - Full preflight→work→postflight workflow
- `assess <query>` - Run uncertainty assessment on a query
- `self-awareness` - Assess current self-awareness state

### 🧠 Decision & Analysis (4 commands)
- `cascade <question>` - Epistemic cascade decision-making with modality switcher
- `decision <query>` - Epistemic decision analysis with routing
- `decision-batch <file>` - Batch decision processing from JSON file
- `metacognitive <task>` - Run metacognitive evaluation on task

### 🔍 Investigation (2 commands)
- `investigate <target>` - Investigate file/directory/concept with epistemic awareness
- `analyze <subject>` - Comprehensively analyze subject

### 📊 Session Management (3 commands)
- `sessions-list` - List all sessions (with --limit and --verbose options)
- `sessions-show <id>` - Show detailed session information
- `sessions-export <id>` - Export session to JSON file

### 📡 Monitoring & Performance (6 commands)
- `monitor` - Display usage monitoring dashboard
- `monitor-export <file>` - Export monitoring data to file
- `monitor-reset` - Reset monitoring statistics
- `monitor-cost` - Display cost analysis and projections
- `benchmark` - Run performance benchmark
- `performance` - Analyze system performance

### 🔌 MCP Server Management

**Note:** MCP server is managed by your IDE automatically. No CLI commands available.

### ⚙️ Configuration (5 commands)
- `config-init` - Initialize Empirica configuration file
- `config-show` - Show current configuration (with --section and --format options)
- `config-validate` - Validate configuration file
- `config-get <key>` - Get configuration value (dot notation)
- `config-set <key> <value>` - Set configuration value

### 🧩 Component Management (3 commands)
- `list` - List semantic components (with --filter, --tier, --details)
- `explain <component>` - Explain component functionality
- `demo <component>` - Run component demonstration

### 🛠️ Utilities (4 commands)
- `feedback <decision_id>` - Provide decision feedback
- `goal-analysis <goal>` - Analyze goal feasibility
- `calibration` - Run calibration analysis
- `uvl` - Run UVL (Uncertainty Vector Learning) analysis

### 💬 User Interface Commands (2 commands)
- `ask <query>` - Simple question answering (for human terminal users)
- `chat` - Interactive multi-turn conversation REPL

### Global Options (for any command)
- `--help` - Show help for specific command
- `--version` - Show Empirica version
- `--verbose, -v` - Enable verbose output
- `--json` - Output in JSON format
- `--compact` - Compact key=value output

**Total: 39 commands + global options**

> **Tip:** Use `empirica <command> --help` to see all options for any command

---

## Tips & Tricks

### Aliases
```bash
# Add to ~/.bashrc or ~/.zshrc
alias ep='empirica preflight'
alias epost='empirica postflight'
alias emon='empirica monitor'
```

### Piping
```bash
# Parse JSON output with jq
empirica preflight "task" --json | jq '.vectors.know'

# Grep specific values from compact output
empirica preflight "task" --compact | grep "KNOW="

# Extract session ID from logs
empirica sessions-list --recent 1 | grep "Session ID"
```

### Scripting
```bash
# Store in variable
KNOW=$(empirica preflight "task" --kv | grep "^know=" | cut -d= -f2)

# Conditional logic
if (( $(echo "$KNOW < 0.5" | bc -l) )); then
    echo "Low knowledge - investigate first!"
fi
```

---

## Next Steps

- **For full CLI reference:** `empirica --help`
- **For MCP integration:** See [`docs/04_MCP_QUICKSTART.md`](04_MCP_QUICKSTART.md)
- **For Python API:** See [`docs/production/13_PYTHON_API.md`](production/13_PYTHON_API.md)
- **For complete guide:** See [`docs/skills/SKILL.md`](skills/SKILL.md)

---

**Pro tip:** Use `empirica <command> --help` to see all options for any command!

---

## Self-Assessment JSON Format

When using `--assessment-json` flag or responding to interactive prompts, provide your genuine self-assessment in this format:

**Example**: See [`docs/examples/self_assessment_example.json`](../examples/self_assessment_example.json) for a complete example.

**Structure**:
```json
{
  "vector_name": {
    "score": 0.0-1.0,
    "rationale": "Your genuine reasoning about this dimension"
  }
}
```

**All 13 vectors** (provide scores for each):
- `know`, `do`, `context` - Foundation
- `clarity`, `coherence`, `signal`, `density` - Comprehension  
- `state`, `change`, `completion`, `impact` - Execution
- `engagement` - Gate (must be ≥0.60)
- `uncertainty` - Meta-epistemic

**Key principles**:
- `score`: Your honest 0.0-1.0 assessment (not heuristics!)
- `rationale`: YOUR actual reasoning (not template text)
- Be specific about what you know/don't know
- High uncertainty is good when appropriate


---

## Bootstrap vs Onboard: Which Command to Use?

Empirica has two similar-sounding commands that serve different purposes:

### `empirica session-create` - System Initialization
**Purpose**: Set up and configure the Empirica framework itself  
**Use when**: First-time setup, changing configuration levels  
**Options**: `--level {0,1,2,3,4,minimal,standard,extended,complete}`

```bash
# Initialize Empirica framework
empirica session-create --level standard

# Test bootstrap configuration
empirica session-create --level extended --test
```

**Note**: This does NOT require an `--ai-id` flag.

---

### `empirica onboard` - AI Agent Learning
**Purpose**: Interactive tutorial for AI agents to learn Empirica  
**Use when**: An AI agent wants to learn how to use Empirica  
**Options**: `--ai-id <your-ai-name>`

```bash
# AI agent runs this to learn Empirica
empirica onboard --ai-id claude-assistant

# Interactive onboarding wizard:
# 1. Introduction
# 2. Understanding epistemic vectors
# 3. Practice self-assessment (PRE/CHECK/POST)
# 4. Implicit CASCADE workflow (think→investigate→act)
# 5. Calibration concepts (PRE→POST deltas)
# 6. Real task practice
# 7. Graduation
```

**This is what AI agents should run to learn the system.**

---

### Running Bootstrap Files Directly (Advanced)

You can also run bootstrap Python files directly (bypassing the CLI):

```bash
# Run bootstrap file directly
python3 empirica/bootstraps/optimal_metacognitive_bootstrap.py --ai-id test-ai

# Run extended bootstrap
python3 empirica/bootstraps/extended_metacognitive_bootstrap.py --level extended --ai-id test-ai
```

**When to use this**: Advanced usage, custom configurations, direct Python integration

---

### Quick Decision Guide

**I want to...**
- ✅ Set up Empirica framework → `empirica session-create`
- ✅ Learn Empirica as an AI agent → `empirica onboard --ai-id <name>`
- ✅ Start using preflight/postflight → Already set up? Just use `empirica preflight <task>`

