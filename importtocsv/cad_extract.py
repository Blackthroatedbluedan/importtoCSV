"""Extract entity summaries from DXF/DWG via ezdxf."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import ezdxf


def _fmt_point(p: Any) -> str:
    if p is None:
        return ""
    try:
        return f"{float(p.x):.4f},{float(p.y):.4f},{float(p.z):.4f}"
    except Exception:
        return str(p)


def extract_cad_rows(path: Path) -> list[dict[str, Any]]:
    """
    Export a flat list of entities with type, layer, and key geometry/text.
    Good for LLM search over drawings; not a full geometry reconstruction.
    """
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    rows: list[dict[str, Any]] = []

    for i, entity in enumerate(msp):
        dxftype = entity.dxftype()
        layer = getattr(entity.dxf, "layer", "")
        row: dict[str, Any] = {
            "source": "cad",
            "page": 1,
            "kind": dxftype,
            "content": "",
            "layer": layer,
            "entity_index": i + 1,
        }

        if dxftype == "LINE":
            row["content"] = (
                f"from {_fmt_point(entity.dxf.start)} to {_fmt_point(entity.dxf.end)}"
            )
        elif dxftype == "CIRCLE":
            row["content"] = (
                f"center {_fmt_point(entity.dxf.center)} r={entity.dxf.radius:.4f}"
            )
        elif dxftype == "ARC":
            row["content"] = (
                f"center {_fmt_point(entity.dxf.center)} r={entity.dxf.radius:.4f} "
                f"start={entity.dxf.start_angle:.4f} end={entity.dxf.end_angle:.4f}"
            )
        elif dxftype == "LWPOLYLINE":
            pts = list(entity.get_points("xy"))
            row["content"] = f"vertices={len(pts)} closed={entity.closed}"
            if pts:
                row["content"] += f" first={pts[0]}"
        elif dxftype == "TEXT":
            row["content"] = str(entity.dxf.text or "")
        elif dxftype == "MTEXT":
            row["content"] = entity.plain_text() or ""
        elif dxftype == "INSERT":
            row["content"] = f"block={entity.dxf.name} at {_fmt_point(entity.dxf.insert)}"
        else:
            row["content"] = repr(entity)[:500]

        rows.append(row)

    return rows
