
from datetime import date
from schemas import Invoice


def validate_invoice(invoice: Invoice) -> None:
    """Validate invoice totals and dates."""

    # Rule 1: Invoice date must not be in the future.
    if invoice.invoice_date > date.today():
        raise ValueError("Invoice date cannot be in the future.")

    # Rule 2: Sum of line items must match the invoice total.
    calculated_total = sum(
        item.quantity * item.price
        for item in invoice.items
    )

    # Allow a small rounding difference.
    if abs(calculated_total - invoice.total) > 0.02:
        raise ValueError(
            f"Invoice total mismatch. "
            f"Expected {calculated_total:.2f}, "
            f"but invoice says {invoice.total:.2f}."
        )