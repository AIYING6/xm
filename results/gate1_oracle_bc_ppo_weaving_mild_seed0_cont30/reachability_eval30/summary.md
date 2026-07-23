# Maneuvering-Target Reachability Analysis

This diagnostic replays maneuvering-target policies step-by-step to determine whether failure comes from poor approach, poor tracking, or inability to form attack geometry.

## Files

- Step trace: `results/gate1_oracle_bc_ppo_weaving_mild_seed0_cont30/reachability_eval30/step_trace.csv`
- Summary: `results/gate1_oracle_bc_ppo_weaving_mild_seed0_cont30/reachability_eval30/summary.csv`

## Summary

| Case | Train seed | Success | Min range | Range reduction | Tracking | Max geometry | Geometry > 0.25 | Attack-window episodes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `seed0_oracle_bc_ppo_cont30` | 0 | 0.767 | 10503.3 | 14201.1 | 0.462 | 0.182 | 0.167 | 0.800 |
