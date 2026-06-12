#!/usr/bin/env python3
# Timestamp: "2026-06-12 (proj-paper-scitex-clew, op-2026-06-12-10)"
# File: src/scitex_clew/_overlay/_datasets.py
"""CRUD for the per-claim dataset provenance table."""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional

from ._migrations import _ensure_overlay_tables
from ._models import Dataset


def set_dataset(claim_id: str, dataset: Dataset) -> Dataset:
    """Attach (or replace) the dataset provenance for ``claim_id``.

    One-to-one with the claim — repeated calls overwrite. Returns the
    stored ``Dataset``.
    """
    from .._db import get_db

    db = get_db()
    _ensure_overlay_tables(db)
    conn = sqlite3.connect(str(db.db_path))
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO datasets
                (claim_id, cohort, source, capsule_id,
                 version, url, license, split)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                claim_id,
                dataset.cohort,
                dataset.source,
                dataset.capsule_id,
                dataset.version,
                dataset.url,
                dataset.license,
                dataset.split,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return dataset


def get_dataset(claim_id: str) -> Optional[Dataset]:
    """Return the dataset record for ``claim_id`` or ``None``."""
    from .._db import get_db

    db = get_db()
    _ensure_overlay_tables(db)
    conn = sqlite3.connect(str(db.db_path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM datasets WHERE claim_id = ?", (claim_id,)
        ).fetchone()
        if not row:
            return None
        return Dataset(
            cohort=row["cohort"],
            source=row["source"],
            capsule_id=row["capsule_id"],
            version=row["version"],
            url=row["url"],
            license=row["license"],
            split=row["split"],
        )
    finally:
        conn.close()


def list_datasets(cohort: Optional[str] = None) -> List[Dict[str, Any]]:
    """List ``(claim_id, dataset)`` records, optionally filtered by ``cohort``.

    Returns a list of ``{"claim_id": ..., "dataset": Dataset}`` dicts so
    callers can join back to the Claim layer with one extra lookup.
    """
    from .._db import get_db

    db = get_db()
    _ensure_overlay_tables(db)
    conn = sqlite3.connect(str(db.db_path))
    conn.row_factory = sqlite3.Row
    try:
        if cohort:
            rows = conn.execute(
                "SELECT * FROM datasets WHERE cohort = ? ORDER BY claim_id",
                (cohort,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM datasets ORDER BY claim_id"
            ).fetchall()
        return [
            {
                "claim_id": row["claim_id"],
                "dataset": Dataset(
                    cohort=row["cohort"],
                    source=row["source"],
                    capsule_id=row["capsule_id"],
                    version=row["version"],
                    url=row["url"],
                    license=row["license"],
                    split=row["split"],
                ),
            }
            for row in rows
        ]
    finally:
        conn.close()


__all__ = [
    "set_dataset",
    "get_dataset",
    "list_datasets",
]

# EOF
