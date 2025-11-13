# Enhanced Tool Management

## Overview

Enhanced tools inspired by Mini-Agent, optimized for Empirica's investigation workflow.

## Tools

### 1. Enhanced File Tools (`enhanced_file_tools.py`)

Token-aware file reading for large codebases.

**Features:**
- Respects context/token limits
- Smart truncation (start, end, middle)
- Line numbering
- Binary search for optimal truncation

**Usage:**
```python
from empirica.components.tool_management.enhanced_file_tools import EnhancedFileTools
from pathlib import Path

tools = EnhancedFileTools()

# Read with token limit
result = tools.read_file_with_limits(
    path=Path('large_file.py'),
    max_tokens=4000,
    add_line_numbers=True
)

# Smart reading (show start + end)
result = tools.smart_read_large_file(
    path=Path('huge_file.py'),
    max_tokens=4000,
    show_start=True,
    show_end=True
)
```

### 2. Enhanced Bash Tools (`enhanced_bash_tools.py`)

Background process management for non-blocking investigations.

**Features:**
- Background execution
- Output streaming
- Session management
- Graceful termination

**Usage:**
```python
from empirica.components.tool_management.enhanced_bash_tools import EnhancedBashTools

bash = EnhancedBashTools()

# Start in background
bash.execute_background("pytest tests/ -v", "test_run")

# Continue work...
# Check progress
status = bash.get_output("test_run", tail_lines=20)

# Wait for completion
final = bash.wait_for_completion("test_run", timeout=300)

# Kill if needed
bash.kill_session("test_run")
```

## Dependencies

- `tiktoken` - Token counting (EnhancedFileTools)

Install: `pip install tiktoken`

## Integration with Empirica

These tools integrate seamlessly with Empirica's investigation framework:

```python
# During INVESTIGATE phase
from empirica.components.tool_management.enhanced_file_tools import EnhancedFileTools
from empirica.components.tool_management.enhanced_bash_tools import EnhancedBashTools

file_tools = EnhancedFileTools()
bash_tools = EnhancedBashTools()

# Start background investigation tools
bash_tools.execute_background("mypy . --check", "typecheck")
bash_tools.execute_background("pytest tests/", "tests")

# Read files with token awareness
for file in codebase_files:
    content = file_tools.read_file_with_limits(file, max_tokens=2000)
    # ... epistemic analysis ...

# Check background tool results
typecheck_result = bash_tools.get_output("typecheck")
test_result = bash_tools.get_output("tests")
```

## Testing

```bash
# Test file tools
python3 empirica/components/tool_management/enhanced_file_tools.py

# Test bash tools
python3 empirica/components/tool_management/enhanced_bash_tools.py
```

## See Also

- Full integration guide: `docs/integrations/MINIMAX_INTEGRATION.md`
- Empirica SKILL.md: `docs/skills/SKILL.md`
- Claude Skills: `claude-skills/`
