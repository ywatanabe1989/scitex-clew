#!/usr/bin/env python3
# Timestamp: "2026-06-12 (proj-paper-scitex-clew, op-2026-06-12-10)"
# File: tests/scitex_clew/test__overlay__datasets.py
"""Sqlite CRUD tests for the per-claim datasets table."""

from __future__ import annotations

from pathlib import Path

import pytest

from scitex_clew._db import set_db
from scitex_clew._overlay import (
    Dataset,
    get_dataset,
    list_datasets,
    migrate_add_overlay_tables,
    set_dataset,
)


@pytest.fixture
def tmp_db(tmp_path: Path):
    """Fresh sqlite DB rooted at ``tmp_path/clew.db`` with overlay schema."""
    db_path = tmp_path / "clew.db"
    db = set_db(db_path)
    migrate_add_overlay_tables(db.db_path)
    return db


def test_set_dataset_then_get_returns_stored_record(tmp_db):
    # Arrange
    stored = Dataset(
        cohort="A", source="corebench", capsule_id="cap-1", split="easy"
    )
    set_dataset("claim_x", stored)
    # Act
    got = get_dataset("claim_x")
    # Assert
    assert got == stored


def test_set_dataset_replaces_previous_record_for_same_claim(tmp_db):
    # Arrange
    set_dataset(
        "claim_x", Dataset(cohort="A", source="corebench", capsule_id="c1")
    )
    # Act
    set_dataset(
        "claim_x", Dataset(cohort="B", source="bixbench", capsule_id="bix-1")
    )
    # Assert
    assert get_dataset("claim_x").cohort == "B"


def test_get_dataset_missing_returns_none(tmp_db):
    # Arrange (no inserts)
    # Act
    got = get_dataset("does-not-exist")
    # Assert
    assert got is None


def test_list_datasets_filter_by_cohort_returns_only_matching(tmp_db):
    # Arrange
    set_dataset("ca1", Dataset(cohort="A", source="corebench", capsule_id="c1"))
    set_dataset("ca2", Dataset(cohort="A", source="corebench", capsule_id="c2"))
    set_dataset("cb1", Dataset(cohort="B", source="bixbench", capsule_id="b1"))
    # Act
    rows = list_datasets(cohort="A")
    # Assert
    assert {r["claim_id"] for r in rows} == {"ca1", "ca2"}


def test_list_datasets_no_filter_returns_all_records(tmp_db):
    # Arrange
    set_dataset("ca1", Dataset(cohort="A", source="corebench", capsule_id="c1"))
    set_dataset("ca2", Dataset(cohort="A", source="corebench", capsule_id="c2"))
    set_dataset("cb1", Dataset(cohort="B", source="bixbench", capsule_id="b1"))
    # Act
    rows = list_datasets()
    # Assert
    assert len(rows) == 3


# EOF
