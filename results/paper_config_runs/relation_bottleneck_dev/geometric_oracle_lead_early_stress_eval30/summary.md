# Geometric-Oracle Maneuvering-Target Reachability

This diagnostic uses a deterministic non-learning policy to test whether the maneuvering-target scenario can form attack windows under the current 3DOF dynamics and attack-window constraints.

## Files

- Step trace: `results/paper_config_runs/relation_bottleneck_dev/geometric_oracle_lead_early_stress_eval30/step_trace.csv`
- Summary: `results/paper_config_runs/relation_bottleneck_dev/geometric_oracle_lead_early_stress_eval30/summary.csv`

## Summary

| Case | Mode | Target | Success | Collision | Min range | Range reduction | Tracking | Max geometry | Geometry > 0.25 | Attack-window episodes |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `straight_lead` | `lead` | `straight` | 0.967 | 0.033 | 5273.1 | 19427.6 | 0.430 | 0.753 | 1.000 | 1.000 |
