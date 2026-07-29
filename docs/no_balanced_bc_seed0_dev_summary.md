# No-Balanced BC Seed-0 Development Summary

Last updated: 2026-07-29

## Purpose

Evaluate whether replacing balanced BC with `--no-balanced-loss` gives a better and fairer development starting point under strict sensing, target-information bottleneck, dropout 0.30, delay 2, and early relay failure.

This is development evidence only. It uses one training seed and a limited checkpoint subset.

## Protocol

```text
seed = 0
target_policy = straight
BC demonstrations = 200 episodes from direct geometric oracle
BC loss = unbalanced cross entropy
PPO updates = 100, evaluated online every 10 updates with 5 episodes
validation = matched 50 episodes, base_seed 140000
strict_target_sensing = true
agent_target_info_bottleneck = true
communication_dropout_prob = 0.30
message_delay_steps = 2
failed_blue_agent = 1
node_failure_start_step = 25
node_failure_duration_steps = 80
```

## BC-Only Starting Points

| Method | Success | Recovery | Tracking during failure | Connectivity during failure | Timeout |
| --- | ---: | ---: | ---: | ---: | ---: |
| ea_rg_mappo | 0.3000 | 0.3000 | 0.4255 | 0.1076 | 0.7000 |
| single_graph | 0.3000 | 0.3000 | 0.4238 | 0.1076 | 0.7000 |
| mappo | 0.4000 | 0.4000 | 0.4719 | 0.0887 | 0.6000 |

## PPO Candidate Validation

| Method | Update | Success | Recovery | Recovery steps only | Recovery steps censored | Tracking during failure | Connectivity during failure | Timeout | Score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ea_rg_mappo | 0040 | 0.4400 | 0.4400 | 19.7727 | 140.3000 | 0.5001 | 0.1211 | 0.5600 | 464.23 |
| ea_rg_mappo | 0050 | 0.4400 | 0.4400 | 19.8182 | 140.3200 | 0.5032 | 0.1214 | 0.5600 | 464.18 |
| ea_rg_mappo | 0100 | 0.4400 | 0.4400 | 19.8182 | 140.3200 | 0.5018 | 0.1213 | 0.5600 | 464.18 |
| single_graph | 0040 | 0.2600 | 0.2600 | 19.5385 | 178.9800 | 0.4157 | 0.2074 | 0.7400 | 266.46 |
| single_graph | 0070 | 0.3800 | 0.3800 | 19.7895 | 153.2200 | 0.4423 | 0.1809 | 0.6200 | 398.21 |
| single_graph | 0080 | 0.4000 | 0.4000 | 19.8500 | 148.9400 | 0.4713 | 0.1691 | 0.6000 | 420.15 |
| mappo | 0030 | 0.2000 | 0.2000 | 20.1000 | 192.0200 | 0.3289 | 0.1113 | 0.8000 | 199.90 |
| mappo | 0050 | 0.2800 | 0.2800 | 20.1429 | 174.8400 | 0.3709 | 0.1020 | 0.7200 | 287.86 |
| mappo | 0070 | 0.3400 | 0.3400 | 19.9412 | 161.8800 | 0.4469 | 0.0988 | 0.6600 | 354.06 |

Best observed checkpoint per method:

| Method | Selected update | Success | Recovery | Timeout |
| --- | ---: | ---: | ---: | ---: |
| ea_rg_mappo | 0040 | 0.4400 | 0.4400 | 0.5600 |
| single_graph | 0080 | 0.4000 | 0.4000 | 0.6000 |
| mappo | 0070 | 0.3400 | 0.3400 | 0.6600 |

## EA u40 Mechanism Ablation

| Variant | Success | Recovery | Tracking during failure | Connectivity during failure | Timeout |
| --- | ---: | ---: | ---: | ---: | ---: |
| EA u40 original | 0.4400 | 0.4400 | 0.5001 | 0.1211 | 0.5600 |
| EA u40 no_task_support | 0.4400 | 0.4400 | 0.5001 | 0.1213 | 0.5600 |
| EA u40 no_role_pair_gate | 0.4400 | 0.4400 | 0.4998 | 0.1214 | 0.5600 |

## Role-Graph Diagnostic

Source: `results/role_graph_diagnostics/no_balanced_bc_ea_seed0_u40/role_graph_diagnostics.md`.

- all | 20 | 0.4000 | 0.0020 | 0.7500 | 0.0571 | 0.7495
- - mean absolute gate deviation from 0.5: `0.002211`
- - max absolute gate deviation from 0.5: `0.020170`

## Interpretation

- `--no-balanced-loss` is a useful training-protocol candidate: all methods get a stronger BC start than the earlier balanced BC setting.
- Seed0 PPO validation gives EA the best observed checkpoint (`0.44` success), but the margin over Single-Graph (`0.40`) is small and not yet paper-level evidence.
- MAPPO/no-graph remains competitive at BC-only and after PPO, so the task cannot be presented as solved only by graph structure.
- EA mechanism evidence remains weak: removing task-support or role-pair gates must show clear degradation before those mechanisms can be claimed strongly.
- The next step should be a 3-seed development repeat with the no-balanced BC protocol and full checkpoint selection; only if EA consistently beats Single/MAPPO should this protocol enter 1M/2M formal training.

## Follow-Up BC-Only Seed 1/2 Check

No-balanced BC initialization was extended to seeds 1 and 2 for EA, Single-Graph,
and MAPPO. All runs used the same strict early-stress protocol and 200 direct
geometric-oracle demonstration episodes.

BC final imitation accuracy:

| Method | Seed 1 acc. | Seed 2 acc. |
| --- | ---: | ---: |
| EA | 0.7233 | 0.7446 |
| Single-Graph | 0.7168 | 0.7092 |
| MAPPO | 0.7040 | 0.6559 |

BC-only task evaluation over 30 matched episodes:

| Method | Seed 0 | Seed 1 | Seed 2 | Mean |
| --- | ---: | ---: | ---: | ---: |
| EA | 0.3000 | 0.4000 | 0.3000 | 0.3333 |
| Single-Graph | 0.3000 | 0.3333 | 0.4000 | 0.3444 |
| MAPPO | 0.4000 | 0.4000 | 0.4000 | 0.4000 |

Interpretation:

- No-balanced BC is stable across seeds as an initialization protocol.
- MAPPO remains strongest at the BC-only stage, so graph advantages must come
  from subsequent PPO adaptation and recovery behavior, not from imitation
  alone.
- The next fair step is PPO seed1/seed2 for all three methods, followed by the
  same fixed validation checkpoint-selection rule.

## Follow-Up PPO Seed 0-2 Validation

Source: `docs/no_balanced_bc_seed0_2_validation_summary.md`.

The no-balanced BC protocol was extended to seeds 0, 1, and 2 with 100 PPO
updates per method. For a fair common checkpoint-selection check, update 30,
update 40, and update 70 were evaluated for EA-RG-MAPPO, Single-Graph, and
MAPPO/no-graph using 50 matched validation episodes with base seed `140000`.

Selected-checkpoint aggregate:

| Method | Selected updates | Success mean | Recovery mean | Timeout mean |
| --- | --- | ---: | ---: | ---: |
| EA-RG-MAPPO | 40/30/40 | 0.3733 | 0.3733 | 0.6200 |
| Single-Graph | 70/70/40 | 0.3533 | 0.3533 | 0.6467 |
| MAPPO/no-graph | 70/70/30 | 0.3400 | 0.3400 | 0.6600 |

Interpretation:

- EA-RG-MAPPO keeps the best mean validation success, but only by a small margin
  over Single-Graph (`+0.0200`) and MAPPO/no-graph (`+0.0333`).
- This is not strong enough for a paper-level graph-mechanism claim.
- No-balanced BC remains useful as a fairer initialization protocol for short
  diagnostics, but it should not be written as an algorithm contribution.
- The next route should strengthen or diagnose the role-conditioned
  communication mechanism before any 1M/2M-scale run from this branch.
