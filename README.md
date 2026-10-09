# Smart Data Extractor (Text + Images)

A Python tool that converts unstructured text and images into clean, structured, validated data.

The project demonstrates structured LLM output, Pydantic validation, business rules, retry-based correction, image analysis, Python tool calling, and batch image processing with CSV export.

## Features

- **Text extraction:** Extract useful information from unstructured text and return JSON.
- **Structured extraction:** Convert text into predefined Pydantic models.
- **Schema validation:** Validate extracted data against required fields and data types.
- **Business rule validation:** Check invoice dates and verify invoice totals.
- **Retry-based correction:** Retry invoice extraction when business validation fails.
- **Image extraction:** Analyze images using Gemini and return structured JSON data.
- **Python tool calling:** Allow the language model to invoke Python functions for invoice calculations and date checks.
- **Batch image processing:** Process supported images in the `images/` folder.
- **CSV export:** Save batch image analysis results, including errors, to `image_results.csv`.

## Technology Stack

- Python
- Pydantic
- LangChain
- Groq API
- Google Gemini API
- Pillow
- Pandas
- Pytest

## Project Structure

```text
Smart Data Extractor/
|
|-- images/                       # Input images
|-- tests/                        # Automated tests
|
|-- app.py                        # Basic text extraction example
|-- extractor.py                  # JSON extraction from text
|-- schemas.py                    # Pydantic data models
|-- structured_extractor.py       # Schema-based LLM extraction
|-- business_rules.py             # Invoice business rules
|-- validated_extractor.py        # Validation and retry workflow
|
|-- image_extractor.py            # Single-image analysis
|-- batch_image_extractor.py      # Batch processing and CSV export
|-- image_result.json             # Example single-image JSON output
|-- image_results.csv             # Batch processing output
|
|-- tools.py                      # Python functions available as tools
|-- tool_calling.py               # LLM tool-calling workflow
|
|-- test_gemini.py                # Gemini API testing
|-- NOTES.md                      # Extraction notes
|-- README.md                     # Project documentation
|-- requirements.txt              # Python dependencies
|-- .env                          # Local API keys (not committed)
|-- .gitignore                    # Git exclusions
```

## Requirements

- Python 3.11 or newer recommended
- A Groq API key for text extraction and tool calling
- A Gemini API key for image extraction
- Internet access for API-based operations

## Installation

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd <your-repository-folder>
```

### 2. Create a virtual environment

```powershell
python -m venv venv
```

### 3. Activate the environment

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

## Environment Configuration

Create a `.env` file in the project root:

```dotenv
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_supported_gemini_model
```

Use valid API keys and a Gemini model supported by your account.

Keep `.env` private. Never commit API keys to GitHub.

## Usage

Run commands from the project root with your virtual environment activated.

### 1. Basic text extraction

```powershell
python app.py
```

This demonstrates extracting useful information from unstructured text and returning JSON.

### 2. Structured invoice extraction

Use the `structured_extractor.py` module to extract text into the `Invoice` Pydantic model.

The module can also be imported into another Python script:

```python
from structured_extractor import structured_extract

text = """
ABC Store
Date: 2026-10-08
Milk: quantity 2, price 250 each
Bread: quantity 1, price 180
Total: 680 PKR
"""

invoice = structured_extract(text)
print(invoice.model_dump_json(indent=2))
```

### 3. Validated invoice extraction

Use `validated_extractor.py` to extract an invoice, check its business rules, and retry after validation errors.

```python
from validated_extractor import extract_valid_invoice

invoice = extract_valid_invoice(
    "ABC Store. Date: 2026-10-08. "
    "Milk: 2 units at 250 each. "
    "Bread: 1 unit at 180. Total: 680 PKR."
)

print(invoice.model_dump_json(indent=2))
```

The extraction requires a valid response from the configured Groq model.

### 4. Single-image extraction

Place an image inside the `images/` directory and run:

```powershell
python image_extractor.py
```

The image extractor analyzes the configured image, validates the result, and saves structured output to `image_result.json`.

Supported image formats include JPG, JPEG, PNG, WEBP, BMP, TIF, and TIFF.

### 5. Batch image extraction

Place one or more supported images in the `images/` directory, then run:

```powershell
python batch_image_extractor.py
```

The batch processor:

1. Finds supported image files.
2. Analyzes each image using Gemini.
3. Records successful results and failures.
4. Writes the results to `image_results.csv`.
5. Prints a summary of successful and failed images.

The CSV contains the filename, status, image type, description, detected text, objects, key details, and error message.

### 6. Python tool calling

Run:

```powershell
python tool_calling.py
```

Enter a question involving invoice calculations or invoice date validation.

The language model can select from these Python tools:

- `calculate_invoice_total` â€” calculates the total from invoice line items.
- `check_invoice_date` â€” checks the date format and whether the invoice date is in the future.

The tool-calling workflow executes requested functions and passes their results back to the model.

## Automated Testing

Run the core test suite:

```powershell
python -m pytest tests/test_schema.py tests/test_business_rules.py tests/test_validated_extractor.py tests/test_image_extractor.py -v
```

The core suite currently contains 22 tests covering:

- Pydantic schema validation
- Invoice business rules
- Validation and retry behavior
- Image extraction and error handling

The latest verified result was **22 passed, 1 warning**.

Some tests use mocked responses, so passing tests does not guarantee that the external APIs are currently available.

## Error Handling

The project handles several expected failures, including:

- Missing or invalid image files
- Invalid model output
- Invoice validation errors
- Repeated image API failures
- Individual failures during batch processing

A failed image analysis is recorded in the batch CSV, allowing processing to continue with other images.

External API availability, rate limits, network timeouts, and model access can still affect live extraction.

## Security

- Store API keys in `.env`.
- Keep `.env` excluded from Git.
- Never hardcode API keys into source files.
- Avoid uploading sensitive invoices or receipts unless you have permission.
- Review extracted information before using it in important business decisions.

## Current Limitations

- Extraction quality depends on the input text, image quality, and model response.
- Business validation currently focuses on invoice dates and invoice totals.
- Image extraction requires a working Gemini API connection.
- Text extraction and tool calling require a working Groq API connection.
- Extracted data should be reviewed when accuracy is important.

## Learning Outcomes

This project provides practical experience with:

- LLM-based information extraction
- Structured JSON output
- Pydantic schemas and validation
- Business-rule validation
- Retry-based correction
- Multimodal image analysis
- Python function and tool calling
- Batch processing and CSV export
- Automated testing with pytest

## License

Add a license if you intend to distribute this project publicly.
'@ | Set-Content README.md -Encoding utf8
