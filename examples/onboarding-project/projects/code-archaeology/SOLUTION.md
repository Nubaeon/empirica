# Solution - Code Archaeology

**SPOILERS BELOW**

---

## What The Code Does

It's a **data processing pipeline** with four operations:

| Function | Cryptic Name | Real Purpose |
|----------|--------------|--------------|
| `proc_x` | Process X | **Group by category** - groups records by a key field |
| `agg_y` | Aggregate Y | **Aggregation** - sum/avg/count/max/min per group |
| `flt_z` | Filter Z | **Filter records** - gt/lt/eq/in predicates |
| `xform_w` | Transform W | **Transform** - rename fields, drop fields, calculate |
| `pipe_main` | Pipeline Main | **Orchestrator** - chains operations via config |

---

## Function Details

### `proc_x(data)` - Grouping
Groups records by `cat` field, collecting `val` values:
```python
# Input: [{"cat": "A", "val": 1}, {"cat": "A", "val": 2}, {"cat": "B", "val": 3}]
# Output: {"A": [1, 2], "B": [3]}
```

### `agg_y(grouped, mode)` - Aggregation
Reduces grouped values: `sum`, `avg`, `cnt`, `max`, `min`

### `flt_z(data, predicates)` - Filtering
Prefix-based predicates:
- `gt_field: value` → field > value
- `lt_field: value` → field < value
- `eq_field: value` → field == value
- `in_field: [values]` → field in values

### `xform_w(data, operations)` - Transformation
Operations as tuples:
- `("rename", "old", "new")` → rename field
- `("drop", "field")` → remove field
- `("calc", "+", "a", "b")` → add fields to `_calc`

---

## Example Usage

```python
# Filter high-value items, group by category, sum values
result = pipe_main("input_a.json", {
    "filter": {"gt_val": 100},
    "group": True,
    "agg": "sum"
})
# Returns: {"electronics": 650}
```

---

## The Epistemic Journey

| Phase | Know | Uncertainty | What You Learned |
|-------|------|-------------|------------------|
| Start | 0.1 | 0.9 | Just cryptic function names |
| After reading | 0.4 | 0.6 | General structure, some patterns |
| After testing | 0.7 | 0.3 | Confirmed behavior with data |
| After documenting | 0.9 | 0.1 | Full understanding |
