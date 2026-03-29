"""Web API smoke tests."""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

reportlab = pytest.importorskip("reportlab")

from importtocsv.web_app import app


def _tiny_pdf_bytes() -> bytes:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(100, 750, "Web test line alpha")
    c.save()
    return buf.getvalue()


def test_health() -> None:
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_convert_pdf() -> None:
    c = TestClient(app)
    data = _tiny_pdf_bytes()
    r = c.post(
        "/api/convert",
        files={"file": ("test.pdf", data, "application/pdf")},
        data={"ocr_lang": "eng"},
    )
    assert r.status_code == 200
    assert "Web test line alpha" in r.text
    assert r.headers.get("X-Row-Count") is not None


def test_convert_preview_json() -> None:
    c = TestClient(app)
    data = _tiny_pdf_bytes()
    r = c.post(
        "/api/convert-preview",
        files={"file": ("test.pdf", data, "application/pdf")},
        data={"ocr_lang": "eng", "preview_limit": "10"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["filename"] == "test.pdf"
    assert body["row_count"] >= 1
    assert "Web test line alpha" in body["csv"]
    assert len(body["rows"]) <= 10
    assert r.headers.get("X-Row-Count") == str(body["row_count"])
