#!/usr/bin/env python3
# Timestamp: "2026-06-12 (proj-paper-scitex-clew, op-2026-06-12-10)"
# File: src/scitex_clew/_overlay/_verify.py
"""CRUD for the per-claim ``verify_statuses`` table.

Written by the structural verifier (separate identity from the capsule
agent — preserves capsule isolation: the agent never writes its own
pass/fail).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional

from ._migrations import _ensure_overlay_tables
from ._models import VerifyStatus


def set_verify_status(
    claim_id: str,
    verdict: str,
    verifier_run: str,
    mask_verified: bool,
    score_json: Optional[str] = None,
) -> VerifyStatus:
    """Record the structural verifier's outcome for ``claim_id``.

    Intentionally accepts primitives (not a pre-built :class:`VerifyStatus`)
    because the typical caller is the verifier script, which already holds
    the fields individually. The validation in :class:`VerifyStatus` still
    runs and raises ``ValueError`` on a bad verdict.
    """
    status = VerifyStatus(
        verdict=verdict,
        verifier_run=verifier_run,
        mask_verified=mask_verified,
        score_json=score_json,
        recorded_at=datetime.now().isoformat(),
    )

    from .._db import get_db

    db = get_db()
    _ensure_overlay_tables(db)
    conn = sqlite3.connect(str(db.db_path))
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO verify_statuses
                (claim_id, verdict, verifier_run, mask_verified,
                 score_json, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                claim_id,
                status.verdict,
                status.verifier_run,
                1 if status.mask_verified else 0,
                status.score_json,
                status.recorded_at,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return status


def get_verify_status(claim_id: str) -> Optional[VerifyStatus]:
    """Return the latest verifier outcome for ``claim_id`` or ``None``."""
    from .._db import get_db

    db = get_db()
    _ensure_overlay_tables(db)
    conn = sqlite3.connect(str(db.db_path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM verify_statuses WHERE claim_id = ?", (claim_id,)
        ).fetchone()
        if not row:
            return None
        return VerifyStatus(
            verdict=row["verdict"],
            verifier_run=row["verifier_run"],
            mask_verified=bool(row["mask_verified"]),
            score_json=row["score_json"],
            recorded_at=row["recorded_at"],
        )
    finally:
        conn.close()


__all__ = [
    "set_verify_status",
    "get_verify_status",
]

# EOF
