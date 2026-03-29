"""FastAPI web UI: upload a file, preview rows, download CSV."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from importtocsv.web_convert import read_upload_and_extract

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
) -> Response:
    rows, csv_text, filename = await read_upload_and_extract(
        file,
        password,
        ocr_lang,
        pdf_ocr_min_chars,
        pdf_ocr_dpi,
        pdf_ocr_max_lines,
        force_pdf_ocr,
    )
    base = Path(filename).stem or "export"
    out_name = f"{base}_extracted.csv"
    data = csv_text.encode("utf-8")

    return Response(
        content=data,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{out_name}"',
            "X-Row-Count": str(len(rows)),
        },
    )


@app.post("/api/convert-preview")
async def api_convert_preview(
    file: UploadFile = File(...),
    password: str | None = Form(None),
    ocr_lang: str = Form("eng"),
    pdf_ocr_min_chars: int = Form(80),
    pdf_ocr_dpi: int = Form(200),
    pdf_ocr_max_lines: int = Form(2),
    force_pdf_ocr: bool = Form(False),
    preview_limit: int = Form(80),
) -> Response:
    rows, csv_text, filename = await read_upload_and_extract(
        file,
        password,
        ocr_lang,
        pdf_ocr_min_chars,
        pdf_ocr_dpi,
        pdf_ocr_max_lines,
        force_pdf_ocr,
    )
    lim = max(1, min(500, preview_limit))
    preview_rows = rows[:lim]
    payload = {
        "filename": filename,
        "row_count": len(rows),
        "preview_limit": lim,
        "preview_truncated": len(rows) > lim,
        "columns": sorted({k for r in preview_rows for k in r.keys()}) if preview_rows else [],
        "rows": preview_rows,
        "csv": csv_text,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return Response(
        content=body,
        media_type="application/json; charset=utf-8",
        headers={
            "X-Row-Count": str(len(rows)),
        },
    )


def create_app() -> FastAPI:
    return app
