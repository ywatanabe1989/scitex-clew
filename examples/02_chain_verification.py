#!/usr/bin/env python3
"""Chain verification - trace provenance of a file.

This example demonstrates dependency chain tracing:
1. Initialize bundled example data
2. Verify the full dependency DAG
3. Print chain details

Run this script to see:
- Complete dependency chain for a target file
- Which sessions produced the file
- Verification status of each step
"""

from pathlib import Path

import scitex_clew as clew

OUT_DIR = Path(__file__).parent / "02_chain_verification_out"


def main():
    """Run chain verification example."""
    OUT_DIR.mkdir(exist_ok=True)

    print("Initializing example pipeline...")
    clew.init_examples("/tmp/clew_example")
    print()

    print("=== Chain Verification ===")
    print("Verifying the full dependency DAG...")
    print()

    # Verify the full DAG with claims support
    result = clew.dag(claims=True)

    print(f"DAG Verification Result:")
    print(
        f"  Overall Status: {result.status.value if hasattr(result, 'status') else 'unknown'}"
    )
    print(
        f"  Is Verified: {result.is_verified if hasattr(result, 'is_verified') else 'unknown'}"
    )
    print()

    # Print runs in the DAG
    if hasattr(result, "runs") and result.runs:
        print(f"  Total Runs: {len(result.runs)}")
        for run in result.runs:
            badge = "✓" if run.is_verified else "✗"
            session_id = run.session_id[:12]
            print(f"    {badge} {session_id}")
    else:
        print("  No runs tracked yet.")
        print(
            "  Run '00_run_all.sh' in /tmp/clew_example to generate pipeline outputs."
        )
    print()

    # Show edges/dependencies if available
    if hasattr(result, "edges") and result.edges:
        print(f"  Total Dependencies: {len(result.edges)}")
    else:
        print("  No dependencies tracked yet.")

    # Save report
    report_path = OUT_DIR / "chain_report.txt"
    with open(report_path, "w") as f:
        f.write(
            f"DAG Status: {result.status.value if hasattr(result, 'status') else 'unknown'}\n"
        )
        f.write(
            f"Verified: {result.is_verified if hasattr(result, 'is_verified') else 'unknown'}\n"
        )
    print(f"\nReport saved to: {report_path}")

    return 0


if __name__ == "__main__":
    main()

# EOF
