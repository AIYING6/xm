# SR-DRTP P0 telemetry schema

## Boundary

The writer emits `sr_drtp_telemetry/training_state.csv` only when
`sr_drtp_telemetry=True`. The default is `False`. The writer returns no value,
and it is not passed to the actor, critic, reward function, reset sampler, PPO
loss, checkpoint selector, or evaluation code.

Each row has `training_only=True`; formal, independent, held-out and manuscript
evaluation episode IDs are forbidden.

## Fixed fields

| Family | Fields |
| --- | --- |
| Identity | `schema_version`, `training_only`, `update`, `sampler_mode` |
| PPO dynamics | `approx_kl`, `entropy`, `value_loss`, `grad_norm`, `explained_variance`, `advantage_mean`, `advantage_std`, `train_avg_reward` |
| Sampler state | `q_*`, `q_uniform_l1`, `q_rank_signature`, `q_step_l1`, `adaptation_count` |
| Online evidence | `ema_N`, `ema_F0/TE/TL/DS/DL/CP`, `difficulty_*`, `window_count_*` |
| Reserved equalized-probe evidence | `probe_available`, `probe_mean_return`, `probe_worst_group_return`, `probe_online_disagreement` |

The reserved probe fields are blank in P0. A future P1 must separately freeze
the probe IDs, cadence and isolation test before these fields may be populated.

## Candidate use in a later study

Candidate signals may include q/rank instability, online-versus-equalized-probe
disagreement, nominal competence trend, equalized-probe worst-group return,
and PPO dynamics. No single field or threshold is a risk gate in P0. Any
future gate must be specified before outcome inspection and may use only
training-time information available at that boundary.
