from datetime import date

import pytest
from pydantic import ValidationError

from schemas import Invoice, LineItem


def make_valid_invoice():
    return Invoice(
        vendor="ABC Store",
        invoice_date=date(2026, 10, 8),
        items=[
            LineItem(name="Milk", quantity=2, price=250),
            LineItem(name="Bread", quantity=1, price=180),
        ],
        total=680,
        currency="PKR",
    )


def test_valid_invoice_passes_schema_validation():
    invoice = make_valid_invoice()

    assert invoice.vendor == "ABC Store"
    assert invoice.total == 680
    assert len(invoice.items) == 2


def test_line_item_fields_are_parsed_correctly():
    item = LineItem(name="Milk", quantity=2, price=250)

    assert item.name == "Milk"
    assert item.quantity == 2
    assert item.price == 250


def test_missing_required_invoice_field_is_rejected():
    with pytest.raises(ValidationError):
        Invoice(
            invoice_date=date(2026, 10, 8),
            items=[],
            total=0,
            currency="PKR",
        )


def test_invalid_invoice_date_is_rejected():
    with pytest.raises(ValidationError):
        Invoice(
            vendor="ABC Store",
            invoice_date="not-a-date",
            items=[],
            total=0,
            currency="PKR",
        )


def test_invoice_can_be_converted_to_json():
    invoice = make_valid_invoice()

    json_data = invoice.model_dump_json()
    restored_invoice = Invoice.model_validate_json(json_data)

    assert restored_invoice == invoice
