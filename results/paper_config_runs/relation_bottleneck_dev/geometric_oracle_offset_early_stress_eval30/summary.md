# Geometric-Oracle Maneuvering-Target Reachability

This diagnostic uses a deterministic non-learning policy to test whether the maneuvering-target scenario can form attack windows under the current 3DOF dynamics and attack-window constraints.

## Files

- Step trace: `results/paper_config_runs/relation_bottleneck_dev/geometric_oracle_offset_early_stress_eval30/step_trace.csv`
- Summary: `results/paper_config_runs/relation_bottleneck_dev/geometric_oracle_offset_early_stress_eval30/summary.csv`

## Summary

| Case | Mode | Target | Success | Collision | Min range | Range reduction | Tracking | Max geometry | Geometry > 0.25 | Attack-window episodes |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `straight_offset` | `offset` | `straight` | 1.000 | 0.000 | 5202.1 | 19498.7 | 0.430 | 0.898 | 1.000 | 1.000 |
