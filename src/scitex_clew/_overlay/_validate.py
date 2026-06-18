#!/usr/bin/env python3
# Timestamp: "2026-06-12 (proj-paper-scitex-clew, op-2026-06-12-10)"
# File: src/scitex_clew/_overlay/_validate.py
"""Cross-ref linter for overlays.

Pure function — does not touch the database. Callers pass overlays parsed
from any source (DB, JSON file, in-memory fixture) and the set of known
claim ids. The report aggregates counts useful for the PR description and
for the validate_overlay.py CLI.
"""

from __future__ import annotations

from typing import Dict, Iterable, List

from ._models import Overlay, ValidationReport


def validate_overlays(
    overlays: Iterable[Overlay],
    known_claim_ids: Iterable[str],
) -> ValidationReport:
    """Cross-ref linter: every ``claims_touched`` id must resolve."""
    known = set(known_claim_ids)
    overlays = list(overlays)
    unresolved: List[Dict[str, str]] = []
    counts_status: Dict[str, int] = {}
    counts_round: Dict[str, int] = {}
    n_touched = 0
    for ov in overlays:
        counts_status[ov.status] = counts_status.get(ov.status, 0) + 1
        if ov.round:
            key = f"{ov.reviewer or '?'}/{ov.round}"
            counts_round[key] = counts_round.get(key, 0) + 1
        for cid in ov.claims_touched:
            n_touched += 1
            if cid not in known:
                unresolved.append({"overlay_id": ov.overlay_id, "claim_id": cid})

    return ValidationReport(
        n_overlays=len(overlays),
        n_claims_touched_total=n_touched,
        n_unresolved_claim_refs=len(unresolved),
        unresolved_refs=unresolved,
        counts_by_status=counts_status,
        counts_by_reviewer_round=counts_round,
        ok=(len(unresolved) == 0),
    )


__all__ = [
    "validate_overlays",
]

# EOF
