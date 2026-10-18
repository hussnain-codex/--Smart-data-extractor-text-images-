import csv
import sys
from pathlib import Path

from image_extractor import extract_invoice_from_image


IMAGE_DIR = Path("images/receipts")
OUTPUT_FILE = Path("image_results.csv")

SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"
}


def batch_extract(image_dir: Path | None = None):
    image_dir = Path(image_dir) if image_dir else IMAGE_DIR

    if not image_dir.is_dir():
        print(f"Image folder not found: {image_dir.resolve()}")
        return

    image_paths = sorted(
        path for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not image_paths:
        print(f"No supported images found in {image_dir.resolve()}")
        return

    results = []

    for index, image_path in enumerate(image_paths, start=1):
        print(f"\n[{index}/{len(image_paths)}] Analyzing {image_path.name}")

        try:
            invoice = extract_invoice_from_image(str(image_path))

            results.append({
                "filename": image_path.name,
                "status": "success",
                "vendor": invoice.vendor,
                "invoice_date": invoice.invoice_date.isoformat(),
                "items": " | ".join(
                    f"{item.name} (qty {item.quantity} x {item.price:.2f})"
                    for item in invoice.items
                ),
                "total": f"{invoice.total:.2f}",
                "currency": invoice.currency,
                "error": "",
            })

            print(f"Extracted invoice for: {invoice.vendor}")

        except (OSError, RuntimeError, ValueError) as error:
            results.append({
                "filename": image_path.name,
                "status": "failed",
                "vendor": "",
                "invoice_date": "",
                "items": "",
                "total": "",
                "currency": "",
                "error": f"{type(error).__name__}: {error}",
            })

            print(f"Failed: {type(error).__name__}: {error}")

    fieldnames = [
        "filename",
        "status",
        "vendor",
        "invoice_date",
        "items",
        "total",
        "currency",
        "error",
    ]

    with OUTPUT_FILE.open(
        "w", newline="", encoding="utf-8-sig"
    ) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    successful = sum(
        result["status"] == "success" for result in results
    )
    failed = len(results) - successful

    print("\n=== BATCH PROCESSING COMPLETE ===")
    print(f"Total images: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"CSV saved to: {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    # Optional folder argument: python batch_image_extractor.py images/other
    batch_extract(sys.argv[1] if len(sys.argv) > 1 else None)