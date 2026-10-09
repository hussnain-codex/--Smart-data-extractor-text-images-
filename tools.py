
from datetime import date
from langchain_core.tools import tool


@tool
def calculate_invoice_total(items: list[dict]) -> float:
    """Calculate an invoice total from line items.

    Each item must contain quantity and price.
    Use this tool when you need to calculate the sum of invoice items.
    """
    total = 0.0

    for item in items:
        quantity = int(item["quantity"])
        price = float(item["price"])

        if quantity < 0:
            raise ValueError("Quantity cannot be negative.")

        if price < 0:
            raise ValueError("Price cannot be negative.")

        total += quantity * price

    return round(total, 2)


@tool
def check_invoice_date(invoice_date: str) -> str:
    """Check whether an invoice date is valid and not in the future.

    Accepts a date in YYYY-MM-DD format.
    Use this tool when checking an invoice date.
    """
    try:
        parsed_date = date.fromisoformat(invoice_date)
    except ValueError:
        return "Invalid date. Use YYYY-MM-DD format."

    if parsed_date > date.today():
        return "Invalid invoice date: date is in the future."

    return "Invoice date is valid and is not in the future."