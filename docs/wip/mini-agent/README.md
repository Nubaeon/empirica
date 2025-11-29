# Mini-Agent Work - Skipped Tests

## Your Task: Fix 10 Skipped CASCADE Tests

**Current Status**: 77 passed, **10 skipped**, 0 failed

### Skipped Tests Location
1. `tests/unit/cascade/test_investigate.py` - 5 skipped
2. `tests/unit/cascade/test_postflight.py` - 2 skipped
3. `tests/unit/cascade/test_think.py` - 3 skipped

### Goal
Get to **87 passed, 0 skipped, 0 failed**

---

## Context: Schema Migration Complete (60%)

Rovo Dev completed 6 phases:
- ✅ Converters (OLD ↔ NEW schema)
- ✅ Assessor migration
- ✅ CASCADE migration
- ✅ PersonaHarness migration
- ✅ CLI/MCP (no changes needed)
- ✅ Test mocks optimized

**All migrations use wrapper pattern** - backwards compatible!

---

## What You Need to Know

### Mock Fixtures Available
- `mock_assessor` - Returns OLD schema (current default)
- `mock_assessor_new` - Returns NEW schema (optimized)
- `mock_cascade_with_assessor` - Complete CASCADE setup

Location: `tests/unit/cascade/conftest.py`

### Schema Info
- Tests expect OLD schema externally (via wrappers)
- Internal implementation uses NEW schema
- Don't remove OLD schema yet (Phase 9)
- Don't change wrapper return types

### Field Names
| OLD (in tests) | NEW (internal) |
|----------------|----------------|
| `assessment.know` | `foundation_know` |
| `assessment.do` | `foundation_do` |
| `assessment.clarity` | `comprehension_clarity` |
| `assessment.state` | `execution_state` |

---

## How to Start

### 1. Run Skipped Tests
```bash
pytest tests/unit/cascade/test_investigate.py -v
pytest tests/unit/cascade/test_postflight.py -v
pytest tests/unit/cascade/test_think.py -v
```

### 2. Check Why Skipped
Look for `@pytest.skip` or `pytest.mark.skip` decorators

### 3. Fix or Remove
- If fixable: Remove skip marker, fix test
- If obsolete: Remove test entirely
- Document your reasoning

---

## Migration Docs

See `docs/wip/schema-migration/` for complete migration details:
- `README.md` - Migration overview
- `PROGRESS_60_PERCENT.md` - Current status
- `HALFWAY_MILESTONE.md` - Mid-point summary

---

## Success Criteria

- [ ] Identify why each test is skipped
- [ ] Fix or remove all 10 skipped tests
- [ ] All tests pass: 87+ passed, 0 skipped
- [ ] No breaking changes
- [ ] Document what you fixed

---

**Start here**: Run the skipped tests and see what's needed!
