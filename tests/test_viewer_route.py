"""Viewer page is served."""

from __future__ import annotations

from fastapi.testclient import TestClient

from importtocsv.web_app import app


def test_viewer_page() -> None:
    c = TestClient(app)
    r = c.get("/viewer")
    assert r.status_code == 200
    assert "View CSV" in r.text
    assert "csv_parse.js" in r.text
