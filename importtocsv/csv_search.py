"""Search UTF-8 CSV rows for a substring (verify parsed data)."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any, Iterable


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Return header fieldnames and list of row dicts."""
    text = path.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    fieldnames = list(reader.fieldnames or [])
    rows = [dict(r) for r in reader]
    return fieldnames, rows


def row_matches(
    row: dict[str, str],
    query: str,
    *,
    column: str | None = None,
    case_sensitive: bool = False,
) -> bool:
    q = query if case_sensitive else query.lower()
    if column:
        if column not in row:
            return False
        val = row.get(column, "") or ""
        hay = val if case_sensitive else val.lower()
        return q in hay
    for val in row.values():
        s = val or ""
        hay = s if case_sensitive else s.lower()
        if q in hay:
            return True
    return False


def search_csv_rows(
    rows: Iterable[dict[str, str]],
    query: str,
    *,
    column: str | None = None,
    case_sensitive: bool = False,
) -> list[dict[str, str]]:
    if not query:
        return list(rows)
    return [r for r in rows if row_matches(r, query, column=column, case_sensitive=case_sensitive)]


def search_csv_file(
    path: Path,
    query: str,
    *,
    column: str | None = None,
    case_sensitive: bool = False,
) -> tuple[list[str], list[dict[str, str]]]:
    fieldnames, rows = read_csv_rows(path)
    matched = search_csv_rows(rows, query, column=column, case_sensitive=case_sensitive)
    return fieldnames, matched


def write_csv_subset(fieldnames: list[str], rows: list[dict[str, str]], out: Any) -> None:
    w = csv.DictWriter(out, fieldnames=fieldnames, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
