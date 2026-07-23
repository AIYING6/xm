# Geometric-Oracle Maneuvering-Target Reachability

This diagnostic uses a deterministic non-learning policy to test whether the maneuvering-target scenario can form attack windows under the current 3DOF dynamics and attack-window constraints.

## Files

- Step trace: `results/gate1_geometric_oracle_reachability_offset_eval30/step_trace.csv`
- Summary: `results/gate1_geometric_oracle_reachability_offset_eval30/summary.csv`

## Summary

| Case | Mode | Target | Success | Collision | Min range | Range reduction | Tracking | Max geometry | Geometry > 0.25 | Attack-window episodes |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `weaving_tiny_offset` | `offset` | `weaving_tiny` | 1.000 | 0.000 | 9486.5 | 15213.4 | 0.518 | 0.576 | 1.000 | 1.000 |
| `weaving_mild_offset` | `offset` | `weaving_mild` | 1.000 | 0.000 | 9266.8 | 15433.1 | 0.515 | 0.624 | 1.000 | 1.000 |
