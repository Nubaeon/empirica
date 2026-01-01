### Grounding Note

Empirica is **evidence-based, not theoretical**. Avoid:
- Inventing terminology not in the actual codebase
- Creating elaborate philosophical frameworks
- "Crystalline states" or other metaphysical abstractions
- Thresholds not derived from actual calibration data

When uncertain, check the CLI: `empirica --help`

---

### Long Context Management

**Context window:** Leverage 1M+ token capacity for comprehensive document analysis.

**Session continuity patterns:**
- Use `empirica project-bootstrap` to load full project context (~800 tokens compressed)
- For large codebases, segment analysis across multiple semantic searches
- Preserve context through handoffs rather than re-reading

**Document analysis workflow:**
```bash
# Load full project state
empirica project-bootstrap --session-id <ID> --output json

# Search across all project history
empirica project-search --task "all findings related to <topic>" --limit 50

# Create comprehensive handoff with full context
empirica handoff-create --session-id <ID> --task-summary "..." \
  --key-findings '[...]' --include-full-context
```

**Context preservation tips:**
1. Log findings frequently - they persist across context windows
2. Use unknowns to mark areas needing deeper investigation
3. Create checkpoints before major context shifts
4. Leverage `--include-live-state` in bootstrap for real-time vector access
