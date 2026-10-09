
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing from your .env file.")

image_path = Path("images/sample.jpg")

if not image_path.is_file():
    raise FileNotFoundError(f"Image not found: {image_path.resolve()}")

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(timeout=60000),
)

max_attempts = 3

for attempt in range(1, max_attempts + 1):
    try:
        print(f"Sending image to Gemini (attempt {attempt}/{max_attempts})...")

        with Image.open(image_path) as image:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=[
                    "Describe this image in two sentences.",
                    image.copy(),
                ],
            )

        print("\nGemini response:")
        print(response.text)
        break

    except Exception as error:
        print(f"Attempt {attempt} failed: {type(error).__name__}: {error}")

        if attempt < max_attempts:
            wait_seconds = attempt * 5
            print(f"Retrying in {wait_seconds} seconds...")
            time.sleep(wait_seconds)
        else:
            print(
                "\nGemini is still unavailable. Try again later, "
                "or test another model available to your API key."
            )