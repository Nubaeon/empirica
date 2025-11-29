# 🐛 Bug Found: Postflight Delta Calculation

**Error:** `unsupported operand type(s) for -: 'float' and 'dict'`  
**Location:** `empirica/cli/command_handlers/workflow_commands.py:377`  
**Root Cause:** Mini-agent sending nested vector structure, code expects flat structure

## The Problem

**Line 377:**
```python
deltas[key] = post_val - pre_val  # ❌ Fails when vectors have nested structure
```

**What mini-agent sends:**
```python
vectors = {
    'comprehension': {
        'clarity': {'rationale': '...', 'score': 0.7},
        'coherence': {'rationale': '...', 'score': 0.75}
    },
    'foundation': {
        'know': {'rationale': '...', 'score': 0.6}
    }
}
```

**What code expects:**
```python
vectors = {
    'clarity': 0.7,  # Flat, or
    'clarity': {'score': 0.7}  # One level dict
}
```

## The Fix

The `_extract_numeric_value()` helper (lines 295-316) handles this, but it's being called on the wrong structure!

**Current code flow:**
1. Gets `vectors[key]` → might be nested dict like `{'clarity': {'score': 0.7}}`
2. Calls `_extract_numeric_value(vectors[key])` → returns None for nested dict
3. Tries `post_val - pre_val` → One is float, one is None → ERROR!

**Solution:** Flatten the nested structure before delta calculation.

## Recommended Fix

Add flattening before line 372:

```python
# Try to calculate deltas by fetching preflight
deltas = {}
try:
    preflight = db.get_preflight_assessment(session_id)
    if preflight and 'vectors_json' in preflight:
        preflight_vectors = json.loads(preflight['vectors_json'])
        
        # FIX: Flatten nested vector structures
        def flatten_vectors(v):
            """Flatten nested vector dict to {vector_name: value}"""
            flat = {}
            if not isinstance(v, dict):
                return {}
            
            for key, val in v.items():
                if isinstance(val, dict):
                    # Check if it's a tier dict (has sub-vectors)
                    if any(isinstance(v, dict) for v in val.values()):
                        # Nested tier structure - recurse
                        for sub_key, sub_val in val.items():
                            flat[sub_key] = sub_val
                    else:
                        # Single vector dict
                        flat[key] = val
                else:
                    # Simple value
                    flat[key] = val
            return flat
        
        flat_post = flatten_vectors(vectors)
        flat_pre = flatten_vectors(preflight_vectors)
        
        for key in flat_post:
            if key in flat_pre:
                # Extract numeric values (handle both float and dict formats)
                post_val = _extract_numeric_value(flat_post[key])
                pre_val = _extract_numeric_value(flat_pre[key])
                if post_val is not None and pre_val is not None:
                    deltas[key] = post_val - pre_val
except Exception as e:
    logger.debug(f"Delta calculation failed: {e}")
    pass  # Delta calculation is optional
```

## Alternative: Check MCP Tool Schema

The real question: **Why is mini-agent sending nested structure?**

MCP tool schema says:
```json
{
  "vectors": {"type": "object", "description": "Epistemic vectors as JSON object with 13 keys"}
}
```

**Expected format:** `{engagement: 0.7, know: 0.6, clarity: 0.7, ...}` (13 flat keys)

**Mini-agent is sending:** Nested tier structure

**Root cause:** Mini-agent might be misunderstanding the schema format or system prompt is unclear.

## Immediate Action

Update mini-agent's system prompt to clarify vector format:

```markdown
## Vector Submission Format

When submitting assessments, use FLAT structure with 13 keys:

```python
vectors = {
    "engagement": 0.7,
    "know": 0.6,
    "do": 0.65,
    "context": 0.7,
    "clarity": 0.7,
    "coherence": 0.75,
    "signal": 0.65,
    "density": 0.6,
    "state": 0.65,
    "change": 0.6,
    "completion": 0.4,
    "impact": 0.65,
    "uncertainty": 0.5
}
```

❌ DON'T use nested tier structure:
```python
# WRONG!
vectors = {
    "comprehension": {
        "clarity": 0.7,
        "coherence": 0.75
    }
}
```
```

## Status

- [x] Bug identified
- [ ] Fix implemented
- [ ] Mini-agent system prompt updated
- [ ] Tests verify fix works
