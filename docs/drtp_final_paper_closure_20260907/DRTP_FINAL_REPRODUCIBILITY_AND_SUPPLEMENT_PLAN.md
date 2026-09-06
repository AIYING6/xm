# DRTP reproducibility and Supplementary Material plan

## Main-text reproducibility disclosure

- Exact environment, policy and PPO configuration shared by UTR and DRTP.
- Frozen topology-group support, nominal mass, q bounds, warm-up and update interval.
- Fresh A/B seed registries, final 10M endpoint, and statement that the training seed is the independent unit.
- Separate cohort reporting and fixed evaluation tapes inaccessible during training.

## Supplementary inventory

1. Seed registry and hash-locked configuration files.
2. Complete per-seed endpoint tables for A, B, held-out/OOD, PLR-style and 6-UAV studies.
3. Definitions of every topology/failure condition and every OOD shift.
4. Sampler manifests and q trajectories for all Original DRTP training seeds.
5. Full evaluation condition manifest and raw episode schema.
6. Commands needed to reproduce training, endpoint evaluation, aggregation and figure generation.
7. Historical development cohorts, labelled as development/historical rather than confirmatory evidence.
8. Runtime-state schema and checkpoint hashes.

## Disclosure boundary

Historical reversals must be reported transparently in the supplement, with their seed ranges and protocol status. They must not be blended with fresh confirmation cohorts or selectively omitted; neither should they replace the frozen primary cohort analyses.

