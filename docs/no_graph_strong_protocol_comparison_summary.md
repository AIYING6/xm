# No-Graph Strong Protocol Comparison

Last updated: 2026-07-29

## Purpose

This note adds MAPPO/no-graph to the strong post-loss reclosure protocol comparison.

The goal is to determine whether the current recovery gains mainly come from:

- recovery-oriented demonstrations and safety PPO alone; or
- explicit graph structure.

## Shared Protocol

No-graph uses the same protocol as EA-RG-MAPPO-S and Single-Graph:

- strong balanced `offset` recovery BC;
- `120` BC episodes and `20` BC epochs;
- attacker action weight `2.0`;
- strict target sensing;
- target-information bottleneck;
- dropout `0.30`;
- delay `2`;
- relay failure start sampled in `[25,70]`;
- `min_success_step=80`;
- post-loss reclosure reward `0.5`;
- safety PPO with proximity distance `2500` and penalty `0.5`;
- validation over the four-scenario suite;
- checkpoint candidates `20,30,40`.

## No-Graph BC Quality

| Seed | Demo success | Final action accuracy |
|---:|---:|---:|
| 0 | 0.908 | 0.516 |
| 1 | 0.908 | 0.502 |
| 2 | 0.917 | 0.488 |

BC imitation quality is not low. Therefore, if no-graph underperforms, the likely limitation is not simply poor demonstration fitting.

## Unconstrained Validation Selection

| Method | Success | Recovery | After-loss recovery | Delayed recovery | Collision |
|---|---:|---:|---:|---:|---:|
| EA-RG-MAPPO-S | 0.625 | 0.717 | 0.717 | 0.342 | 0.000 |
| Single-Graph | 0.675 | 0.783 | 0.783 | 0.358 | 0.008 |
| No-Graph | 0.383 | 0.517 | 0.517 | 0.333 | 0.008 |

Unconstrained selection shows:

- no-graph can produce some delayed recovery after strong recovery demonstrations;
- graph methods are clearly better on success and recovery;
- Single-Graph is competitive with EA but has a small collision cost in this selection.

## Zero-Collision Diagnostic

| Method | Success | Recovery | After-loss recovery | Delayed recovery | Collision | Timeout |
|---|---:|---:|---:|---:|---:|---:|
| EA-RG-MAPPO-S | 0.625 | 0.717 | 0.717 | 0.342 | 0.000 | 0.375 |
| Single-Graph | 0.600 | 0.783 | 0.783 | 0.333 | 0.000 | 0.400 |
| No-Graph | 0.367 | 0.492 | 0.492 | 0.308 | 0.000 | 0.633 |

EA minus no-graph under zero-collision selection:

| Metric | EA - No-Graph |
|---|---:|
| Success | +0.258 |
| Recovery | +0.225 |
| After-loss recovery | +0.225 |
| Delayed recovery | +0.033 |
| Timeout | -0.258 |
| Collision | 0.000 |

Single minus no-graph under zero-collision selection:

| Metric | Single - No-Graph |
|---|---:|
| Success | +0.233 |
| Recovery | +0.292 |
| After-loss recovery | +0.292 |
| Delayed recovery | +0.025 |
| Timeout | -0.233 |
| Collision | 0.000 |

## Interpretation

The current evidence supports a graph-structure claim:

- both graph methods outperform no-graph MAPPO in zero-collision success and recovery;
- no-graph has similar but slightly lower delayed-recovery probability, while failing more often overall;
- the clearest graph advantage is task completion/recovery reliability, not raw delayed-recovery alone.

The current evidence does not yet support a strong claim that multi-relation EA dominates Single-Graph. EA is slightly better on zero-collision success and delayed recovery, while Single is better on raw recovery.

## Recommended Paper Claim Adjustment

Use a two-level claim:

1. Graph-based coordination improves safe post-loss kill-chain recovery over no-graph MAPPO.
2. The proposed multi-relation role graph improves the safety/delayed-recovery balance and interpretability over a plain single graph, but Single-Graph remains a strong baseline.

This is more defensible than claiming EA is uniformly best across all metrics.

## Next Step

Run HAPPO under the same strong recovery protocol if time permits. If HAPPO remains weak, the main fair comparison set becomes:

- MAPPO/no-graph;
- Single-Graph MAPPO;
- EA-RG-MAPPO-S;
- HAPPO as an additional MARL baseline.

Formal testing should still wait until the validation/test split and checkpoint-selection rule are frozen.
