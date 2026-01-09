"""
Tests for the Calculator Module

Run with: python -m pytest test_calculator.py -v
"""

import pytest
from calculator import add, subtract, multiply, divide


class TestAdd:
    def test_add_positive_numbers(self):
        assert add(2, 3) == 5

    def test_add_negative_numbers(self):
        assert add(-1, -1) == -2

    def test_add_mixed_numbers(self):
        assert add(-1, 5) == 4

    def test_add_floats(self):
        assert add(1.5, 2.5) == 4.0


class TestSubtract:
    def test_subtract_positive_numbers(self):
        assert subtract(5, 3) == 2

    def test_subtract_negative_result(self):
        assert subtract(3, 5) == -2

    def test_subtract_floats(self):
        assert subtract(5.5, 2.5) == 3.0


class TestMultiply:
    def test_multiply_positive_numbers(self):
        assert multiply(3, 4) == 12

    def test_multiply_by_zero(self):
        assert multiply(5, 0) == 0

    def test_multiply_negative_numbers(self):
        assert multiply(-2, -3) == 6

    def test_multiply_floats(self):
        assert multiply(2.5, 4) == 10.0


class TestDivide:
    def test_divide_positive_numbers(self):
        assert divide(10, 2) == 5

    def test_divide_with_remainder(self):
        assert divide(7, 2) == 3.5

    def test_divide_negative_numbers(self):
        assert divide(-10, 2) == -5

    def test_divide_by_zero_raises_error(self):
        with pytest.raises(ValueError):
            divide(10, 0)
