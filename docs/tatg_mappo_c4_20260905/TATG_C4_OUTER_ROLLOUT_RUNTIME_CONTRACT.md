# TATG-MAPPO C4 — outer rollout and strict continuation contract

## Scope

C4 is the first real-environment integration audit. It uses only the existing 3D UAV environment and fixed UTR exposure. The brief two-step timeout is audit instrumentation to exercise completed-slot reset; it is not a training condition or performance benchmark.

## Frozen system boundary

- The temporal actor is CETM, generic snapshot-GRU, or zero-residual CETM through the C3.5 adapter.
- The centralized critic is architecturally and initially weight-identical to the snapshot critic.
- The copied snapshot policy head is excluded from the temporal optimizer because the replacement `temporal_policy_head` is its active policy output.
- The outer runtime checkpoint contains model state, unstepped optimizer state, environment states, current observations/graphs, action-generator state and the three CETM runtime tensors.

## Prohibitions

No PPO optimizer step, reward or environment-source change, adaptive sampler, group weighting, evaluation, return comparison, checkpoint selection, fresh-seed training or cloud execution is permitted.

## Decision boundary

`TATG_C4_OUTER_ROLLOUT_RUNTIME_PASS` permits only a separately frozen first-update same-rollout audit. It does not authorize a training pilot or performance claim.
