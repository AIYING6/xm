# Maneuvering-Target Reachability Analysis

This diagnostic replays maneuvering-target policies step-by-step to determine whether failure comes from poor approach, poor tracking, or inability to form attack geometry.

## Files

- Step trace: `results/gate1_oracle_bc_ppo_weaving_mild_single_seed0_cont30/reachability_eval30/step_trace.csv`
- Summary: `results/gate1_oracle_bc_ppo_weaving_mild_single_seed0_cont30/reachability_eval30/summary.csv`

## Summary

| Case | Train seed | Success | Min range | Range reduction | Tracking | Max geometry | Geometry > 0.25 | Attack-window episodes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `single_seed0_oracle_bc_ppo_cont30` | 0 | 0.333 | 13310.5 | 11399.8 | 0.395 | 0.109 | 0.100 | 0.467 |
