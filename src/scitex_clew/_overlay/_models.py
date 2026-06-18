#!/usr/bin/env python3
# Timestamp: "2026-06-12 (proj-paper-scitex-clew, op-2026-06-12-10)"
# File: src/scitex_clew/_overlay/_models.py
"""Dataclasses + vocabularies for the overlay layer.

Pure data definitions — no sqlite, no I/O — so they can be reused by
consumers (scitex-writer, scitex-live-paper) without paying the DB cost.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Vocabularies
# ---------------------------------------------------------------------------

#: Verdicts emitted by the structural verifier.
VERDICTS = ("pass", "fail", "inconclusive")

#: Overlay kinds — extensible; readers should treat unknown kinds as opaque.
OVERLAY_KINDS = (
    "reviewer_comment",
    "editor_note",
    "preprint_revision",
    "external_audit",
)

#: Overlay lifecycle status.
OVERLAY_STATUSES = ("open", "addressed", "deferred", "wontfix")


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------


@dataclass
class Dataset:
    """Schema'd dataset provenance pointer for a claim.

    The ``(cohort, source, capsule_id)`` triple is the dataset identity —
    sufficient to mechanise cross-cohort reuse and to render "from
    CORE-Bench capsule-1624349" chips in the manuscript.

    Optional ``version`` / ``url`` / ``license`` / ``split`` provide enough
    surface for reviewers to audit dataset origin without resolving the
    capsule manually.
    """

    cohort: str
    source: str
    capsule_id: str
    version: Optional[str] = None
    url: Optional[str] = None
    license: Optional[str] = None
    split: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Dataset":
        return cls(
            cohort=d["cohort"],
            source=d["source"],
            capsule_id=d["capsule_id"],
            version=d.get("version"),
            url=d.get("url"),
            license=d.get("license"),
            split=d.get("split"),
        )


# ---------------------------------------------------------------------------
# VerifyStatus
# ---------------------------------------------------------------------------


@dataclass
class VerifyStatus:
    """Per-claim verifier outcome — written by the structural verifier.

    ``mask_verified`` records whether the verifier confirmed that the
    capsule that produced the claim could NOT read the oracle at OS level
    (the structural-masking discipline). A verdict without
    ``mask_verified=True`` is honor-system only.
    """

    verdict: str  # one of VERDICTS
    verifier_run: str
    mask_verified: bool
    score_json: Optional[str] = None
    recorded_at: Optional[str] = None

    def __post_init__(self) -> None:
        if self.verdict not in VERDICTS:
            raise ValueError(
                f"Invalid verdict '{self.verdict}'. Must be one of: {VERDICTS}"
            )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "VerifyStatus":
        return cls(
            verdict=d["verdict"],
            verifier_run=d["verifier_run"],
            mask_verified=bool(d["mask_verified"]),
            score_json=d.get("score_json"),
            recorded_at=d.get("recorded_at"),
        )


# ---------------------------------------------------------------------------
# Overlay
# ---------------------------------------------------------------------------


@dataclass
class Overlay:
    """A peer-review / preprint overlay record.

    An overlay annotates one or more claims with reviewer commentary or
    revision metadata. ``claims_touched`` is the join key; the same overlay
    can reference any number of claims, and the same claim can carry any
    number of overlays.
    """

    overlay_id: str
    kind: str  # one of OVERLAY_KINDS (consumers should treat unknown kinds as opaque)
    status: str  # one of OVERLAY_STATUSES
    claims_touched: List[str] = field(default_factory=list)
    round: Optional[str] = None
    reviewer: Optional[str] = None
    comment_idx: Optional[int] = None
    preprint_section: Optional[str] = None
    preprint_line_marker: Optional[str] = None
    resolution_commit: Optional[str] = None
    resolution_data_run: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self) -> None:
        if self.status not in OVERLAY_STATUSES:
            raise ValueError(
                f"Invalid overlay status '{self.status}'. "
                f"Must be one of: {OVERLAY_STATUSES}"
            )
        # NB: ``kind`` intentionally not validated against OVERLAY_KINDS —
        # downstream consumers should accept unknown kinds (forward compat).

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Overlay":
        return cls(
            overlay_id=d["overlay_id"],
            kind=d["kind"],
            status=d["status"],
            claims_touched=list(d.get("claims_touched") or []),
            round=d.get("round"),
            reviewer=d.get("reviewer"),
            comment_idx=d.get("comment_idx"),
            preprint_section=d.get("preprint_section"),
            preprint_line_marker=d.get("preprint_line_marker"),
            resolution_commit=d.get("resolution_commit"),
            resolution_data_run=d.get("resolution_data_run"),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
        )


# ---------------------------------------------------------------------------
# ValidationReport
# ---------------------------------------------------------------------------


@dataclass
class ValidationReport:
    """Result of :func:`scitex_clew._overlay.validate_overlays`."""

    n_overlays: int
    n_claims_touched_total: int
    n_unresolved_claim_refs: int
    unresolved_refs: List[Dict[str, str]]  # [{"overlay_id":..., "claim_id":...}, ...]
    counts_by_status: Dict[str, int]
    counts_by_reviewer_round: Dict[str, int]
    ok: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


__all__ = [
    "VERDICTS",
    "OVERLAY_KINDS",
    "OVERLAY_STATUSES",
    "Dataset",
    "VerifyStatus",
    "Overlay",
    "ValidationReport",
]

# EOF
