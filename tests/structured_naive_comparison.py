
from extractor import naive_extract
from sample_invoices import INVOICE_TEXTS
from structured_extractor import structured_extract


test_inputs = INVOICE_TEXTS


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