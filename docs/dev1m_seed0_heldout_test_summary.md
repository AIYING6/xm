# Seed-0 Held-Out Test Summary

Generated: 2026-07-27

Protocol: validation-selected checkpoints, strict-sensing relay-failure test split, 100 held-out matched episodes, base seed `220000`, zero-collision reporting.

| Method | Checkpoint update | Success | Recovery | Recovery steps | Tracking during failure | Connectivity during failure | Timeout | Collision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EA-RG-MAPPO | 1600 | 0.89 | 0.89 | 18.9663 | 0.562743 | 0.332292 | 0.11 | 0 |
| Single-Graph MAPPO | 3907 | 0.8 | 0.8 | 19.4875 | 0.819542 | 0.303333 | 0.2 | 0 |
| MAPPO/no-graph | 3800 | 0.6 | 0.6 | 17.8667 | 0.404787 | 0.301625 | 0.4 | 0 |
| HAPPO | 900 | 0.08 | 0.08 | 79.875 | 0.122026 | 0.0708423 | 0.92 | 0 |

Interpretation: the held-out test split preserves the validation ordering: EA-RG-MAPPO > Single-Graph MAPPO > MAPPO/no-graph > HAPPO. This is a strong seed-0 signal that the multi-relation role graph improves strict-sensing relay-failure recovery, but it is not yet a final paper claim until seeds 1/2 are trained and evaluated under the same protocol.
