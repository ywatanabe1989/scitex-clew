#!/usr/bin/env python3
# Timestamp: "2026-06-27 (ywatanabe)"
"""Claim dataclasses and canonical claim types."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

# Canonical claim types
CLAIM_TYPES = ("statistic", "figure", "table", "text", "value")


@dataclass
class Claim:
    """A traceable assertion in a manuscript."""

    claim_id: str
    file_path: str
    line_number: Optional[int]
    claim_type: str
    claim_value: Optional[str]
    source_session: Optional[str]
    source_file: Optional[str]
    source_hash: Optional[str]
    registered_at: Optional[str] = None
    verified_at: Optional[str] = None
    status: str = "registered"

    @property
    def location(self) -> str:
        """Human-readable location string."""
        if self.line_number:
            return f"{self.file_path}:L{self.line_number}"
        return self.file_path

    def to_dict(self) -> Dict:
        return {
            "claim_id": self.claim_id,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "claim_type": self.claim_type,
            "claim_value": self.claim_value,
            "source_session": self.source_session,
            "source_file": self.source_file,
            "source_hash": self.source_hash,
            "registered_at": self.registered_at,
            "verified_at": self.verified_at,
            "status": self.status,
        }


@dataclass
class ClaimVerification:
    """Per-claim verification outcome (one row of a :class:`VerificationResult`)."""

    claim_id: str
    location: str
    claim_value: Optional[str]
    status: Optional[str]
    source_file: Optional[str]
    source_session: Optional[str]
    source_verified: bool
    chain_verified: bool
    outcome: str  # exit-code NAME: "OK" / "UNVERIFIED" / "HASH_MISMATCH" / ...
    severity: str  # resolved severity for this outcome: error/warning/ignore/ok
    details: List[str]

    @property
    def is_verified(self) -> bool:
        return self.outcome == "OK"

    def to_dict(self) -> Dict:
        return {
            "claim_id": self.claim_id,
            "location": self.location,
            "claim_value": self.claim_value,
            "status": self.status,
            "source_file": self.source_file,
            "source_session": self.source_session,
            "source_verified": self.source_verified,
            "chain_verified": self.chain_verified,
            "outcome": self.outcome,
            "severity": self.severity,
            "details": self.details,
        }


@dataclass
class VerificationResult:
    """Structured result of ``verify_all_claims`` / ``clew verify`` (claim-set mode).

    The single object a harness branches on. ``exit_code`` is the fail-loud
    contract code (see :mod:`scitex_clew._cli._exit_codes`); ``ok`` is the
    DONE-gate. Per-pattern severity (configurable via ``.scitex/clew``) decides
    which fired patterns count as ``errors`` (fail) vs ``warnings`` (tolerated).
    ``.to_dict()`` returns the canonical CLI ``--json`` shape.
    """

    exit_code: int
    exit_name: str
    reason: str
    strict: bool
    total: int
    verified: int
    counts: Dict[str, int]
    claims: List[ClaimVerification]
    severities: Dict[str, str]  # pattern key -> resolved severity (transparency)
    errors: List[str]  # pattern NAMES that fired at ERROR severity
    warnings: List[str]  # pattern NAMES that fired at WARNING severity

    @property
    def ok(self) -> bool:
        """True iff exit_code == 0 — a solver may then legitimately signal DONE."""
        return self.exit_code == 0

    def to_dict(self) -> Dict:
        return {
            "exit_code": self.exit_code,
            "exit_name": self.exit_name,
            "reason": self.reason,
            "strict": self.strict,
            "total": self.total,
            "verified": self.verified,
            "counts": self.counts,
            "severities": self.severities,
            "errors": self.errors,
            "warnings": self.warnings,
            "claims": [c.to_dict() for c in self.claims],
        }


# EOF
