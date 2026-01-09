#!/usr/bin/env python3
"""
Payment Processor - Code needing refactoring.

This module has grown organically and now has several problems:
1. Giant if/elif chain for payment types
2. Duplicated validation logic
3. Hard to add new payment methods
4. Testing is difficult due to tight coupling
"""


class PaymentProcessor:
    """Process payments through various providers."""

    def __init__(self):
        self.processed = []
        self.failed = []

    def process_payment(self, payment_type: str, amount: float, details: dict) -> dict:
        """
        Process a payment.

        Problems:
        - Giant conditional block
        - Each branch has duplicated validation
        - Adding new payment types requires modifying this method
        - Tightly coupled to specific provider implementations
        """
        result = {"type": payment_type, "amount": amount, "status": "unknown"}

        # Credit card payment
        if payment_type == "credit_card":
            # Validation (duplicated pattern)
            if amount <= 0:
                result["status"] = "failed"
                result["error"] = "Invalid amount"
                self.failed.append(result)
                return result
            if "card_number" not in details:
                result["status"] = "failed"
                result["error"] = "Missing card number"
                self.failed.append(result)
                return result
            if len(details.get("card_number", "")) != 16:
                result["status"] = "failed"
                result["error"] = "Invalid card number length"
                self.failed.append(result)
                return result

            # Process credit card
            result["provider"] = "StripeAPI"
            result["fee"] = amount * 0.029 + 0.30  # 2.9% + $0.30
            result["net"] = amount - result["fee"]
            result["status"] = "success"
            result["transaction_id"] = f"CC-{hash(details['card_number']) % 100000}"
            self.processed.append(result)

        # PayPal payment
        elif payment_type == "paypal":
            # Validation (duplicated pattern)
            if amount <= 0:
                result["status"] = "failed"
                result["error"] = "Invalid amount"
                self.failed.append(result)
                return result
            if "email" not in details:
                result["status"] = "failed"
                result["error"] = "Missing PayPal email"
                self.failed.append(result)
                return result
            if "@" not in details.get("email", ""):
                result["status"] = "failed"
                result["error"] = "Invalid email format"
                self.failed.append(result)
                return result

            # Process PayPal
            result["provider"] = "PayPalAPI"
            result["fee"] = amount * 0.034 + 0.49  # 3.4% + $0.49
            result["net"] = amount - result["fee"]
            result["status"] = "success"
            result["transaction_id"] = f"PP-{hash(details['email']) % 100000}"
            self.processed.append(result)

        # Bank transfer
        elif payment_type == "bank_transfer":
            # Validation (duplicated pattern)
            if amount <= 0:
                result["status"] = "failed"
                result["error"] = "Invalid amount"
                self.failed.append(result)
                return result
            if "account_number" not in details:
                result["status"] = "failed"
                result["error"] = "Missing account number"
                self.failed.append(result)
                return result
            if "routing_number" not in details:
                result["status"] = "failed"
                result["error"] = "Missing routing number"
                self.failed.append(result)
                return result

            # Process bank transfer
            result["provider"] = "PlaidAPI"
            result["fee"] = 0.25  # Flat fee
            result["net"] = amount - result["fee"]
            result["status"] = "pending"  # Bank transfers take time
            result["transaction_id"] = f"BT-{hash(details['account_number']) % 100000}"
            self.processed.append(result)

        # Crypto payment
        elif payment_type == "crypto":
            # Validation (duplicated pattern)
            if amount <= 0:
                result["status"] = "failed"
                result["error"] = "Invalid amount"
                self.failed.append(result)
                return result
            if "wallet_address" not in details:
                result["status"] = "failed"
                result["error"] = "Missing wallet address"
                self.failed.append(result)
                return result
            if not details.get("wallet_address", "").startswith("0x"):
                result["status"] = "failed"
                result["error"] = "Invalid wallet address format"
                self.failed.append(result)
                return result

            # Process crypto
            result["provider"] = "CoinbaseAPI"
            result["fee"] = amount * 0.015  # 1.5%
            result["net"] = amount - result["fee"]
            result["status"] = "success"
            result["transaction_id"] = f"CR-{hash(details['wallet_address']) % 100000}"
            self.processed.append(result)

        # Unknown payment type
        else:
            result["status"] = "failed"
            result["error"] = f"Unsupported payment type: {payment_type}"
            self.failed.append(result)

        return result

    def get_summary(self) -> dict:
        """Get processing summary."""
        total_processed = sum(p["amount"] for p in self.processed)
        total_fees = sum(p["fee"] for p in self.processed)
        return {
            "transactions": len(self.processed),
            "failed": len(self.failed),
            "total_processed": total_processed,
            "total_fees": total_fees,
            "net_revenue": total_processed - total_fees,
        }


# Quick test
if __name__ == "__main__":
    processor = PaymentProcessor()

    # Test various payments
    print(processor.process_payment("credit_card", 100.00, {"card_number": "4111111111111111"}))
    print(processor.process_payment("paypal", 50.00, {"email": "user@example.com"}))
    print(processor.process_payment("bank_transfer", 200.00, {"account_number": "123456789", "routing_number": "987654321"}))
    print(processor.process_payment("crypto", 75.00, {"wallet_address": "0xabc123def456"}))
    print(processor.process_payment("venmo", 25.00, {}))  # Unsupported

    print("\nSummary:", processor.get_summary())
