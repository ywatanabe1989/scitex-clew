#!/usr/bin/env python3
# Timestamp: "2026-06-12 (proj-paper-scitex-clew, op-2026-06-12-10)"
# File: src/scitex_clew/_overlay/_json_io.py
"""JSON import / export for overlays.

Round-trips an ``overlays.json`` sibling file using the convention
``{"<overlay_id>": {...overlay fields, no overlay_id}}``. Consumers can
write the file with ``Path("overlays.json").write_text(...)`` and read it
back without touching sqlite — useful for fixtures and for the writer-side
build path (which may not have DB access at render time).
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List

from ._models import Overlay


def overlays_to_json(overlays: Iterable[Overlay]) -> str:
    """Serialize an iterable of overlays to a pretty JSON string."""
    payload: Dict[str, Dict[str, Any]] = {}
    for ov in overlays:
        d = ov.to_dict()
        oid = d.pop("overlay_id")
        payload[oid] = d
    return json.dumps(payload, indent=2, sort_keys=True)


def overlays_from_json(text: str) -> List[Overlay]:
    """Parse the ``overlays.json`` schema back to :class:`Overlay` objects."""
    raw = json.loads(text)
    if not isinstance(raw, dict):
        raise ValueError("overlays.json must be a JSON object keyed by overlay_id")
    out: List[Overlay] = []
    for oid, body in raw.items():
        body = dict(body)
        body["overlay_id"] = oid
        out.append(Overlay.from_dict(body))
    return out


__all__ = [
    "overlays_to_json",
    "overlays_from_json",
]

# EOF
