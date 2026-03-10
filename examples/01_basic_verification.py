#!/usr/bin/env python3
"""Basic verification example - verify a session run.

This example demonstrates the simplest usage of scitex-clew:
1. Initialize bundled example data
2. Query the verification status
3. List tracked runs

Run this script to see:
- Overall verification status summary
- List of tracked session runs
- Status of each run (success/failed/unknown)
"""

import scitex_clew as clew


def main():
    """Run basic verification example."""
    # Initialize example pipeline
    # This copies bundled example scripts to /tmp/clew_example
    # You would run "python 00_run_all.sh" to generate the pipeline outputs
    print("Initializing example pipeline...")
    examples = clew.init_examples("/tmp/clew_example")
    print(f"  Copied to: {examples['path']}")
    print(f"  Files: {examples['file_count']}")
    print()

    # Show verification status (like git status)
    print("=== Verification Status ===")
    status = clew.status()
    print(f"Total runs: {status.get('total_runs', 0)}")
    print(f"Verified runs: {status.get('verified_runs', 0)}")
    print(f"Failed runs: {status.get('failed_runs', 0)}")
    print()

    # List recent runs
    print("=== Recent Runs (limit=5) ===")
    runs = clew.list_runs(limit=5)
    if runs:
        for run in runs:
            session_id = run["session_id"]
            script_path = run.get("script_path", "unknown")
            run_status = run.get("status", "unknown")
            print(f"  {session_id}: {script_path} [{run_status}]")
    else:
        print("  No runs tracked yet.")
        print(
            "  Run '00_run_all.sh' in the examples directory to generate pipeline outputs."
        )
    print()

    # Show database statistics
    print("=== Database Statistics ===")
    stats = clew.stats()
    print(f"Total sessions: {stats.get('total_runs', 0)}")
    print(f"Total files: {stats.get('total_files', 0)}")
    print(f"Database location: {stats.get('db_path', 'unknown')}")

    return 0


if __name__ == "__main__":
    main()

# EOF
