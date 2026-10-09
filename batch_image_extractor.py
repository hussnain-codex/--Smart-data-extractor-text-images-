
import csv
from pathlib import Path

from image_extractor import analyze_image


IMAGE_DIR = Path("images")
OUTPUT_FILE = Path("image_results.csv")

SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"
}


def batch_extract():
    if not IMAGE_DIR.is_dir():
        print(f"Image folder not found: {IMAGE_DIR.resolve()}")
        return

    image_paths = sorted(
        path for path in IMAGE_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not image_paths:
        print(f"No supported images found in {IMAGE_DIR.resolve()}")
        return

    results = []

    for index, image_path in enumerate(image_paths, start=1):
        print(f"\n[{index}/{len(image_paths)}] Analyzing {image_path.name}")

        try:
            analysis = analyze_image(str(image_path))

            results.append({
                "filename": image_path.name,
                "status": "success",
                "image_type": analysis.image_type,
                "description": analysis.description,
                "detected_text": " | ".join(analysis.detected_text),
                "objects": " | ".join(analysis.objects),
                "key_details": "; ".join(
                    f"{key}: {value}"
                    for key, value in analysis.key_details.items()
                ),
                "error": "",
            })

            print(f"Detected type: {analysis.image_type}")

        except Exception as error:
            results.append({
                "filename": image_path.name,
                "status": "failed",
                "image_type": "",
                "description": "",
                "detected_text": "",
                "objects": "",
                "key_details": "",
                "error": f"{type(error).__name__}: {error}",
            })

            print(f"Failed: {type(error).__name__}: {error}")

    fieldnames = [
        "filename",
        "status",
        "image_type",
        "description",
        "detected_text",
        "objects",
        "key_details",
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
    batch_extract()