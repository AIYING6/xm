# Gate 1 Oracle-BC Seed-1 Maneuvering-Target Diagnostic

Last updated: 2026-07-22

## Purpose

This diagnostic tests whether the geometric-oracle signal can unstick the previously failed seed-1 nominal `weaving_mild` policy.

The goal is not to produce paper-facing evidence yet. The goal is to decide whether the next route should be:

- more generic PPO updates;
- pure reward shaping;
- oracle-assisted behavior cloning plus PPO;
- a redesign of the maneuvering-target task.

## Implementation

`scripts/pretrain_ri_gmappo_3d_bc.py` now supports:

- `--geometric-policy-mode direct|lead|offset`;
- `--attacker-action-weight`;
- per-role BC diagnostics:
  - `attacker_action_accuracy`;
  - `support_action_accuracy`.

The default geometric policy remains `direct`, preserving previous BC behavior unless the new option is explicitly used.

## Seed-1 Diagnostics

Source checkpoint:

`results/gate1_safety_fx60_weaving_mild_finetune_source_update60/runs/multi_relation/bc_ppo_seed1/actor_critic_best.pt`

Evaluation setting:

- target policy: `weaving_mild`
- graph encoder: `multi_relation`
- hidden dimension: `64`
- evaluation episodes: `30`
- evaluation base seed: `409000`
- strict sensing: off
- relay failure: off
- target-information bottleneck: off

| Run | Demo episodes | Epochs | Balanced loss | Attacker weight | Final action acc. | Final attacker acc. | Success | Attack-window formed | Collision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `seed1_dev30e5` | 30 | 5 | yes | 1.0 | 0.229 | n/a | 0.000 | 0.000 | 0.000 |
| `seed1_unbalanced_dev30e12` | 30 | 12 | no | 1.0 | 0.422 | n/a | 0.000 | 0.000 | 0.000 |
| `seed1_attackerw4_dev30e12` | 30 | 12 | no | 4.0 | 0.416 | 0.386 | 0.033 | 0.033 | 0.000 |

Artifacts:

- `results/gate1_oracle_bc_weaving_mild_seed1_dev30e5/`
- `results/gate1_oracle_bc_weaving_mild_seed1_unbalanced_dev30e12/`
- `results/gate1_oracle_bc_weaving_mild_seed1_attackerw4_dev30e12/`

## Interpretation

The oracle itself solves matched nominal `weaving_mild` episodes with `100%` success and `0%` collision, so the scenario is feasible.

Pure BC only partially transfers the oracle behavior into the neural policy:

- balanced BC is too weak for this setting;
- unbalanced BC improves action imitation but still forms no attack windows;
- attacker-weighted BC creates the first nonzero attack-window/success signal for seed 1, but the effect is only `3.3%`.

This suggests the next route should not be more generic PPO or larger blind BC alone. The useful next step is an oracle-assisted Stage 1 training protocol:

- use offset/lead oracle BC as warm start;
- then run short nominal PPO fine-tuning;
- optionally keep a small attacker-focused imitation auxiliary loss during early PPO updates;
- compare against the existing curriculum-only baseline.

## Decision

Proceed with a small oracle-BC + PPO seed-1 development run before launching any three-seed or five-seed maneuvering-target budget.

Acceptance target for the next diagnostic:

- seed-1 nominal `weaving_mild` success clearly above the current `0%` curriculum-only result;
- attack-window formed rate clearly nonzero;
- collision remains near zero.
