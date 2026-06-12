#!/usr/bin/env python3
# Timestamp: "2026-06-12 (proj-paper-scitex-clew, op-2026-06-12-10)"
# File: tests/scitex_clew/test__overlay__validate.py
"""Cross-ref linter behaviour for overlays."""

from __future__ import annotations

from scitex_clew._overlay import Overlay, validate_overlays


def test_validate_overlays_clean_returns_ok_true():
    # Arrange
    overlays = [
        Overlay(
            overlay_id="o1",
            kind="reviewer_comment",
            status="open",
            claims_touched=["c1", "c2"],
            round="R1",
            reviewer="R1",
        ),
    ]
    # Act
    report = validate_overlays(overlays, known_claim_ids=["c1", "c2", "c3"])
    # Assert
    assert report.ok is True


def test_validate_overlays_counts_total_claims_touched():
    # Arrange
    overlays = [
        Overlay(
            overlay_id="o1",
            kind="reviewer_comment",
            status="open",
            claims_touched=["c1", "c2"],
        ),
    ]
    # Act
    report = validate_overlays(overlays, known_claim_ids=["c1", "c2"])
    # Assert
    assert report.n_claims_touched_total == 2


def test_validate_overlays_aggregates_reviewer_round_key():
    # Arrange
    overlays = [
        Overlay(
            overlay_id="o1",
            kind="reviewer_comment",
            status="open",
            round="R1",
            reviewer="R1",
        ),
    ]
    # Act
    report = validate_overlays(overlays, known_claim_ids=[])
    # Assert
    assert report.counts_by_reviewer_round == {"R1/R1": 1}


def test_validate_overlays_dangling_ref_marks_report_not_ok():
    # Arrange
    overlays = [
        Overlay(
            overlay_id="o1",
            kind="reviewer_comment",
            status="open",
            claims_touched=["c1", "ghost"],
        ),
    ]
    # Act
    report = validate_overlays(overlays, known_claim_ids=["c1"])
    # Assert
    assert report.ok is False


def test_validate_overlays_dangling_refs_counted_in_unresolved():
    # Arrange
    overlays = [
        Overlay(
            overlay_id="o1",
            kind="reviewer_comment",
            status="open",
            claims_touched=["c1", "ghost", "also_ghost"],
        ),
    ]
    # Act
    report = validate_overlays(overlays, known_claim_ids=["c1"])
    # Assert
    assert report.n_unresolved_claim_refs == 2


def test_validate_overlays_dangling_refs_record_offending_claim_ids():
    # Arrange
    overlays = [
        Overlay(
            overlay_id="o1",
            kind="reviewer_comment",
            status="open",
            claims_touched=["c1", "ghost", "also_ghost"],
        ),
    ]
    # Act
    report = validate_overlays(overlays, known_claim_ids=["c1"])
    # Assert
    assert {r["claim_id"] for r in report.unresolved_refs} == {
        "ghost",
        "also_ghost",
    }


def test_validate_overlays_aggregates_status_counts_open_branch():
    # Arrange
    overlays = [
        Overlay(overlay_id="o1", kind="reviewer_comment", status="open"),
        Overlay(overlay_id="o2", kind="reviewer_comment", status="open"),
        Overlay(overlay_id="o3", kind="reviewer_comment", status="addressed"),
    ]
    # Act
    report = validate_overlays(overlays, known_claim_ids=[])
    # Assert
    assert report.counts_by_status["open"] == 2


def test_validate_overlays_aggregates_status_counts_addressed_branch():
    # Arrange
    overlays = [
        Overlay(overlay_id="o1", kind="reviewer_comment", status="open"),
        Overlay(overlay_id="o2", kind="reviewer_comment", status="open"),
        Overlay(overlay_id="o3", kind="reviewer_comment", status="addressed"),
    ]
    # Act
    report = validate_overlays(overlays, known_claim_ids=[])
    # Assert
    assert report.counts_by_status["addressed"] == 1


# EOF
