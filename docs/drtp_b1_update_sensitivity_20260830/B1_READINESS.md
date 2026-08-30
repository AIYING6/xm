# B1 update-sensitivity readiness

**Status:** `B1_READY_FOR_AUTHORIZATION`.

The frozen design, diagnostic RNG boundary, slim checkpoint asset builder,
branch runner, development tape, evaluator, automatic evidence builder, and
cloud launcher are present. No B1 branch training or evaluation has run.

## Integrity audit

- 40/40 paired 0.5M runtime checkpoints load successfully.
- Every checkpoint reports update 1953, four environment states, a model and
  optimizer state, and the expected UTR/Original-DRTP sampler mode and seed.
- Freeze SHA256: `385d6c954d9f203caae6eb81900ef6767368804dabff7b1617b8a9e6695f5fed`.
- Development tape SHA256:
  `a49be9ad54ee0e6b2dabfb437a71ffcf0e11ac265d62cd552e0ef841f0071950`.
- Slim asset manifest SHA256:
  `c61edf331413e577a6dbb01b98dbb9d09528d23b41849c4b05b57230c76c6e4d`.
- Slim uncompressed assets: approximately 70.4 MiB instead of roughly 3 GiB
  of source archives.

The source-log copies retain only updates 1954--2017 for technical replay
comparison. Source archives and checkpoints are never overwritten.

## Frozen compute

- 20 source training seeds across four cohorts.
- UTR and Original DRTP at the same 0.5M source checkpoint.
- Four rollout-RNG and four minibatch negative-control branches per source.
- 320 short trajectories, 64 updates each.
- 5,242,880 training environment interactions.
- Fixed evaluation only at branch horizons 16 and 64: 64,000 episodes.
- Default cloud concurrency: 20; every worker uses one CPU thread.
- Expected assets plus branch artifacts fit comfortably on a 50 GiB data
  disk; the final result archive may be several GiB because all frozen
  diagnostic checkpoints are retained.

## Authorization boundary

The launcher refuses to run unless `B1_EXECUTION_AUTHORIZED=YES` is supplied.
Successful execution ends at
`B1_UPDATE_RELIABILITY_GATE_READY_FOR_REVIEW`; it cannot declare a mechanism,
create Reliable-DRTP, or continue training automatically.

Mainline A is unchanged.
