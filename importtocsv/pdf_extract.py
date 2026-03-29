"""Extract text and tables from PDFs (including password-protected)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pdfplumber


def extract_pdf_rows(path: Path, password: str | None = None) -> list[dict[str, Any]]:
    """
    Return rows suitable for CSV: one row per text block and per table cell cluster.
    Columns: source, page, kind, content, extra (JSON-serialized in writer).
    """
    rows: list[dict[str, Any]] = []
    kwargs: dict[str, Any] = {}
    if password:
        kwargs["password"] = password

    with pdfplumber.open(str(path), **kwargs) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                for line in text.splitlines():
                    line = line.strip()
                    if line:
                        rows.append(
                            {
                                "source": "pdf_text",
                                "page": page_num,
                                "kind": "line",
                                "content": line,
                            }
                        )

            tables = page.extract_tables() or []
            for t_idx, table in enumerate(tables, start=1):
                if not table:
                    continue
                for r_idx, row in enumerate(table, start=1):
                    cells = [str(c).strip() if c is not None else "" for c in row]
                    if not any(cells):
                        continue
                    rows.append(
                        {
                            "source": "pdf_table",
                            "page": page_num,
                            "kind": f"table_{t_idx}_row_{r_idx}",
                            "content": " | ".join(cells),
                        }
                    )

    return rows
