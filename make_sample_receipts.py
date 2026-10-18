"""Generate 5 sample receipt images for testing vision and batch mode.

The stores are fictional. Replace or add real receipt photos in
images/receipts/ for a real-world test.
"""

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUTPUT_DIR = Path("images/receipts")

RECEIPTS = [
    {
        "file": "receipt_01_grocery.png",
        "vendor": "GREEN VALLEY MART",
        "address": "12 Mall Road, Lahore",
        "date": "2026-10-03",
        "currency": "PKR",
        "items": [("Basmati Rice 5kg", 1, 1850.00), ("Milk 1L", 3, 260.00),
                  ("Eggs (dozen)", 2, 420.00), ("Bread", 1, 180.00)],
    },
    {
        "file": "receipt_02_cafe.png",
        "vendor": "BEAN THERE COFFEE",
        "address": "48 Market St, London",
        "date": "2026-09-27",
        "currency": "GBP",
        "items": [("Flat White", 2, 3.40), ("Croissant", 2, 2.75),
                  ("Bottled Water", 1, 1.50)],
    },
    {
        "file": "receipt_03_electronics.png",
        "vendor": "CIRCUIT TECH STORE",
        "address": "301 Main Ave, Austin TX",
        "date": "2026-10-10",
        "currency": "USD",
        "items": [("USB-C Cable", 2, 12.99), ("Wireless Mouse", 1, 24.50),
                  ("Laptop Stand", 1, 39.00)],
    },
    {
        "file": "receipt_04_office.png",
        "vendor": "PAPER & PEN SUPPLIES",
        "address": "7 Blue Area, Islamabad",
        "date": "2026-10-01",
        "currency": "PKR",
        "items": [("A4 Paper Ream", 2, 1450.00), ("Gel Pens (10)", 1, 650.00),
                  ("Stapler", 1, 900.00)],
    },
    {
        "file": "receipt_05_restaurant.png",
        "vendor": "LA PIAZZA RESTAURANT",
        "address": "22 Via Roma, Berlin",
        "date": "2026-09-20",
        "currency": "EUR",
        "items": [("Margherita Pizza", 1, 11.50), ("Pasta Carbonara", 1, 13.90),
                  ("Lemonade", 2, 3.80)],
    },
]


def load_font(size, bold=False):
    names = ["consolab.ttf" if bold else "consola.ttf", "cour.ttf",
             "DejaVuSansMono.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_receipt(receipt):
    width = 520
    line_height = 30
    lines = 14 + len(receipt["items"])
    height = 80 + lines * line_height

    paper = Image.new("RGB", (width, height), (250, 248, 240))
    draw = ImageDraw.Draw(paper)
    regular = load_font(20)
    bold = load_font(26, bold=True)
    y = 30

    def center(text, font):
        nonlocal y
        text_width = draw.textlength(text, font=font)
        draw.text(((width - text_width) / 2, y), text, fill="black", font=font)
        y += line_height + 4

    def row(left, right="", font=regular):
        nonlocal y
        draw.text((30, y), left, fill="black", font=font)
        if right:
            right_width = draw.textlength(right, font=font)
            draw.text((width - 30 - right_width, y), right,
                      fill="black", font=font)
        y += line_height

    center(receipt["vendor"], bold)
    center(receipt["address"], regular)
    row(f"Date: {receipt['date']}")
    row("-" * 38)

    total = 0.0
    for name, quantity, price in receipt["items"]:
        amount = quantity * price
        total += amount
        row(name)
        row(f"  {quantity} x {price:.2f}", f"{amount:.2f}")

    row("-" * 38)
    row("TOTAL", f"{receipt['currency']} {total:.2f}", font=bold)
    y += 10
    center("Thank you for shopping!", regular)

    return paper, round(total, 2)


def photograph(paper, seed):
    """Make the receipt look like a phone photo: tilt, background, noise."""
    rng = random.Random(seed)
    tilted = paper.rotate(rng.uniform(-4, 4), expand=True,
                          fillcolor=(90, 80, 70))
    background = Image.new(
        "RGB",
        (tilted.width + 120, tilted.height + 120),
        (90, 80, 70),
    )
    background.paste(tilted, (60, 60))

    noise = Image.effect_noise(background.size, 18).convert("RGB")
    photo = Image.blend(background, noise, 0.06)
    return photo.filter(ImageFilter.GaussianBlur(0.6))


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for index, receipt in enumerate(RECEIPTS, start=1):
        paper, total = draw_receipt(receipt)
        path = OUTPUT_DIR / receipt["file"]
        photograph(paper, seed=index).save(path)
        print(f"Saved {path} ({receipt['currency']} {total:.2f})")


if __name__ == "__main__":
    main()
