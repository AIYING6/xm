# TATG-MAPPO C3 — chronological same-rollout PPO correctness contract

## Scope

C3 implements the actor-side chronological replay specified by C2.5. It consumes only synthetic `[time, environment]` graph/action/done tensors and a frozen rollout-start CETM state. It does not instantiate an environment or modify the existing rollout runner.

## Required behavior

- Before an optimizer mutation, chronological replay must exactly reproduce the stored action log-probabilities.
- The replay must reset only a completed environment slot before its following graph row.
- The ordinary clipped PPO actor objective must remain finite.
- The first synthetic gradient must reach the added temporal policy head. Because its new memory columns are zero-initialized to preserve snapshot equivalence, one deterministic synthetic optimizer step may be used only to confirm that the second same-rollout gradient reaches CETM's GRUCell.
- CETM, generic current-snapshot GRU and zero-residual CETM must share the replay routine and identical added actor capacity.

The synthetic optimizer mutation is a unit-level gradient-connectivity check only. It has zero environment steps, zero formal PPO updates, no checkpoint artifact, no evaluation and no return criterion.

## Decision boundary

`TATG_C3_SEQUENCE_PPO_CORRECTNESS_PASS` authorizes only a separately frozen rollout-runner integration and exact continuation audit. It does not authorize fresh-seed training, cloud training, evaluation or a performance claim.
