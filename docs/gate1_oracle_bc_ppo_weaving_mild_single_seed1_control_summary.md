# Gate 1 Oracle-Assisted `single` Graph Seed-1 Control

Last updated: 2026-07-22

## Purpose

This diagnostic checks whether the nominal `weaving_mild` improvement is mainly caused by the oracle-assisted training route or still depends on the multi-relation role graph.

The control uses the same seed-1 protocol as the successful `multi_relation` run:

- offset geometric-oracle BC;
- 30 demo episodes;
- 12 BC epochs;
- attacker action weight `4.0`;
- balanced loss off;
- 30 PPO updates;
- learning rate `1e-5`;
- matched 30-episode evaluation with base seed `409000`.

The only intended method change is `graph_encoder=single`.

## Artifacts

- BC: `results/gate1_oracle_bc_weaving_mild_single_seed1_attackerw4_dev30e12/`
- PPO: `results/gate1_oracle_bc_ppo_weaving_mild_single_seed1_cont30/`
- Evaluation: `results/gate1_oracle_bc_ppo_weaving_mild_single_seed1_cont30/eval_best_weaving_mild_test30.csv`
- Reachability: `results/gate1_oracle_bc_ppo_weaving_mild_single_seed1_cont30/reachability_eval30/summary.csv`

## Results

| Method | Seed | Success | Attack-window formed | Collision | Timeout | Tracking | Connectivity |
|---|---:|---:|---:|---:|---:|---:|---:|
| `multi_relation` | 1 | 0.400 | 0.400 | 0.000 | 0.600 | 0.426 | 0.478 |
| `single` | 1 | 0.000 | 0.000 | 0.000 | 1.000 | 0.134 | 0.592 |

Reachability for `single`:

| Case | Success | Min range | Range reduction | Tracking | Max geometry | Geometry > 0.25 | Attack-window episodes |
|---|---:|---:|---:|---:|---:|---:|---:|
| `single_seed1_oracle_bc_ppo_cont30` | 0.000 | 14732.7 | 9977.7 | 0.134 | 0.074 | 0.167 | 0.000 |

## Interpretation

The oracle-assisted route does not automatically solve the maneuvering-target task for every graph encoder. Under the same seed, training aid, PPO budget, and evaluation split:

- `multi_relation` reaches `40.0%` success;
- `single` remains at `0.0%` success;
- `single` never forms an attack window;
- `single` has much lower tracking and larger final-range divergence.

This is an important credibility result. It suggests the maneuvering-target improvement is not only due to geometric demonstrations; the multi-relation role graph still matters for converting the training signal into a usable cooperative policy.

## Decision

The next fair-control step is to run `single` controls for seeds 0 and 2, then compute a three-seed method comparison. If the seed-1 pattern holds, the oracle-assisted maneuvering-target route can become a stronger scenario-depth experiment after validation/test protocol hardening.
