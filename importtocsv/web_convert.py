"""Shared multipart handling for convert endpoints."""

from __future__ import annotations

import csv
import io
import tempfile
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile

from importtocsv.convert_core import ConvertOptions, convert_path_to_rows_or_raise


async def read_upload_and_extract(
    file: UploadFile,
    password: str | None,
    ocr_lang: str,
    pdf_ocr_min_chars: int,
    pdf_ocr_dpi: int,
    pdf_ocr_max_lines: int,
    force_pdf_ocr: bool,
) -> tuple[list[dict[str, Any]], str, str]:
    """
    Validate upload, run extraction, return rows and UTF-8 CSV text.
    """
    if not file.filename:
        raise HTTPException(400, "No filename")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".tif",
        ".tiff",
        ".bmp",
        ".webp",
        ".dxf",
        ".dwg",
    }:
        raise HTTPException(400, f"Unsupported type {suffix!r}")

    raw = await file.read()
    if not raw:
        raise HTTPException(400, "Empty file")

    opts = ConvertOptions(
        password=password or None,
        ocr_lang=ocr_lang.strip() or "eng",
        pdf_ocr_min_chars=max(0, pdf_ocr_min_chars),
        pdf_ocr_resolution=max(72, min(600, pdf_ocr_dpi)),
        pdf_ocr_max_lines=max(0, min(50, pdf_ocr_max_lines)),
        force_pdf_ocr=force_pdf_ocr,
    )

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(raw)
        tmp_path = Path(tmp.name)

    try:
        rows = convert_path_to_rows_or_raise(tmp_path, opts)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    finally:
        tmp_path.unlink(missing_ok=True)

    csv_text = _rows_to_csv_text(rows)
    return rows, csv_text, file.filename


def _rows_to_csv_text(rows: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    if not rows:
        buf.write("source,page,kind,content\n")
        return buf.getvalue()
    fieldnames = sorted({k for r in rows for k in r.keys()})
    w = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()
