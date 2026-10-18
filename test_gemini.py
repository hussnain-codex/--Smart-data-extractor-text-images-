"""Manual Gemini connectivity check: python test_gemini.py

Not a pytest test. It sends a real request and uses API quota.
"""

from pathlib import Path

from PIL import Image

from image_extractor import call_gemini, create_image_client


def main():
    image_path = Path("images/sample.jpg")

    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path.resolve()}")

    client = create_image_client()

    with Image.open(image_path) as original:
        image = original.copy()

    def request(model_name):
        return client.models.generate_content(
            model=model_name,
            contents=["Describe this image in two sentences.", image],
        )

    try:
        response = call_gemini(request, "Sending image to Gemini")
    except RuntimeError as error:
        print(f"\n{error}")
        return

    print("\nGemini response:")
    print(response.text)


if __name__ == "__main__":
    main()
