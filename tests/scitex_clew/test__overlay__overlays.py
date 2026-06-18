#!/usr/bin/env python3
# Timestamp: "2026-06-12 (proj-paper-scitex-clew, op-2026-06-12-10)"
# File: tests/scitex_clew/test__overlay__overlays.py
"""Sqlite CRUD tests for the overlays + overlay_claims tables."""

from __future__ import annotations

from pathlib import Path

import pytest

from scitex_clew._db import set_db
from scitex_clew._overlay import (
    add_overlay,
    get_overlay,
    list_overlays,
    migrate_add_overlay_tables,
    update_overlay_status,
)


@pytest.fixture
def tmp_db(tmp_path: Path):
    db_path = tmp_path / "clew.db"
    db = set_db(db_path)
    migrate_add_overlay_tables(db.db_path)
    return db


def test_add_overlay_preserves_claims_touched_order(tmp_db):
    # Arrange
    add_overlay(
        overlay_id="rev_R1_03",
        kind="reviewer_comment",
        status="open",
        claims_touched=["cohort_a_pass_rate", "session_overhead_s_median"],
        round="R1",
        reviewer="R1",
        comment_idx=3,
    )
    # Act
    got = get_overlay("rev_R1_03")
    # Assert
    assert got.claims_touched == [
        "cohort_a_pass_rate",
        "session_overhead_s_median",
    ]


def test_add_overlay_stores_initial_status(tmp_db):
    # Arrange
    add_overlay("o1", "reviewer_comment", "open", ["c1"])
    # Act
    got = get_overlay("o1")
    # Assert
    assert got.status == "open"


def test_add_overlay_replace_drops_old_claim_links(tmp_db):
    # Arrange
    add_overlay("o1", "reviewer_comment", "open", ["c1", "c2"])
    # Act
    add_overlay("o1", "reviewer_comment", "open", ["c3"])
    # Assert
    assert get_overlay("o1").claims_touched == ["c3"]


def test_update_overlay_status_changes_status_field(tmp_db):
    # Arrange
    add_overlay("o1", "reviewer_comment", "open", ["c1"])
    # Act
    updated = update_overlay_status("o1", "addressed")
    # Assert
    assert updated.status == "addressed"


def test_update_overlay_status_stores_resolution_commit(tmp_db):
    # Arrange
    add_overlay("o1", "reviewer_comment", "open", ["c1"])
    # Act
    updated = update_overlay_status(
        "o1", "addressed", resolution_commit="deadbeef"
    )
    # Assert
    assert updated.resolution_commit == "deadbeef"


def test_update_overlay_status_stores_resolution_data_run(tmp_db):
    # Arrange
    add_overlay("o1", "reviewer_comment", "open", ["c1"])
    # Act
    updated = update_overlay_status(
        "o1", "addressed", resolution_data_run="run-42"
    )
    # Assert
    assert updated.resolution_data_run == "run-42"


def test_update_overlay_status_unknown_id_returns_none(tmp_db):
    # Arrange (no inserts)
    # Act
    result = update_overlay_status("missing", "addressed")
    # Assert
    assert result is None


def test_update_overlay_status_rejects_bad_status(tmp_db):
    # Arrange
    add_overlay("o1", "reviewer_comment", "open", ["c1"])
    bad_status = "bogus_status"
    # Act
    call = lambda: update_overlay_status("o1", bad_status)
    # Assert
    with pytest.raises(ValueError):
        call()


def test_list_overlays_join_by_claim_id_returns_only_touching_overlays(tmp_db):
    # Arrange
    add_overlay("o1", "reviewer_comment", "open", ["c1", "c2"])
    add_overlay("o2", "reviewer_comment", "open", ["c2", "c3"])
    add_overlay("o3", "reviewer_comment", "addressed", ["c3"])
    # Act
    on_c2 = list_overlays(claim_id="c2")
    # Assert
    assert {ov.overlay_id for ov in on_c2} == {"o1", "o2"}


def test_list_overlays_filter_by_status_returns_only_matching(tmp_db):
    # Arrange
    add_overlay("o1", "reviewer_comment", "open", ["c1"])
    add_overlay("o2", "reviewer_comment", "open", ["c1"])
    add_overlay("o3", "reviewer_comment", "addressed", ["c1"])
    # Act
    open_only = list_overlays(status="open")
    # Assert
    assert {ov.overlay_id for ov in open_only} == {"o1", "o2"}


def test_list_overlays_filter_by_reviewer_and_round_combines_predicates(tmp_db):
    # Arrange
    add_overlay(
        "o1", "reviewer_comment", "open", ["c1"], round="R1", reviewer="R1"
    )
    add_overlay(
        "o2", "reviewer_comment", "open", ["c1"], round="R1", reviewer="R2"
    )
    add_overlay(
        "o3", "reviewer_comment", "open", ["c1"], round="R2", reviewer="R1"
    )
    # Act
    rows = list_overlays(reviewer="R1", round="R1")
    # Assert
    assert {ov.overlay_id for ov in rows} == {"o1"}


# EOF
