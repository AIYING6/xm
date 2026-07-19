# Hardened 60-Update Collision Replay

Generated: 2026-07-19T01:30:20

This audit replays the disjoint-test collision episodes from the hardened 60-update development run. It is a safety diagnostic, not a new training result.

## Files

- Per-step trace CSV: `results/intercept_3d_gate1_hardened_60update_3seed_dev/collision_replay/collision_replay_trace.csv`

## Summary

| Case | Method | Train seed | Episode seed | Steps | Collision pair | Min blue-red | Min blue-red step | Min blue-blue | Min blue-blue step | Tracking during failure | Connectivity during failure |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| case01 | `multi_relation` | 1 | 250019 | 45 | blue0-blue2 | 5173.4 (blue2-red0) | 45 | 114.2 (blue0-blue2) | 45 | 0.666667 | 0.305555 |
| case02 | `single` | 1 | 250009 | 55 | blue0-red0 | 31.3 (blue0-red0) | 55 | 1931.0 (blue0-blue2) | 45 | 0.541667 | 0.239583 |
| case03 | `single` | 1 | 250025 | 55 | blue0-red0 | 103.0 (blue0-red0) | 55 | 1935.3 (blue1-blue2) | 30 | 0.520833 | 0.208333 |

## Diagnostic Interpretation

- Blue-blue collision cases: 1.
- Blue-target collision cases: 2.
- All listed cases terminate during the configured node-failure interval, so they are relevant to the relay-failure safety analysis.
- The collision pairs identify different failure modes: intra-blue deconfliction for blue-blue collisions, and terminal overshoot/unsafe target approach for blue-target collisions.
- Because the validation split was zero-collision but the test split was not, safety should be reported separately from recovery and considered before a five-seed formal rerun.

## Interpretation Boundary

- A collision is triggered below the environment collision radius of 120 m.
- This replay determines which pair caused termination and whether the collision occurred during node failure.
- It does not by itself decide whether to change rewards; that decision should compare collision timing, pair type, and recovery behavior.