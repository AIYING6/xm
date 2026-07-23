# Maneuvering-Target Reachability Analysis

This diagnostic replays maneuvering-target policies step-by-step to determine whether failure comes from poor approach, poor tracking, or inability to form attack geometry.

## Files

- Step trace: `results/gate1_maneuver_reachability_smoke/step_trace.csv`
- Summary: `results/gate1_maneuver_reachability_smoke/summary.csv`

## Summary

| Case | Train seed | Success | Min range | Range reduction | Tracking | Max geometry | Geometry > 0.25 | Attack-window episodes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `seed0` | 0 | 1.000 | 11809.5 | 12912.1 | 0.317 | 0.325 | 1.000 | 1.000 |
| `seed1` | 1 | 0.000 | 12194.3 | 12527.4 | 0.112 | 0.060 | 0.000 | 0.000 |
