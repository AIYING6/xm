# TATG-MAPPO C3.5 — actor-runner integration contract

## Scope

C3.5 creates only an isolated actor adapter. It is the unique owner of the CETM state used while collecting a vectorized rollout and replaying its actor term. The legacy snapshot runner remains unmodified.

## Required lifecycle

1. Snapshot `TATGRuntimeStateBank` before the rollout's first action.
2. At each graph row, calculate logits and selected-action log-probability before storing the selected action as `a_previous`.
3. After a completed environment has reset, replace only that slot's CETM state using the reset graph before the next graph row.
4. For every PPO actor epoch, recreate a temporary state bank from the saved rollout-start payload and replay the full `[time, environment]` tensor chronologically.
5. A strict runtime restore must contain only `tatg_memory_state.memory`, `previous_topology`, and `previous_action`, and reproduce the next actor call exactly when the outer model/optimizer/RNG payload is equivalently restored.

## Controls and prohibitions

CETM, generic current-snapshot GRU, and zero-residual CETM must use this exact adapter. The adapter must not own an environment, reward, sampler, critic, evaluation tape, return, failure schedule, seed label, checkpoint selection or a PPO optimizer step.

## Decision boundary

`TATG_C35_ACTOR_RUNNER_INTEGRATION_PASS` permits only a separately frozen outer rollout-loop and strict runtime-checkpoint integration audit. It does not authorize environment rollout, cloud/fresh-seed training, evaluation, or a performance claim.
