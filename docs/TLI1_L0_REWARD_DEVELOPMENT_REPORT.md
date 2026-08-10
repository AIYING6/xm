# TLI1 L0 Reward-only Development Test

## Verdict

`TLI1_REWARD_ONLY_NO_GO__REWARD_MISALIGNMENT_NOT_SUFFICIENT`

This was a paired, non-evidentiary development test. It retrained vanilla
PPO/MAPPO-equivalent from scratch with the original L0 seeds `8101/8102`, 60
updates, the same task distribution, 32 evaluation seeds, observation,
9-action guidance interface, timescale, `engage_commit`, N0 physics,
horizon, and PPO hyperparameters. The only changed semantic switch was:

`mission_reward_alignment_v1_enabled=true`

with potential-difference shaping enabled.

## Frozen evaluation summary

| controller | geometry entry | neutralization by 180 | mean RMTN180 |
|---|---:|---:|---:|
| random | 1/32 (3.1%) | 1/32 (3.1%) | 175.94 |
| scripted | 32/32 (100%) | 32/32 (100%) | 54.19 |
| oracle | 32/32 (100%) | 32/32 (100%) | 52.97 |
| TLI1 seed 8101 | 9/32 (28.1%) | 0/32 (0%) | 180.00 |
| TLI1 seed 8102 | 0/32 (0%) | 0/32 (0%) | 180.00 |

The reward change therefore produced a detectable geometry signal for one
seed, but not a stable mission-completion signal across the paired seeds.
Neither seed produced a neutralization event within the frozen horizon.

## Interpretation boundary

This result does not show that the new potential is physically invalid; the
deterministic TLI1 reward validation passed 7/7. It shows that reward
realignment alone is insufficient to make the current L0 PPO formulation
learnable within the frozen development budget. No action, observation,
timescale, task-physics, or algorithm conclusion is drawn from this test.

The authorized TLI1 question is answered: reward-only is not enough. No reward
v2/v3, additional training, L1, N3, or formal training is authorized by this
stage.

Raw outputs:

- `results/tli1_l0_reward_development/TLI1_MANIFEST.json`
- `results/tli1_l0_reward_development/episode_outcomes.csv`
- `results/tli1_l0_reward_development/summary.csv`
- `results/tli1_l0_reward_development/TLI1_VERDICT.json`
