"""Extract text and tables from PDFs (including password-protected)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pdfplumber
import pytesseract
from PIL import Image


def _ocr_page_image(page: Any, resolution: int, lang: str) -> list[dict[str, Any]]:
    """Render a PDF page to a bitmap and OCR line by line."""
    rows: list[dict[str, Any]] = []
    img = page.to_image(resolution=resolution).original
    if not isinstance(img, Image.Image):
        return rows
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    raw = pytesseract.image_to_string(img, lang=lang) or ""
    for line in raw.splitlines():
        line = line.strip()
        if line:
            rows.append(
                {
                    "source": "pdf_ocr",
                    "page": page.page_number,
                    "kind": "line",
                    "content": line,
                }
            )
    return rows


def extract_pdf_rows(
    path: Path,
    password: str | None = None,
    *,
    ocr_lang: str = "eng",
    ocr_resolution: int = 200,
    ocr_min_chars: int = 80,
    ocr_max_text_lines: int = 2,
    force_pdf_ocr: bool = False,
) -> list[dict[str, Any]]:
    """
    Return rows suitable for CSV: one row per text block and per table cell cluster.
    Scanned pages (little or no extractable text) are OCR'd via rendered page images.
    """
    rows: list[dict[str, Any]] = []
    kwargs: dict[str, Any] = {}
    if password:
        kwargs["password"] = password

    with pdfplumber.open(str(path), **kwargs) as pdf:
        for page in pdf.pages:
            page_num = page.page_number
            text = (page.extract_text() or "").strip()
            text_lines = len([ln for ln in text.splitlines() if ln.strip()])
            # True scans: almost no text layers but bitmaps; cover pages with a few
            # title lines stay on extract_text (avoid noisy full-page OCR).
            likely_scan = (
                bool(page.images)
                and len(text) < ocr_min_chars
                and text_lines <= ocr_max_text_lines
            )
            use_ocr = force_pdf_ocr or likely_scan

            if use_ocr:
                rows.extend(_ocr_page_image(page, ocr_resolution, ocr_lang))
                continue

            for line in text.splitlines():
                line = line.strip()
                if line:
                    rows.append(
                        {
                            "source": "pdf_text",
                            "page": page_num,
                            "kind": "line",
                            "content": line,
                        }
                    )

            tables = page.extract_tables() or []
            for t_idx, table in enumerate(tables, start=1):
                if not table:
                    continue
                for r_idx, row in enumerate(table, start=1):
                    cells = [str(c).strip() if c is not None else "" for c in row]
                    if not any(cells):
                        continue
                    rows.append(
                        {
                            "source": "pdf_table",
                            "page": page_num,
                            "kind": f"table_{t_idx}_row_{r_idx}",
                            "content": " | ".join(cells),
                        }
                    )

    return rows
