#!/usr/bin/env python3
# Timestamp: "2026-06-27 (ywatanabe)"
"""Claims DAG verification: build unified DAG from all claims."""

from __future__ import annotations

from typing import Optional

from ._db_ops import list_claims


def verify_claims_dag(
    file_path: Optional[str] = None,
    claim_type: Optional[str] = None,
):
    """Build a unified DAG from all claims, tracing each back to its source.

    Parameters
    ----------
    file_path : str, optional
        Filter claims by manuscript file path.
    claim_type : str, optional
        Filter claims by type.

    Returns
    -------
    DAGVerification
        Unified verification result covering all claim source chains merged.
    """
    from .._chain import DAGVerification, VerificationStatus
    from .._chain._dag import verify_dag

    claims = list_claims(file_path=file_path, claim_type=claim_type)

    # Collect unique source files from claims
    source_files = []
    for c in claims:
        if c.source_file and c.source_file not in source_files:
            source_files.append(c.source_file)

    if not source_files:
        return DAGVerification(
            target_files=[],
            runs=[],
            edges=[],
            status=VerificationStatus.UNKNOWN,
            topological_order=[],
        )

    return verify_dag(source_files)


# EOF
