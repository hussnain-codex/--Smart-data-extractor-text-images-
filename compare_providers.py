"""Compare speed and quality of Groq, Gemini, and local Ollama.

Each provider extracts the same 10 invoice texts into the Invoice schema.
Run: python compare_providers.py
Results are printed as a Markdown table and saved to provider_comparison.json.
"""

import json
import os
import statistics
import time
from pathlib import Path

from dotenv import load_dotenv

from sample_invoices import EXPECTED, INVOICE_TEXTS
from schemas import Invoice

load_dotenv()

RESULTS_FILE = Path("provider_comparison.json")


def groq_extractor():
    from langchain_groq import ChatGroq

    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    llm = ChatGroq(model=model, temperature=0)
    return model, llm.with_structured_output(Invoice, method="json_schema")


def gemini_extractor():
    from langchain_google_genai import ChatGoogleGenerativeAI

    model = os.getenv("COMPARE_GEMINI_MODEL", "gemini-3.5-flash-lite")
    llm = ChatGoogleGenerativeAI(
        model=model,
        temperature=0,
        api_key=os.getenv("GEMINI_API_KEY"),
        retries=0,
    )
    return model, llm.with_structured_output(Invoice)


def ollama_extractor():
    from langchain_ollama import ChatOllama

    model = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
    llm = ChatOllama(model=model, temperature=0)
    return model, llm.with_structured_output(Invoice, method="json_schema")


PROVIDERS = {
    "Groq": groq_extractor,
    "Google Gemini": gemini_extractor,
    "Ollama (local)": ollama_extractor,
}


def score(invoice: Invoice, expected) -> tuple[int, int]:
    """Return (correct checks, total checks) against the expected answer."""
    vendor, invoice_date, items, total, currency = expected
    extracted_items = sorted(
        (item.quantity, round(item.price, 2)) for item in invoice.items
    )
    checks = [
        invoice.vendor.strip().casefold() == vendor.casefold(),
        invoice.invoice_date == invoice_date,
        extracted_items == sorted(items),
        abs(invoice.total - total) < 0.01,
        invoice.currency.strip().upper() == currency,
    ]
    return sum(checks), len(checks)


def run_provider(name, factory):
    print(f"\n--- {name} ---")
    model, extractor = factory()
    latencies = []
    successes = 0
    correct = 0
    possible = 0
    errors = []

    for index, (text, expected) in enumerate(
        zip(INVOICE_TEXTS, EXPECTED), start=1
    ):
        possible += 5
        start = time.perf_counter()
        try:
            invoice = extractor.invoke(text)
            latencies.append(time.perf_counter() - start)
            successes += 1
            right, _ = score(invoice, expected)
            correct += right
            print(f"Test {index}: OK ({right}/5 fields correct)")
        except Exception as error:  # count any provider failure
            message = f"{type(error).__name__}: {str(error)[:150]}"
            errors.append(f"Test {index}: {message}")
            print(f"Test {index}: FAILED {message}")

    return {
        "provider": name,
        "model": model,
        "valid_outputs": successes,
        "total": len(INVOICE_TEXTS),
        "field_accuracy": round(100 * correct / possible, 1),
        "avg_latency_s": round(statistics.mean(latencies), 2)
        if latencies else None,
        "median_latency_s": round(statistics.median(latencies), 2)
        if latencies else None,
        "errors": errors,
    }


def markdown_table(results) -> str:
    lines = [
        "| Provider | Model | Valid outputs | Field accuracy "
        "| Avg latency | Median latency |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in results:
        avg = f"{r['avg_latency_s']:.2f}s" if r["avg_latency_s"] else "n/a"
        median = (
            f"{r['median_latency_s']:.2f}s" if r["median_latency_s"] else "n/a"
        )
        lines.append(
            f"| {r['provider']} | `{r['model']}` "
            f"| {r['valid_outputs']}/{r['total']} "
            f"| {r['field_accuracy']:.1f}% | {avg} | {median} |"
        )
    return "\n".join(lines)


def main():
    results = []
    for name, factory in PROVIDERS.items():
        try:
            results.append(run_provider(name, factory))
        except Exception as error:  # e.g. missing key or Ollama not running
            print(f"Skipping {name}: {type(error).__name__}: {error}")

    RESULTS_FILE.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print("\n" + markdown_table(results))
    print(f"\nSaved to {RESULTS_FILE.resolve()}")


if __name__ == "__main__":
    main()
