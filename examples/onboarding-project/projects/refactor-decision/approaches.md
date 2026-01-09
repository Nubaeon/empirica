# Refactoring Approaches

Three valid ways to improve this code. Each has real tradeoffs.

---

## Approach A: Strategy Pattern

Replace the if/elif chain with a strategy pattern using separate handler classes.

```python
class PaymentHandler(ABC):
    @abstractmethod
    def validate(self, amount, details): pass
    @abstractmethod
    def process(self, amount, details): pass

class CreditCardHandler(PaymentHandler):
    def validate(self, amount, details): ...
    def process(self, amount, details): ...

class PaymentProcessor:
    handlers = {
        "credit_card": CreditCardHandler(),
        "paypal": PayPalHandler(),
        ...
    }
    def process_payment(self, type, amount, details):
        return self.handlers[type].process(amount, details)
```

**Pros:**
- Clean separation of concerns
- Easy to add new payment types
- Each handler is independently testable

**Cons:**
- More files/classes to manage
- Potential over-engineering for 4 payment types
- Runtime registration can be confusing

---

## Approach B: Data-Driven Configuration

Keep a single method but externalize the differences into config.

```python
PAYMENT_CONFIG = {
    "credit_card": {
        "provider": "StripeAPI",
        "fee_percent": 0.029,
        "fee_flat": 0.30,
        "required_fields": ["card_number"],
        "validators": [validate_card_number],
    },
    ...
}

class PaymentProcessor:
    def process_payment(self, type, amount, details):
        config = PAYMENT_CONFIG[type]
        for validator in config["validators"]:
            validator(details)
        fee = amount * config["fee_percent"] + config["fee_flat"]
        ...
```

**Pros:**
- All payment config in one place
- Easy to compare payment types
- Less code than strategy pattern

**Cons:**
- Validators as functions can be awkward
- Complex payment logic hard to express in config
- Type safety is weaker

---

## Approach C: Inheritance Hierarchy

Use class inheritance with a base payment class.

```python
class Payment(ABC):
    fee_percent = 0.0
    fee_flat = 0.0

    @abstractmethod
    def validate(self): pass

    def calculate_fee(self, amount):
        return amount * self.fee_percent + self.fee_flat

class CreditCardPayment(Payment):
    fee_percent = 0.029
    fee_flat = 0.30
    def validate(self): ...

processor.process(CreditCardPayment(100, details))
```

**Pros:**
- OOP purists love it
- Fees/config as class attributes
- Polymorphism handles dispatch

**Cons:**
- Creates object per transaction (memory)
- Inheritance hierarchies can become rigid
- "Is-a" relationship may not fit all cases

---

## Your Task

1. Read `payment_processor.py` thoroughly
2. Consider each approach's fit for THIS codebase
3. Log your reasoning as it evolves
4. Make a defensible choice
5. Implement your chosen refactor

**There is no "right" answer** - the epistemic value is in your reasoning process.
