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
