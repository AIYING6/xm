# KLR Final Replication P0 readiness report

**Status:** `KLR_FINAL_REPLICATION_READY_FOR_AUTHORIZATION`

P0 performed no environment rollout, checkpoint evaluation, algorithm modification, or cloud training. The five synthetic Full-Rollback KLR tests passed, including actor/Adam rollback, critic retention, non-finite transaction restoration, default-off equivalence, and deterministic save/reload.

- Historical KLR implementation commit: `3c17bf62`
- Exact KLR: `post_step_actor_rollback`, full-rollout empirical KL threshold `0.02`
- Cohort A: 3701--3705; Cohort B: 3706--3710
- Seed provenance: `CLEAN` across 1112 source/config/document files; no declared-seed identifier hit
- Frozen development tape IDs: 620000--620099; canonical tape hash: `9eee7463ae55ea0a2a5a263810e432b47923704a5d517a464784db278378b455`
- Future-only scope: 30 trajectories × 499,968 training steps = 14,999,040 steps; 0.25M and 0.5M milestones; 15,000 evaluation episodes at the fixed 5 conditions.
- Recommended cloud cap: 9 parallel training/evaluation workers on a single 12-GB GPU; expected result/log/checkpoint footprint below 2 GiB, with a 15-GiB minimum free-disk preflight.

The two cohorts must be judged separately. A pass requires both cohorts to satisfy all frozen retention, downside, catastrophic, dispersion, upper-tail, safety and integrity criteria. This document authorizes nothing: a separate human authorization is required before training.

## Integrity hashes

| Artifact | SHA-256 |
|---|---|
| freeze | `145d673d55d944d61745f1fbe4cb054423f10d89c2dd0fc1026fedd2325e5985` |
| tape file | `3af1874ee4a6d6bc8290099c508c698c8e6460671e15ba0e6e857c76eb24a676` |
| technical audit | `81218303efceb246f1c7d771abf848945900ecc712815f80335c9b230f323965` |
| seed provenance | `87001a8462f6b94b70a1ae95201315d13f10fd9900803f1f5ac1457cc0c0d084` |
