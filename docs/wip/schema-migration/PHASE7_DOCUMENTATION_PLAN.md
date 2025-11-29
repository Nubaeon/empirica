# Phase 7: Documentation Update - Plan

## Goal
Update all documentation to reflect NEW schema field names and usage patterns.

---

## Documentation Audit

### Key Changes Needed

#### Field Name Updates
| OLD Name | NEW Name | Where Used |
|----------|----------|------------|
| `assessment.know` | `assessment.foundation_know` | Examples, API docs |
| `assessment.do` | `assessment.foundation_do` | Examples, API docs |
| `assessment.context` | `assessment.foundation_context` | Examples |
| `assessment.clarity` | `assessment.comprehension_clarity` | Examples |
| `assessment.coherence` | `assessment.comprehension_coherence` | Examples |
| `assessment.signal` | `assessment.comprehension_signal` | Examples |
| `assessment.density` | `assessment.comprehension_density` | Examples |
| `assessment.state` | `assessment.execution_state` | Examples |
| `assessment.change` | `assessment.execution_change` | Examples |
| `assessment.completion` | `assessment.execution_completion` | Examples |
| `assessment.impact` | `assessment.execution_impact` | Examples |

#### Metadata Changes
| OLD | NEW | Notes |
|-----|-----|-------|
| `assessment_id` | Not in NEW schema | Removed |
| `task` | Not in NEW schema | Removed |
| `timestamp` | Not in NEW schema | Auto-generated |
| N/A | `phase` (enum) | Added |
| N/A | `round_num` | Added |
| N/A | `investigation_count` | Added |

---

## Strategy

### Approach 1: Add Migration Notes (Quick - Recommended)
- Add banner to key docs: "⚠️ Schema Migration in Progress"
- Link to migration docs
- Note that examples may show OLD field names
- **Effort**: 5-10 iterations

### Approach 2: Update All Examples (Complete)
- Find all assessment examples
- Update field names
- Update code snippets
- Test examples work
- **Effort**: 20-30 iterations

### Approach 3: Create NEW Schema Guide (Balanced)
- Create comprehensive NEW schema guide
- Add migration/transition notes to existing docs
- Mark OLD examples as "legacy"
- **Effort**: 10-15 iterations

**Recommendation**: Approach 3 (Balanced)

---

## Files to Update/Create

### High Priority
1. ✅ CREATE: `docs/reference/NEW_SCHEMA_GUIDE.md` - Complete NEW schema reference
2. ✅ UPDATE: `docs/production/05_EPISTEMIC_VECTORS.md` - Add NEW schema info
3. ✅ UPDATE: `README.md` - Add migration notice
4. ✅ UPDATE: `docs/examples/assessment_format_example.json` - NEW format

### Medium Priority
5. UPDATE: `docs/guides/CLI_GENUINE_SELF_ASSESSMENT.md` - Add NEW format
6. UPDATE: `docs/system-prompts/comprehensive/COMPLETE_MCP_TOOL_REFERENCE.md` - Note wrappers
7. UPDATE: `/home/yogapad/.rovodev/EMPIRICA_MCP_USAGE.md` - Add schema notes

### Low Priority (Can defer)
8. Various example files
9. System prompts (minimal impact)
10. Old guides (mark as legacy)

---

## Time Estimate

- High priority (4 files): 8-10 iterations
- Medium priority (3 files): 4-6 iterations
- Testing/verification: 2-3 iterations

**Total**: 14-19 iterations (within budget!)

---

## Next Steps

1. Create NEW_SCHEMA_GUIDE.md (comprehensive reference)
2. Update README with migration notice
3. Update key example files
4. Add migration banners to existing docs
5. Verify links and cross-references

---

**Status**: Ready to start Phase 7
**Estimated**: 14-19 iterations
**Remaining budget**: ~125 iterations ✅
