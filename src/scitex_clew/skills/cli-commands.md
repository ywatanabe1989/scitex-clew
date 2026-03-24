## CLI Commands

```bash
# Execution
scitex-clew run <claim>          # Run single claim
scitex-clew run --all            # Run all claims
scitex-clew rerun-claims         # Rerun failed
scitex-clew rerun-dag            # Rerun full DAG

# Inspection
scitex-clew list                 # List all claims
scitex-clew status               # Verification status
scitex-clew stats                # Summary statistics
scitex-clew chain <claim>        # Show dependency chain
scitex-clew dag                  # Show full DAG
scitex-clew mermaid              # DAG as Mermaid diagram

# Skills
scitex-clew skills list
scitex-clew skills get SKILL
```
