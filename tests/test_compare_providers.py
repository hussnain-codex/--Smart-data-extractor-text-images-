from datetime import date

import compare_providers
from sample_invoices import EXPECTED, INVOICE_TEXTS
from schemas import Invoice, LineItem


def make_invoice(**overrides):
    data = {
        "vendor": "ABC Store",
        "invoice_date": date(2026, 10, 8),
        "items": [
            LineItem(name="Milk", quantity=2, price=250),
            LineItem(name="Bread", quantity=1, price=180),
        ],
        "total": 680,
        "currency": "PKR",
    }
    data.update(overrides)
    return Invoice(**data)


def test_sample_inputs_and_answers_line_up():
    assert len(INVOICE_TEXTS) == len(EXPECTED) == 10
    for text, (vendor, *_rest) in zip(INVOICE_TEXTS, EXPECTED):
        assert vendor in text


def test_score_counts_every_correct_field():
    assert compare_providers.score(make_invoice(), EXPECTED[0]) == (5, 5)


def test_score_ignores_vendor_case_and_item_order():
    invoice = make_invoice(
        vendor="abc store ",
        items=[
            LineItem(name="Bread", quantity=1, price=180),
            LineItem(name="Milk", quantity=2, price=250),
        ],
    )

    assert compare_providers.score(invoice, EXPECTED[0]) == (5, 5)


def test_score_flags_wrong_fields():
    invoice = make_invoice(vendor="Other Shop", currency="USD")

    assert compare_providers.score(invoice, EXPECTED[0]) == (3, 5)


def test_run_provider_records_failures_and_accuracy(monkeypatch):
    answers = iter(
        [make_invoice()] + [ValueError("bad output")] * 9
    )

    class FakeExtractor:
        def invoke(self, _text):
            answer = next(answers)
            if isinstance(answer, Exception):
                raise answer
            return answer

    result = compare_providers.run_provider(
        "Fake", lambda: ("fake-model", FakeExtractor())
    )

    assert result["valid_outputs"] == 1
    assert result["field_accuracy"] == 10.0
    assert len(result["errors"]) == 9


def test_markdown_table_shows_missing_latency():
    table = compare_providers.markdown_table(
        [
            {
                "provider": "Fake",
                "model": "m",
                "valid_outputs": 0,
                "total": 10,
                "field_accuracy": 0.0,
                "avg_latency_s": None,
                "median_latency_s": None,
            }
        ]
    )

    assert "| Fake | `m` | 0/10 | 0.0% | n/a | n/a |" in table
