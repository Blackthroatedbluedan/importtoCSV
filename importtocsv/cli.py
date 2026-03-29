"""CLI: convert PDF, images, DXF/DWG to CSV."""

from __future__ import annotations

from pathlib import Path

import ezdxf
import typer

from importtocsv.cad_extract import extract_cad_rows
from importtocsv.csv_out import write_csv
from importtocsv.image_ocr import extract_image_rows
from importtocsv.pdf_extract import extract_pdf_rows

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
        help="If a PDF page has fewer extracted characters, render and OCR the page (scanned PDFs)",
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
    if suf == ".pdf":
        rows = extract_pdf_rows(
            input_path,
            password=password,
            ocr_lang=ocr_lang,
            ocr_resolution=pdf_ocr_resolution,
            ocr_min_chars=pdf_ocr_min_chars,
            ocr_max_text_lines=pdf_ocr_max_lines,
            force_pdf_ocr=force_pdf_ocr,
        )
    elif suf in (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"):
        rows = extract_image_rows(input_path, lang=ocr_lang)
    elif suf in (".dxf", ".dwg"):
        try:
            rows = extract_cad_rows(input_path)
        except ezdxf.DXFStructureError as e:
            typer.echo(f"CAD read failed (try converting DWG to DXF in CAD software): {e}", err=True)
            raise typer.Exit(1) from e
    else:
        typer.echo(
            f"Unsupported extension {suf!r}. Use .pdf, image formats, .dxf, or .dwg.",
            err=True,
        )
        raise typer.Exit(1)

    write_csv(rows, output_csv)
    typer.echo(f"Wrote {len(rows)} row(s) to {output_csv}")
