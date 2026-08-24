from decimal import Decimal

from invoice_processor import to_decimal


def test_to_decimal_valid_number():
    assert to_decimal("717.97") == Decimal("717.97")


def test_to_decimal_integer():
    assert to_decimal(100) == Decimal("100")


def test_to_decimal_empty_value():
    assert to_decimal("") is None


def test_to_decimal_none():
    assert to_decimal(None) is None


def test_to_decimal_invalid_value():
    assert to_decimal("not-a-number") is None