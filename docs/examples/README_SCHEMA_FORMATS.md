# Assessment Format Examples

## Schema Migration Status

**60% complete** as of Jan 2025. We're migrating to `EpistemicAssessmentSchema`.

## Files

### NEW Schema (Current - Recommended)
- `assessment_format_NEW_schema.json` - Complete NEW format with prefixed field names
- See [NEW Schema Guide](../reference/NEW_SCHEMA_GUIDE.md) for details

### OLD Schema (Legacy - Still Supported)
- `assessment_format_example.json` - Original format (still works via wrappers)
- `self_assessment_example.json` - Self-assessment format

## Key Differences

| Aspect | OLD | NEW |
|--------|-----|-----|
| Field names | `know`, `clarity`, `state` | `foundation_know`, `comprehension_clarity`, `execution_state` |
| Metadata | `assessment_id`, `task`, `timestamp` | `phase`, `round_num`, `investigation_count` |
| Confidences | Stored in assessment | Calculated via methods |
| Action | Enum (`Action.INVESTIGATE`) | String (`'investigate'`) |

## Backwards Compatibility

**All OLD code continues to work!** Wrappers handle conversion automatically.

```python
# OLD code still works
if assessment.know.score < 0.5:  # ✅ Works
    print("Low knowledge")

# NEW code recommended
if assessment.foundation_know.score < 0.5:  # ✅ Better
    print("Low knowledge")
```

## See Also

- [NEW Schema Guide](../reference/NEW_SCHEMA_GUIDE.md) - Complete documentation
- [Migration Status](../wip/schema-migration/PROGRESS_60_PERCENT.md) - Progress tracking
