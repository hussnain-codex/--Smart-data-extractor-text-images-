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
- **Receipt extraction:** Send receipt images to Gemini through LangChain and validate them with the shared `Invoice` schema.
- **Python tool calling:** Allow the language model to invoke Python functions for currency conversion, expense categorization, invoice calculations, and date checks.
- **Conversation context:** Keep earlier text turns in memory until the interactive tool-calling session exits.
- **Batch image processing:** Process every receipt image in the `images/receipts/` folder.
- **CSV export:** Save batch receipt results, including errors, to `image_results.csv`.
- **Web UI:** Upload an image in a small Streamlit page and see the extracted JSON.
- **Provider comparison:** Benchmark Groq, Google Gemini, and local Ollama on the same 10 invoices.

## Technology Stack

- Python
- Pydantic
- LangChain
- LangChain Google Gemini integration
- LangChain Ollama integration
- Groq API
- Google Gemini API
- Ollama (local models)
- Pillow
- Streamlit
- Pytest

## Project Structure

```text
Smart Data Extractor/
|
|-- images/                       # Input images
|   |-- receipts/                 # Receipt images for batch mode
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
|-- make_sample_receipts.py       # Generates 5 sample receipt images
|-- streamlit_app.py              # Upload-an-image web UI
|
|-- tools.py                      # Python functions available as tools
|-- tool_calling.py               # LLM tool-calling workflow
|
|-- sample_invoices.py            # 10 invoice texts with expected answers
|-- compare_providers.py          # Groq vs Gemini vs Ollama benchmark
|-- provider_comparison.json      # Latest benchmark results
|
|-- test_gemini.py                # Manual Gemini connectivity check
|-- pytest.ini                    # Limits pytest to tests/
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
GEMINI_MODEL=gemini-3.5-flash
GEMINI_FALLBACK_MODELS=gemini-3.8-flash
```

Use valid API keys and a Gemini model supported by your account.
Image extraction tries `GEMINI_MODEL` first, then each model in the
comma-separated `GEMINI_FALLBACK_MODELS` list:

- `503` overload, timeouts, and network errors are retried on the same model
  with growing waits (about 5s, then 15s), then the next model is tried.
- `429` quota or rate limit and `404` unavailable model switch straight to the
  next model, because retrying them only wastes requests.
- Other client errors, such as an invalid API key, stop immediately.

Free-tier quotas are counted per model, so a fallback model often still works
when the primary model's daily quota is used up.

`python test_gemini.py` is a manual connectivity check that sends a real
request. Pytest only collects the `tests/` folder (see `pytest.ini`), so
running the unit tests never uses Gemini quota.

Groq is not an automatic image fallback because the configured Groq model is
used for text and tool calling.

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

The general image extractor analyzes the image and saves structured output to
`image_result.json`. For receipts, `tool_calling.py` and batch mode extract and
validate data with the shared `Invoice` schema.

Supported image formats include JPG, JPEG, PNG, WEBP, BMP, TIF, and TIFF.

### 5. Batch image extraction

Put receipt photos in `images/receipts/`. To create 5 sample receipts
(fictional stores, tilted and lightly blurred to look like phone photos), run:

```powershell
python make_sample_receipts.py
```

Then run the batch extractor (an optional argument picks another folder):

```powershell
python batch_image_extractor.py
python batch_image_extractor.py images/other_folder
```

The batch processor is for receipt/invoice images and:

1. Finds supported image files.
2. Extracts each image using Gemini and the shared `Invoice` schema.
3. Records successful results and failures.
4. Writes the results to `image_results.csv`.
5. Prints a summary of successful and failed images.

The CSV contains the filename, status, vendor, invoice date, line items, total,
currency, and error message.

### 6. Python tool calling

Run:

```powershell
python tool_calling.py
```

Enter a question involving currency conversion, expense categorization, invoice
calculations, or invoice date validation.

The language model can select from these Python tools:

- `convert_currency` — converts between USD, PKR, EUR, and GBP using example fixed rates.
- `categorize_expense` — assigns a basic category using vendor-name keywords.
- `calculate_invoice_total` - calculates the total from invoice line items.
- `check_invoice_date` - checks the date format and whether the invoice date is in the future.

The tool-calling workflow executes requested functions and passes their results
back to the model. Example exchange rates and vendor categories are not live
financial data. Conversation context lasts until the program exits.

### 7. Streamlit web UI

```powershell
streamlit run streamlit_app.py
```

Upload an image, choose **Invoice / receipt** or **Any image**, and click
**Extract** to see the JSON.

### Provider comparison

`compare_providers.py` sends the same 10 invoice texts (`sample_invoices.py`)
to three providers through `with_structured_output(Invoice)`. It checks five
fields per invoice against the known answer: vendor, date, line items, total,
and currency.

```powershell
python compare_providers.py
```

Results from 2026-10-18:

| Provider | Model | Valid outputs | Field accuracy | Avg latency | Median latency |
|---|---|---:|---:|---:|---:|
| Groq | `openai/gpt-oss-20b` | 10/10 | 100.0% | 1.04s | 0.98s |
| Google Gemini | `gemini-3.5-flash-lite` | 10/10 | 100.0% | 1.09s | 1.05s |
| Ollama (local) | `qwen2.5:1.5b` | 9/10 | 90.0% | 7.29s | 5.73s |

- **Groq and Gemini** were equally accurate and about equally fast on these
  simple invoices.
- **Ollama** is free and runs offline, but the 1.5B model was about 7x slower on
  this machine. It dropped a line item on invoice 10; the business-rule
  validator caught the resulting total mismatch instead of accepting bad data.
- Latency depends on network, provider load, and local hardware, so re-run the
  script for current numbers. Models can be changed with `GROQ_MODEL`,
  `COMPARE_GEMINI_MODEL`, and `OLLAMA_MODEL`.

## Automated Testing

Run the offline test suite (no paid API requests are made):

```powershell
python -m pytest tests -v
```

The suite includes tests covering:

- Pydantic schema validation
- Invoice business rules
- Validation and retry behavior
- Image extraction and error handling
- Gemini vision message encoding and image resizing
- Currency conversion and expense categorization
- Tool-calling conversation context
- Batch receipt CSV fields and per-image errors

Some tests use mocked responses, so passing tests does not guarantee that the
external APIs are currently available.

## Error Handling

The project handles several expected failures, including:

- Missing or invalid image files
- Invalid model output
- Invoice validation errors
- Repeated image API failures
- Temporary Gemini 503 service failures (retried with backoff, then the next fallback model is tried)
- Gemini 429 rate limits/quota exhaustion and 404 retired models (skipped straight to the next fallback model)
- Groq rate limits and API errors in the tool-calling loop (reported, and the session continues)
- Individual failures during batch processing

A failed image analysis is recorded in the batch CSV, allowing processing to continue with other images.

External API availability, rate limits, network timeouts, and model access can still affect live extraction.
For example, a Gemini `503 UNAVAILABLE` response means its remote model service
is overloaded or unavailable.
A `429 RESOURCE_EXHAUSTED` response means the model's request rate or daily
free-tier quota has been reached. In both cases the extractor moves on to the
models in `GEMINI_FALLBACK_MODELS`; if every model fails, it reports the reason
for each one.

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
