"""Write extracted rows to CSV."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable


def write_csv(rows: Iterable[dict[str, Any]], out_path: Path) -> None:
    rows = list(rows)
    if not rows:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("source,page,kind,content\n", encoding="utf-8")
        return

    fieldnames = sorted({k for r in rows for k in r.keys()})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
