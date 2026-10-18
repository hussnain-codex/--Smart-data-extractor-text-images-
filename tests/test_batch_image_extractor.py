import csv
from datetime import date
from pathlib import Path

from PIL import Image

import batch_image_extractor
from schemas import Invoice, LineItem


def test_batch_writes_invoice_rows_and_records_failures(
    tmp_path,
    monkeypatch,
):
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    Image.new("RGB", (10, 10), color="white").save(image_dir / "success.png")
    Image.new("RGB", (10, 10), color="white").save(image_dir / "failure.png")
    output_file = tmp_path / "results.csv"
    monkeypatch.setattr(batch_image_extractor, "IMAGE_DIR", image_dir)
    monkeypatch.setattr(batch_image_extractor, "OUTPUT_FILE", output_file)

    def extract(image_path):
        if Path(image_path).name == "failure.png":
            raise RuntimeError("temporary model error")
        return Invoice(
            vendor="ABC Store",
            invoice_date=date.today(),
            items=[LineItem(name="Milk", quantity=2, price=250)],
            total=500,
            currency="PKR",
        )

    monkeypatch.setattr(
        batch_image_extractor,
        "extract_invoice_from_image",
        extract,
    )

    batch_image_extractor.batch_extract()

    with output_file.open(newline="", encoding="utf-8-sig") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert [row["status"] for row in rows] == ["failed", "success"]
    assert rows[1]["vendor"] == "ABC Store"
    assert rows[1]["invoice_date"] == date.today().isoformat()
    assert rows[1]["items"] == "Milk (qty 2 x 250.00)"
    assert rows[1]["total"] == "500.00"
    assert rows[1]["currency"] == "PKR"
    assert "temporary model error" in rows[0]["error"]


def test_batch_reads_folder_passed_as_argument(tmp_path, monkeypatch):
    image_dir = tmp_path / "custom"
    image_dir.mkdir()
    Image.new("RGB", (10, 10), color="white").save(image_dir / "a.png")
    output_file = tmp_path / "results.csv"
    monkeypatch.setattr(batch_image_extractor, "OUTPUT_FILE", output_file)
    seen = []

    def extract(image_path):
        seen.append(Path(image_path).name)
        raise RuntimeError("not needed")

    monkeypatch.setattr(
        batch_image_extractor, "extract_invoice_from_image", extract
    )

    batch_image_extractor.batch_extract(image_dir)

    assert seen == ["a.png"]
    assert output_file.is_file()
