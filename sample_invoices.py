"""The 10 invoice texts used by the extraction experiments, with answers."""

from datetime import date

INVOICE_TEXTS = [
    """
    ABC Store
    Date: October 8, 2026
    Items: Milk, quantity 2, price 250 each;
    Bread, quantity 1, price 180.
    Total: 680 PKR.
    """,
    """
    Fresh Mart
    Date: October 7, 2026
    Items: Rice, quantity 2, price 300 each.
    Total: 600 PKR.
    """,
    """
    City Bakery
    Date: October 6, 2026
    Items: Bread, quantity 3, price 100 each.
    Total: 300 PKR.
    """,
    """
    Tech Shop
    Date: October 5, 2026
    Items: Mouse, quantity 1, price 1200;
    Keyboard, quantity 1, price 2500.
    Total: 3700 PKR.
    """,
    """
    Green Grocery
    Date: October 4, 2026
    Items: Apples, quantity 2, price 200 each.
    Total: 400 PKR.
    """,
    """
    Book World
    Date: October 3, 2026
    Items: Notebook, quantity 4, price 150 each.
    Total: 600 PKR.
    """,
    """
    Office Supplies
    Date: October 2, 2026
    Items: Pens, quantity 5, price 40 each.
    Total: 200 PKR.
    """,
    """
    Coffee Corner
    Date: October 1, 2026
    Items: Coffee, quantity 2, price 500 each.
    Total: 1000 PKR.
    """,
    """
    Clothing Store
    Date: September 30, 2026
    Items: Shirt, quantity 1, price 1800.
    Total: 1800 PKR.
    """,
    """
    Super Market
    Date: September 29, 2026
    Items: Milk, quantity 2, price 250 each;
    Eggs, quantity 1, price 350.
    Total: 850 PKR.
    """,
]

# Expected values: (vendor, date, [(quantity, price), ...], total, currency)
EXPECTED = [
    ("ABC Store", date(2026, 10, 8), [(2, 250), (1, 180)], 680, "PKR"),
    ("Fresh Mart", date(2026, 10, 7), [(2, 300)], 600, "PKR"),
    ("City Bakery", date(2026, 10, 6), [(3, 100)], 300, "PKR"),
    ("Tech Shop", date(2026, 10, 5), [(1, 1200), (1, 2500)], 3700, "PKR"),
    ("Green Grocery", date(2026, 10, 4), [(2, 200)], 400, "PKR"),
    ("Book World", date(2026, 10, 3), [(4, 150)], 600, "PKR"),
    ("Office Supplies", date(2026, 10, 2), [(5, 40)], 200, "PKR"),
    ("Coffee Corner", date(2026, 10, 1), [(2, 500)], 1000, "PKR"),
    ("Clothing Store", date(2026, 9, 30), [(1, 1800)], 1800, "PKR"),
    ("Super Market", date(2026, 9, 29), [(2, 250), (1, 350)], 850, "PKR"),
]
