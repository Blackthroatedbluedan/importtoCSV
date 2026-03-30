"""CLI: convert PDF, images, DXF/DWG to CSV."""

from __future__ import annotations

from pathlib import Path

import typer

from importtocsv.convert_core import ConvertOptions, convert_path_to_rows_or_raise
from importtocsv.csv_out import write_csv
from importtocsv.csv_search import search_csv_file, write_csv_subset

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


@app.command("search")
def search_csv(
    csv_path: Path = typer.Argument(..., exists=True, readable=True, help="CSV file produced by importtocsv"),
    query: str = typer.Argument(..., help="Substring to find in any cell (or use --column to limit)"),
    column: str | None = typer.Option(
        None,
        "--column",
        "-c",
        help="Only search this column name (must match CSV header)",
    ),
    case_sensitive: bool = typer.Option(False, "--case-sensitive", help="Match case"),
    out: Path | None = typer.Option(
        None,
        "--out",
        "-o",
        help="Write matching rows to this CSV (optional)",
    ),
    limit: int = typer.Option(50, "--limit", "-n", min=0, help="Max rows to print (0 = no limit)"),
) -> None:
    """Print CSV rows that contain QUERY in any cell (or in --column). Use to verify extracted data."""
    fieldnames, matched = search_csv_file(
        csv_path, query, column=column, case_sensitive=case_sensitive
    )
    typer.echo(f"Matches: {len(matched)} row(s) in {csv_path}")
    if not fieldnames:
        typer.echo("(No header row found.)", err=True)
        raise typer.Exit(1)
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="", encoding="utf-8") as f:
            write_csv_subset(fieldnames, matched, f)
        typer.echo(f"Wrote {len(matched)} row(s) to {out}")
    show = matched if limit == 0 else matched[:limit]
    for i, row in enumerate(show, start=1):
        parts = [f"{k}={row.get(k, '')!r}" for k in fieldnames if row.get(k)]
        typer.echo(f"  {i}. " + " | ".join(parts))
    if limit and len(matched) > limit:
        typer.echo(f"  … {len(matched) - limit} more (use --limit 0 to print all)")
