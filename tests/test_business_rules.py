from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from schemas import Invoice, LineItem
from business_rules import validate_invoice


def make_invoice(invoice_date: date, total: float) -> Invoice:
    """Create a sample invoice for testing."""
    return Invoice(
        vendor="ABC Store",
        invoice_date=invoice_date,
        items=[
            LineItem(name="Milk", quantity=2, price=250),
            LineItem(name="Bread", quantity=1, price=180),
        ],
        total=total,
        currency="PKR",
    )


def test_valid_invoice():
    invoice = make_invoice(date.today(), 680)
    validate_invoice(invoice)


def test_incorrect_total_is_rejected():
    with pytest.raises(ValidationError, match="Invoice total mismatch"):
        make_invoice(date.today(), 700)


def test_future_invoice_date_is_rejected():
    future_date = date.today() + timedelta(days=1)
    with pytest.raises(ValidationError, match="future"):
        make_invoice(future_date, 680)


def test_mutated_invoice_is_revalidated():
    invoice = make_invoice(date.today(), 680)
    invoice.total = 700

    with pytest.raises(ValidationError, match="Invoice total mismatch"):
        validate_invoice(invoice)


def test_rounding_difference_of_two_cents_is_allowed():
    invoice = make_invoice(date.today(), 680.02)
    validate_invoice(invoice)


def test_rounding_difference_greater_than_two_cents_is_rejected():
    with pytest.raises(ValidationError, match="Invoice total mismatch"):
        make_invoice(date.today(), 680.03)


def test_empty_invoice_items_with_zero_total():
    invoice = Invoice(
        vendor="ABC Store",
        invoice_date=date.today(),
        items=[],
        total=0,
        currency="PKR",
    )
    validate_invoice(invoice)


def test_negative_total_is_rejected_when_items_are_present():
    with pytest.raises(ValidationError):
        make_invoice(date.today(), -100)