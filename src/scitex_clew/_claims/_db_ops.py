#!/usr/bin/env python3
# Timestamp: "2026-06-27 (ywatanabe)"
"""Claim database operations: CRUD, migration, resolution."""

from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from .._db import get_db
from ._types import CLAIM_TYPES, Claim


def migrate_add_claims_table(db_path: Path) -> None:
    """Create claims table if not present. Safe to call multiple times."""
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_id TEXT UNIQUE NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER,
                claim_type TEXT NOT NULL,
                claim_value TEXT,
                source_session TEXT,
                source_file TEXT,
                source_hash TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified_at TIMESTAMP,
                status TEXT DEFAULT 'registered'
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_claims_file ON claims(file_path)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_claims_source ON claims(source_file)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_claims_session ON claims(source_session)"
        )
        conn.commit()
    finally:
        conn.close()


def _ensure_claims_table(db) -> None:
    """Ensure the claims table exists (run migration)."""
    migrate_add_claims_table(db.db_path)


def _generate_claim_id(
    file_path: str, line_number: Optional[int], claim_type: str
) -> str:
    """Generate a deterministic claim ID."""
    loc = f"{file_path}:L{line_number}" if line_number else file_path
    h = hashlib.sha256(f"{loc}:{claim_type}".encode()).hexdigest()[:12]
    return f"claim_{h}"


def add_claim(
    file_path: str,
    claim_type: str,
    line_number: Optional[int] = None,
    claim_value: Optional[str] = None,
    source_file: Optional[str] = None,
    source_session: Optional[str] = None,
) -> Claim:
    """Register a claim linking a manuscript assertion to the verification chain.

    Parameters
    ----------
    file_path : str
        Path to the manuscript file (e.g., paper.tex).
    claim_type : str
        One of: statistic, figure, table, text, value.
    line_number : int, optional
        Line number in the manuscript.
    claim_value : str, optional
        The asserted value (e.g., "p = 0.003").
    source_file : str, optional
        Path to the source file that produced this claim.
    source_session : str, optional
        Session ID that produced the source.

    Returns
    -------
    Claim
        The registered claim object.
    """
    if claim_type not in CLAIM_TYPES:
        raise ValueError(
            f"Invalid claim_type '{claim_type}'. Must be one of: {CLAIM_TYPES}"
        )

    file_path = str(Path(file_path).resolve())
    claim_id = _generate_claim_id(file_path, line_number, claim_type)

    # Compute source hash if source_file exists
    source_hash = None
    if source_file:
        source_file = str(Path(source_file).resolve())
        source_path = Path(source_file)
        if source_path.exists():
            from .._hash import hash_file

            source_hash = hash_file(source_path)

    # Auto-detect source session if not provided
    if source_file and not source_session:
        db = get_db()
        sessions = db.find_session_by_file(source_file, role="output")
        if sessions:
            source_session = sessions[0]

    claim = Claim(
        claim_id=claim_id,
        file_path=file_path,
        line_number=line_number,
        claim_type=claim_type,
        claim_value=claim_value,
        source_session=source_session,
        source_file=source_file,
        source_hash=source_hash,
    )

    # Store in database
    db = get_db()
    _ensure_claims_table(db)
    conn = sqlite3.connect(str(db.db_path))
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO claims
                (claim_id, file_path, line_number, claim_type, claim_value,
                 source_session, source_file, source_hash, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'registered')
            """,
            (
                claim.claim_id,
                claim.file_path,
                claim.line_number,
                claim.claim_type,
                claim.claim_value,
                claim.source_session,
                claim.source_file,
                claim.source_hash,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    # Auto-export the canonical claims.json so consumers (verifier,
    # scitex-writer, human eyes) can read a stable artifact without
    # talking to sqlite. Default ON; opt out with
    # SCITEX_CLEW_AUTO_EXPORT_CLAIMS=0 if you're streaming thousands of
    # claims and the per-call rewrite cost matters. The cost is O(N×K)
    # where N is total claims in the DB and K is rewrite size — for
    # typical research papers (N < 100, K < 50 KB) it's negligible.
    if os.environ.get("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "1") != "0":
        try:
            from ._export import export_claims_json

            export_claims_json()
        except Exception as exc:  # noqa: BLE001
            warnings.warn(
                f"scitex_clew auto-export of claims.json failed "
                f"(set SCITEX_CLEW_AUTO_EXPORT_CLAIMS=0 to silence): "
                f"{exc!r}",
                RuntimeWarning,
                stacklevel=2,
            )

    return claim


def list_claims(
    file_path: Optional[str] = None,
    claim_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[Claim]:
    """List registered claims with optional filters.

    Parameters
    ----------
    file_path : str, optional
        Filter by manuscript file path.
    claim_type : str, optional
        Filter by claim type.
    status : str, optional
        Filter by verification status.
    limit : int
        Maximum number of claims to return.

    Returns
    -------
    list of Claim
    """
    db = get_db()
    _ensure_claims_table(db)

    query = "SELECT * FROM claims WHERE 1=1"
    params = []

    if file_path:
        file_path = str(Path(file_path).resolve())
        query += " AND file_path = ?"
        params.append(file_path)
    if claim_type:
        query += " AND claim_type = ?"
        params.append(claim_type)
    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY file_path, line_number LIMIT ?"
    params.append(limit)

    conn = sqlite3.connect(str(db.db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(query, params).fetchall()
        return [
            Claim(
                claim_id=row["claim_id"],
                file_path=row["file_path"],
                line_number=row["line_number"],
                claim_type=row["claim_type"],
                claim_value=row["claim_value"],
                source_session=row["source_session"],
                source_file=row["source_file"],
                source_hash=row["source_hash"],
                registered_at=row["registered_at"],
                verified_at=row["verified_at"],
                status=row["status"],
            )
            for row in rows
        ]
    finally:
        conn.close()


def _resolve_claim(identifier: str, db) -> Optional[Claim]:
    """Resolve a claim by ID or location string."""
    conn = sqlite3.connect(str(db.db_path))
    conn.row_factory = sqlite3.Row
    try:
        # Try claim_id first
        row = conn.execute(
            "SELECT * FROM claims WHERE claim_id = ?", (identifier,)
        ).fetchone()

        if not row:
            # Try location format: file.tex:L42
            match = re.match(r"^(.+):L(\d+)$", identifier)
            if match:
                fpath = str(Path(match.group(1)).resolve())
                line = int(match.group(2))
                row = conn.execute(
                    "SELECT * FROM claims WHERE file_path = ? AND line_number = ?",
                    (fpath, line),
                ).fetchone()

        if not row:
            # Try file path only (returns first match)
            fpath = str(Path(identifier).resolve())
            row = conn.execute(
                "SELECT * FROM claims WHERE file_path = ? ORDER BY line_number LIMIT 1",
                (fpath,),
            ).fetchone()

        if row:
            return Claim(
                claim_id=row["claim_id"],
                file_path=row["file_path"],
                line_number=row["line_number"],
                claim_type=row["claim_type"],
                claim_value=row["claim_value"],
                source_session=row["source_session"],
                source_file=row["source_file"],
                source_hash=row["source_hash"],
                registered_at=row["registered_at"],
                verified_at=row["verified_at"],
                status=row["status"],
            )
        return None
    finally:
        conn.close()


def _update_claim_status(claim_id: str, status: str, db) -> None:
    """Update claim verification status."""
    conn = sqlite3.connect(str(db.db_path))
    try:
        conn.execute(
            "UPDATE claims SET status = ?, verified_at = ? WHERE claim_id = ?",
            (status, datetime.now().isoformat(), claim_id),
        )
        conn.commit()
    finally:
        conn.close()


# EOF
