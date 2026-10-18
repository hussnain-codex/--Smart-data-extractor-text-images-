
from datetime import date
from langchain_core.tools import tool


USD_RATES = {
    "USD": 1.0,
    "PKR": 278.0,
    "EUR": 0.92,
    "GBP": 0.79,
}


@tool
def convert_currency(amount: float, from_cur: str, to_cur: str) -> float:
    """Convert an amount between USD, PKR, EUR, and GBP using fixed example rates."""
    source = from_cur.upper()
    target = to_cur.upper()

    if amount < 0:
        raise ValueError("Amount cannot be negative.")
    if source not in USD_RATES or target not in USD_RATES:
        supported = ", ".join(sorted(USD_RATES))
        raise ValueError(f"Unsupported currency. Use one of: {supported}.")

    converted = amount / USD_RATES[source] * USD_RATES[target]
    return round(converted, 2)


@tool
def categorize_expense(vendor: str) -> str:
    """Assign a simple expense category based on a vendor name."""
    normalized_vendor = vendor.casefold()
    categories = {
        "groceries": ("mart", "market", "grocery", "supermarket"),
        "transport": ("uber", "careem", "shell", "fuel", "petrol"),
        "food": ("restaurant", "cafe", "coffee", "bakery"),
        "office": ("office", "stationery", "supplies"),
        "technology": ("tech", "computer", "electronics"),
    }

    for category, keywords in categories.items():
        if any(keyword in normalized_vendor for keyword in keywords):
            return category

    return "other"


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