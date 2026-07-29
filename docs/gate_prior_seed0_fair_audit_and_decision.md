# Gate-Prior Seed0 Fair Audit and Decision

Last updated: 2026-07-29

## Purpose

This audit addresses a fairness risk: gate-prior seed0 had been trained for
100 updates, while the original EA comparison previously used only 40-update
development checkpoints. The goal is to compare both methods under the same
checkpoint candidate set before deciding whether gate-prior deserves seed1/2
runs.

## Completed Checks

1. Gate-prior seed0 fixed suite sweep is complete.
2. Original EA seed0 was extended from update 40 to update 100 using the same
   training state, optimizer state, safety settings, reward settings, BC
   initialization family, and checkpointing rule.
3. Both methods were evaluated over checkpoints 20/40/60/80/100.
4. Both methods were diagnosed with relation-attention and role-pair-gate
   metrics on the same fixed episode seeds.

## Same-Budget Suite Results

| Method | Selected update | Success | Post-loss recovery | Delayed recovery | Collision | Timeout |
|---|---:|---:|---:|---:|---:|---:|
| Original EA seed0 | 40 | 0.525 | 0.675 | 0.200 | 0.000 | 0.475 |
| Gate-prior EA seed0 | 60 | 0.925 | 0.950 | 0.525 | 0.000 | 0.075 |

## Checkpoint Curve

| Method | Update | Success | Post-loss recovery | Delayed recovery | Collision | Timeout |
|---|---:|---:|---:|---:|---:|---:|
| Original EA | 20 | 0.450 | 0.700 | 0.200 | 0.050 | 0.500 |
| Original EA | 40 | 0.525 | 0.675 | 0.200 | 0.000 | 0.475 |
| Original EA | 60 | 0.025 | 0.350 | 0.025 | 0.000 | 0.975 |
| Original EA | 80 | 0.025 | 0.400 | 0.000 | 0.050 | 0.925 |
| Original EA | 100 | 0.025 | 0.500 | 0.000 | 0.000 | 0.975 |
| Gate-prior EA | 20 | 0.750 | 0.850 | 0.425 | 0.050 | 0.200 |
| Gate-prior EA | 40 | 0.625 | 0.800 | 0.325 | 0.000 | 0.375 |
| Gate-prior EA | 60 | 0.925 | 0.950 | 0.525 | 0.000 | 0.075 |
| Gate-prior EA | 80 | 0.800 | 0.925 | 0.475 | 0.000 | 0.200 |
| Gate-prior EA | 100 | 0.275 | 0.625 | 0.125 | 0.000 | 0.725 |

## Mechanism Diagnostics

Diagnostics used 20 fixed episodes under the same relay-failure setting.

| Method | Success episodes | Failure episodes | Task-support attention | Perception attention | Gate mean abs delta | Gate max abs delta |
|---|---:|---:|---:|---:|---:|---:|
| Original EA update40 | 12 | 8 | 0.0111 | 0.0382 | 0.005914 | 0.060720 |
| Gate-prior EA update60 | 18 | 2 | 0.0228 | 0.0628 | 0.025573 | 0.121487 |

The gate-prior model improves both behavior-level metrics and mechanism-level
metrics. Role-pair gates are no longer near-neutral, and task-support/perception
relation usage is higher.

## Decision Rule

Proceed to gate-prior seed1/2 only if seed0 satisfies all conditions:

- Same-budget selected checkpoint improves success and delayed recovery over
  original EA.
- Selected checkpoint has zero collision.
- Gate diagnostics show clearly larger role-pair-gate deviation than original
  EA.
- No new reward, safety, BC, or checkpoint-selection rule is introduced.

Seed0 satisfies all four conditions.

## Decision

Run gate-prior seed1 and seed2 under the exact same dev100 protocol.

If the three-seed result does not show stable improvement over original EA and
Single-Graph MAPPO, stop gate optimization and freeze either original EA or the
best defensible gate-prior candidate. Do not keep changing the gate mechanism or
scenario difficulty.
