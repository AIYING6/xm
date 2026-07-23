# Maneuvering-Target Reachability Analysis

This diagnostic replays maneuvering-target policies step-by-step to determine whether failure comes from poor approach, poor tracking, or inability to form attack geometry.

## Files

- Step trace: `results/gate1_oracle_bc_ppo_weaving_mild_seed2_cont30/reachability_eval30/step_trace.csv`
- Summary: `results/gate1_oracle_bc_ppo_weaving_mild_seed2_cont30/reachability_eval30/summary.csv`

## Summary

| Case | Train seed | Success | Min range | Range reduction | Tracking | Max geometry | Geometry > 0.25 | Attack-window episodes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `seed2_oracle_bc_ppo_cont30` | 2 | 0.700 | 9219.9 | 15479.9 | 0.499 | 0.528 | 0.900 | 0.733 |
