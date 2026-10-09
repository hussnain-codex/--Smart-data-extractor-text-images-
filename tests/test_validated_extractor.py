from datetime import date

import pytest

import validated_extractor
from schemas import Invoice, LineItem


def make_invoice(total: float) -> Invoice:
    return Invoice(
        vendor="ABC Store",
        invoice_date=date.today(),
        items=[
            LineItem(name="Milk", quantity=2, price=250),
            LineItem(name="Bread", quantity=1, price=180),
        ],
        total=total,
        currency="PKR",
    )


def test_returns_valid_invoice_without_retry(monkeypatch):
    invoice = make_invoice(680)
    prompts = []

    def fake_structured_extract(text: str) -> Invoice:
        prompts.append(text)
        return invoice

    monkeypatch.setattr(
        validated_extractor,
        "structured_extract",
        fake_structured_extract,
    )

    result = validated_extractor.extract_valid_invoice("Original invoice")

    assert result is invoice
    assert prompts == ["Original invoice"]


def test_retries_after_validation_error(monkeypatch):
    invalid_invoice = make_invoice(700)
    valid_invoice = make_invoice(680)
    prompts = []
    responses = iter([invalid_invoice, valid_invoice])

    def fake_structured_extract(text: str) -> Invoice:
        prompts.append(text)
        return next(responses)

    monkeypatch.setattr(
        validated_extractor,
        "structured_extract",
        fake_structured_extract,
    )

    result = validated_extractor.extract_valid_invoice(
        "Original invoice",
        max_retries=1,
    )

    assert result is valid_invoice
    assert len(prompts) == 2
    assert prompts[0] == "Original invoice"
    assert "Invoice total mismatch" in prompts[1]
    assert "Original invoice" in prompts[1]


def test_raises_after_all_attempts_fail(monkeypatch):
    prompts = []

    def fake_structured_extract(text: str) -> Invoice:
        prompts.append(text)
        return make_invoice(700)

    monkeypatch.setattr(
        validated_extractor,
        "structured_extract",
        fake_structured_extract,
    )

    with pytest.raises(
        ValueError,
        match="Invoice validation failed after 1 retries",
    ):
        validated_extractor.extract_valid_invoice(
            "Original invoice",
            max_retries=1,
        )

    assert len(prompts) == 2
