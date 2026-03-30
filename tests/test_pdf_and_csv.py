"""Integration tests for PDF extraction and CSV writer."""

from __future__ import annotations

import csv
import tempfile
from pathlib import Path

import pytest

from importtocsv.csv_out import write_csv
from importtocsv.pdf_extract import extract_pdf_rows

reportlab = pytest.importorskip("reportlab")


def _minimal_pdf(path: Path) -> None:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=letter)
    c.drawString(100, 750, "Equipment Model X-100")
    c.showPage()
    c.save()


def test_pdf_extract_and_csv(tmp_path: Path) -> None:
    pdf = tmp_path / "manual.pdf"
    _minimal_pdf(pdf)
    rows = extract_pdf_rows(pdf)
    assert any("Equipment Model" in str(r.get("content", "")) for r in rows)

    out = tmp_path / "out.csv"
    write_csv(rows, out)
    with out.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        headers = r.fieldnames
        assert headers
        assert "content" in headers
        data = list(r)
    assert len(data) >= 1
