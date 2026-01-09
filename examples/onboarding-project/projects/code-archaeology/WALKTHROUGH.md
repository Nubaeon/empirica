# Code Archaeology Walkthrough

Understand mystery code while tracking your epistemic journey.

---

## Step 1: PREFLIGHT - Honest Starting Point

```bash
empirica session-create --ai-id claude-code --output json

empirica preflight-submit - << 'EOF'
{
  "session_id": "<YOUR-SESSION-ID>",
  "task_context": "Document what mystery_module.py does",
  "vectors": {
    "know": 0.1,
    "uncertainty": 0.9,
    "context": 0.2,
    "clarity": 0.5
  },
  "reasoning": "I haven't read the code. Function names are cryptic (proc_x, agg_y). Only know it 'handles data processing'. Very high uncertainty."
}
EOF
```

---

## Step 2: First Read - Form Hypotheses

Read `mystery_module.py` WITHOUT running it. Log initial observations:

```bash
empirica unknown-log --session-id <ID> \
  --unknown "What does proc_x do? Seems to group by 'cat' field"

empirica unknown-log --session-id <ID> \
  --unknown "What do the prefixes gt_, lt_, eq_, in_ mean in flt_z?"

empirica finding-log --session-id <ID> \
  --finding "Code structure: 4 functions (proc_x, agg_y, flt_z, xform_w) + main pipeline orchestrator" \
  --impact 0.4
```

---

## Step 3: Test Hypotheses

Run with sample data:

```bash
# Basic run - just load and print
python mystery_module.py data_samples/input_a.json

# With grouping
python mystery_module.py data_samples/input_a.json << 'EOF'
{"group": true}
EOF
```

Each test confirms or refutes a hypothesis. Log findings:

```bash
empirica finding-log --session-id <ID> \
  --finding "proc_x groups records by 'cat' field, collecting 'val' values into lists" \
  --impact 0.6

empirica unknown-resolve --unknown-id <ID> \
  --resolved-by "Confirmed: proc_x groups by category"
```

---

## Step 4: Document Your Understanding

As confidence grows, document each function:

```bash
empirica finding-log --session-id <ID> \
  --finding "flt_z is a filter: gt_X means 'field X greater than', lt_ means less than, eq_ means equals, in_ means 'in list'" \
  --impact 0.7
```

---

## Step 5: POSTFLIGHT - Measure Learning

```bash
empirica postflight-submit - << 'EOF'
{
  "session_id": "<YOUR-SESSION-ID>",
  "task_context": "Documented mystery_module.py - it's a data processing pipeline",
  "vectors": {
    "know": 0.85,
    "uncertainty": 0.15,
    "context": 0.90,
    "clarity": 0.90
  },
  "reasoning": "Fully understood the module: grouping, aggregation, filtering, transformation pipeline. Could now maintain or extend it."
}
EOF
```

**Learning delta:** know +0.75, uncertainty -0.75

---

## Key Epistemic Lessons

1. **Start with zero is okay** - Honest low confidence is valuable data
2. **Hypothesize before testing** - Log what you think, then verify
3. **Incremental confidence** - Each finding nudges vectors
4. **Dead-ends are data** - Wrong guesses prevent future mistakes
