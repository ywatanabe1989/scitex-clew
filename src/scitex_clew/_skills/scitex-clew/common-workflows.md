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
