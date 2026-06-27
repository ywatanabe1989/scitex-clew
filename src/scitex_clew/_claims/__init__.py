#!/usr/bin/env python3
# Timestamp: "2026-06-27 (ywatanabe)"
"""Claims package — public re-export surface (mirrors old _claim.py)."""

from __future__ import annotations

from ._dag import verify_claims_dag
from ._db_ops import (
    _ensure_claims_table,
    _generate_claim_id,
    _resolve_claim,
    _update_claim_status,
    add_claim,
    list_claims,
    migrate_add_claims_table,
)
from ._export import export_claims_json
from ._format import format_claims
from ._types import (
    CLAIM_TYPES,
    Claim,
    ClaimVerification,
    VerificationResult,
)
from ._verify import _classify_claim, verify_all_claims, verify_claim

__all__ = [
    # Types
    "CLAIM_TYPES",
    "Claim",
    "ClaimVerification",
    "VerificationResult",
    # DB operations
    "migrate_add_claims_table",
    "add_claim",
    "list_claims",
    # Verification
    "verify_claim",
    "verify_all_claims",
    "verify_claims_dag",
    # Export
    "export_claims_json",
    # Formatting
    "format_claims",
]


# EOF
