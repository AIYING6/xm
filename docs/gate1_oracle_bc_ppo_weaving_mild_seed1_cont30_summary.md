# Gate 1 Oracle-BC + PPO Seed-1 Continuation Diagnostic

Last updated: 2026-07-22

## Purpose

This diagnostic continues the seed-1 oracle-assisted nominal `weaving_mild` route after the initial dev10 result.

The question is whether the previous nonzero signal (`13.3%` success) can become a stable development result above the `30%` threshold without introducing collisions.

## Protocol

Resume checkpoint:

`results/gate1_oracle_bc_ppo_weaving_mild_seed1_dev10/actor_critic_best.pt`

Training:

- method: `multi_relation`
- seed: `1`
- target policy: `weaving_mild`
- additional updates: `30`
- rollout envs: `8`
- rollout steps: `128`
- learning rate: `1e-5`
- entropy coefficient: `0.01`
- strict sensing: off
- relay failure: off
- target-information bottleneck: off

Evaluation:

- matched test episodes: `30`
- base seed: `409000`
- evaluated checkpoints:
  - `actor_critic_best.pt`
  - `actor_critic_update_0020.pt`
  - `actor_critic_update_0030.pt`

Artifacts:

- `results/gate1_oracle_bc_ppo_weaving_mild_seed1_cont30/train_log.csv`
- `results/gate1_oracle_bc_ppo_weaving_mild_seed1_cont30/eval_best_weaving_mild_test30.csv`
- `results/gate1_oracle_bc_ppo_weaving_mild_seed1_cont30/eval_update20_weaving_mild_test30.csv`
- `results/gate1_oracle_bc_ppo_weaving_mild_seed1_cont30/eval_update30_weaving_mild_test30.csv`
- `results/gate1_oracle_bc_ppo_weaving_mild_seed1_cont30/reachability_eval30/summary.csv`

## Results

| Checkpoint | Success | Attack-window formed | Collision | Timeout | Tracking | Connectivity |
|---|---:|---:|---:|---:|---:|---:|
| update20 | 0.267 | 0.300 | 0.000 | 0.733 | 0.424 | 0.480 |
| update30 / best | 0.400 | 0.400 | 0.000 | 0.600 | 0.426 | 0.478 |

Reachability for the best checkpoint:

| Case | Success | Min range | Range reduction | Tracking | Max geometry | Geometry > 0.25 | Attack-window episodes |
|---|---:|---:|---:|---:|---:|---:|---:|
| `seed1_oracle_bc_ppo_cont30` | 0.400 | 13871.4 | 10833.0 | 0.426 | 0.143 | 0.300 | 0.400 |

## Interpretation

This is the first seed-1 maneuvering-target result that clears the development threshold:

- curriculum-only seed 1 was `0.0%`;
- pure attacker-weighted oracle BC was `3.3%`;
- oracle-BC + PPO dev10 was `13.3%`;
- oracle-BC + PPO continuation reaches `40.0%`.

The result is still development-scale, but it is strong enough to justify expanding the route to the other development seeds. The improvement is also mechanistically consistent: attack-window episodes increase to `40.0%`, and geometry score above `0.25` appears in `30.0%` of episodes.

## Decision

The maneuvering-target route should now expand from seed 1 to seeds 0 and 2 using the same oracle-assisted protocol.

Do not add strict sensing or relay failure yet. The next acceptance gate is a three-seed nominal `weaving_mild` development result:

- aggregate success should be meaningfully above the previous curriculum-only `27.3%`;
- seed 1 should remain nonzero;
- collision should remain near zero;
- checkpoint selection should be explicit and matched across seeds.
