
from extractor import naive_extract
from structured_extractor import structured_extract


test_inputs = [
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
    """
]


def run_test(label, extract_function):
    successful = 0
    failed = 0

    print(f"\n--- {label} ---")

    for index, text in enumerate(test_inputs, start=1):
        try:
            result = extract_function(text)
            successful += 1
            print(f"Test {index}: SUCCESS")
            print(result)

        except Exception as error:
            failed += 1
            print(f"\nTest {index}: FAILED")
            print("Error type:", type(error).__name__)
            print("Error details:", repr(error))

    total = len(test_inputs)
    failure_rate = failed / total * 100

    print(f"\nTotal: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Failure rate: {failure_rate:.1f}%")

    return failure_rate


naive_failure_rate = run_test(
    "Naive JSON Extraction",
    naive_extract
)

structured_failure_rate = run_test(
    "Structured Extraction",
    structured_extract
)

print("\n--- FINAL COMPARISON ---")
print(f"Naive failure rate: {naive_failure_rate:.1f}%")
print(f"Structured failure rate: {structured_failure_rate:.1f}%")