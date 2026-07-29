# Dev-1M Strict Recovery Metric Hardening

Last updated: 2026-07-29

## Purpose

Harden the recovery evaluation so that early geometric interception is not
mistaken for post-failure kill-chain recovery.

The immediate trigger is the MAPPO/no-graph seed-1 anomaly under
`fresh20_dropout030_delay2`: it reaches `0.9667` legacy recovery mostly by
forming an attack window around step `57`, shortly after relay failure starts at
step `40`.

## Implementation

Added a post-processing script:

`scripts/analyze_strict_recovery_hardening.py`

The script reads an evaluation summary CSV, expands its referenced per-episode
CSVs, and reports:

- legacy recovery;
- recovered-after-loss;
- delayed recovery with configurable minimum first-chain step thresholds.

For this diagnostic:

```text
input = results/paper_config_runs/dev_1m/fresh_message_stress/fresh20_dropout030_delay2_seed0_2/episode_summary.csv
min_recovery_steps = 60, 80, 100
```

Outputs:

- `results/paper_config_runs/dev_1m/fresh_message_stress/fresh20_dropout030_delay2_seed0_2/strict_recovery_hardening/strict_recovery_episode_metrics.csv`
- `results/paper_config_runs/dev_1m/fresh_message_stress/fresh20_dropout030_delay2_seed0_2/strict_recovery_hardening/strict_recovery_seed_summary.csv`
- `results/paper_config_runs/dev_1m/fresh_message_stress/fresh20_dropout030_delay2_seed0_2/strict_recovery_hardening/strict_recovery_aggregate_summary.csv`

## Aggregate Results

| Method | Legacy recovery | Recovered after loss | Delayed recovery >= 60 | Delayed recovery >= 80 | Delayed recovery >= 100 |
| --- | ---: | ---: | ---: | ---: | ---: |
| EA-RG-MAPPO | 0.2222 | 0.2222 | 0.1222 | 0.0333 | 0.0333 |
| MAPPO/no-graph | 0.3222 | 0.3222 | 0.1778 | 0.0000 | 0.0000 |
| Single-Graph | 0.0778 | 0.0778 | 0.0778 | 0.0000 | 0.0000 |

## Seed-Level Results

| Method | Train seed | Legacy recovery | Delayed >= 60 | Delayed >= 80 | Delayed >= 100 |
| --- | ---: | ---: | ---: | ---: | ---: |
| EA-RG-MAPPO | 0 | 0.2000 | 0.2000 | 0.0000 | 0.0000 |
| EA-RG-MAPPO | 1 | 0.4333 | 0.1333 | 0.1000 | 0.1000 |
| EA-RG-MAPPO | 2 | 0.0333 | 0.0333 | 0.0000 | 0.0000 |
| MAPPO/no-graph | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| MAPPO/no-graph | 1 | 0.9667 | 0.5333 | 0.0000 | 0.0000 |
| MAPPO/no-graph | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Single-Graph | 0 | 0.2333 | 0.2333 | 0.0000 | 0.0000 |
| Single-Graph | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Single-Graph | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Interpretation

- The existing `post_failure_chain_recovered_after_loss` field is not sufficient
  to filter out fast geometric interception in this stress setting.
- A delayed-recovery threshold is effective. With `>=80` or `>=100`, the
  MAPPO/no-graph seed-1 anomaly drops from `0.9667` to `0.0000`.
- EA-RG-MAPPO still retains a small amount of delayed recovery at `>=80` and
  `>=100` through seed 1 (`0.1000`), but the absolute rate is still low.
- This means metric hardening can prevent misleading conclusions, but it does
  not yet create a strong positive main result. The final protocol needs both:
  a stricter metric and retraining or task design that produces enough delayed
  recoveries for meaningful comparison.

## Decision

Use delayed post-failure recovery as a candidate primary metric for the next
formal protocol.

Recommended candidate:

```text
delayed_recovery_ge_80
```

Reason:

- it starts after relay failure has been active for 40 steps;
- it filters early geometry-driven closure;
- it still leaves nonzero EA signal in the diagnostic.

Do not use raw success or legacy post-failure recovery alone as the main paper
metric for the final strict relay-failure task.

