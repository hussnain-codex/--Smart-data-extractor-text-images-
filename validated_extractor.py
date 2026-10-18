
from structured_extractor import structured_extract
from business_rules import validate_invoice


def extract_valid_invoice(text: str, max_retries: int = 2):
    """
    Extract an invoice, validate it, and retry after validation errors.
    max_retries=2 means at most 3 extraction attempts:
    1 initial attempt + 2 retries.
    """
    if max_retries < 0:
        raise ValueError("max_retries cannot be negative.")

    current_text = text
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            invoice = structured_extract(current_text)
            validate_invoice(invoice)
            print(f"Validation successful on attempt {attempt + 1}.")
            return invoice

        except ValueError as error:
            last_error = error
            print(f"Attempt {attempt + 1} failed validation: {error}")

            if attempt < max_retries:
                current_text = f"""
The invoice below failed validation.

Validation error:
{error}

Re-read the original invoice and fix only extraction mistakes, such as a
misread number, a missed line item, or a wrong date format. Copy every
value exactly as the original text states it. Never change a date, total,
quantity, or price to something the original text does not say just to
pass validation; if the original itself is inconsistent, return the
values as written. Return the invoice matching the required schema.

Original invoice:
{text}
"""

    raise ValueError(
        f"Invoice validation failed after {max_retries} retries. "
        f"Last error: {last_error}"
    )