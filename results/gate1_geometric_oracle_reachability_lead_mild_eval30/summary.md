# Geometric-Oracle Maneuvering-Target Reachability

This diagnostic uses a deterministic non-learning policy to test whether the maneuvering-target scenario can form attack windows under the current 3DOF dynamics and attack-window constraints.

## Files

- Step trace: `results/gate1_geometric_oracle_reachability_lead_mild_eval30/step_trace.csv`
- Summary: `results/gate1_geometric_oracle_reachability_lead_mild_eval30/summary.csv`

## Summary

| Case | Mode | Target | Success | Collision | Min range | Range reduction | Tracking | Max geometry | Geometry > 0.25 | Attack-window episodes |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `weaving_mild_lead` | `lead` | `weaving_mild` | 1.000 | 0.000 | 8778.4 | 15921.3 | 0.515 | 0.566 | 1.000 | 1.000 |
