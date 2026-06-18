#!/usr/bin/env python3
# Timestamp: "2026-06-12 (proj-paper-scitex-clew, op-2026-06-12-10)"
# File: tests/scitex_clew/test__overlay__models.py
"""Pure-data tests for the overlay subpackage's dataclasses + vocabularies.

No sqlite / no I/O — every test is dependency-free.
"""

from __future__ import annotations

import pytest

from scitex_clew._overlay import (
    OVERLAY_KINDS,
    OVERLAY_STATUSES,
    VERDICTS,
    Dataset,
    Overlay,
    VerifyStatus,
)


def test_verdicts_vocab_matches_documented_set():
    # Arrange
    expected = ("pass", "fail", "inconclusive")
    # Act
    actual = VERDICTS
    # Assert
    assert actual == expected


def test_overlay_statuses_vocab_matches_documented_set():
    # Arrange
    expected = ("open", "addressed", "deferred", "wontfix")
    # Act
    actual = OVERLAY_STATUSES
    # Assert
    assert actual == expected


def test_overlay_kinds_includes_reviewer_comment():
    # Arrange (vocab is module-level)
    # Act
    kinds = OVERLAY_KINDS
    # Assert
    assert "reviewer_comment" in kinds


def test_dataset_full_dict_roundtrip_preserves_all_fields():
    # Arrange
    d = Dataset(
        cohort="A",
        source="corebench",
        capsule_id="capsule-1624349",
        version="v2024-09",
        url="https://corebench.cs.princeton.edu/capsules/1624349",
        license="Code Ocean Compute Capsule",
        split="easy",
    )
    # Act
    rehydrated = Dataset.from_dict(d.to_dict())
    # Assert
    assert rehydrated == d


def test_dataset_minimal_required_fields_leaves_version_none():
    # Arrange
    cohort, source, capsule_id = "A", "corebench", "cap-1"
    # Act
    d = Dataset(cohort=cohort, source=source, capsule_id=capsule_id)
    # Assert
    assert d.version is None


def test_dataset_minimal_dict_roundtrips_cleanly():
    # Arrange
    d = Dataset(cohort="A", source="corebench", capsule_id="cap-1")
    # Act
    rehydrated = Dataset.from_dict(d.to_dict())
    # Assert
    assert rehydrated == d


def test_verify_status_rejects_bad_verdict():
    # Arrange
    bad_verdict = "maybe"
    # Act
    construct = lambda: VerifyStatus(
        verdict=bad_verdict, verifier_run="r1", mask_verified=True
    )
    # Assert
    with pytest.raises(ValueError, match="Invalid verdict"):
        construct()


def test_verify_status_dict_roundtrip_preserves_score_json():
    # Arrange
    v = VerifyStatus(
        verdict="pass",
        verifier_run="cohort_a_structural_2026-06-12T08:40Z",
        mask_verified=True,
        score_json="runs/cohort_a_structural/cap-23/score.json",
    )
    # Act
    rehydrated = VerifyStatus.from_dict(v.to_dict())
    # Assert
    assert rehydrated == v


def test_overlay_rejects_bad_status():
    # Arrange
    bad_status = "bogus"
    # Act
    construct = lambda: Overlay(
        overlay_id="o1", kind="reviewer_comment", status=bad_status
    )
    # Assert
    with pytest.raises(ValueError, match="Invalid overlay status"):
        construct()


def test_overlay_accepts_unknown_kind_for_forward_compat():
    # Arrange: a kind not in the canonical OVERLAY_KINDS vocabulary
    forward_kind = "future_kind_not_in_vocab"
    overlay_id = "o1"
    status = "open"
    # Act: construct the overlay (should not raise)
    ov = Overlay(overlay_id=overlay_id, kind=forward_kind, status=status)
    # Assert: the unknown kind is stored verbatim (forward compatibility)
    assert ov.kind == forward_kind


def test_overlay_full_dict_roundtrip_preserves_all_fields():
    # Arrange
    ov = Overlay(
        overlay_id="rev_R1_03",
        kind="reviewer_comment",
        status="open",
        claims_touched=["c1", "c2"],
        round="R1",
        reviewer="R1",
        comment_idx=3,
        preprint_section="Results §3.6",
        preprint_line_marker="L412",
    )
    # Act
    rehydrated = Overlay.from_dict(ov.to_dict())
    # Assert
    assert rehydrated == ov


# EOF
