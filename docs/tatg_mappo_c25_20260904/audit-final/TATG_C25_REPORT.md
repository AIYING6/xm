# TATG-MAPPO C2.5 recurrent PPO interface audit

**Verdict:** `TATG_C25_SEQUENCE_PPO_RUNNER_REQUIRED`.

The current PPO implementation correctly stores rollout arrays with time and vectorized-environment axes, but it then flattens and randomly permutes those rows for actor updates. That is valid for the snapshot actor and invalid for CETM: a later graph row would not have the legal preceding state needed to reconstruct its memory.

The frozen resolution is a full-sequence actor replay: save the exact TATG state at rollout start; replay each environment sequence chronologically for each PPO epoch; apply stored actions only after calculating each log-probability; and reset only completed slots before the next graph. The critic remains the ordinary snapshot centralized critic. The candidate, generic GRU control and delta-zero ablation must use this identical sequence runner.

## Checks

- `existing_rollout_preserves_time_environment_layout`: `True`
- `existing_actor_update_flattens_time_environment_rows`: `True`
- `existing_flat_random_minibatch_is_not_valid_for_temporal_state_replay`: `True`
- `exact_rollout_start_state_is_required`: `True`
- `episode_reset_semantics_are_explicit`: `True`
- `each_ppo_epoch_replays_ordered_sequences`: `True`
- `critic_remains_snapshot_and_ordinary`: `True`
- `candidate_and_generic_control_share_sequence_runner`: `True`
- `no_training_or_evaluation_authorized`: `True`

This is a runner-design result, not an algorithm result. It authorizes a separately frozen sequence-runner implementation and same-rollout PPO correctness audit only. No PPO parameter update, environment rollout, evaluation or cloud training was run.
