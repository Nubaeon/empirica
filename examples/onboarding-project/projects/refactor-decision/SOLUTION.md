# Solution - Refactor Decision

**SPOILERS BELOW**

---

## Analysis of Each Approach

### Approach A: Strategy Pattern - RECOMMENDED

**Best for this codebase because:**
1. Payment types are genuinely different strategies
2. Validation logic varies significantly per type
3. Likely to add more payment methods
4. Each handler testable in isolation

**Implementation sketch:**

```python
from abc import ABC, abstractmethod

class PaymentHandler(ABC):
    provider: str
    fee_percent: float = 0.0
    fee_flat: float = 0.0

    @abstractmethod
    def validate(self, details: dict) -> None:
        """Raise ValueError if invalid."""
        pass

    def calculate_fee(self, amount: float) -> float:
        return amount * self.fee_percent + self.fee_flat

    def process(self, amount: float, details: dict) -> dict:
        self.validate(details)
        fee = self.calculate_fee(amount)
        return {
            "provider": self.provider,
            "fee": fee,
            "net": amount - fee,
            "status": "success",
        }

class CreditCardHandler(PaymentHandler):
    provider = "StripeAPI"
    fee_percent = 0.029
    fee_flat = 0.30

    def validate(self, details):
        if "card_number" not in details:
            raise ValueError("Missing card number")
        if len(details["card_number"]) != 16:
            raise ValueError("Invalid card number length")
```

---

### Approach B: Data-Driven Config - VIABLE

**Could work if:**
- Payment logic is truly uniform (just different parameters)
- You prioritize config visibility over code structure
- Team prefers declarative over OOP

**Limitation:** Validation logic doesn't fit cleanly in config.

---

### Approach C: Inheritance - NOT RECOMMENDED

**Problems:**
- Conceptual mismatch: payments aren't subtypes of each other
- Creates object per transaction (unnecessary allocation)
- Inheritance is rigid; composition (Strategy) is more flexible

---

## The Code Problems (Reference)

| Problem | Where | Impact |
|---------|-------|--------|
| Giant if/elif | Lines 22-130 | Hard to add types |
| Duplicated validation | Every branch | DRY violation |
| Hardcoded providers | Each branch | Not mockable |
| Amount validation | Repeated 4x | Should be shared |

---

## The Epistemic Journey

| Phase | Know | Uncertainty | What Changed |
|-------|------|-------------|--------------|
| Start | 0.3 | 0.7 | Haven't analyzed code |
| After reading code | 0.5 | 0.5 | See problems clearly |
| After evaluating A | 0.6 | 0.4 | Strategy looks promising |
| After evaluating B | 0.6 | 0.4 | Config could work too |
| After evaluating C | 0.7 | 0.3 | Ruled out inheritance |
| After deciding | 0.85 | 0.2 | Confident in Strategy |

---

## Key Insight

The "right" answer depends on:
- Team preferences (OOP vs functional vs declarative)
- Expected growth (more payment types?)
- Testing requirements
- Existing codebase patterns

**Your reasoning process is more valuable than matching this solution.**
