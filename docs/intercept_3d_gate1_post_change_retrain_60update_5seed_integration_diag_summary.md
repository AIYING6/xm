# Five-Seed Post-Gate-1 Integration Diagnostic

Last updated: 2026-07-18

## Purpose

This diagnostic verifies that the five-seed post-Gate-1 checkpoint-sweep path works before launching the full formal validation/test budget.

It is not final paper evidence because the evaluation budget is intentionally small:

```text
validation episodes = 3 per candidate checkpoint
test episodes = 10 per selected checkpoint
```

## Setting

- Scenario: `dropout030_relay_failure`.
- Target policy: `straight`.
- Strict target sensing: enabled.
- Agent target-information bottleneck: enabled.
- Methods: `no_graph`, `single`, `multi_relation`.
- Seeds: `0, 1, 2, 3, 4`.
- Candidate checkpoints: updates `10, 20, 30, 40, 50, 60`.
- Validation collision threshold: `0.0`.

Output directory:

```text
results/intercept_3d_gate1_post_change_retrain_60update_5seed_integration_diag/
```

## Aggregate Test Result

| Method | Recovery | Timeout | Collision |
|---|---:|---:|---:|
| `no_graph` | 26.0% | 74.0% | 0.0% |
| `single` | 46.0% | 52.0% | 2.0% |
| `multi_relation` | 94.0% | 6.0% | 0.0% |

The `single` aggregate collision rate comes from one selected seed/checkpoint on the small test split. This reinforces why the formal run must keep collision as a reported metric and use validation-time collision rejection.

## Seed-Aware Statistics

### `multi_relation` vs `single`

| Metric | `single` | `multi_relation` | Delta | 95% CI |
|---|---:|---:|---:|---:|
| Task success | 46.0% | 94.0% | +48.0 pp | [+18.0, +82.0] pp |
| Post-failure recovery | 46.0% | 94.0% | +48.0 pp | [+18.0, +82.0] pp |
| Timeout | 52.0% | 6.0% | -46.0 pp | [-80.0, -16.0] pp |
| Restricted mean recovery steps | 117.28 | 27.32 | -89.96 | [-164.39, -27.24] |
| Tracking during failure | 44.7% | 81.7% | +37.0 pp | [+11.3, +67.0] pp |
| Connectivity during failure | 21.5% | 31.2% | +9.7 pp | [+0.9, +19.8] pp |
| Chain closure during failure | 7.4% | 14.4% | +7.0 pp | [+1.7, +13.2] pp |

`multi_relation` is better than or tied with `single` on recovery for all five seeds. Seed 0 is tied; seeds 1--4 favor `multi_relation`.

### `multi_relation` vs `no_graph`

| Metric | `no_graph` | `multi_relation` | Delta | 95% CI |
|---|---:|---:|---:|---:|
| Task success | 26.0% | 94.0% | +68.0 pp | [+40.0, +94.0] pp |
| Post-failure recovery | 26.0% | 94.0% | +68.0 pp | [+40.0, +94.0] pp |
| Timeout | 74.0% | 6.0% | -68.0 pp | [-94.0, -40.0] pp |
| Restricted mean recovery steps | 164.24 | 27.32 | -136.92 | [-189.22, -81.56] |
| Tracking during failure | 18.6% | 81.7% | +63.1 pp | [+38.8, +86.2] pp |

## Interpretation

The five-seed integration diagnostic passes.

It confirms:

- all method/seed checkpoint directories are present and loadable;
- validation checkpoint selection works with `--max-selection-collision-rate 0.0`;
- disjoint test evaluation works for all selected checkpoints;
- seed-aware statistics work with five training seeds;
- the expected method ordering remains visible after adding seeds `3` and `4`.

It does not replace the formal run.

## Decision

Proceed to the full five-seed formal validation/test budget:

```text
validation episodes = 50
test episodes = 100
validation base seed = 750000
test base seed = 760000
max_selection_collision_rate = 0.0
```

The full run will be substantially slower than this integration diagnostic. Do not tune hyperparameters using the formal test split.

