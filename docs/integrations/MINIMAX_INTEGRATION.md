# MiniMax and Mini-Agent Integration with Empirica

**Date**: 2025-11-11  
**Status**: Phase 1 Complete ✅

---

## Executive Summary

✅ **MiniMax M2**: Fully integrated via modality switcher  
✅ **Claude Skills**: Added as git submodule (15 professional tools)  
✅ **Enhanced Tools**: Token-aware files + background bash execution  

**Result**: Epistemic-aware agents with MiniMax reasoning + Claude tooling

---

## Quick Start

### 1. Use MiniMax M2
```bash
export MINIMAX_API_KEY="your_key"
empirica query-ai "analyze this code" --adapter minimax
```

### 2. Use Enhanced File Tools
```python
from empirica.components.tool_management.enhanced_file_tools import EnhancedFileTools

tools = EnhancedFileTools()
result = tools.read_file_with_limits(
    path=Path('large_file.py'),
    max_tokens=4000  # Respects context limits
)
```

### 3. Use Enhanced Bash Tools
```python
from empirica.components.tool_management.enhanced_bash_tools import EnhancedBashTools

bash = EnhancedBashTools()
bash.execute_background("pytest tests/", "test_run")
# ... continue work ...
status = bash.get_output("test_run")
```

### 4. Use Claude Skills
```bash
# List available skills
ls claude-skills/*/SKILL.md

# Load skill into context
cat claude-skills/document-skills/SKILL.md
```

---

## Architecture

```
EMPIRICA (Epistemic Assessment)
    ↓
┌───────────────────────────────────────┐
│   Modality Switcher                   │
│   ├─ MiniMax M2 Adapter ✅            │
│   ├─ Qwen, Gemini, etc.              │
│   └─ AI-to-AI routing                │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│   Enhanced Tool Layer                 │
│   ├─ Enhanced File Tools ✅ NEW       │
│   ├─ Enhanced Bash Tools ✅ NEW       │
│   └─ Claude Skills (15) ✅ NEW        │
└───────────────────────────────────────┘
```

---

## Integration Details

### MiniMax M2 Adapter

**Location**: `empirica/plugins/modality_switcher/adapters/minimax_adapter.py`  
**Version**: 3.0.0  
**Features**:
- Anthropic SDK with MiniMax base URL
- Thinking blocks extraction
- Genuine epistemic assessment from thinking
- Streaming support

### Enhanced File Tools

**Location**: `empirica/components/tool_management/enhanced_file_tools.py`  
**Features**:
- Token-aware truncation (respects context limits)
- Smart reading strategies (start+end for large files)
- Line numbering support
- Handles large codebases gracefully

**Use Cases**:
- Reading large files during investigations
- Analyzing codebases within token limits
- Intelligent file truncation

### Enhanced Bash Tools

**Location**: `empirica/components/tool_management/enhanced_bash_tools.py`  
**Features**:
- Background process execution
- Non-blocking investigations
- Output capture and streaming
- Session management

**Use Cases**:
- Running tests while investigating
- Long-running builds/linters
- Concurrent tool execution

### Claude Skills

**Location**: `claude-skills/` (git submodule)  
**Count**: 15 professional skills  
**Skills Include**:
- Document generation (PDF, DOCX)
- Canvas design
- Algorithmic art
- Webapp testing
- MCP builder
- Internal comms templates
- And more...

---

## How Empirica SKILL.md and Claude Skills Work Together

### Empirica SKILL.md (`docs/skills/SKILL.md`)
**Purpose**: Epistemic self-awareness framework  
**Teaches**: How to assess KNOW, DO, CONTEXT, UNCERTAINTY  
**Use**: Before/during/after tasks for calibration

### Claude Skills (`claude-skills/*/SKILL.md`)
**Purpose**: Task execution tools  
**Provides**: Document generation, design, testing tools  
**Use**: When building specific artifacts

### Combined Workflow
```
1. PREFLIGHT (Empirica) → Assess capability
2. LOAD SKILL (Claude)  → Get execution knowledge
3. EXECUTE (Task)       → Create artifact
4. POSTFLIGHT (Empirica) → Measure learning
```

**Result**: Epistemically-aware task execution 🎯

---

## Examples

### Example 1: Document Generation with Epistemic Awareness

```bash
# 1. Assess capability
SESSION=$(empirica preflight "Generate technical PDF")

# 2. Load Claude document skill
cat claude-skills/document-skills/SKILL.md > /tmp/skill.txt

# 3. Execute PDF generation
# ... use skill knowledge ...

# 4. Measure learning
empirica postflight $SESSION --summary "PDF completed"
# Shows: Were you appropriately confident? What did you learn?
```

### Example 2: Large Codebase Investigation

```python
from empirica.components.tool_management.enhanced_file_tools import EnhancedFileTools
from pathlib import Path

tools = EnhancedFileTools()

# Investigate large file without context overflow
for file in codebase_files:
    result = tools.smart_read_large_file(
        path=Path(file),
        max_tokens=2000,  # Leave room for analysis
        show_start=True,
        show_end=True
    )
    
    # ... epistemic analysis ...
    print(f"Analyzed {result['lines_shown']}/{result['total_lines']} lines")
```

### Example 3: Background Test Execution

```python
from empirica.components.tool_management.enhanced_bash_tools import EnhancedBashTools

bash = EnhancedBashTools()

# Start tests in background
bash.execute_background("pytest tests/ -v --cov", "tests")
bash.execute_background("mypy . --check", "typecheck")

# Continue investigation...
# ... epistemic work ...

# Check results
test_result = bash.wait_for_completion("tests", timeout=300)
type_result = bash.get_output("typecheck")

# Assess based on results
# ... postflight calibration ...
```

---

## File Locations

```
empirica/
├── plugins/modality_switcher/
│   └── adapters/
│       └── minimax_adapter.py       # MiniMax M2 API
│
├── components/tool_management/
│   ├── enhanced_file_tools.py        # NEW: Token-aware files
│   └── enhanced_bash_tools.py        # NEW: Background processes
│
├── docs/
│   ├── skills/
│   │   └── SKILL.md                  # Empirica epistemic framework
│   └── integrations/
│       └── MINIMAX_INTEGRATION.md    # This file
│
└── claude-skills/ (submodule)        # NEW: 15 Claude Skills
    ├── document-skills/
    ├── canvas-design/
    └── ... (13 more)
```

---

## Testing

```bash
# Test enhanced file tools
python3 empirica/components/tool_management/enhanced_file_tools.py

# Test enhanced bash tools  
python3 empirica/components/tool_management/enhanced_bash_tools.py

# Test MiniMax adapter
export MINIMAX_API_KEY="your_key"
empirica query-ai "test" --adapter minimax

# Test Claude Skills
cat claude-skills/document-skills/SKILL.md
```

---

## Resources

### Internal
- Empirica Skills: `docs/skills/SKILL.md`
- MiniMax Adapter: `empirica/plugins/modality_switcher/adapters/minimax_adapter.py`
- Enhanced Tools: `empirica/components/tool_management/`
- Claude Skills: `claude-skills/`

### External
- Mini-Agent: https://github.com/MiniMax-AI/Mini-Agent
- Claude Skills: https://github.com/anthropics/skills
- MiniMax Platform: https://platform.minimax.io

---

## Conclusion

**Integration Status**: ✅ Phase 1 Complete

- MiniMax M2: Production-ready
- Enhanced Tools: Implemented and tested
- Claude Skills: Available via submodule

**Next**: Phase 2 will add unified tool interface and context summarization.

The combination of Empirica (epistemic awareness) + MiniMax (extended reasoning) + Claude Skills (execution tools) creates a powerful agent framework. 🚀

---

**Last Updated**: 2025-11-11
