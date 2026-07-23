# Gate 1 Nominal `weaving_mild` Validation-Selected Protocol Diagnostic

Last updated: 2026-07-22

## Purpose

This diagnostic hardens the oracle-assisted nominal `weaving_mild` result by separating checkpoint selection from test evaluation.

The previous three-seed comparison was useful development evidence, but it evaluated `actor_critic_best.pt` or manually inspected checkpoints. This run adds an explicit validation split:

- validation split selects checkpoints;
- test split only evaluates the frozen validation-selected checkpoints;
- the existing matched test seed `409000` is not used for selection.

This is still development-scale because validation uses only 10 episodes per checkpoint, but the protocol boundary is now correct.

## Implementation

Added:

`scripts/evaluate_3d_nominal_checkpoint_selection.py`

The script supports repeated cases:

```text
--case method=graph_encoder:seed:run_dir
```

Selection score:

```text
1000 * success + 100 * attack_window_formed + 10 * tracking
```

Checkpoints with collision above the configured threshold are invalidated. Here the threshold is `0.0`.

## Validation Selection

Validation configuration:

- target policy: `weaving_mild`
- episodes per checkpoint: `10`
- validation base seed: `509000`
- checkpoints swept: `actor_critic_update_*.pt`
- methods: `multi_relation`, `single`
- seeds: `0`, `1`, `2`

Validation artifacts:

- `results/gate1_nominal_weaving_mild_oracle_assisted_validation_selection_dev10/validation_checkpoint_summary.csv`
- `results/gate1_nominal_weaving_mild_oracle_assisted_validation_selection_dev10/validation_selected_checkpoints.csv`
- `results/gate1_nominal_weaving_mild_oracle_assisted_validation_selection_dev10/validation_checkpoint_selection.md`

Selected checkpoints:

| Method | Seed | Selected update | Validation success | Validation attack window |
|---|---:|---:|---:|---:|
| `multi_relation` | 0 | 30 | 0.900 | 1.000 |
| `multi_relation` | 1 | 30 | 0.500 | 0.500 |
| `multi_relation` | 2 | 25 | 0.700 | 0.800 |
| `single` | 0 | 25 | 0.500 | 0.500 |
| `single` | 1 | 25 | 0.000 | 0.000 |
| `single` | 2 | 20 | 0.000 | 0.000 |

## Test Evaluation

Test configuration:

- test base seed: `409000`
- episodes per selected checkpoint: `30`
- selected checkpoints frozen from validation CSV

Test artifacts:

- `results/gate1_nominal_weaving_mild_oracle_assisted_validation_selection_dev10_test30/test_checkpoint_summary.csv`
- `results/gate1_nominal_weaving_mild_oracle_assisted_validation_selection_dev10_test30/test_selected_checkpoints.csv`
- `results/gate1_nominal_weaving_mild_oracle_assisted_validation_selection_dev10_test30/test_checkpoint_selection.md`
- `results/gate1_nominal_weaving_mild_oracle_assisted_validation_selection_dev10_test30/test_aggregate_summary.json`

Per-seed test results:

| Method | Seed | Test success | Attack-window formed | Collision | Tracking | Connectivity |
|---|---:|---:|---:|---:|---:|---:|
| `multi_relation` | 0 | 0.800 | 0.867 | 0.000 | 0.475 | 0.770 |
| `multi_relation` | 1 | 0.400 | 0.400 | 0.000 | 0.426 | 0.478 |
| `multi_relation` | 2 | 0.700 | 0.733 | 0.000 | 0.499 | 0.984 |
| `single` | 0 | 0.333 | 0.467 | 0.000 | 0.395 | 0.597 |
| `single` | 1 | 0.000 | 0.000 | 0.000 | 0.160 | 0.628 |
| `single` | 2 | 0.000 | 0.000 | 0.000 | 0.114 | 0.425 |

Aggregate test results:

| Method | Success | Attack-window formed | Collision | Tracking | Connectivity |
|---|---:|---:|---:|---:|---:|
| `multi_relation` | 0.633 | 0.667 | 0.000 | 0.466 | 0.744 |
| `single` | 0.111 | 0.156 | 0.000 | 0.223 | 0.550 |
| delta | +0.522 | +0.511 | 0.000 | +0.243 | +0.194 |

## Interpretation

The validation-selected result preserves the method separation:

- `multi_relation` remains nonzero on all three seeds;
- `single` only partially solves seed 0 and fails on seeds 1 and 2;
- success gap is `+52.2` percentage points;
- attack-window gap is `+51.1` percentage points;
- both methods remain collision-free.

This strengthens the scenario-depth evidence because the reported test result is no longer selected on the test split.

## Remaining Limitations

- Validation uses only `10` episodes per checkpoint, so selection noise remains possible.
- This is not a final formal result; a paper-facing run should use more validation episodes or a fixed-update protocol agreed before testing.
- `no_graph` has not yet been added to this oracle-assisted fairness control.
- The result is nominal `weaving_mild` only; strict sensing and relay failure remain deferred for maneuvering targets.

## Decision

Retain oracle-assisted nominal `weaving_mild` as the current scenario-depth enhancement candidate.

Next step before paper-facing use:

1. Decide whether to add `no_graph` as an additional fairness control.
2. If promoting this experiment, rerun with a stronger validation budget, for example 30 validation episodes and 50 test episodes per seed.
3. Do not tune further on the current `409000` test split.
