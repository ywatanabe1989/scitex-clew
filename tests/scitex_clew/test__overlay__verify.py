#!/usr/bin/env python3
# Timestamp: "2026-06-12 (proj-paper-scitex-clew, op-2026-06-12-10)"
# File: tests/scitex_clew/test__overlay__verify.py
"""Sqlite CRUD tests for the per-claim verify_statuses table."""

from __future__ import annotations

from pathlib import Path

import pytest

from scitex_clew._db import set_db
from scitex_clew._overlay import (
    get_verify_status,
    migrate_add_overlay_tables,
    set_verify_status,
)


@pytest.fixture
def tmp_db(tmp_path: Path):
    db_path = tmp_path / "clew.db"
    db = set_db(db_path)
    migrate_add_overlay_tables(db.db_path)
    return db


def test_set_verify_status_stores_verdict_field(tmp_db):
    # Arrange
    set_verify_status("claim_x", "pass", "run-1", True, "runs/x/score.json")
    # Act
    got = get_verify_status("claim_x")
    # Assert
    assert got.verdict == "pass"


def test_set_verify_status_stores_mask_verified_as_bool(tmp_db):
    # Arrange
    set_verify_status("claim_x", "pass", "run-1", True)
    # Act
    got = get_verify_status("claim_x")
    # Assert
    assert got.mask_verified is True


def test_set_verify_status_stores_verifier_run_field(tmp_db):
    # Arrange
    set_verify_status("claim_x", "pass", "structural-2026-06-12", True)
    # Act
    got = get_verify_status("claim_x")
    # Assert
    assert got.verifier_run == "structural-2026-06-12"


def test_set_verify_status_replaces_previous_verdict(tmp_db):
    # Arrange
    set_verify_status("claim_x", "pass", "run-1", True)
    # Act
    set_verify_status("claim_x", "fail", "run-2", True)
    # Assert
    assert get_verify_status("claim_x").verdict == "fail"


def test_set_verify_status_replaces_verifier_run_on_second_write(tmp_db):
    # Arrange
    set_verify_status("claim_x", "pass", "run-1", True)
    # Act
    set_verify_status("claim_x", "fail", "run-2", True)
    # Assert
    assert get_verify_status("claim_x").verifier_run == "run-2"


def test_set_verify_status_rejects_bad_verdict(tmp_db):
    # Arrange
    bad_verdict = "unknown"
    # Act
    call = lambda: set_verify_status("claim_x", bad_verdict, "run-1", True)
    # Assert
    with pytest.raises(ValueError):
        call()


def test_get_verify_status_missing_returns_none(tmp_db):
    # Arrange (no inserts)
    # Act
    got = get_verify_status("missing")
    # Assert
    assert got is None


# EOF
