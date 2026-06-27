#!/usr/bin/env python3
# Timestamp: "2026-06-27 (ywatanabe)"
"""Claims formatting for terminal display."""

from __future__ import annotations

from pathlib import Path
from typing import List

from ._types import Claim


def format_claims(claims: List[Claim], verbose: bool = False) -> str:
    """Format claims list for terminal display."""
    if not claims:
        return "No claims registered."

    lines = []
    status_icons = {
        "registered": "○",  # ○
        "verified": "✓",  # ✓
        "mismatch": "✗",  # ✗
        "missing": "?",
        "partial": "~",
    }

    for c in claims:
        icon = status_icons.get(c.status, "?")
        loc = c.location
        val = f" = {c.claim_value}" if c.claim_value else ""
        lines.append(f"  {icon} [{c.claim_type}] {loc}{val}")
        if verbose and c.source_file:
            src = Path(c.source_file).name
            lines.append(
                f"      source: {src} (session: {c.source_session or 'unknown'})"
            )

    return "\n".join(lines)


# EOF
