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

import scitex_clew as clew


def main():
    """Run Mermaid diagram generation example."""
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
        print()
        print("Usage:")
        print("  1. Embed in GitHub Markdown:")
        print("     ``` mermaid")
        print("     <paste code above>")
        print("     ```")
        print()
        print(
            "  2. Render with mermaid-cli (requires: npm install -g @mermaid-js/mermaid-cli):"
        )
        print("     mmdc -i diagram.mmd -o diagram.png")
        print()
        print("  3. View online at https://mermaid.live")
    else:
        print("No runs tracked yet.")
        print("Run '00_run_all.sh' in /tmp/clew_example to generate pipeline outputs.")
        print()
        print("Then run this script again to see the DAG diagram.")

    return 0


if __name__ == "__main__":
    main()

# EOF
