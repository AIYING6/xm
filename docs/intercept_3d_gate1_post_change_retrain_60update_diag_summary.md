# Post-Gate-1 60-Update Retraining Diagnostic

Last updated: 2026-07-18

## Purpose

This diagnostic extends the post-Gate-1 retraining check from `20` to `60` PPO continuation updates under the communication-feasible 3DOF semantics.

It tests whether the strict-sensing bottleneck dropout-relay protocol remains a credible candidate for five-seed formal expansion after:

- task-support edges require delivered communication;
- target information propagates through delayed per-agent caches;
- 3DOF actors no longer receive global intent-context broadcasts.

This is still development evidence, not final paper evidence.

## Setting

- Scenario: `dropout030_relay_failure`.
- Target policy: `straight`.
- Strict target sensing: enabled.
- Agent target-information bottleneck: enabled.
- Methods: `single`, `multi_relation`.
- Training seeds: `0, 1, 2`.
- Continuation budget: `60` PPO updates.
- Checkpoint snapshots: updates `10, 20, 30, 40, 50, 60`.
- Validation split: `10` matched episodes per candidate checkpoint.
- Test split: `20` matched episodes per selected seed/method checkpoint.

Validation and test episodes are disjoint. Checkpoints were selected on validation before test evaluation.

## Selected Checkpoints

| Method | Seed | Selected update | Validation recovery |
|---|---:|---:|---:|
| `single` | 0 | 60 | 90.0% |
| `single` | 1 | 60 | 30.0% |
| `single` | 2 | 10 | 10.0% |
| `multi_relation` | 0 | 40 | 100.0% |
| `multi_relation` | 1 | 20 | 100.0% |
| `multi_relation` | 2 | 60 | 100.0% |

The validation sweep again shows stronger seed stability for `multi_relation`. The `single` model improves over the 20-update diagnostic but remains sensitive to seed.

## Test Results

| Method | Seed | Success | Recovery | Timeout | Collision | Tracking during failure | Connectivity during failure |
|---|---:|---:|---:|---:|---:|---:|---:|
| `single` | 0 | 75.0% | 75.0% | 25.0% | 0.0% | 78.8% | 29.6% |
| `single` | 1 | 35.0% | 35.0% | 65.0% | 0.0% | 44.8% | 17.3% |
| `single` | 2 | 20.0% | 20.0% | 80.0% | 0.0% | 30.6% | 14.9% |
| `multi_relation` | 0 | 90.0% | 90.0% | 5.0% | 5.0% | 94.9% | 31.7% |
| `multi_relation` | 1 | 90.0% | 90.0% | 10.0% | 0.0% | 91.1% | 31.4% |
| `multi_relation` | 2 | 100.0% | 100.0% | 0.0% | 0.0% | 100.0% | 33.5% |

Aggregate recovery over `60` matched test episodes:

- `single`: `43.3%`.
- `multi_relation`: `93.3%`.

## Seed-Aware Statistics

Hierarchical bootstrap resampled training seeds first and matched episodes second.

| Metric | `single` | `multi_relation` | Delta | 95% CI |
|---|---:|---:|---:|---:|
| Task success | 43.3% | 93.3% | +50.0 pp | [+15.0, +80.0] pp |
| Post-failure recovery | 43.3% | 93.3% | +50.0 pp | [+15.0, +80.0] pp |
| Timeout | 56.7% | 5.0% | -51.7 pp | [-80.0, -20.0] pp |
| Restricted mean recovery steps | 127.32 | 16.75 | -110.57 | [-171.70, -42.23] |
| Tracking during failure | 51.4% | 95.3% | +44.0 pp | [+16.4, +69.0] pp |
| Connectivity during failure | 20.6% | 32.2% | +11.6 pp | [+2.5, +19.1] pp |
| Chain closure during failure | 6.3% | 14.1% | +7.8 pp | [+1.9, +12.9] pp |

Recovered-only mean recovery time:

- `single`: `6.12` steps over `26` recovered episodes.
- `multi_relation`: `5.89` steps over `56` recovered episodes.

As before, paper claims should emphasize recovery probability, timeout reduction, tracking preservation, connectivity, and restricted mean recovery time. Recovered-only speed is descriptive only.

## Comparison with 20-Update Diagnostic

| Budget | `single` recovery | `multi_relation` recovery | Delta |
|---:|---:|---:|---:|
| 20 updates | 33.3% | 93.3% | +60.0 pp |
| 60 updates | 43.3% | 93.3% | +50.0 pp |

Longer continuation improves `single` somewhat but does not close the gap. `multi_relation` remains stable at `93.3%` recovery across both diagnostics.

## Risk Notes

- This remains only a three-seed development diagnostic.
- One selected `multi_relation` seed produced `5.0%` collision on the 20-episode test split. Collision and flight-safety metrics must remain hard constraints in the formal run.
- The current test split has only `20` episodes per seed, so exact rates may move when expanded to five seeds and more episodes.
- `no_graph` is not included in this post-Gate-1 60-update diagnostic yet.

## Decision

The `single` vs `multi_relation` route is stable enough to proceed toward formal expansion planning.

Recommended next step:

1. Add a post-Gate-1 `no_graph` diagnostic or clearly document why `no_graph` will be handled in the final five-seed run.
2. Prepare the five-seed frozen protocol for `single` and `multi_relation` with larger disjoint test sets.
3. Before launching five seeds, define a collision handling rule: report collisions separately and reject checkpoints if validation collision exceeds a fixed threshold.
4. Keep 4v2, JSBSim, missile, and self-play deferred until the 3v1 communication-feasible evidence is locked.

