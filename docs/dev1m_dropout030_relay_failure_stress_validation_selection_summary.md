# Dev-1M Dropout030 Relay-Failure Stress Validation Selection

Generated: 2026-07-28

## Scope

This document summarizes validation checkpoint selection performed directly under the `dropout030_relay_failure` stress scenario.

Protocol:

- scenario: `dropout030_relay_failure`;
- split: validation;
- 50 matched validation episodes per checkpoint;
- strict target sensing enabled;
- agent target information bottleneck enabled;
- zero-collision checkpoint-selection constraint;
- checkpoints from the existing dev-1M training runs;
- no retraining for this stress-selection pass.

## Selected Checkpoints

| Method | Seed | Selected update | Success | Recovery | Recovery steps | Collision |
|---|---:|---:|---:|---:|---:|---:|
| MAPPO/no-graph | 0 | 3600 | 0.52 | 0.52 | 17.5385 | 0.00 |
| MAPPO/no-graph | 1 | 2300 | 0.90 | 0.90 | 22.9111 | 0.00 |
| MAPPO/no-graph | 2 | 3907 | 0.00 | 0.00 | inf | 0.00 |
| Single-Graph MAPPO | 0 | 1800 | 0.50 | 0.50 | 10.0000 | 0.00 |
| Single-Graph MAPPO | 1 | 200 | 0.16 | 0.16 | 20.7500 | 0.00 |
| Single-Graph MAPPO | 2 | 2560 | 0.58 | 0.58 | 22.1034 | 0.00 |
| EA-RG-MAPPO | 0 | 1500 | 0.20 | 0.20 | 17.5000 | 0.00 |
| EA-RG-MAPPO | 1 | 3800 | 0.40 | 0.40 | 163.7000 | 0.00 |
| EA-RG-MAPPO | 2 | 2400 | 0.42 | 0.42 | 27.2857 | 0.00 |
| HAPPO | 0 | 900 | 0.26 | 0.26 | 80.0000 | 0.00 |
| HAPPO | 1 | 1000 | 0.04 | 0.04 | 71.0000 | 0.00 |
| HAPPO | 2 | 2400 | 0.12 | 0.12 | 105.1670 | 0.00 |

## Aggregate

| Method | Mean success | Std success | Min | Max |
|---|---:|---:|---:|---:|
| MAPPO/no-graph | 0.4733 | 0.4518 | 0.00 | 0.90 |
| Single-Graph MAPPO | 0.4133 | 0.2230 | 0.16 | 0.58 |
| EA-RG-MAPPO | 0.3400 | 0.1217 | 0.20 | 0.42 |
| HAPPO | 0.1400 | 0.1114 | 0.04 | 0.26 |

## Interpretation

This stress-validation result does **not** support using `dropout030_relay_failure` as the final main experiment in its current form.

The earlier stress test used nominal validation-selected checkpoints and showed EA-RG-MAPPO ahead of MAPPO/no-graph. After checkpoint selection is performed directly under the stress scenario, MAPPO/no-graph becomes the best 3-seed mean method and Single-Graph MAPPO also exceeds EA-RG-MAPPO.

This means the apparent stress advantage was partly a checkpoint-selection artifact. The current evidence does not justify the claim that the multi-relation role graph is robustly better under dropout plus relay failure.

## Decision

Do not proceed to final paper reporting with `dropout030_relay_failure` as the sole stress scenario.

Running held-out stress testing from these stress-selected checkpoints may still be useful as an audit, but it is unlikely to rescue the main claim because validation ordering already favors MAPPO/no-graph and Single-Graph over EA-RG-MAPPO.

## Required Next Direction

The next experiment must make the task depend more directly on communication-mediated information recovery, not just target interception under noisy communication.

Recommended next stress escalation:

1. add or use a delay-plus-dropout relay-failure scenario:

```text
dropout030 + delay2 + relay_failure + strict_target_sensing + bottleneck
```

2. if still insufficient, move to earlier relay failure:

```text
dropout030 + delay2 + relay_failure_early
```

3. if no-graph remains competitive, introduce mild weaving target or retrain under a topology-randomized curriculum instead of only evaluating existing nominal-trained checkpoints.

The next implementation step is likely a small scenario-definition addition, because the current scenario list contains `dropout030_delay2_scout_failure` but not `dropout030_delay2_relay_failure`.
