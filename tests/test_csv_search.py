"""csv_search helpers and CLI search."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from importtocsv.cli import app
from importtocsv.csv_search import read_csv_rows, search_csv_file, search_csv_rows


def test_search_rows_column() -> None:
    rows = [
        {"a": "hello", "b": "world"},
        {"a": "foo", "b": "EVEREST"},
    ]
    m = search_csv_rows(rows, "EVER", column="b")
    assert len(m) == 1
    assert m[0]["a"] == "foo"


def test_search_rows_all_columns() -> None:
    rows = [{"x": "1", "y": "alpha"}]
    assert len(search_csv_rows(rows, "alp")) == 1
    assert len(search_csv_rows(rows, "beta")) == 0


def test_search_csv_file_tmp(tmp_path: Path) -> None:
    p = tmp_path / "t.csv"
    p.write_text("source,content\npdf_text,Bin model E4\npdf_text,other\n", encoding="utf-8")
    fn, m = search_csv_file(p, "E4")
    assert fn == ["source", "content"]
    assert len(m) == 1


def test_cli_search(tmp_path: Path) -> None:
    p = tmp_path / "out.csv"
    p.write_text("content,kind\nhello world,line\nfoo,line\n", encoding="utf-8")
    runner = CliRunner()
    r = runner.invoke(app, ["search", str(p), "world"])
    assert r.exit_code == 0
    assert "Matches: 1" in r.output
    assert "hello world" in r.output
