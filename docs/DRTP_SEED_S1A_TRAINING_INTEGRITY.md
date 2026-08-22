# DRTP-SEED-S1-A Training Integrity

Status before execution: `PRE-FLIGHT PASS — RUNS NOT YET COMPLETED`

Frozen checks:

- exactly seven registered trajectories;
- one-factor RNG intervention matrix passes;
- `eval_seed` is shared across all seven runs;
- `rng_decomposition=True` is required;
- SG backbone, PPO, reward, environment, failure semantics and actor boundary are unchanged;
- 5,859 updates and fixed milestone map are shared;
- no canonical or held-out namespace is consumed;
- all run directories refuse overwrite;
- final and milestone checkpoints are hashed after completion;
- bad performance is never a technical stop reason.

Completion status is written only from the actual run manifests. A scientific decision is not valid until all seven run manifests, checkpoints, telemetry schemas, and tape hashes pass the post-run audit.

