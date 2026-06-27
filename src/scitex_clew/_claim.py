#!/usr/bin/env python3
# Timestamp: "2026-06-27 (ywatanabe)"
"""Thin re-exporter — public API preserved from the refactored _claims/ package.

All logic has been extracted to src/scitex_clew/_claims/ for maintainability.
This module continues to expose the same public symbols so that existing
``from scitex_clew._claim import ...`` imports continue to work unchanged.
"""

from __future__ import annotations

from ._claims import (
    CLAIM_TYPES,
    Claim,
    ClaimVerification,
    VerificationResult,
    _classify_claim,
    _ensure_claims_table,
    _generate_claim_id,
    _resolve_claim,
    _update_claim_status,
    add_claim,
    export_claims_json,
    format_claims,
    list_claims,
    migrate_add_claims_table,
    verify_all_claims,
    verify_claim,
    verify_claims_dag,
)

# Expose the DAGVerification type that callers of verify_claims_dag may use.
from ._chain import DAGVerification

__all__ = [
    "CLAIM_TYPES",
    "Claim",
    "ClaimVerification",
    "VerificationResult",
    "DAGVerification",
    "add_claim",
    "list_claims",
    "verify_claim",
    "verify_all_claims",
    "verify_claims_dag",
    "export_claims_json",
    "format_claims",
    "migrate_add_claims_table",
]
