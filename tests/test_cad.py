"""CAD extraction smoke test."""

from __future__ import annotations

import tempfile
from pathlib import Path

import ezdxf

from importtocsv.cad_extract import extract_cad_rows


def test_dxf_line_and_text() -> None:
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_line((0, 0), (1, 1))
    msp.add_text("Label", dxfattribs={"height": 1}).set_placement((0, 0))
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as f:
        p = Path(f.name)
    try:
        doc.saveas(p)
        rows = extract_cad_rows(p)
        kinds = {r["kind"] for r in rows}
        assert "LINE" in kinds
        assert any(r.get("content") == "Label" for r in rows)
    finally:
        p.unlink(missing_ok=True)
