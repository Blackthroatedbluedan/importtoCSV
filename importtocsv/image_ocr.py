"""OCR for screenshots and scanned pages."""

from __future__ import annotations

from pathlib import Path

from PIL import Image
import pytesseract


def extract_image_rows(path: Path, lang: str = "eng") -> list[dict[str, object]]:
    """Return one row per non-empty line of OCR text."""
    img = Image.open(path)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    text = pytesseract.image_to_string(img, lang=lang) or ""
    rows: list[dict[str, object]] = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            rows.append(
                {
                    "source": "image_ocr",
                    "page": 1,
                    "kind": "line",
                    "content": line,
                }
            )
    return rows
