# Post-Gate-1 60-Update Three-Method Safety-Selected Diagnostic

Last updated: 2026-07-18

## Purpose

This diagnostic adds `no_graph` to the post-Gate-1 60-update setting and uses a validation-time safety rule before final testing.

The safety rule is:

```text
--max-selection-collision-rate 0.0
```

Validation checkpoints with nonzero collision rate are rejected before checkpoint selection. The final test split is disjoint from validation.

This is a development diagnostic and a formal-expansion gate, not final paper evidence.

## Setting

- Scenario: `dropout030_relay_failure`.
- Target policy: `straight`.
- Strict target sensing: enabled.
- Agent target-information bottleneck: enabled.
- Methods: `no_graph`, `single`, `multi_relation`.
- Training seeds: `0, 1, 2`.
- Continuation budget: `60` PPO updates.
- Checkpoint snapshots: updates `10, 20, 30, 40, 50, 60`.
- Validation split: `10` matched episodes per candidate checkpoint.
- Test split: `20` matched episodes per selected checkpoint.
- Validation collision threshold: `0.0`.

Outputs:

```text
results/intercept_3d_gate1_post_change_retrain_60update_three_method_safety_selected_diag/
```

## Selected Checkpoints

| Method | Seed | Selected update | Validation recovery | Validation collision |
|---|---:|---:|---:|---:|
| `no_graph` | 0 | 60 | 0.0% | 0.0% |
| `no_graph` | 1 | 20 | 90.0% | 0.0% |
| `no_graph` | 2 | 60 | 0.0% | 0.0% |
| `single` | 0 | 60 | 70.0% | 0.0% |
| `single` | 1 | 50 | 50.0% | 0.0% |
| `single` | 2 | 10 | 20.0% | 0.0% |
| `multi_relation` | 0 | 40 | 100.0% | 0.0% |
| `multi_relation` | 1 | 40 | 90.0% | 0.0% |
| `multi_relation` | 2 | 60 | 100.0% | 0.0% |

`no_graph` seed 0 and seed 2 had no useful collision-free recovery checkpoint on the validation split. This is a baseline stability issue, not a checkpoint-selection artifact.

## Test Results

| Method | Seed | Success | Recovery | Timeout | Collision | Tracking during failure | Connectivity during failure |
|---|---:|---:|---:|---:|---:|---:|---:|
| `no_graph` | 0 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 4.7% |
| `no_graph` | 1 | 95.0% | 95.0% | 5.0% | 0.0% | 60.3% | 33.8% |
| `no_graph` | 2 | 0.0% | 0.0% | 100.0% | 0.0% | 0.8% | 4.8% |
| `single` | 0 | 75.0% | 75.0% | 25.0% | 0.0% | 78.6% | 31.0% |
| `single` | 1 | 25.0% | 25.0% | 75.0% | 0.0% | 36.3% | 14.8% |
| `single` | 2 | 15.0% | 15.0% | 85.0% | 0.0% | 26.6% | 13.4% |
| `multi_relation` | 0 | 100.0% | 100.0% | 0.0% | 0.0% | 100.0% | 34.0% |
| `multi_relation` | 1 | 95.0% | 95.0% | 5.0% | 0.0% | 95.7% | 32.4% |
| `multi_relation` | 2 | 100.0% | 100.0% | 0.0% | 0.0% | 100.0% | 33.0% |

Aggregate recovery:

- `no_graph`: `31.7%`.
- `single`: `38.3%`.
- `multi_relation`: `98.3%`.

All selected test checkpoints had zero collision on this split.

## Seed-Aware Statistics

### `multi_relation` vs `single`

| Metric | `single` | `multi_relation` | Delta | 95% CI |
|---|---:|---:|---:|---:|
| Task success | 38.3% | 98.3% | +60.0 pp | [+26.7, +86.7] pp |
| Post-failure recovery | 38.3% | 98.3% | +60.0 pp | [+26.7, +86.7] pp |
| Timeout | 61.7% | 1.7% | -60.0 pp | [-86.7, -26.7] pp |
| Restricted mean recovery steps | 138.00 | 9.32 | -128.68 | [-186.23, -57.12] |
| Tracking during failure | 47.2% | 98.6% | +51.4 pp | [+22.9, +74.8] pp |
| Connectivity during failure | 19.7% | 33.1% | +13.4 pp | [+3.3, +20.9] pp |
| Chain closure during failure | 5.6% | 15.2% | +9.6 pp | [+4.0, +14.4] pp |

All three seeds favor `multi_relation` over `single`.

### `multi_relation` vs `no_graph`

| Metric | `no_graph` | `multi_relation` | Delta | 95% CI |
|---|---:|---:|---:|---:|
| Task success | 31.7% | 98.3% | +66.7 pp | [+1.7, +100.0] pp |
| Post-failure recovery | 31.7% | 98.3% | +66.7 pp | [+1.7, +100.0] pp |
| Timeout | 68.3% | 1.7% | -66.7 pp | [-100.0, -1.7] pp |
| Restricted mean recovery steps | 152.05 | 9.32 | -142.73 | [-214.65, -3.28] |
| Tracking during failure | 20.4% | 98.6% | +78.2 pp | [+37.1, +100.0] pp |

The `no_graph` comparison is very high variance because seed 1 performs well while seeds 0 and 2 fail completely. This reinforces the need for seed-level reporting.

## Decision

`no_graph` should be included in the formal baseline set, but it should not be tuned or repaired seed-by-seed.

Formal policy:

- keep a predefined source policy for all `no_graph` seeds;
- include seed-level points and appendix rows;
- report that `no_graph` is unstable under communication-feasible strict sensing;
- do not selectively replace only weak `no_graph` seeds after seeing validation or test outcomes.

The graph-method comparison is now strong enough to prepare five-seed expansion. Before launching, the remaining practical blocker is source-checkpoint availability for seeds `3` and `4`.

## Next Launch Gate

Prepare five-seed formal expansion with:

- methods: `no_graph`, `single`, `multi_relation`;
- seeds: `0, 1, 2, 3, 4`;
- validation episodes: at least `50` matched episodes per method/seed;
- test episodes: preferably `100` matched episodes per method/seed;
- validation collision threshold: `0.0`;
- checkpoint interval: `10` updates;
- post-Gate-1 continuation budget: `60` updates unless a new budget diagnostic is explicitly opened.

Do not start 5v2, JSBSim, missile, or self-play until this five-seed 3v1 evidence is complete.

