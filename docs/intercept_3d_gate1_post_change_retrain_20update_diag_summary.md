# Post-Gate-1 20-Update Retraining Diagnostic

Last updated: 2026-07-18

## Purpose

This diagnostic checks whether the Gate 1 communication-feasibility changes remain trainable under the frozen strict-sensing bottleneck dropout-relay setting.

It is a development decision run, not final paper evidence. The goal is to decide whether the protocol is stable enough to justify longer-budget retraining.

## Setting

- Scenario: `dropout030_relay_failure`.
- Target policy: `straight`.
- Strict target sensing: enabled.
- Agent target-information bottleneck: enabled.
- Methods: `single`, `multi_relation`.
- Training seeds: `0, 1, 2`.
- Continuation budget: `20` PPO updates from existing source checkpoints.
- Checkpoint snapshots: updates `5, 10, 15, 20`.
- Validation split: `10` matched episodes per seed/method/checkpoint.
- Test split: `20` matched episodes per selected seed/method checkpoint.

Validation and test episodes are disjoint. Checkpoints were selected on validation before test evaluation.

## Selected Checkpoints

| Method | Seed | Selected update | Validation recovery |
|---|---:|---:|---:|
| `single` | 0 | 20 | 100.0% |
| `single` | 1 | 5 | 10.0% |
| `single` | 2 | 5 | 10.0% |
| `multi_relation` | 0 | 5 | 100.0% |
| `multi_relation` | 1 | 10 | 100.0% |
| `multi_relation` | 2 | 15 | 100.0% |

The selected updates show that `multi_relation` is stable across seeds, while `single` remains seed-sensitive under the stricter communication-feasible setting.

## Test Results

| Method | Seed | Success | Recovery | Timeout | Tracking during failure | Connectivity during failure |
|---|---:|---:|---:|---:|---:|---:|
| `single` | 0 | 70.0% | 70.0% | 30.0% | 74.8% | 28.9% |
| `single` | 1 | 20.0% | 20.0% | 80.0% | 32.0% | 13.0% |
| `single` | 2 | 10.0% | 10.0% | 85.0% | 24.4% | 13.2% |
| `multi_relation` | 0 | 85.0% | 85.0% | 15.0% | 87.7% | 30.1% |
| `multi_relation` | 1 | 95.0% | 95.0% | 5.0% | 95.5% | 31.6% |
| `multi_relation` | 2 | 100.0% | 100.0% | 0.0% | 100.0% | 30.7% |

Aggregate recovery over `60` matched test episodes:

- `single`: `33.3%`.
- `multi_relation`: `93.3%`.

## Seed-Aware Statistics

Hierarchical bootstrap resampled training seeds first and matched episodes second.

| Metric | `single` | `multi_relation` | Delta | 95% CI |
|---|---:|---:|---:|---:|
| Task success | 33.3% | 93.3% | +60.0 pp | [+16.7, +91.7] pp |
| Post-failure recovery | 33.3% | 93.3% | +60.0 pp | [+16.7, +91.7] pp |
| Timeout | 65.0% | 6.7% | -58.3 pp | [-88.3, -16.7] pp |
| Restricted mean recovery steps | 145.25 | 20.12 | -125.13 | [-189.58, -35.85] |
| Tracking during failure | 43.7% | 94.4% | +50.7 pp | [+14.5, +76.8] pp |
| Connectivity during failure | 18.3% | 30.8% | +12.5 pp | [+1.5, +19.8] pp |
| Chain closure during failure | 5.0% | 14.3% | +9.3 pp | [+2.4, +14.4] pp |

Recovered-only mean recovery time is similar:

- `single`: `6.05` steps over `20` recovered episodes.
- `multi_relation`: `5.84` steps over `56` recovered episodes.

For paper claims, use recovery probability and restricted mean recovery time, not recovered-only speed.

## Interpretation

The 20-update post-Gate-1 diagnostic strongly supports continuing the communication-feasible route.

The main finding is not that training is complete. The useful decision is:

- Gate 1 changes did not break trainability.
- `multi_relation` remains robust after delayed-message causality and target-cache constraints.
- `single` becomes unstable across seeds when the actor can only use delivered target information.
- The bottleneck dropout-relay protocol is still the best current formal-candidate setting.

## Decision

Proceed to a longer-budget post-Gate-1 diagnostic before any five-seed paper run.

Recommended next step:

1. Run `single` and `multi_relation` for `60` post-Gate-1 PPO continuation updates with snapshots every `10` updates.
2. Use the same validation/test split discipline.
3. If the 60-update result keeps positive seed-level deltas and does not collapse, expand to five seeds.
4. Add or retrain `no_graph` only after the `single` vs `multi_relation` route is stable.

Do not start 4v2, JSBSim, missile, ELO, or full self-play before this longer-budget communication-feasible evidence is locked.

