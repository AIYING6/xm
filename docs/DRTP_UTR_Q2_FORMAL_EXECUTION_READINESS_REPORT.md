# DRTP/UTR Q2 Formal Confirmation Execution Readiness

**Status:** `TECHNICAL_PREFLIGHT_PASS / LOCAL LONG TRAINING IN PROGRESS`

The remaining high-value experiment has been converted from a general wish
list into one prospective, executable comparison. It is intentionally limited
to matched UTR versus DRTP; no new method, component ablation, scalability run,
HIL run, or canonical-seed experiment is bundled into this stage.

## Frozen execution scope

- methods: `UTR-SG-MAPPO`, `DRTP-SG-MAPPO`;
- paired training seeds: `2301–2305`;
- ten strict-continuous, from-scratch trajectories;
- common budget: `39,063` updates / `10,000,128` environment steps each;
- total authorized training volume: `100,001,280` environment steps;
- common 116,728-parameter Single-Graph actor/critic and frozen PPO/S2 task;
- prospective tape: `490000–490099`, 12 conditions, 100 episodes each;
- final common 10M checkpoint only for the method decision;
- training seed is the independent inferential unit (`n=5`).

## Technical evidence

The zero-training preflight in
`artifacts/drtp_utr_q2_formal/preflight.json` passed all checks:

- ten authorized trajectories and no canonical seed;
- exact common budget and fixed milestones;
- 116,728 parameters for both arms;
- every non-sampler configuration field identical;
- uniform versus adaptive sampler mode is the sole method difference;
- runtime-state persistence from update zero and no historical resume;
- frozen 490k tape and all 12 condition definitions;
- no training started by the preflight.

Additional local verification passed:

- three prospective-contract and synthetic aggregation tests;
- three actor information-boundary regression tests;
- all five frozen S2 graph-legality checks;
- Python compilation for the tape, training, evaluation, aggregation,
  preflight, and packaging entry points.

Frozen tape hash:

`84e31ed185ced0608a30c9cb9f9659c7423c952e4603aac53cf691c54fc64ac2`

The executable path contains fail-closed overwrite guards, per-run manifests,
checkpoint/runtime hashes, progress logs, common final evaluation, seed-level
aggregation, result packaging, and a strict stop after the decision report.

## Evidence-chain boundary

This experiment does not erase or relabel historical development `NO-GO`,
held-out `FAIL`, `DRTP_Q2_LIMITATION_ONLY`, seed1902 weakness, seed2002
catastrophic reversal, or unresolved S1-R mechanism causality. A favorable
result can support only a high-upside, seed-sensitive DRTP claim. An
unfavorable result demotes DRTP; it does not trigger another algorithm search.

## Next authorized action

Local execution started on 2026-08-24 after the contract-freeze commit. The
Windows controller runs two trajectories concurrently on the available GTX
1650 Ti and queues the remaining trajectories without changing their budgets.
After the ten final checkpoints are evaluated, stop and reconstruct the
manuscript from the combined historical and prospective evidence. No follow-on
experiment is automatically authorized.
