# Gate 1 Oracle-Assisted `no_graph` Control for Nominal `weaving_mild`

Last updated: 2026-07-22

## Purpose

This diagnostic adds a `no_graph` fairness control to the oracle-assisted nominal `weaving_mild` scenario-depth route.

The goal is to check whether oracle-assisted behavior cloning plus PPO can solve the maneuvering target task even without graph structure. This addresses a possible criticism that the oracle demonstrations, rather than the multi-relation graph, may be doing most of the work.

## Protocol

The `no_graph` route uses the same maneuvering-target training assistance as the previous `multi_relation` and `single` controls:

- target policy: `weaving_mild`
- offset geometric-oracle BC
- 30 demonstration episodes
- 12 BC epochs
- attacker action weight: `4.0`
- balanced BC loss: off
- PPO updates: `30`
- learning rate: `1e-5`
- matched validation selection
- frozen test split evaluation

Source checkpoints:

`results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed*/actor_critic_update_0060.pt`

Validation/test artifacts:

- `results/gate1_nominal_weaving_mild_no_graph_validation_selection_dev10/validation_selected_checkpoints.csv`
- `results/gate1_nominal_weaving_mild_no_graph_validation_selection_dev10_test30/test_selected_checkpoints.csv`

Combined three-method artifacts:

- `results/gate1_nominal_weaving_mild_oracle_assisted_3method_validation_selected_dev10_test30/test_selected_checkpoints_3method.csv`
- `results/gate1_nominal_weaving_mild_oracle_assisted_3method_validation_selected_dev10_test30/test_aggregate_summary_3method.json`

## Results

Validation-selected test results:

| Method | Success | Attack-window formed | Collision | Tracking | Connectivity |
|---|---:|---:|---:|---:|---:|
| `multi_relation` | 0.633 | 0.667 | 0.000 | 0.466 | 0.744 |
| `single` | 0.111 | 0.156 | 0.000 | 0.223 | 0.550 |
| `no_graph` | 0.000 | 0.000 | 0.000 | 0.055 | 0.404 |

Per-seed `no_graph` test results:

| Seed | Selected update | Success | Attack-window formed | Collision | Tracking | Connectivity |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 30 | 0.000 | 0.000 | 0.000 | 0.047 | 0.552 |
| 1 | 20 | 0.000 | 0.000 | 0.000 | 0.086 | 0.324 |
| 2 | 20 | 0.000 | 0.000 | 0.000 | 0.032 | 0.336 |

## Interpretation

The `no_graph` control confirms that oracle-assisted demonstrations are not sufficient by themselves:

- `no_graph` never forms attack windows on the frozen test split;
- `single` partially solves only seed 0;
- `multi_relation` remains nonzero on every seed and has the highest aggregate success.

This gives a clean method hierarchy under equal oracle-assisted training:

```text
no_graph < single < multi_relation
```

The maneuvering-target scenario-depth result is now stronger because it includes both graph-free and single-graph controls.

## Decision

Freeze nominal `weaving_mild` as supporting scenario-depth evidence for now. Do not add strict sensing or relay failure to the maneuvering-target branch yet.

The next experimental priority should return to the main strict-sensing relay-failure package:

- review which main results still need seed-aware statistics or formalization;
- avoid further tuning on the maneuvering-target `409000` test split;
- keep the maneuvering-target result as a supporting experiment unless a later formal budget is explicitly approved.
