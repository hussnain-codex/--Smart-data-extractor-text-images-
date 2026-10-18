import pytest

from tools import categorize_expense, convert_currency


def test_convert_currency_uses_fixed_rates_case_insensitively():
    converted = convert_currency.invoke({
        "amount": 10,
        "from_cur": "usd",
        "to_cur": "PKR",
    })

    assert converted == 2780


def test_convert_currency_rejects_unsupported_currency():
    with pytest.raises(ValueError, match="Unsupported currency"):
        convert_currency.invoke({
            "amount": 10,
            "from_cur": "USD",
            "to_cur": "JPY",
        })


def test_categorize_expense_uses_vendor_keywords():
    assert categorize_expense.invoke({"vendor": "ABC Supermarket"}) == "groceries"
    assert categorize_expense.invoke({"vendor": "Careem"}) == "transport"
    assert categorize_expense.invoke({"vendor": "Unknown vendor"}) == "other"
