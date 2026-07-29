# Strong-Protocol Four-Method Development Comparison

Last updated: 2026-07-29

## Scope

This document merges the current 3-seed development validation results for the
strong post-loss recovery protocol.

Methods:

- EA-RG-MAPPO.
- Single-Graph MAPPO.
- MAPPO/no-graph.
- HAPPO.

All rows use suite-level checkpoint selection over the four relay-failure timing
scenarios with `delayed_recovery_min_step=80`. These are development validation
results, not final held-out test results.

## Selected-Checkpoint Means

| Method | Updates | Success | Post-loss recovery | Delayed recovery | Collision |
|---|---:|---:|---:|---:|---:|
| EA-RG-MAPPO | 30/30/20 | 0.625 | 0.717 | 0.342 | 0.000 |
| Single-Graph MAPPO | 20/20/20 | 0.675 | 0.783 | 0.358 | 0.008 |
| MAPPO/no-graph | 20/20/20 | 0.383 | 0.517 | 0.333 | 0.008 |
| HAPPO | 20/40/40 | 0.167 | 0.258 | 0.083 | 0.017 |

## Seed-Level Results

| Method | Seed | Update | Success | Post-loss recovery | Delayed recovery | Collision |
|---|---:|---:|---:|---:|---:|---:|
| EA-RG-MAPPO | 0 | 30 | 0.575 | 0.725 | 0.275 | 0.000 |
| EA-RG-MAPPO | 1 | 30 | 0.825 | 0.850 | 0.375 | 0.000 |
| EA-RG-MAPPO | 2 | 20 | 0.475 | 0.575 | 0.375 | 0.000 |
| Single-Graph MAPPO | 0 | 20 | 0.725 | 0.750 | 0.400 | 0.025 |
| Single-Graph MAPPO | 1 | 20 | 0.550 | 0.725 | 0.275 | 0.000 |
| Single-Graph MAPPO | 2 | 20 | 0.750 | 0.875 | 0.400 | 0.000 |
| MAPPO/no-graph | 0 | 20 | 0.400 | 0.625 | 0.325 | 0.000 |
| MAPPO/no-graph | 1 | 20 | 0.450 | 0.575 | 0.375 | 0.025 |
| MAPPO/no-graph | 2 | 20 | 0.300 | 0.350 | 0.300 | 0.000 |
| HAPPO | 0 | 20 | 0.425 | 0.475 | 0.200 | 0.000 |
| HAPPO | 1 | 40 | 0.075 | 0.200 | 0.050 | 0.000 |
| HAPPO | 2 | 40 | 0.000 | 0.100 | 0.000 | 0.050 |

## Interpretation

The current evidence supports a strong but careful claim:

1. Graph-based coordination is clearly better than no-graph baselines for safe
   post-loss recovery. EA-RG-MAPPO improves over MAPPO/no-graph by `+0.242`
   success and `+0.200` post-loss recovery, and over HAPPO by `+0.458` success
   and `+0.459` post-loss recovery.
2. Single-Graph MAPPO is a strong competitor. It slightly exceeds EA-RG-MAPPO
   on raw success, post-loss recovery, and delayed recovery in this development
   result, but has a small collision rate.
3. EA-RG-MAPPO is safer in this protocol, with zero selected-checkpoint
   collisions across all three seeds. This is useful, but it is not enough by
   itself to claim broad dominance over Single-Graph MAPPO.

## Consequence for Paper Strategy

Do not write the method claim as:

> EA-RG-MAPPO fully outperforms all baselines.

The defensible current claim is:

> Graph-structured coordination substantially improves strict-sensing
> relay-failure recovery over no-graph MARL baselines. The proposed
> multi-relation role graph provides a safer and more interpretable
> mechanism-level alternative to a strong single-graph baseline, but the current
> role-pair gate needs strengthening before it can support a clean performance
> superiority claim over Single-Graph MAPPO.

## Next Decision

Before launching expensive 1M/2M formal training, run the role-gate prior
100-update diagnostic. The reason is practical: current diagnostics show
role-pair gates remain almost neutral, so a longer run may only reproduce the
same Single-Graph versus EA ambiguity at higher cost.
