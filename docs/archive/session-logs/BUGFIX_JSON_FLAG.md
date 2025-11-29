# 🐛 Bug Fix: --json Flag Causing AttributeError

**Date:** 2025-11-27  
**Issue:** Mini-agent tests failing with `'Namespace' object has no attribute 'json'`  
**Status:** ✅ **FIXED**

---

## 🔍 Problem

Mini-agent trying to run:
```bash
empirica preflight "Phase 1 test" \
    --ai-id "mini-agent" \
    --session-id "$SESSION_1" \
    --assessment-json docs/examples/assessment_format_example.json \
    --json
```

**Error:**
```
❌ Preflight assessment error: 'Namespace' object has no attribute 'json'
```

---

## 🔎 Root Cause

In `cli_core.py` line 191-192:
```python
preflight_parser.add_argument('--json', action='store_const', const='json', dest='output_format', ...)
```

The `--json` flag sets `output_format` attribute, **not** `json` attribute.

But in `cascade_commands.py` line 322:
```python
if args.json:  # ❌ This attribute doesn't exist!
```

The code was checking for `args.json` which doesn't exist because `--json` sets `args.output_format='json'` instead.

---

## ✅ Solution

Updated `cascade_commands.py` to handle both deprecated `--json` and new `--output json` flags:

```python
# Handle both --json (deprecated, sets output_format) and --output json
output_format = getattr(args, 'output_format', None) or getattr(args, 'output', 'default')
json_output = output_format == 'json' or getattr(args, 'json', False)

if json_output:
    # Output as JSON
    ...
```

**Fixed in:**
- `handle_preflight_command()` (line 322)
- `handle_postflight_command()` (line 596)

---

## 🧪 Testing

### Before Fix:
```bash
empirica preflight "test" --assessment-json FILE --json
# ❌ 'Namespace' object has no attribute 'json'
```

### After Fix:
```bash
empirica preflight "test" --assessment-json FILE --json
# ✅ Works! Returns JSON output

empirica preflight "test" --assessment-json FILE --output json
# ✅ Also works! (Recommended new way)
```

---

## 📝 Updated Documentation

Mini-agent should now use **either**:

### Option 1: Deprecated --json flag (now works)
```bash
empirica preflight "task" \
    --ai-id mini-agent \
    --assessment-json docs/examples/assessment_format_example.json \
    --json
```

### Option 2: Recommended --output json (preferred)
```bash
empirica preflight "task" \
    --ai-id mini-agent \
    --assessment-json docs/examples/assessment_format_example.json \
    --output json
```

**Both now work correctly!**

---

## 🎯 Impact

**Files Fixed:**
- `empirica/cli/command_handlers/cascade_commands.py` (2 locations)

**Commands Fixed:**
- `empirica preflight --json`
- `empirica postflight --json`

**Mini-agent can now:**
- ✅ Use `--json` flag without errors
- ✅ Use `--output json` flag (recommended)
- ✅ Get JSON output for parsing
- ✅ Proceed with Phase 1/2/3 testing

---

## 🔄 Updated Test Command

**Working command for mini-agent:**
```bash
SESSION_1="test-complete-$(date +%s)-phase1"

empirica preflight "Phase 1 test" \
    --ai-id "mini-agent" \
    --session-id "$SESSION_1" \
    --assessment-json docs/examples/assessment_format_example.json \
    --output json  # Use this instead of --json (or both work)
```

---

## ✅ Verification

Run this to verify fix:
```bash
bash test_working_checkpoint.sh
```

Should now complete without `AttributeError`.

---

**Status:** ✅ Fixed and ready for mini-agent testing
