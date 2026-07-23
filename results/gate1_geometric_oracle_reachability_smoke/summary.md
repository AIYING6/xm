# Geometric-Oracle Maneuvering-Target Reachability

This diagnostic uses a deterministic non-learning policy to test whether the maneuvering-target scenario can form attack windows under the current 3DOF dynamics and attack-window constraints.

## Files

- Step trace: `results/gate1_geometric_oracle_reachability_smoke/step_trace.csv`
- Summary: `results/gate1_geometric_oracle_reachability_smoke/summary.csv`

## Summary

| Case | Mode | Target | Success | Collision | Min range | Range reduction | Tracking | Max geometry | Geometry > 0.25 | Attack-window episodes |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `weaving_tiny_offset` | `offset` | `weaving_tiny` | 1.000 | 0.000 | 8748.1 | 15939.7 | 0.522 | 0.597 | 1.000 | 1.000 |
| `weaving_mild_offset` | `offset` | `weaving_mild` | 1.000 | 0.000 | 8511.9 | 16175.9 | 0.521 | 0.618 | 1.000 | 1.000 |
