
import os
import json
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field, ValidationError


load_dotenv()


# -----------------------------
# 1. Structured output schema
# -----------------------------

class ImageAnalysis(BaseModel):
    image_type: str = Field(
        description="Likely category of the image"
    )
    description: str = Field(
        description="Description of the visible content"
    )
    detected_text: list[str] = Field(
        description="Readable text found in the image"
    )
    objects: list[str] = Field(
        description="Visible objects or subjects"
    )
    key_details: dict[str, str] = Field(
        description="Relevant details identified from the image"
    )


# -----------------------------
# 2. Create Gemini client
# -----------------------------

def create_image_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing. "
            "Add it to your .env file."
        )

    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=120000
        ),
    )


# -----------------------------
# 3. Analyze any image
# -----------------------------

def analyze_image(
    image_path: str,
    max_attempts: int = 3,
) -> ImageAnalysis:

    path = Path(image_path).expanduser()

    if not path.is_file():
        raise FileNotFoundError(
            f"Image not found: {path.resolve()}"
        )

    # Open and prepare the image
    try:
        with Image.open(path) as original:
            original.load()

            image = original.convert("RGB")
            image.thumbnail((1600, 1600))

    except (UnidentifiedImageError, OSError) as error:
        raise ValueError(
            "The selected file is not a valid or supported image."
        ) from error

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")

    prompt = """
Analyze this image regardless of its type.

Return a JSON object containing:
- image_type: the likely category of the image
- description: a concise description of visible content
- detected_text: a list of readable text
- objects: a list of visible objects or subjects
- key_details: a dictionary of relevant details

Examples:
- Receipts: identify visible items, quantities and prices.
- Job advertisements: identify the job title and requirements.
- Business cards: identify names and visible contact details.
- Screenshots and documents: extract readable text.
- Products: describe the visible product and its features.
- People and animals: describe only visible characteristics.
- Landscapes and buildings: describe visible surroundings.
- Diagrams and charts: describe their visible structure and labels.

Do not invent information or guess unreadable text.
If no text is visible, return an empty list.
If no objects can be identified, return an empty list.
If no additional details are available, return an empty dictionary.
"""

    client = create_image_client()

    model_name = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.8-flash",
    )

    last_error = None

    # Retry temporary API failures
    for attempt in range(1, max_attempts + 1):
        try:
            print(
                f"Analyzing {path.name} "
                f"(attempt {attempt}/{max_attempts})..."
            )

            response = client.models.generate_content(
                model=model_name,
                contents=[
                    prompt,
                    image,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=(
                        ImageAnalysis.model_json_schema()
                    ),
                    temperature=0,
                ),
            )

            if not response.text:
                raise ValueError(
                    "Gemini returned an empty response."
                )

            data = json.loads(response.text)

            result = ImageAnalysis.model_validate(data)

            print("Image analysis completed successfully.")

            return result

        except (json.JSONDecodeError, ValidationError) as error:
            raise ValueError(
                "Gemini returned JSON that did not match "
                "the expected schema."
            ) from error

        except ValueError:
            raise

        except Exception as error:
            last_error = error

            print(
                f"Attempt {attempt} failed: "
                f"{type(error).__name__}: {error}"
            )

            if attempt < max_attempts:
                wait_seconds = attempt * 5

                print(
                    f"Retrying in {wait_seconds} seconds..."
                )

                time.sleep(wait_seconds)

    raise RuntimeError(
        f"Image analysis failed after {max_attempts} attempts. "
        "Check model availability, API quota, and network connection."
    ) from last_error


# -----------------------------
# 4. Run from terminal
# -----------------------------

if __name__ == "__main__":
    print("=" * 45)
    print(" SMART DATA EXTRACTOR")
    print(" Image Analysis")
    print("=" * 45)

    image_path = input(
        "Enter image path (e.g. images/sample.jpg): "
    ).strip().strip('"')

    try:
        result = analyze_image(image_path)

        print("\n" + "=" * 45)
        print(" IMAGE ANALYSIS RESULT")
        print("=" * 45)

        print(result.model_dump_json(indent=2))

        # Save the result beside the script
        output_path = Path("image_result.json")

        output_path.write_text(
            result.model_dump_json(indent=2),
            encoding="utf-8",
        )

        print(f"\nJSON result saved to: {output_path.resolve()}")

    except FileNotFoundError as error:
        print(f"\nFile error: {error}")

    except ValueError as error:
        print(f"\nInput or configuration error: {error}")

    except RuntimeError as error:
        print(f"\nAnalysis failed: {error}")

    except Exception as error:
        print(
            f"\nUnexpected error: "
            f"{type(error).__name__}: {error}"
        )