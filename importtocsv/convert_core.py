"""Shared conversion logic for CLI and web UI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import ezdxf

from importtocsv.cad_extract import extract_cad_rows
from importtocsv.image_ocr import extract_image_rows
from importtocsv.pdf_extract import extract_pdf_rows


@dataclass
class ConvertOptions:
    password: str | None = None
    ocr_lang: str = "eng"
    pdf_ocr_min_chars: int = 80
    pdf_ocr_resolution: int = 200
    pdf_ocr_max_lines: int = 2
    force_pdf_ocr: bool = False


def convert_path_to_rows(path: Path, options: ConvertOptions | None = None) -> list[dict[str, Any]]:
    """Return extracted rows for a supported file type."""
    if options is None:
        options = ConvertOptions()

    suf = path.suffix.lower()
    if suf == ".pdf":
        return extract_pdf_rows(
            path,
            password=options.password,
            ocr_lang=options.ocr_lang,
            ocr_resolution=options.pdf_ocr_resolution,
            ocr_min_chars=options.pdf_ocr_min_chars,
            ocr_max_text_lines=options.pdf_ocr_max_lines,
            force_pdf_ocr=options.force_pdf_ocr,
        )
    if suf in (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"):
        return extract_image_rows(path, lang=options.ocr_lang)
    if suf in (".dxf", ".dwg"):
        return extract_cad_rows(path)
    raise ValueError(f"Unsupported file type: {suf!r}")


def convert_path_to_rows_or_raise(path: Path, options: ConvertOptions | None = None) -> list[dict[str, Any]]:
    """Like convert_path_to_rows but maps CAD errors to ValueError."""
    try:
        return convert_path_to_rows(path, options)
    except ezdxf.DXFStructureError as e:
        raise ValueError(f"CAD read failed: {e}") from e
