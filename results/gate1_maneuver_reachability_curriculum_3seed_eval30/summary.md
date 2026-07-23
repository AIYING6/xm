# Maneuvering-Target Reachability Analysis

This diagnostic replays maneuvering-target policies step-by-step to determine whether failure comes from poor approach, poor tracking, or inability to form attack geometry.

## Files

- Step trace: `results/gate1_maneuver_reachability_curriculum_3seed_eval30/step_trace.csv`
- Summary: `results/gate1_maneuver_reachability_curriculum_3seed_eval30/summary.csv`

## Summary

| Case | Train seed | Success | Min range | Range reduction | Tracking | Max geometry | Geometry > 0.25 | Attack-window episodes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `seed0` | 0 | 0.533 | 12047.9 | 12652.1 | 0.285 | 0.165 | 0.367 | 0.533 |
| `seed1` | 1 | 0.000 | 12761.0 | 11939.2 | 0.193 | 0.031 | 0.000 | 0.000 |
| `seed2` | 2 | 0.267 | 12998.3 | 11701.6 | 0.234 | 0.223 | 0.467 | 0.267 |
