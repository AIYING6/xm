# Geometric-Oracle Maneuvering-Target Reachability

This diagnostic uses a deterministic non-learning policy to test whether the maneuvering-target scenario can form attack windows under the current 3DOF dynamics and attack-window constraints.

## Files

- Step trace: `results/gate1_geometric_oracle_reachability_direct_mild_eval30/step_trace.csv`
- Summary: `results/gate1_geometric_oracle_reachability_direct_mild_eval30/summary.csv`

## Summary

| Case | Mode | Target | Success | Collision | Min range | Range reduction | Tracking | Max geometry | Geometry > 0.25 | Attack-window episodes |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `weaving_mild_direct` | `direct` | `weaving_mild` | 0.667 | 0.367 | 8775.5 | 15924.2 | 0.521 | 0.520 | 1.000 | 0.667 |
