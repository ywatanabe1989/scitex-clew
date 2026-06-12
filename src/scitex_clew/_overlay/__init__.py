#!/usr/bin/env python3
# Timestamp: "2026-06-12 (proj-paper-scitex-clew, op-2026-06-12-10)"
# File: src/scitex_clew/_overlay/__init__.py
"""Overlay subpackage — dataset, verify-status, and peer-review overlays.

Additive on top of :mod:`scitex_clew._claim`. The Claim layer is unchanged;
this subpackage introduces three sibling tables joined by ``claim_id``:

  * ``datasets``         — schema'd dataset provenance per claim
  * ``verify_statuses``  — per-claim verifier verdict (mask_verified)
  * ``overlays`` + ``overlay_claims`` — peer-review overlay records

Design contract (op-2026-06-12-10, lead msg c2474a18):

  * Pure additive — old payloads / old DBs continue to work unchanged.
  * Schema'd dataset id ``{cohort, source, capsule_id}`` for mechanical
    cross-cohort reuse.
  * Render policy stays in consumers (writer / live-paper).
  * Zero new deps — pure stdlib + sqlite3.
"""

from __future__ import annotations

from ._datasets import get_dataset, list_datasets, set_dataset
from ._json_io import overlays_from_json, overlays_to_json
from ._migrations import migrate_add_overlay_tables
from ._models import (
    OVERLAY_KINDS,
    OVERLAY_STATUSES,
    VERDICTS,
    Dataset,
    Overlay,
    ValidationReport,
    VerifyStatus,
)
from ._overlays import (
    add_overlay,
    get_overlay,
    list_overlays,
    update_overlay_status,
)
from ._validate import validate_overlays
from ._verify import get_verify_status, set_verify_status

__all__ = [
    # Vocabularies
    "VERDICTS",
    "OVERLAY_KINDS",
    "OVERLAY_STATUSES",
    # Data classes
    "Dataset",
    "VerifyStatus",
    "Overlay",
    "ValidationReport",
    # Migration
    "migrate_add_overlay_tables",
    # Dataset CRUD
    "set_dataset",
    "get_dataset",
    "list_datasets",
    # VerifyStatus CRUD
    "set_verify_status",
    "get_verify_status",
    # Overlay CRUD
    "add_overlay",
    "update_overlay_status",
    "get_overlay",
    "list_overlays",
    # JSON I/O
    "overlays_to_json",
    "overlays_from_json",
    # Validation
    "validate_overlays",
]

# EOF
