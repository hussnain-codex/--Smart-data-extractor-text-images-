from datetime import date
from schemas import Invoice, LineItem


invoice = Invoice(
    vendor="ABC Store",
    invoice_date=date(2026, 10, 8),
    items=[
        LineItem(
            name="Milk",
            quantity=2,
            price=250
        ),
        LineItem(
            name="Bread",
            quantity=1,
            price=180
        )
    ],
    total=680,
    currency="PKR"
)

print(invoice)
print("\nSchema validation successful!")