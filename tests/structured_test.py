from structured_extractor import structured_extract


text = """
ABC Store
Date: October 8, 2026

Items:
Milk - 2 units - Rs. 250 each
Bread - 1 unit - Rs. 180

Total: Rs. 680
Currency: PKR
"""


try:
    result = structured_extract(text)

    print("Structured extraction successful!")
    print()
    print(result)
    print()
    print("As dictionary:")
    print(result.model_dump())

except Exception as error:
    print("Extraction failed:")
    print(error)

