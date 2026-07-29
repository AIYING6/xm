# Single-Graph Strong Protocol Comparison

Last updated: 2026-07-29

## Purpose

This note compares Single-Graph MAPPO against the current EA-RG-MAPPO-S recovery-oriented development protocol from `docs/post_loss_reclosure_strong_protocol_3seed_summary.md`.

The goal is to check whether the recovery signal comes only from strong recovery demonstrations and safety PPO, or whether the multi-relation role graph still provides an advantage.

## Shared Protocol

Both EA-RG-MAPPO-S and Single-Graph use:

- strong balanced `offset` recovery BC;
- `120` BC episodes and `20` BC epochs;
- attacker action weight `2.0`;
- strict sensing and target-information bottleneck;
- communication dropout `0.30`;
- message delay `2`;
- relay failure start sampled in `[25,70]`;
- `min_success_step=80`;
- post-loss reclosure reward `0.5`;
- safety PPO with proximity distance `2500` and penalty `0.5`;
- validation over the same four-scenario suite;
- checkpoint candidates `20,30,40`.

Single-Graph seed 0 had nonzero validation collision under the shared safety0.5 PPO. An additional stronger-safety seed-0 run was tested:

- safety proximity distance `3000`;
- safety penalty `1.0`.

This stronger-safety run is a development diagnostic only. It shows the safety/performance tradeoff for Single-Graph and should not be mixed into final formal results unless the same safety protocol is frozen and applied consistently.

## BC Quality

| Method | Seed | Demo success | Final action accuracy |
|---|---:|---:|---:|
| EA-RG-MAPPO-S | 0 | 0.908 | 0.510 |
| EA-RG-MAPPO-S | 1 | 0.908 | 0.510 |
| EA-RG-MAPPO-S | 2 | 0.917 | 0.479 |
| Single-Graph | 0 | 0.908 | 0.470 |
| Single-Graph | 1 | 0.908 | 0.488 |
| Single-Graph | 2 | 0.917 | 0.486 |

## Single-Graph Safety0.5 Validation

Unconstrained suite delayed-recovery selection selected:

| Seed | Update | Success | Recovery | Delayed recovery | Collision |
|---:|---:|---:|---:|---:|---:|
| 0 | 20 | 0.725 | 0.750 | 0.400 | 0.025 |
| 1 | 20 | 0.550 | 0.725 | 0.275 | 0.000 |
| 2 | 20 | 0.750 | 0.875 | 0.400 | 0.000 |
| Mean | - | 0.675 | 0.783 | 0.358 | 0.008 |

This is slightly stronger than EA on raw recovery, but seed 0 violates the zero-collision safety gate.

Single seed-0 safety0.5 by update:

| Update | Success | Recovery | Delayed recovery | Collision |
|---:|---:|---:|---:|---:|
| 20 | 0.725 | 0.750 | 0.400 | 0.025 |
| 30 | 0.500 | 0.600 | 0.225 | 0.075 |
| 40 | 0.475 | 0.550 | 0.225 | 0.100 |

## Zero-Collision Diagnostic

Using zero-collision checkpoint choices:

EA-RG-MAPPO-S:

| Seed | Update | Success | Recovery | Delayed recovery | Collision |
|---:|---:|---:|---:|---:|---:|
| 0 | 30 | 0.575 | 0.725 | 0.275 | 0.000 |
| 1 | 30 | 0.825 | 0.850 | 0.375 | 0.000 |
| 2 | 20 | 0.475 | 0.575 | 0.375 | 0.000 |
| Mean | - | 0.625 | 0.717 | 0.342 | 0.000 |

Single-Graph:

| Seed | Update | Success | Recovery | Delayed recovery | Collision |
|---:|---:|---:|---:|---:|---:|
| 0 | 40 safety1.0 | 0.400 | 0.550 | 0.175 | 0.000 |
| 1 | 40 safety0.5 | 0.650 | 0.925 | 0.425 | 0.000 |
| 2 | 20 safety0.5 | 0.750 | 0.875 | 0.400 | 0.000 |
| Mean | - | 0.600 | 0.783 | 0.333 | 0.000 |

EA minus Single under this zero-collision diagnostic:

| Metric | EA - Single |
|---|---:|
| Success | +0.025 |
| Recovery | -0.067 |
| Delayed recovery | +0.008 |
| Timeout | -0.025 |
| Collision | 0.000 |

## Interpretation

Single-Graph is a strong baseline under the recovery-oriented protocol.

Current evidence does **not** support a broad claim that EA-RG-MAPPO-S dominates Single-Graph in every metric. The safer interpretation is:

- both graph methods can exploit recovery-oriented demonstrations;
- Single-Graph can achieve high raw recovery, but may require a safety tradeoff in seed 0;
- EA-RG-MAPPO-S currently gives a slightly better zero-collision success/delayed-recovery balance, but the margin is small;
- MAPPO/no-graph is now necessary to establish whether graph structure itself is the major gain.

## Decision

Do not move directly to formal paper test yet.

Next step:

1. run MAPPO/no-graph under the same strong recovery protocol;
2. compare EA, Single, and no-graph under the same zero-collision and unconstrained selection rules;
3. only then decide whether the main contribution should emphasize:
   - multi-relation graph superiority over Single-Graph, or
   - graph-based recovery over no-graph MAPPO with a nuanced EA-vs-Single discussion.
