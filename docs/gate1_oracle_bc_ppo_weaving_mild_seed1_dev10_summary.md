# Gate 1 Oracle-BC + PPO Seed-1 Maneuvering-Target Diagnostic

Last updated: 2026-07-22

## Purpose

This diagnostic tests whether short PPO fine-tuning from the attacker-weighted offset oracle-BC checkpoint can improve the previously failed seed-1 nominal `weaving_mild` policy.

This is development evidence only. It is not a formal three-seed or five-seed result.

## Protocol

Warm-start checkpoint:

`results/gate1_oracle_bc_weaving_mild_seed1_attackerw4_dev30e12/actor_critic_best.pt`

PPO fine-tuning:

- method: `multi_relation`
- seed: `1`
- target policy: `weaving_mild`
- updates: `10`
- rollout envs: `8`
- rollout steps: `128`
- learning rate: `1e-5`
- entropy coefficient: `0.01`
- strict sensing: off
- relay failure: off
- target-information bottleneck: off

Evaluation:

- checkpoint: `results/gate1_oracle_bc_ppo_weaving_mild_seed1_dev10/actor_critic_best.pt`
- episodes: `30`
- base seed: `409000`

Artifacts:

- `results/gate1_oracle_bc_ppo_weaving_mild_seed1_dev10/train_log.csv`
- `results/gate1_oracle_bc_ppo_weaving_mild_seed1_dev10/eval_best_weaving_mild_test30.csv`
- `results/gate1_oracle_bc_ppo_weaving_mild_seed1_dev10/reachability_eval30/summary.csv`
- `results/gate1_oracle_bc_ppo_weaving_mild_seed1_dev10/reachability_eval30/step_trace.csv`

## Result

| Seed-1 route | Success | Attack-window formed | Collision | Timeout | Mean tracking | Mean connectivity |
|---|---:|---:|---:|---:|---:|---:|
| curriculum-only reference | 0.000 | 0.000 | 0.000 | 1.000 | not re-estimated here | not re-estimated here |
| pure attacker-weighted oracle BC | 0.033 | 0.033 | 0.000 | 0.967 | 0.415 | 0.479 |
| oracle BC + PPO dev10 | 0.133 | 0.133 | 0.000 | 0.867 | 0.388 | 0.469 |

Reachability summary for oracle BC + PPO:

| Case | Success | Min range | Range reduction | Tracking | Max geometry | Geometry > 0.25 | Attack-window episodes |
|---|---:|---:|---:|---:|---:|---:|---:|
| `seed1_oracle_bc_ppo` | 0.133 | 13966.4 | 10738.1 | 0.388 | 0.088 | 0.067 | 0.133 |

## Interpretation

The oracle-assisted route is directionally useful:

- seed 1 is no longer locked at zero;
- attack-window formation appears in matched evaluation;
- collision remains zero.

However, the result is still far below the acceptance gate for scenario-depth experiments. The policy still does not reliably enter high-quality attack geometry: mean maximum geometry score is only `0.088`, and only `6.7%` of episodes exceed geometry score `0.25`.

The next development run should extend this route cautiously rather than switching back to blind training:

- evaluate update-5 and update-10 snapshots separately if needed;
- run a 20-40 update extension from the best dev10 checkpoint;
- keep learning rate small;
- consider keeping a lightweight attacker-focused imitation auxiliary only during early updates if PPO alone plateaus.

## Decision

Do not launch three-seed maneuvering-target formal training yet.

Proceed with a short seed-1 continuation or checkpoint sweep to see whether oracle BC + PPO can reach a stable nonzero regime. If seed 1 can reach roughly `30%` to `50%` nominal `weaving_mild` success without collisions, then expand to seeds 0 and 2.
