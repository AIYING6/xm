# Gate 1 Oracle-Assisted `weaving_mild` Multi-Relation vs Single-Graph Development Comparison

Last updated: 2026-07-22

## Purpose

This comparison checks whether the maneuvering-target improvement remains method-dependent under equal oracle-assisted training.

Both methods use the same development protocol:

- nominal `weaving_mild`;
- no strict sensing;
- no relay failure;
- no target-information bottleneck;
- offset geometric-oracle BC;
- 30 demonstration episodes;
- 12 BC epochs;
- attacker action weight `4.0`;
- balanced BC loss off;
- 30 PPO updates;
- learning rate `1e-5`;
- matched 30-episode evaluation with base seed `409000`.

This is development evidence. It is not yet a formal manuscript table because validation/test separation and more baselines still need to be hardened.

## Artifacts

- `results/gate1_oracle_bc_ppo_weaving_mild_multirelation_vs_single_3seed_dev30/per_seed_summary.csv`
- `results/gate1_oracle_bc_ppo_weaving_mild_multirelation_vs_single_3seed_dev30/aggregate_summary.json`

Single-graph controls:

- `results/gate1_oracle_bc_ppo_weaving_mild_single_seed0_cont30/`
- `results/gate1_oracle_bc_ppo_weaving_mild_single_seed1_cont30/`
- `results/gate1_oracle_bc_ppo_weaving_mild_single_seed2_cont30/`

Multi-relation runs:

- `results/gate1_oracle_bc_ppo_weaving_mild_seed0_cont30/`
- `results/gate1_oracle_bc_ppo_weaving_mild_seed1_cont30/`
- `results/gate1_oracle_bc_ppo_weaving_mild_seed2_cont30/`

## Per-Seed Results

| Method | Seed | Success | Attack-window formed | Collision | Timeout | Tracking | Connectivity |
|---|---:|---:|---:|---:|---:|---:|---:|
| `multi_relation` | 0 | 0.767 | 0.800 | 0.000 | 0.233 | 0.462 | 0.771 |
| `multi_relation` | 1 | 0.400 | 0.400 | 0.000 | 0.600 | 0.426 | 0.478 |
| `multi_relation` | 2 | 0.700 | 0.733 | 0.000 | 0.300 | 0.499 | 0.984 |
| `single` | 0 | 0.333 | 0.467 | 0.000 | 0.667 | 0.395 | 0.597 |
| `single` | 1 | 0.000 | 0.000 | 0.000 | 1.000 | 0.134 | 0.592 |
| `single` | 2 | 0.000 | 0.000 | 0.000 | 1.000 | 0.102 | 0.437 |

## Aggregate Results

| Method | Success | Attack-window formed | Collision | Timeout | Tracking | Connectivity |
|---|---:|---:|---:|---:|---:|---:|
| `multi_relation` | 0.622 | 0.644 | 0.000 | 0.378 | 0.462 | 0.744 |
| `single` | 0.111 | 0.156 | 0.000 | 0.889 | 0.210 | 0.542 |
| delta | +0.511 | +0.489 | 0.000 | -0.511 | +0.252 | +0.202 |

## Interpretation

The result supports the mechanism route:

- oracle assistance does not erase the difference between graph encoders;
- `single` can partially solve seed 0 but fails on seeds 1 and 2;
- `multi_relation` remains nonzero on every seed;
- the aggregate success gap is `+51.1` percentage points in favor of `multi_relation`;
- the attack-window gap is `+48.9` percentage points.

This is a stronger scenario-depth result than the earlier curriculum-only maneuvering-target run. It also helps defend against the criticism that the oracle simply solves the task for the learner.

## Decision

The nominal `weaving_mild` scenario-depth route should be retained as a candidate enhancement experiment.

Do not add strict sensing or relay failure yet. The next step should harden the protocol:

- add an explicit validation split for checkpoint selection;
- avoid selecting by the same matched test split;
- decide whether to include `no_graph` as a second fairness control;
- run seed-aware statistics only after the protocol is frozen.

The current evidence is strong enough to justify protocol hardening, but not yet enough for final paper tables.
