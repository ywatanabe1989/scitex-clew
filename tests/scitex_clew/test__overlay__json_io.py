#!/usr/bin/env python3
# Timestamp: "2026-06-12 (proj-paper-scitex-clew, op-2026-06-12-10)"
# File: tests/scitex_clew/test__overlay__json_io.py
"""Round-trip + shape tests for overlays.json serialization."""

from __future__ import annotations

import json

import pytest

from scitex_clew._overlay import Overlay, overlays_from_json, overlays_to_json


def test_overlays_json_roundtrip_preserves_overlay_ids():
    # Arrange
    overlays = [
        Overlay(overlay_id="rev_R1_03", kind="reviewer_comment", status="open"),
        Overlay(
            overlay_id="rev_R1_04", kind="reviewer_comment", status="addressed"
        ),
    ]
    # Act
    parsed = overlays_from_json(overlays_to_json(overlays))
    # Assert
    assert {ov.overlay_id for ov in parsed} == {"rev_R1_03", "rev_R1_04"}


def test_overlays_json_roundtrip_preserves_claims_touched():
    # Arrange
    ov = Overlay(
        overlay_id="rev_R1_03",
        kind="reviewer_comment",
        status="open",
        claims_touched=["c1", "c2"],
    )
    # Act
    parsed = overlays_from_json(overlays_to_json([ov]))
    # Assert
    assert parsed[0].claims_touched == ["c1", "c2"]


def test_overlays_json_roundtrip_preserves_resolution_commit():
    # Arrange
    ov = Overlay(
        overlay_id="rev_R1_04",
        kind="reviewer_comment",
        status="addressed",
        resolution_commit="cafef00d",
    )
    # Act
    parsed = overlays_from_json(overlays_to_json([ov]))
    # Assert
    assert parsed[0].resolution_commit == "cafef00d"


def test_overlays_to_json_outer_key_is_overlay_id():
    # Arrange
    overlays = [
        Overlay(overlay_id="o1", kind="reviewer_comment", status="open"),
    ]
    # Act
    raw = json.loads(overlays_to_json(overlays))
    # Assert
    assert "o1" in raw


def test_overlays_to_json_body_does_not_duplicate_overlay_id():
    # Arrange
    overlays = [
        Overlay(overlay_id="o1", kind="reviewer_comment", status="open"),
    ]
    # Act
    raw = json.loads(overlays_to_json(overlays))
    # Assert — id lives on the outer key, never inside the body
    assert "overlay_id" not in raw["o1"]


def test_overlays_from_json_rejects_non_object_payload():
    # Arrange
    bad_payload = "[]"
    # Act
    call = lambda: overlays_from_json(bad_payload)
    # Assert
    with pytest.raises(ValueError, match="JSON object"):
        call()


# EOF
