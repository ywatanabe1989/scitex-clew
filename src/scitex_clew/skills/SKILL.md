---
name: scitex-clew
description: Computational claim verification with DAG-based reproducibility tracking. Use when defining, running, verifying, or auditing scientific claims and their evidence chains.
allowed-tools: mcp__scitex__clew_*
---

# Claim Verification with scitex-clew

## Quick Start

```python
import scitex_clew as clew

# Run a claim verification
result = clew.run("claim_accuracy_above_95")

# Check DAG of dependencies
dag = clew.dag()

# Get status of all claims
status = clew.status()
```

## Common Workflows

### "Define a claim"

Claims are defined in `claims.yaml`:
```yaml
claims:
  accuracy_above_95:
    description: "Model accuracy exceeds 95%"
    script: scripts/evaluate_model.py
    depends_on: [train_model]
    evidence: results/metrics.json
```

### "Run verification"

```bash
# Run single claim
scitex-clew run accuracy_above_95

# Run all claims
scitex-clew run --all

# Rerun failed claims
scitex-clew rerun-claims
```

### "Check dependency DAG"

```bash
# Show DAG structure
scitex-clew dag

# Visualize as Mermaid
scitex-clew mermaid > claims_dag.mmd

# Show chain for a claim
scitex-clew chain accuracy_above_95
```

### "Audit reproducibility"

```bash
# Overall status
scitex-clew status

# Statistics
scitex-clew stats
```

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

## MCP Tools (for AI agents)

| Tool | Purpose |
|------|---------|
| `clew_run` | Run a claim verification |
| `clew_list` | List all defined claims |
| `clew_status` | Get verification status |
| `clew_stats` | Summary statistics |
| `clew_chain` | Show dependency chain |
| `clew_dag` | Show full DAG |
| `clew_mermaid` | DAG as Mermaid diagram |
| `clew_rerun_claims` | Rerun failed claims |
| `clew_rerun_dag` | Rerun full DAG |
