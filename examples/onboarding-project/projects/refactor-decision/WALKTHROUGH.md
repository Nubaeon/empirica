# Refactor Decision Walkthrough

Make an architectural decision while tracking your epistemic journey.

---

## Step 1: PREFLIGHT - Honest Starting Point

```bash
empirica session-create --ai-id claude-code --output json

empirica preflight-submit - << 'EOF'
{
  "session_id": "<YOUR-SESSION-ID>",
  "task_context": "Choose and implement a refactoring approach for payment_processor.py",
  "vectors": {
    "know": 0.3,
    "uncertainty": 0.7,
    "context": 0.4,
    "clarity": 0.3
  },
  "reasoning": "Haven't analyzed the code yet. Know three approaches exist but don't know which fits best. High uncertainty about tradeoffs in this specific context."
}
EOF
```

---

## Step 2: Analyze the Current Code

Read `payment_processor.py` carefully. Identify:
- What patterns repeat?
- What would change if you added a new payment type?
- What makes testing difficult?

```bash
empirica finding-log --session-id <ID> \
  --finding "Identified 4 code smells: (1) if/elif chain, (2) duplicated validation, (3) hardcoded providers, (4) tight coupling to specific APIs" \
  --impact 0.4
```

---

## Step 3: Evaluate Approach A (Strategy Pattern)

Consider the Strategy Pattern:

```bash
empirica unknown-log --session-id <ID> \
  --unknown "Is 4 payment types enough to justify Strategy Pattern complexity?"

empirica finding-log --session-id <ID> \
  --finding "Strategy Pattern pros: Testable handlers, open/closed principle. Cons: More files, might be overkill." \
  --impact 0.5
```

---

## Step 4: Evaluate Approach B (Data-Driven Config)

Consider the Config approach:

```bash
empirica finding-log --session-id <ID> \
  --finding "Config approach pros: Single source of truth, easy comparison. Cons: Complex validation hard to express, weak typing." \
  --impact 0.5

empirica unknown-log --session-id <ID> \
  --unknown "Could validators be lambdas? Or would that hurt readability?"
```

---

## Step 5: Evaluate Approach C (Inheritance)

Consider Inheritance:

```bash
empirica finding-log --session-id <ID> \
  --finding "Inheritance pros: Clean OOP, fees as attributes. Cons: Object-per-transaction overhead, rigid hierarchy." \
  --impact 0.5

# Maybe hit a dead-end
empirica deadend-log --session-id <ID> \
  --deadend "Inheritance feels wrong - payments aren't really 'types' of each other, they're processing strategies"
```

---

## Step 6: Make Your Decision

By now your confidence should be shifting. Log your reasoning:

```bash
empirica finding-log --session-id <ID> \
  --finding "Decision: Strategy Pattern (A). Reasoning: (1) Team may add more payment types, (2) each handler testable in isolation, (3) dead-ended on inheritance due to conceptual mismatch" \
  --impact 0.7

empirica unknown-resolve --unknown-id <ID> \
  --resolved-by "4 types is borderline, but extensibility tips the scale toward Strategy"
```

---

## Step 7: Implement the Refactor

Create your refactored version. Test it works.

```bash
# Run the original
python payment_processor.py

# Run your refactored version
python payment_processor_refactored.py
```

---

## Step 8: POSTFLIGHT - Measure Learning

```bash
empirica postflight-submit - << 'EOF'
{
  "session_id": "<YOUR-SESSION-ID>",
  "task_context": "Implemented Strategy Pattern refactor with clear reasoning",
  "vectors": {
    "know": 0.85,
    "uncertainty": 0.20,
    "context": 0.90,
    "clarity": 0.85
  },
  "reasoning": "Made defensible choice after evaluating all three. Documented tradeoffs. Some uncertainty remains (could Config have worked too?) but confident in decision process."
}
EOF
```

**Learning delta:** know +0.55, clarity +0.55

---

## Key Epistemic Lessons

1. **No perfect answer** - Real architectural decisions have genuine tradeoffs
2. **Reasoning > Result** - The process of evaluation matters more than the choice
3. **Dead-ends inform** - Ruling out options is valuable knowledge
4. **Residual uncertainty is OK** - You don't need 100% confidence to act
