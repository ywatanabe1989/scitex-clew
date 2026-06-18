#!/usr/bin/env python3
# Timestamp: "2026-06-12 (proj-paper-scitex-clew, op-2026-06-12-10)"
# File: src/scitex_clew/_overlay/_overlays.py
"""CRUD for the peer-review ``overlays`` table and its claim-link table."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any, Iterable, List, Optional

from ._migrations import _ensure_overlay_tables
from ._models import OVERLAY_STATUSES, Overlay


def add_overlay(
    overlay_id: str,
    kind: str,
    status: str,
    claims_touched: Iterable[str],
    round: Optional[str] = None,
    reviewer: Optional[str] = None,
    comment_idx: Optional[int] = None,
    preprint_section: Optional[str] = None,
    preprint_line_marker: Optional[str] = None,
    resolution_commit: Optional[str] = None,
    resolution_data_run: Optional[str] = None,
) -> Overlay:
    """Create (or replace) a peer-review overlay entity.

    ``claims_touched`` may be empty — the overlay will still be created,
    but it will not appear when a reader asks for "overlays on this
    claim". Validation of cross-refs is the linter's job
    (:func:`scitex_clew._overlay.validate_overlays`), not this writer's,
    so test fixtures and drafts can be inserted incrementally.
    """
    now = datetime.now().isoformat()
    overlay = Overlay(
        overlay_id=overlay_id,
        kind=kind,
        status=status,
        claims_touched=list(claims_touched),
        round=round,
        reviewer=reviewer,
        comment_idx=comment_idx,
        preprint_section=preprint_section,
        preprint_line_marker=preprint_line_marker,
        resolution_commit=resolution_commit,
        resolution_data_run=resolution_data_run,
        created_at=now,
        updated_at=now,
    )

    from .._db import get_db

    db = get_db()
    _ensure_overlay_tables(db)
    conn = sqlite3.connect(str(db.db_path))
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO overlays
                (overlay_id, kind, status, round, reviewer, comment_idx,
                 preprint_section, preprint_line_marker,
                 resolution_commit, resolution_data_run,
                 created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                overlay.overlay_id,
                overlay.kind,
                overlay.status,
                overlay.round,
                overlay.reviewer,
                overlay.comment_idx,
                overlay.preprint_section,
                overlay.preprint_line_marker,
                overlay.resolution_commit,
                overlay.resolution_data_run,
                overlay.created_at,
                overlay.updated_at,
            ),
        )
        # Replace the link rows for this overlay
        conn.execute(
            "DELETE FROM overlay_claims WHERE overlay_id = ?", (overlay.overlay_id,)
        )
        conn.executemany(
            "INSERT INTO overlay_claims(overlay_id, claim_id) VALUES (?, ?)",
            [(overlay.overlay_id, cid) for cid in overlay.claims_touched],
        )
        conn.commit()
    finally:
        conn.close()
    return overlay


def update_overlay_status(
    overlay_id: str,
    status: str,
    resolution_commit: Optional[str] = None,
    resolution_data_run: Optional[str] = None,
) -> Optional[Overlay]:
    """Update an overlay's lifecycle status (e.g. ``open -> addressed``)."""
    if status not in OVERLAY_STATUSES:
        raise ValueError(
            f"Invalid overlay status '{status}'. "
            f"Must be one of: {OVERLAY_STATUSES}"
        )

    from .._db import get_db

    db = get_db()
    _ensure_overlay_tables(db)
    conn = sqlite3.connect(str(db.db_path))
    try:
        now = datetime.now().isoformat()
        cur = conn.execute(
            """
            UPDATE overlays
            SET status = ?,
                resolution_commit = COALESCE(?, resolution_commit),
                resolution_data_run = COALESCE(?, resolution_data_run),
                updated_at = ?
            WHERE overlay_id = ?
            """,
            (status, resolution_commit, resolution_data_run, now, overlay_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            return None
    finally:
        conn.close()

    return get_overlay(overlay_id)


def get_overlay(overlay_id: str) -> Optional[Overlay]:
    """Fetch a single overlay by id, including its ``claims_touched`` list."""
    from .._db import get_db

    db = get_db()
    _ensure_overlay_tables(db)
    conn = sqlite3.connect(str(db.db_path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM overlays WHERE overlay_id = ?", (overlay_id,)
        ).fetchone()
        if not row:
            return None
        links = conn.execute(
            "SELECT claim_id FROM overlay_claims WHERE overlay_id = ? "
            "ORDER BY claim_id",
            (overlay_id,),
        ).fetchall()
        return _row_to_overlay(row, [r["claim_id"] for r in links])
    finally:
        conn.close()


def list_overlays(
    claim_id: Optional[str] = None,
    status: Optional[str] = None,
    reviewer: Optional[str] = None,
    round: Optional[str] = None,
    limit: int = 200,
) -> List[Overlay]:
    """List overlays, with optional joins/filters.

    ``claim_id`` joins through ``overlay_claims`` and returns only overlays
    that touch that claim — this is the primary read used by the
    live-paper web viewer.
    """
    from .._db import get_db

    db = get_db()
    _ensure_overlay_tables(db)
    conn = sqlite3.connect(str(db.db_path))
    conn.row_factory = sqlite3.Row
    try:
        if claim_id:
            base_sql = (
                "SELECT o.* FROM overlays o "
                "JOIN overlay_claims oc ON oc.overlay_id = o.overlay_id "
                "WHERE oc.claim_id = ?"
            )
            params: List[Any] = [claim_id]
        else:
            base_sql = "SELECT * FROM overlays WHERE 1=1"
            params = []
        if status:
            base_sql += " AND status = ?"
            params.append(status)
        if reviewer:
            base_sql += " AND reviewer = ?"
            params.append(reviewer)
        if round:
            base_sql += " AND round = ?"
            params.append(round)
        base_sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(base_sql, params).fetchall()

        out: List[Overlay] = []
        for row in rows:
            links = conn.execute(
                "SELECT claim_id FROM overlay_claims "
                "WHERE overlay_id = ? ORDER BY claim_id",
                (row["overlay_id"],),
            ).fetchall()
            out.append(_row_to_overlay(row, [r["claim_id"] for r in links]))
        return out
    finally:
        conn.close()


def _row_to_overlay(row, claim_ids: List[str]) -> Overlay:
    """Internal: rehydrate a sqlite row + link list into an :class:`Overlay`."""
    return Overlay(
        overlay_id=row["overlay_id"],
        kind=row["kind"],
        status=row["status"],
        claims_touched=claim_ids,
        round=row["round"],
        reviewer=row["reviewer"],
        comment_idx=row["comment_idx"],
        preprint_section=row["preprint_section"],
        preprint_line_marker=row["preprint_line_marker"],
        resolution_commit=row["resolution_commit"],
        resolution_data_run=row["resolution_data_run"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


__all__ = [
    "add_overlay",
    "update_overlay_status",
    "get_overlay",
    "list_overlays",
]

# EOF
