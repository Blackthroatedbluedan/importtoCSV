"""CLI: convert PDF, images, DXF/DWG to CSV."""

from __future__ import annotations

from pathlib import Path

import typer

from importtocsv.convert_core import ConvertOptions, convert_path_to_rows_or_raise
from importtocsv.csv_out import write_csv

app = typer.Typer(no_args_is_help=True, help="Convert manuals and drawings to CSV for LLMs.")


def _suffix(path: Path) -> str:
    return path.suffix.lower()


@app.command()
def convert(
    input_path: Path = typer.Argument(..., exists=True, readable=True, help="PDF, image, .dxf, or .dwg"),
    output_csv: Path = typer.Argument(..., help="Output .csv path"),
    password: str | None = typer.Option(
        None,
        "--password",
        "-p",
        help="PDF password (encrypted / owner-restricted PDFs)",
    ),
    ocr_lang: str = typer.Option(
        "eng",
        "--ocr-lang",
        help="Tesseract language(s), e.g. eng or eng+deu",
    ),
    pdf_ocr_min_chars: int = typer.Option(
        80,
        "--pdf-ocr-min-chars",
        help="If a PDF page has fewer extracted characters, consider it for OCR (with images)",
        min=0,
    ),
    pdf_ocr_resolution: int = typer.Option(
        200,
        "--pdf-ocr-dpi",
        help="Render resolution (DPI) for PDF page OCR when text extraction is thin",
        min=72,
        max=600,
    ),
    pdf_ocr_max_lines: int = typer.Option(
        2,
        "--pdf-ocr-max-lines",
        help="OCR a page only if extractable text has at most this many non-empty lines (scanned PDF heuristic)",
        min=0,
        max=50,
    ),
    force_pdf_ocr: bool = typer.Option(
        False,
        "--force-pdf-ocr",
        help="Always OCR every PDF page (ignore embedded text)",
    ),
) -> None:
    """Detect file type and write a UTF-8 CSV of extracted content."""
    suf = _suffix(input_path)
    if suf not in {
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
        typer.echo(
            f"Unsupported extension {suf!r}. Use .pdf, image formats, .dxf, or .dwg.",
            err=True,
        )
        raise typer.Exit(1)

    opts = ConvertOptions(
        password=password,
        ocr_lang=ocr_lang,
        pdf_ocr_min_chars=pdf_ocr_min_chars,
        pdf_ocr_resolution=pdf_ocr_resolution,
        pdf_ocr_max_lines=pdf_ocr_max_lines,
        force_pdf_ocr=force_pdf_ocr,
    )
    try:
        rows = convert_path_to_rows_or_raise(input_path, opts)
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e

    write_csv(rows, output_csv)
    typer.echo(f"Wrote {len(rows)} row(s) to {output_csv}")
