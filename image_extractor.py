
import base64
import json
import os
import random
import time
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from langchain_core.messages import HumanMessage
from langchain_core.exceptions import (
    ModelAuthenticationError,
    ModelInvalidRequestError,
    ModelNotFoundError,
    ModelPermissionDeniedError,
    ModelRateLimitError,
)
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field, ValidationError

from schemas import Invoice

load_dotenv()

DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"

# Error kinds returned by classify_gemini_error()
TEMPORARY = "temporary"            # 5xx, timeouts, network: retry same model
QUOTA = "quota"                    # 429: switch to a fallback model
MODEL_NOT_FOUND = "model_not_found"  # 404: switch to a fallback model
FATAL = "fatal"                    # other 4xx (bad key, bad request): stop


# -----------------------------
# Gemini model selection and retries
# -----------------------------

def gemini_models() -> list[str]:
    """Return GEMINI_MODEL followed by any GEMINI_FALLBACK_MODELS."""
    primary = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    fallbacks = os.getenv("GEMINI_FALLBACK_MODELS", "").split(",")

    models = []
    for name in [primary, *fallbacks]:
        name = name.strip()
        if name and name not in models:
            models.append(name)
    return models


def _gemini_error_status(error: BaseException) -> int | None:
    """Find the HTTP status of a Gemini error, following wrapped causes."""
    if isinstance(error, ModelRateLimitError):
        return 429
    if isinstance(error, ModelNotFoundError):
        return 404
    if isinstance(error, ModelAuthenticationError):
        return 401
    if isinstance(error, ModelPermissionDeniedError):
        return 403
    if isinstance(error, ModelInvalidRequestError):
        return 400

    current = error
    while current is not None:
        code = getattr(current, "code", None)
        if isinstance(code, int):
            return code
        current = current.__cause__
    return None


def classify_gemini_error(error: BaseException) -> str:
    status = _gemini_error_status(error)

    if status == 429:
        return QUOTA
    if status == 404:
        return MODEL_NOT_FOUND
    if status is not None and 400 <= status < 500 and status != 408:
        return FATAL
    return TEMPORARY


def retry_delay(attempt: int) -> float:
    """Exponential backoff (5s, 15s, 45s, max 60s) with a little jitter."""
    return min(5 * 3 ** (attempt - 1), 60) + random.uniform(0, 1)


def _short_error(error: BaseException, limit: int = 200) -> str:
    text = f"{type(error).__name__}: {error}"
    return text if len(text) <= limit else text[:limit] + "..."


def call_gemini(request, task: str, max_attempts: int = 3):
    """Run request(model_name) on the configured models until one succeeds.

    Temporary failures (503 overload, timeouts, network) are retried on the
    same model with backoff. Quota limits (429) and unavailable models (404)
    switch straight to the next fallback model, because retrying them wastes
    requests. Other client errors (bad key, invalid request) stop at once.
    ValueError (including schema validation errors) is raised unchanged.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")

    models = gemini_models()
    failures = {}
    last_error = None

    for index, model_name in enumerate(models):
        if index > 0:
            print(f"Switching to fallback model '{model_name}'...")

        for attempt in range(1, max_attempts + 1):
            print(
                f"{task} with {model_name} "
                f"(attempt {attempt}/{max_attempts})..."
            )
            try:
                return request(model_name)
            except ValueError:
                raise
            except Exception as error:
                last_error = error
                kind = classify_gemini_error(error)

                if kind == FATAL:
                    raise RuntimeError(
                        f"Gemini rejected the request for model "
                        f"'{model_name}' ({_short_error(error)}). Retrying "
                        "will not help; check GEMINI_API_KEY and the request."
                    ) from error

                if kind == QUOTA:
                    print(
                        f"Model '{model_name}' has hit its rate limit or "
                        "daily quota (429). Not retrying it."
                    )
                    failures[model_name] = kind
                    break

                if kind == MODEL_NOT_FOUND:
                    print(
                        f"Model '{model_name}' is not available to this "
                        "API key (404). Not retrying it."
                    )
                    failures[model_name] = kind
                    break

                print(f"Attempt {attempt} failed: {_short_error(error)}")
                if attempt < max_attempts:
                    wait_seconds = retry_delay(attempt)
                    print(f"Retrying in {wait_seconds:.0f} seconds...")
                    time.sleep(wait_seconds)
                else:
                    failures[model_name] = kind

    raise RuntimeError(
        _failure_message(task, failures, max_attempts)
    ) from last_error


def _failure_message(task: str, failures: dict, max_attempts: int) -> str:
    reasons = {
        QUOTA: "rate limit or daily quota reached (429)",
        MODEL_NOT_FOUND: "model not available to this API key (404)",
        TEMPORARY: f"failed after {max_attempts} attempts (server busy "
                   "or unreachable)",
    }
    details = "; ".join(
        f"'{name}' {reasons[kind]}" for name, kind in failures.items()
    )
    message = f"{task} failed. Gemini model {details}."
    kinds = set(failures.values())

    if kinds == {QUOTA}:
        message += (
            " Further retries will not help right now. Check usage at "
            "https://ai.dev/rate-limit, wait for the quota to reset, or add "
            "a model with available quota to GEMINI_FALLBACK_MODELS."
        )
    elif TEMPORARY in kinds:
        message += (
            " Gemini is overloaded or unreachable; try again in a few "
            "minutes, or add another model to GEMINI_FALLBACK_MODELS."
        )
    if MODEL_NOT_FOUND in kinds:
        message += (
            " Update GEMINI_MODEL or GEMINI_FALLBACK_MODELS to a model "
            "your API key can use."
        )
    return message


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


def create_invoice_model(model_name: str | None = None):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing. "
            "Add it to your .env file."
        )

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ModuleNotFoundError as error:
        if error.name != "langchain_google_genai":
            raise
        raise ModuleNotFoundError(
            "Receipt image extraction requires langchain-google-genai. "
            "Install project dependencies with "
            "'python -m pip install -r requirements.txt', or run the "
            "project virtual environment with "
            "'.\\venv\\Scripts\\python.exe'.",
            name=error.name,
        ) from error

    model_name = model_name or gemini_models()[0]
    model = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0,
        api_key=api_key,
        request_timeout=120,
        retries=0,
    )
    return model.with_structured_output(Invoice)


def extract_invoice_from_image(
    image_path: str,
    max_attempts: int = 3,
) -> Invoice:
    """Extract and validate invoice data from a receipt or invoice image."""
    path = Path(image_path).expanduser()

    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {path.resolve()}")
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")

    try:
        with Image.open(path) as original:
            original.load()
            image = original.convert("RGB")
            image.thumbnail((1024, 1024))
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=85)
    except (UnidentifiedImageError, OSError) as error:
        raise ValueError(
            "The selected file is not a valid or supported image."
        ) from error

    image_data = base64.b64encode(buffer.getvalue()).decode("ascii")
    image_url = f"data:image/jpeg;base64,{image_data}"
    prompt = (
        "Extract this receipt or invoice into the required schema. "
        "Use the visible vendor, invoice date, line items, total, and currency. "
        "Do not invent information. If the image is not a receipt or invoice, "
        "or a required value is unreadable, report that clearly rather than "
        "guessing."
    )
    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]
    )
    models = {}

    def request(model_name):
        if model_name not in models:
            models[model_name] = create_invoice_model(model_name)
        response = models[model_name].invoke([message])
        return Invoice.model_validate(response)

    return call_gemini(
        request,
        f"Invoice extraction from {path.name}",
        max_attempts,
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

    def request(model_name):
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

        try:
            data = json.loads(response.text)
            return ImageAnalysis.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as error:
            raise ValueError(
                "Gemini returned JSON that did not match "
                "the expected schema."
            ) from error

    # Retries temporary failures and falls back to other models
    result = call_gemini(request, f"Image analysis of {path.name}", max_attempts)

    print("Image analysis completed successfully.")

    return result


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