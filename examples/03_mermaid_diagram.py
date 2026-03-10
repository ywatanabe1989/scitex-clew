#!/usr/bin/env python3
"""Generate a Mermaid DAG diagram.

This example demonstrates Mermaid diagram generation:
1. Initialize bundled example data
2. Generate Mermaid code for the DAG
3. Print the code (can be embedded in Markdown)

Run this script to see:
- Mermaid flowchart code for the dependency DAG
- Can be embedded directly in Markdown files
- Shows nodes (scripts/data) and edges (dependencies)

The output can be:
- Embedded in GitHub markdown with ` ```mermaid ... ``` `
- Rendered using mermaid-cli: `mmdc -i diagram.mmd -o diagram.png`
- Visualized with https://mermaid.live
"""

from pathlib import Path

import scitex_clew as clew

OUT_DIR = Path(__file__).parent / "03_mermaid_diagram_out"


def main():
    """Run Mermaid diagram generation example."""
    OUT_DIR.mkdir(exist_ok=True)

    print("Initializing example pipeline...")
    clew.init_examples("/tmp/clew_example")
    print()

    print("=== Generating Mermaid DAG Diagram ===")
    print("Generating diagram from all registered claims...")
    print()

    # Generate Mermaid code
    mermaid_code = clew.mermaid(claims=True)

    if mermaid_code:
        print("Mermaid Diagram Code:")
        print("-" * 60)
        print(mermaid_code)
        print("-" * 60)

        # Save mermaid file
        mmd_path = OUT_DIR / "dag.mmd"
        with open(mmd_path, "w") as f:
            f.write(mermaid_code + "\n")
        print(f"\nDiagram saved to: {mmd_path}")
        print()
        print("Usage:")
        print("  1. Embed in GitHub Markdown with ```mermaid ... ```")
        print("  2. Render: mmdc -i dag.mmd -o dag.png")
        print("  3. View online at https://mermaid.live")
    else:
        print("No runs tracked yet.")
        print("Run '00_run_all.sh' in /tmp/clew_example to generate pipeline outputs.")

    return 0


if __name__ == "__main__":
    main()

# EOF
