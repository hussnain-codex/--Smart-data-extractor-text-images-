
from schemas import Invoice


def validate_invoice(invoice: Invoice) -> None:
    """Revalidate invoice business rules, including after mutation."""
    Invoice.model_validate(invoice.model_dump())