"""FastAPI web UI: upload a file, download extracted CSV."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from importtocsv.convert_core import ConvertOptions, convert_path_to_rows_or_raise
from importtocsv.csv_out import write_csv

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="importtoCSV", description="Extract manuals and drawings to CSV")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    html_path = STATIC_DIR / "index.html"
    if html_path.is_file():
        return html_path.read_text(encoding="utf-8")
    return "<p>Missing static/index.html</p>"


@app.post("/api/convert")
async def api_convert(
    file: UploadFile = File(...),
    password: str | None = Form(None),
    ocr_lang: str = Form("eng"),
    pdf_ocr_min_chars: int = Form(80),
    pdf_ocr_dpi: int = Form(200),
    pdf_ocr_max_lines: int = Form(2),
    force_pdf_ocr: bool = Form(False),
) -> StreamingResponse:
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

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as out_tmp:
        out_path = Path(out_tmp.name)
    try:
        write_csv(rows, out_path)
        data = out_path.read_bytes()
    finally:
        out_path.unlink(missing_ok=True)
    base = Path(file.filename).stem or "export"
    out_name = f"{base}_extracted.csv"

    return StreamingResponse(
        iter([data]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{out_name}"',
            "X-Row-Count": str(len(rows)),
        },
    )


def create_app() -> FastAPI:
    return app
