# Code Archaeology

**Difficulty:** ⭐⭐⭐ | **Time:** 30 minutes

You've inherited legacy code with no documentation. Your mission: figure out what it does.

## The Scenario

A colleague left the company. Their code is "critical" but nobody knows exactly what it does. Variable names are cryptic, there are no comments, and the only docs say "handles data processing."

Your task: Document what this code actually does.

## Why This Is Epistemic

- You start with **near-zero knowledge** of the code's purpose
- You must form and test **hypotheses** about behavior
- Some assumptions will be **wrong** (dead-ends)
- Confidence should build incrementally as you understand more

## Files

```
code-archaeology/
├── README.md           # This file
├── WALKTHROUGH.md      # Guided investigation
├── mystery_module.py   # The undocumented code (~100 lines)
├── data_samples/       # Sample input files
│   ├── input_a.json
│   └── input_b.json
└── SOLUTION.md         # What it actually does
```

## Your Mission

1. Read the code (don't run it yet)
2. Form hypotheses about what each function does
3. Test your hypotheses with the sample data
4. Document the module's purpose
5. Rate your confidence at each step

## Start Here

Follow [WALKTHROUGH.md](WALKTHROUGH.md) for the guided experience with Empirica.
