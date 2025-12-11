# Multi-AI Setup Complete

**Date**: 2025-12-11
**Status**: ✅ Ready for coordination

## AI Configurations

### 1. Vibe (Devstral/Codestral)
- **Config**: `~/.vibe/agents/empirica.toml`
- **System Prompt**: `~/.vibe/prompts/empirica.md`
- **AI_ID**: `devstral`
- **Role**: Action-based file operations specialist
- **Working Dir**: `/home/yogapad/empirical-ai/empirica`
- **MCP Server**: ✅ Configured (same as Claude Code)
- **Usage**: `vibe --agent empirica -p "your prompt"`

### 2. Qwen (Alibaba)
- **System Prompt**: `~/.qwen/QWEN.md`
- **AI_ID**: `qwen`
- **Role**: Fast execution and code operations
- **Working Dir**: `/home/yogapad/empirical-ai/empirica`
- **Usage**: `qwen "your prompt"` (positional, one-shot by default)

### 3. Gemini (Google)
- **System Prompt**: `~/.gemini/GEMINI.md`
- **AI_ID**: `gemini`
- **Role**: Reasoning and judgment specialist
- **Working Dir**: `/home/yogapad/empirical-ai/empirica`
- **Usage**: `gemini "your prompt"`

## All AIs Now Have

✅ **Empirica System Prompt** - Understanding of CASCADE workflow
✅ **Working Directory** - Set to `/home/yogapad/empirical-ai/empirica`
✅ **AI Identity** - Each knows their role and biases
✅ **Empirica Commands** - Know how to use `empirica` CLI
✅ **Project Context** - Can run `empirica project-bootstrap --check-integrity`

## MCP Server Details

**Vibe MCP Configuration**:
```toml
[[mcp_servers]]
name = "empirica"
transport = "stdio"
command = "env"
args = [
    "LD_LIBRARY_PATH=",
    "/home/yogapad/empirical-ai/empirica/.venv-mcp/bin/python3",
    "/home/yogapad/empirical-ai/empirica/mcp_local/empirica_mcp_server.py"
]
```

**Environment**:
- PYTHONPATH=/home/yogapad/empirical-ai/empirica
- EMPIRICA_ENABLE_MODALITY_SWITCHER=false

**Tools**: All Empirica MCP tools enabled (`empirica_*`)

## Coordination Commands

### Get Project Context (All AIs)
```bash
empirica project-bootstrap --project-id ea2f33a4-d808-434b-b776-b7246bd6134a --check-integrity --output json
```

### Delegation Examples

**Vibe (file operations)**:
```bash
vibe --agent empirica -p "Scan docs/ directory, identify files with 'PLANNED' or 'TODO' keywords, move to docs/future/. Output list of moved files to /tmp/vibe_moved_files.json"
```

**Qwen (fast execution)**:
```bash
qwen "Read /tmp/phantom_commands_audit.json, process all RENAMED category commands, update docs with correct command names. Save results to /tmp/qwen_fixes.json"
```

**Gemini (judgment)**:
```bash
gemini "Review phantom commands in UNKNOWN category from /tmp/phantom_commands_audit.json. For each, decide: keep (with reason), remove (with reason), or mark as [PLANNED]. Save decisions to /tmp/gemini_decisions.json"
```

## Next Steps

1. **Claude Code** (you): Complete Phase 1 categorization
2. **Delegate to AIs**: Use commands above
3. **Review outputs**: Check /tmp/*.json files
4. **Integrate**: Merge approved changes
5. **Verify**: Run integrity check again

## Notes

- All AIs understand Empirica workflow (PREFLIGHT → CHECK → POSTFLIGHT)
- They know to use noetic reasoning, not just pattern matching
- Working directory is set - they start in the right place
- System prompts emphasize epistemic integrity

Ready for multi-AI coordination! 🚀
