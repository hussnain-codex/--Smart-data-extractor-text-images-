# Smart Data Extractor — Experiment Notes

## Step 1: Pydantic Schemas

Created Pydantic models for:

* Invoice
* LineItem
* JobPost

These schemas define the expected structure and types of extracted data.

## Step 2: Naive JSON Extraction

* Total test inputs: 10
* Successful extractions: 10
* Failed extractions: 0
* Failure rate: 0%

The naive approach asks the LLM to return JSON and uses Python's `json.loads()` to parse the response.

## Step 3: Structured Output

* Total test inputs: 10
* Successful extractions: 10
* Failed extractions: 0
* Failure rate: 0%

The structured approach uses LangChain's `with_structured_output(Invoice)` and a Pydantic schema to validate the extracted invoice data.

## Comparison

| Metric       | Naive Extraction | Structured Extraction |
| ------------ | ---------------: | --------------------: |
| Total tests  |               10 |                    10 |
| Successful   |               10 |                    10 |
| Failed       |                0 |                     0 |
| Failure rate |               0% |                    0% |

## Conclusion

Both approaches achieved a 0% failure rate on the 10 invoice test inputs. Structured extraction offers schema-based validation and typed data, making it a useful foundation for further validation.

Note: This is a small test set. Additional tests with malformed or ambiguous invoices are needed to evaluate reliability more thoroughly.

## Latest local verification

* Offline automated test suite: 62 passed, 1 dependency deprecation warning.
* Tests mock model responses; they do not make Groq or Gemini API requests. `pytest.ini` limits collection to `tests/`, so the manual `test_gemini.py` script no longer runs (and spends quota) during `pytest`.
* Re-run of Steps 2 and 3 on Groq: naive 0% failures, structured 0% failures. Before switching `with_structured_output` to `method="json_schema"`, structured extraction failed 1/10 (10%) with Groq `400 tool_use_failed`: the model answered in plain text instead of calling the schema tool.
* Step 4 retry: an invoice whose items do not add up to its total, and an invoice dated in the future, are now rejected after 2 retries. With the earlier retry prompt the LLM "fixed" them by inventing a different date and total, so the prompt now tells it to correct extraction mistakes only.
* Step 6 tool calling: "Convert 5000 PKR to USD and categorize Fresh Mart" called `convert_currency` (17.99) and `categorize_expense` (groceries).
* Gemini free tier: `gemini-3.5-flash` often returns `503 UNAVAILABLE` (high demand), and each model allows about 20 requests per day (`429 RESOURCE_EXHAUSTED`). Image extraction now retries 503s with backoff, skips 429/404 models without retrying, and falls back through `GEMINI_FALLBACK_MODELS`. `gemini-3.5-flash-lite` completed the sample image analysis.

## Step 5 and 7: Vision and batch mode (2026-10-18)

* `make_sample_receipts.py` generated 5 receipt images (fictional stores, PKR/GBP/USD/EUR, tilted and blurred to look like phone photos) in `images/receipts/`.
* `python batch_image_extractor.py`: 5/5 receipts extracted with every vendor, date, line item, total, and currency correct; `image_results.csv` written.
* During the run `gemini-3.5-flash` returned 503 twice (retried successfully) and then 429; the last receipt fell back to `gemini-3.5-flash-lite`.

## Step 8: Streamlit UI

* `streamlit run streamlit_app.py` serves an upload page (invoice/receipt or general image mode) that shows the extracted JSON. The page renders without errors and the server health check returns `ok`.

## Provider comparison (2026-10-18)

Same 10 invoice texts, `with_structured_output(Invoice)`, 5 fields checked per invoice:

| Provider | Model | Valid outputs | Field accuracy | Avg latency |
|---|---|---:|---:|---:|
| Groq | `openai/gpt-oss-20b` | 10/10 | 100% | 1.04s |
| Google Gemini | `gemini-3.5-flash-lite` | 10/10 | 100% | 1.09s |
| Ollama (local) | `qwen2.5:1.5b` | 9/10 | 90% | 7.29s |

The Ollama failure: the 1.5B model dropped the "Eggs" line item on invoice 10, and the total-matches-items validator rejected it.
