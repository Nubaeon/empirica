# Version Update Command Design

**Status:** Archived (not implemented)
**Author:** Claude Code
**Date:** 2026-01-14
**Version:** 0.1.0

---

## Problem Statement

Version bumps in Empirica require updating 24+ files across the codebase. Current process:
1. Manual grep for version strings
2. Human judgment on which to update
3. Easy to miss edge cases or update things that shouldn't change

**Pain points:**
- CHANGELOG entries should never be updated (historical)
- Minimum requirements (`>=1.3.0`) may or may not need updating
- Wheel filenames in Dockerfiles need updating
- System prompt versions need updating but sync script has hardcoded values
- Some "1.3.0" references are examples, not actual versions

---

## Proposed Solution

An LLM-assisted `empirica version-update` command that:
1. Scans codebase for version patterns
2. Classifies each occurrence semantically
3. Learns from past decisions via Qdrant
4. Applies updates with human review
5. Persists outlier decisions for future runs

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    version-update CLI                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Scanner    │───►│  Classifier  │───►│   Applier    │       │
│  │  (ripgrep)   │    │    (LLM)     │    │   (patch)    │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                │
│         │                   ▼                   │                │
│         │           ┌──────────────┐            │                │
│         │           │   Qdrant     │            │                │
│         │           │  (patterns)  │            │                │
│         │           └──────────────┘            │                │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌─────────────────────────────────────────────────────┐        │
│  │              .empirica/version-policy.yaml           │        │
│  │  (outliers, learned decisions, pattern overrides)    │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Scanner

Fast regex-based scanning using ripgrep patterns:

```python
VERSION_PATTERNS = [
    r'\d+\.\d+\.\d+',           # Semantic versions: 1.3.2
    r'v\d+\.\d+\.\d+',          # Tagged versions: v1.3.2
    r'>=\d+\.\d+\.\d+',         # Minimum requirements
    r'==\d+\.\d+\.\d+',         # Pinned requirements
    r'~=\d+\.\d+\.\d+',         # Compatible release
]

EXCLUDE_PATTERNS = [
    '*.pyc', '__pycache__', '.git', 'node_modules',
    '.empirica/sessions', '*.db', '*.log'
]
```

**Output:** List of `VersionOccurrence` objects:
```python
@dataclass
class VersionOccurrence:
    file_path: str
    line_number: int
    line_content: str
    version_string: str
    context_before: list[str]  # 3 lines before
    context_after: list[str]   # 3 lines after
    file_type: str             # py, md, yaml, toml, etc.
```

### 2. Classifier (LLM)

Uses local LLM (Qwen/Mistral via Ollama) to classify each occurrence:

```python
class VersionClassification(Enum):
    EXACT = "exact"           # Update to new version
    MINIMUM = "minimum"       # Floor requirement, maybe update
    HISTORICAL = "historical" # Never update (changelog, comments about past)
    EXAMPLE = "example"       # Documentation example, context-dependent
    OUTLIER = "outlier"       # Needs human decision
```

**Prompt template:**
```
You are classifying version references for an automated update tool.

Current version: {old_version}
New version: {new_version}

Occurrence:
File: {file_path}
Line {line_number}: {line_content}

Context:
{context_before}
>>> {line_content}
{context_after}

Classify this version reference:
- EXACT: This is the current version and should be updated (e.g., __version__ = "1.3.2")
- MINIMUM: This is a minimum requirement floor (e.g., "empirica>=1.3.0"), may or may not need update
- HISTORICAL: This is a historical reference that should never change (e.g., changelog entry, "Added in v1.2.0")
- EXAMPLE: This is a documentation example that may need updating for accuracy
- OUTLIER: Unclear, needs human review

Respond with JSON:
{"classification": "EXACT|MINIMUM|HISTORICAL|EXAMPLE|OUTLIER", "confidence": 0.0-1.0, "reasoning": "brief explanation"}
```

**LLM Selection:**
- Primary: Local Qwen 2.5 7B or Mistral 7B via Ollama (fast, free)
- Fallback: Claude API for complex outliers (optional)
- Batch processing: Group similar patterns to reduce LLM calls

### 3. Qdrant Pattern Memory

Store classified patterns for semantic similarity matching:

**Collection:** `empirica_version_patterns`

```python
@dataclass
class VersionPattern:
    id: str
    file_pattern: str          # e.g., "*.md", "pyproject.toml"
    context_pattern: str       # Semantic description of context
    classification: str        # EXACT, MINIMUM, etc.
    confidence: float
    example_file: str
    example_line: str
    decision_date: str
    decided_by: str            # "llm", "human"
```

**Semantic search flow:**
1. New occurrence found
2. Embed: `f"{file_type}: {context_before} {line_content} {context_after}"`
3. Query Qdrant for top-3 similar patterns
4. If similarity > 0.85 and same classification across matches → use cached decision
5. Otherwise → LLM classification

**Opposite search (finding edge cases):**
- Query with negated embedding to find dissimilar patterns
- Helps identify when a pattern looks similar but has different semantics
- Example: "version: 1.3.0" in YAML config vs "version: 1.3.0" in changelog

### 4. Policy File

`.empirica/version-policy.yaml`:

```yaml
version: 1.0
last_update: 2026-01-14
from_version: 1.3.2
to_version: 1.3.3

# Explicit rules (highest priority)
rules:
  - pattern: "CHANGELOG.md"
    action: skip
    reason: "Historical record, never update"

  - pattern: "pyproject.toml:version"
    action: update
    reason: "Canonical version source"

  - pattern: ">=*.*.* in requirements"
    action: prompt
    reason: "Minimum floor, ask if should bump"

# Learned outliers (persisted decisions)
outliers:
  - file: docs/architecture/SUPPORTING_COMPONENTS.md
    line: 194
    pattern: 'tag_name="v1.3.0"'
    decision: skip
    reason: "Example showing how to use git tags, not actual version"
    decided_by: human
    decided_at: 2026-01-14

  - file: docs/human/developers/EXTENDING_EMPIRICA.md
    line: 350
    pattern: ">=1.2.3"
    decision: skip
    reason: "Example of version pinning, not actual requirement"
    decided_by: llm
    decided_at: 2026-01-14

# Statistics
stats:
  total_occurrences: 47
  auto_updated: 38
  skipped_historical: 5
  human_decisions: 4
```

### 5. Applier

Generates and applies patches:

```python
def apply_updates(occurrences: list[VersionOccurrence],
                  old_version: str,
                  new_version: str,
                  dry_run: bool = True) -> PatchResult:
    """
    Apply version updates to files.

    Args:
        occurrences: Classified occurrences marked for update
        old_version: Version to replace
        new_version: New version
        dry_run: If True, show diff without applying

    Returns:
        PatchResult with files modified, lines changed, errors
    """
```

**Safety features:**
- Always dry-run first
- Show unified diff for review
- Atomic updates (all or nothing per file)
- Git integration: create branch, commit with metadata

---

## CLI Interface

```bash
# Basic usage
empirica version-update 1.3.2 1.3.3

# Dry run (default)
empirica version-update 1.3.2 1.3.3 --dry-run

# Apply changes
empirica version-update 1.3.2 1.3.3 --apply

# Interactive mode (prompt for each outlier)
empirica version-update 1.3.2 1.3.3 --interactive

# Use specific LLM
empirica version-update 1.3.2 1.3.3 --model qwen2.5:7b

# Skip LLM, use only cached patterns
empirica version-update 1.3.2 1.3.3 --cached-only

# Export decisions for review
empirica version-update 1.3.2 1.3.3 --export decisions.json

# Learn from manual updates (after human edits)
empirica version-learn --from-diff HEAD~1

# Show pattern statistics
empirica version-patterns --stats
```

---

## Workflow Example

```bash
$ empirica version-update 1.3.2 1.3.3

🔍 Scanning for version patterns...
   Found 47 occurrences of "1.3.2" across 24 files

🧠 Classifying occurrences...
   Using local model: qwen2.5:7b
   Querying Qdrant for similar patterns...

   ├── 38 EXACT (will update)
   ├── 5 HISTORICAL (will skip)
   ├── 2 MINIMUM (will prompt)
   └── 2 OUTLIER (need decision)

📋 MINIMUM requirements (floor versions):

   1. empirica-mcp/pyproject.toml:26
      "empirica>=1.3.2",  # Main package

      [u]pdate to >=1.3.3  [k]eep as >=1.3.2  [s]kip: u

   2. docs/human/developers/EXTENDING_EMPIRICA.md:284
      "empirica>=1.3.2",  # Pin to minimum required version

      [u]pdate  [k]eep  [s]kip: k (this is an example)

❓ OUTLIERS (need human decision):

   1. docs/architecture/SUPPORTING_COMPONENTS.md:194
      tag_name="v1.3.2",

      Context: Example of creating a GitHub release
      LLM says: EXAMPLE (confidence: 0.72)

      [u]pdate  [s]kip  [?] explain: s

      💾 Decision saved to version-policy.yaml

📝 Dry run complete. Changes to apply:

   Modified files: 22
   Lines changed: 39
   Skipped: 7

   Run with --apply to execute changes.
   Run with --diff to see full unified diff.
```

---

## Implementation Plan

### Phase 1: Core Scanner (2-3 hours)
- [ ] Ripgrep-based version pattern scanner
- [ ] Context extraction (lines before/after)
- [ ] Basic CLI structure

### Phase 2: Policy File (1-2 hours)
- [ ] YAML schema for version-policy.yaml
- [ ] Rule matching logic
- [ ] Outlier persistence

### Phase 3: LLM Classifier (3-4 hours)
- [ ] Ollama integration for local models
- [ ] Prompt engineering and testing
- [ ] Batch processing for efficiency
- [ ] Confidence thresholds

### Phase 4: Qdrant Integration (2-3 hours)
- [ ] Pattern embedding and storage
- [ ] Similarity search for cached decisions
- [ ] Opposite search for edge cases

### Phase 5: Applier (2-3 hours)
- [ ] Patch generation
- [ ] Dry-run diff display
- [ ] Atomic file updates
- [ ] Git branch/commit integration

### Phase 6: Polish (2-3 hours)
- [ ] Interactive mode
- [ ] Learning from manual diffs
- [ ] Statistics and reporting
- [ ] Documentation

**Total estimate:** 12-18 hours

---

## Dependencies

```toml
[project.optional-dependencies]
version-update = [
    "ollama",           # Local LLM client
    "qdrant-client",    # Already in empirica[all]
]
```

---

## Open Questions

1. **Minimum version bumping policy:**
   - Always bump minimums with major/minor releases?
   - Keep minimums stable for patch releases?
   - User-configurable policy?

2. **Multi-version support:**
   - Handle cases where multiple versions exist (e.g., empirica 1.3.2, empirica-mcp 1.3.2)
   - Separate tracking per package?

3. **Pre-release versions:**
   - Handle 1.3.2-rc1, 1.3.2.dev1, etc.?
   - Different classification rules?

4. **Monorepo vs multi-repo:**
   - Current design assumes monorepo
   - Extend to handle homebrew-tap as separate repo?

---

## Success Metrics

- **Accuracy:** >95% correct classifications on first run
- **Speed:** <30 seconds for full scan + classify (with caching)
- **Learning:** Outlier decisions persist, same pattern never asked twice
- **Safety:** Zero accidental updates to historical/changelog entries

---

## References

- [Semantic Versioning](https://semver.org/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)
- Current version locations: Finding `394deb01-ae79-4e65-bc79-9ec143b4da11`
