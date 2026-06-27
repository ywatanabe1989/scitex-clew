#!/usr/bin/env python3
# Timestamp: "2026-06-27 (clew-feature-impl)"
# File: src/scitex_clew/_db/_file_hashes.py
"""File-hash record operations for VerificationDB (Phase 2: adds size_bytes)."""

from __future__ import annotations

import os
from typing import Dict, List, Optional


class FileHashMixin:
    """Mixin providing file-hash CRUD operations.

    Requires ``_connect()`` context manager from VerificationDB.

    Phase 2 adds ``size_bytes`` (nullable INTEGER) to every insert so the
    estimate engine can predict output data volume.
    """

    # -------------------------------------------------------------------------
    # Migration helper — called from _core.py _init_schema
    # -------------------------------------------------------------------------

    def _migrate_file_hashes_size_bytes(self) -> None:
        """Add size_bytes column to pre-existing file_hashes tables (idempotent).

        Safe to call even when the column already exists: the PRAGMA check
        guards the ALTER TABLE so no exception is raised on repeated runs.
        """
        with self._connect() as conn:
            columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(file_hashes)"
                ).fetchall()
            }
            if "size_bytes" not in columns:
                conn.execute(
                    "ALTER TABLE file_hashes ADD COLUMN size_bytes INTEGER"
                )

    # -------------------------------------------------------------------------
    # Insert
    # -------------------------------------------------------------------------

    def add_file_hash(
        self,
        session_id: str,
        file_path: str,
        hash_value: str,
        role: str,
        size_bytes: Optional[int] = None,
    ) -> None:
        """Add a file hash record.

        Parameters
        ----------
        session_id : str
            Session identifier.
        file_path : str
            Path to the file.
        hash_value : str
            Hash of the file.
        role : str
            Role of the file (input, script, output).
        size_bytes : int, optional
            File size in bytes at recording time.  ``None`` when unknown or
            the file is no longer accessible.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO file_hashes
                (session_id, file_path, hash, role, size_bytes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, file_path, hash_value, role, size_bytes),
            )

    def add_file_hashes(
        self,
        session_id: str,
        hashes: Dict[str, str],
        role: str,
    ) -> None:
        """Add multiple file hashes at once (without size_bytes — batch variant).

        Parameters
        ----------
        session_id : str
            Session identifier.
        hashes : dict
            Mapping of file paths to hashes.
        role : str
            Role of the files (input, script, output).
        """
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO file_hashes
                (session_id, file_path, hash, role)
                VALUES (?, ?, ?, ?)
                """,
                [(session_id, path, h, role) for path, h in hashes.items()],
            )

    # -------------------------------------------------------------------------
    # Query
    # -------------------------------------------------------------------------

    def get_file_hashes(
        self,
        session_id: str,
        role: Optional[str] = None,
    ) -> Dict[str, str]:
        """Get file hashes for a session.

        Parameters
        ----------
        session_id : str
            Session identifier.
        role : str, optional
            Filter by role.

        Returns
        -------
        dict
            Mapping of file paths to hashes.
        """
        with self._connect() as conn:
            if role:
                rows = conn.execute(
                    """
                    SELECT file_path, hash FROM file_hashes
                    WHERE session_id = ? AND role = ?
                    """,
                    (session_id, role),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT file_path, hash FROM file_hashes
                    WHERE session_id = ?
                    """,
                    (session_id,),
                ).fetchall()
            return {row["file_path"]: row["hash"] for row in rows}

    def find_session_by_file(
        self,
        file_path: str,
        role: Optional[str] = None,
    ) -> List[str]:
        """Find sessions that used a specific file.

        Parameters
        ----------
        file_path : str
            Path to the file.
        role : str, optional
            Filter by role (input, output).

        Returns
        -------
        list of str
            List of session IDs.
        """
        with self._connect() as conn:
            if role:
                rows = conn.execute(
                    """
                    SELECT DISTINCT session_id FROM file_hashes
                    WHERE file_path = ? AND role = ?
                    ORDER BY recorded_at DESC
                    """,
                    (file_path, role),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT DISTINCT session_id FROM file_hashes
                    WHERE file_path = ?
                    ORDER BY recorded_at DESC
                    """,
                    (file_path,),
                ).fetchall()
            return [row["session_id"] for row in rows]


def _stat_size(path: str) -> Optional[int]:
    """Return os.path.getsize for *path*, or None if the file is inaccessible."""
    try:
        return os.path.getsize(path)
    except OSError:
        return None


# EOF
