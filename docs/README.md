# Empirica Documentation (v4.0)

**Last Updated:** 2025-12-16  
**Status:** Generated from codebase (100% accurate)

---

## Quick Navigation

### 📖 Primary Documentation

**Start here for accurate, up-to-date information:**

- **[CLI Commands Reference](reference/CLI_COMMANDS_GENERATED.md)** - All 67 commands with complete syntax
- **[Python API Reference](reference/PYTHON_API_GENERATED.md)** - Core classes and methods
- **[Database Schema Reference](reference/DATABASE_SCHEMA_GENERATED.md)** - All 23 tables and relationships

### 🧠 Philosophy & Design

**Understand the "why" behind Empirica:**

- **[Canonical System Prompt](../system-prompts/CANONICAL_SYSTEM_PROMPT.md)** - Complete philosophy + workflow
- **[Architecture Docs](architecture/)** - Design decisions and patterns
- **[Integrations](integrations/)** - BEADS-Git bridge, etc.

### 🔍 Discovery

- **[Semantic Index](SEMANTIC_INDEX.yaml)** - Find docs by concept, tag, or question

---

## What Changed in v4.0

**Documentation Regeneration Project (2025-12-16):**

We rebuilt the documentation system from scratch to eliminate legacy cruft and ensure 100% accuracy.

### Before (v3.x):
- 67 commands in code, 136 in docs
- **45% integrity score**
- 73 phantom commands
- Unknown legacy code/docs relationship

### After (v4.0):
- 67 commands in code, 67 in docs
- **100% integrity score** (for generated docs)
- 0 phantom commands
- Clear legacy visibility

**Key Change:** Documentation is now **generated from the codebase**, not written by hand.

---

## Generated Documentation

All files in `reference/` are auto-generated from the actual codebase:

| File | Source | Lines | Updated |
|------|--------|-------|---------|
| `CLI_COMMANDS_GENERATED.md` | `cli_core.py` (AST) | 1833 | On demand |
| `PYTHON_API_GENERATED.md` | Python modules (introspection) | 1339 | On demand |
| `DATABASE_SCHEMA_GENERATED.md` | `session_database.py` (SQL) | 698 | On demand |

**Total:** 3870 lines of guaranteed-accurate documentation

### Regenerating Docs

```bash
cd dev_scripts/doc_regeneration

# Extract from code (5 seconds)
python3 extract_cli_commands.py
python3 extract_python_api.py
python3 extract_database_schema.py

# Generate markdown (2 seconds)
python3 generate_cli_markdown.py
python3 generate_python_api_markdown.py
python3 generate_database_schema_markdown.py
```

**Result:** Fresh, accurate docs in ~7 seconds.

---

## Archived Documentation (v3.x)

Old documentation has been moved to `archive/v3/` for reference.

**Why archived:**
- Many phantom commands (docs for features that don't exist)
- Outdated patterns (pre-v4.0 bootstrap ceremony)
- Inconsistent examples
- Manual maintenance led to drift

**See:** [archive/v3/README.md](archive/v3/README.md) for details.

---

## Documentation Philosophy (v4.0)

### Single Source of Truth: The Codebase

**If it's in generated docs → it EXISTS in code**  
**If it's not → it's LEGACY**

This eliminates uncertainty about what's current vs what's old.

### Three Document Types

1. **Generated Reference** (CLI, API, Schema)
   - 100% accurate
   - Regenerated from code
   - Trust as ground truth

2. **Curated Philosophy** (System prompts, architecture)
   - Written by humans
   - Explains "why" not "what"
   - Maintained manually

3. **Archived Legacy** (v3.x docs)
   - Historical reference only
   - May contain phantoms
   - Use with caution

---

## File Structure

```
docs/
├── README.md                         # This file
├── SEMANTIC_INDEX.yaml               # Doc discovery
│
├── reference/                        # Generated docs ✅
│   ├── CLI_COMMANDS_GENERATED.md
│   ├── PYTHON_API_GENERATED.md
│   └── DATABASE_SCHEMA_GENERATED.md
│
├── architecture/                     # Design decisions
│   ├── WHY_UNIFIED_STORAGE_MATTERS.md
│   ├── DOC_CODE_INTELLIGENCE.md
│   └── ...
│
├── integrations/                     # Integration guides
│   └── BEADS_GIT_BRIDGE.md
│
├── archive/
│   └── v3/                          # Archived v3.x docs
│       ├── README.md
│       ├── production/
│       ├── guides/
│       └── ...
│
└── system-prompts/                   # In parent directory
    └── CANONICAL_SYSTEM_PROMPT.md
```

---

## Contributing to Documentation

### For Generated Docs (CLI, API, Schema):

**Don't edit manually!** They're auto-generated.

Instead:
1. Make changes to the source code
2. Regenerate docs with scripts
3. Commit both code + generated docs

### For Philosophy Docs:

Edit freely! These are curated human writing that explains concepts, philosophy, and design decisions.

### For New Features:

1. Implement in code
2. Regenerate reference docs (captures automatically)
3. Add philosophy/guide doc if needed (explain "why")

---

## Documentation Integrity

Check integrity anytime:

```bash
empirica project-bootstrap --check-integrity --output json
```

**Current integrity:**
- Generated docs: 100% (by design)
- Overall project: Improving (legacy being pruned)

---

## Support

**Questions about the system?**
- Read: `system-prompts/CANONICAL_SYSTEM_PROMPT.md` (comprehensive)
- Check: Generated reference docs (accurate)
- Search: `SEMANTIC_INDEX.yaml` (find by concept)

**Found a bug in docs?**
- If in `*_GENERATED.md` → bug is in source code, fix there
- If in philosophy docs → edit directly, file PR

---

## Version History

**v4.0 (2025-12-16):**
- Complete documentation regeneration
- CLI commands: 100% coverage (67/67)
- Python API: Core classes documented
- Database schema: 100% coverage (23/23 tables)
- Old docs archived to v3/

**v3.x (pre-2025-12-16):**
- Manual documentation
- 45% integrity score
- 73 phantom commands
- See archive/v3/ for historical reference

---

**System Status:** Production Ready ✅  
**Documentation Coverage:** 100% (for generated docs)  
**Regeneration Time:** ~7 seconds  
**Maintenance:** Fully automated
