# TATG-MAPPO C3.5 actor-runner integration audit

**Verdict:** `TATG_C35_ACTOR_RUNNER_INTEGRATION_PASS`.

The isolated actor adapter now owns the frozen collection/replay lifecycle: it saves the CETM state before a rollout, evaluates log-probability before recording the selected action, resets only completed slots from their new reset graph, and replays full sequences chronologically. Restoring its three-tensor runtime payload reproduces the next actor call exactly.

It deliberately has no environment, critic, reward, sampler, evaluation or checkpoint-selection path. CETM, the capacity-matched current-snapshot GRU control and zero-residual CETM all use the same actor-runner interface. This is synthetic interface verification only, not PPO training or a performance result.

## Checks

- `collection_records_actions_only_after_logprobability`: `True`
- `stored_rollout_start_state_replays_exactly`: `True`
- `completed_environment_resets_before_following_graph`: `True`
- `strict_runner_state_restore_continues_exactly`: `True`
- `generic_control_uses_identical_collection_and_replay_interface`: `True`
- `zero_residual_control_uses_identical_collection_and_replay_interface`: `True`
- `runtime_payload_contains_only_frozen_tatg_state`: `True`
- `adapter_owns_no_environment_critic_or_evaluation_path`: `True`

A pass authorizes only a separately frozen outer rollout-loop and strict runtime-checkpoint integration audit. It does not authorize environment rollout, fresh-seed/cloud training, evaluation or a performance claim.
