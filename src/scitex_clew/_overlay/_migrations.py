#!/usr/bin/env python3
# Timestamp: "2026-06-12 (proj-paper-scitex-clew, op-2026-06-12-10)"
# File: src/scitex_clew/_overlay/_migrations.py
"""Sqlite schema migrations for the overlay subpackage.

Sibling of :func:`scitex_clew._claim.migrate_add_claims_table`. None of
these tables modify the existing ``claims`` schema — the Claim layer is
byte-identical for callers that don't use overlays.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


def migrate_add_overlay_tables(db_path: Path) -> None:
    """Create overlay-side tables if not present. Safe to call multiple times.

    Adds:

      * ``datasets``         (claim_id PK)
      * ``verify_statuses``  (claim_id PK)
      * ``overlays``         (overlay_id PK)
      * ``overlay_claims``   (overlay_id, claim_id composite PK)
    """
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS datasets (
                claim_id TEXT PRIMARY KEY,
                cohort TEXT NOT NULL,
                source TEXT NOT NULL,
                capsule_id TEXT NOT NULL,
                version TEXT,
                url TEXT,
                license TEXT,
                split TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_datasets_cohort ON datasets(cohort)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_datasets_capsule ON datasets(capsule_id)"
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS verify_statuses (
                claim_id TEXT PRIMARY KEY,
                verdict TEXT NOT NULL,
                verifier_run TEXT NOT NULL,
                mask_verified INTEGER NOT NULL,
                score_json TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_verify_run "
            "ON verify_statuses(verifier_run)"
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS overlays (
                overlay_id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                status TEXT NOT NULL,
                round TEXT,
                reviewer TEXT,
                comment_idx INTEGER,
                preprint_section TEXT,
                preprint_line_marker TEXT,
                resolution_commit TEXT,
                resolution_data_run TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_overlays_status ON overlays(status)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_overlays_round ON overlays(round)"
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS overlay_claims (
                overlay_id TEXT NOT NULL,
                claim_id TEXT NOT NULL,
                PRIMARY KEY (overlay_id, claim_id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_overlay_claims_claim "
            "ON overlay_claims(claim_id)"
        )

        conn.commit()
    finally:
        conn.close()


def _ensure_overlay_tables(db) -> None:
    """Internal helper invoked by CRUD modules before any read/write."""
    migrate_add_overlay_tables(db.db_path)


__all__ = [
    "migrate_add_overlay_tables",
    "_ensure_overlay_tables",
]

# EOF
