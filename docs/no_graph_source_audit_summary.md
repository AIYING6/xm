# No-Graph Source Checkpoint Audit

Last updated: 2026-07-17

## Purpose

This audit checks whether the `no_graph` source checkpoints used in the strict-sensing fair baseline diagnostic are task-capable before interpreting the strict relay-failure comparison.

The audit re-evaluates the final curriculum source checkpoint for each `no_graph` training seed with 50 deterministic episodes.

## Checkpoints

Root:

`results/intercept_3d_no_graph_source_curriculum/runs/no_graph/`

Checkpoint per seed:

- `bc_ppo_seed0/actor_critic_best.pt`
- `bc_ppo_seed1/actor_critic_best.pt`
- `bc_ppo_seed2/actor_critic_best.pt`

## Audit Results

| Seed | Nominal success | Nominal timeout | Strict relay-failure success | Strict relay-failure timeout | Interpretation |
|---:|---:|---:|---:|---:|---|
| 0 | 46.0% | 50.0% | 38.0% | 62.0% | Weak but nonzero source |
| 1 | 88.0% | 12.0% | 88.0% | 12.0% | Usable source |
| 2 | 22.0% | 78.0% | 0.0% | 100.0% | Failed / very weak source |

## Decision

`no_graph` seed 2 is a genuine weak source, not just a 10-episode online-evaluation fluctuation.

For development diagnostics, retaining this seed is acceptable because it reflects the instability of removing graph communication. For formal paper reporting, avoid cherry-picking only this seed. Use one of the following predefined policies:

1. Keep all `no_graph` seeds and report seed-level variance clearly.
2. Retrain all `no_graph` seeds with a stronger standardized source budget before rerunning the fair strict-sensing diagnostic.

Do not replace only seed 2 after seeing the final test result.

## Generated Artifacts

- `results/intercept_3d_no_graph_source_curriculum/audit/no_graph_seed0_nominal.csv`
- `results/intercept_3d_no_graph_source_curriculum/audit/no_graph_seed0_strict_relay_failure.csv`
- `results/intercept_3d_no_graph_source_curriculum/audit/no_graph_seed1_nominal.csv`
- `results/intercept_3d_no_graph_source_curriculum/audit/no_graph_seed1_strict_relay_failure.csv`
- `results/intercept_3d_no_graph_source_curriculum/audit/no_graph_seed2_nominal.csv`
- `results/intercept_3d_no_graph_source_curriculum/audit/no_graph_seed2_strict_relay_failure.csv`
