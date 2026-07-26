# Dev-1M Seed-0 1000-Update Audit

Generated: 2026-07-24

## Status

The first seed-0 development-budget checkpoint stage reached:

```text
1000 / 3907 updates
25.60% of dev_1m
```

Methods completed to update 1000:

- EA-RG-MAPPO;
- Single-Graph MAPPO;
- MAPPO/no-graph;
- HAPPO.

## Validation

Command:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/audit_training_outputs.py --mode dev_1m --methods ea_rg_mappo single_graph mappo happo --seeds 0 --min-update 1000
```

Result:

```text
training output audit passed
```

Summary CSV:

```text
results/dev1m_seed0_1000update_summary.csv
```

All four methods have a `latest` checkpoint and an update-1000 snapshot.

## Online Monitor Snapshot

The online eval uses only 5 episodes and is not formal paper evidence.

| Method | Update | Online Success | Timeout | Avg Distance |
|---|---:|---:|---:|---:|
| EA-RG-MAPPO | 1000 | 0.0 | 1.0 | 41897.61 |
| Single-Graph MAPPO | 1000 | 0.0 | 1.0 | 56761.12 |
| MAPPO/no-graph | 1000 | 0.0 | 1.0 | 26687.40 |
| HAPPO | 1000 | 0.0 | 1.0 | 25210.00 |

Earlier online signals within this run:

- EA-RG-MAPPO reached `eval_success_rate=0.4` at update 900 and `0.2` at update 800.
- MAPPO/no-graph reached `eval_success_rate=0.4` at update 500 and `0.2` at updates 600 and 800.
- Single-Graph and HAPPO have not yet shown online success by update 1000.

## Interpretation

This is a development-training checkpoint, not a conclusion.

Current meaning:

- the training pipeline is now reliable through foreground resumable chunks;
- all four main methods have passed the first 1000-update output audit;
- online metrics are noisy and not suitable for final comparison;
- no method should be discarded before validation checkpoint sweeps over full dev_1m training.

## Next Step

Continue seed-0 chunks toward 3907 updates.

Recommended next milestone:

```text
1500 updates
```

At 1500 updates, repeat:

```text
scripts/audit_training_outputs.py --mode dev_1m --methods ea_rg_mappo single_graph mappo happo --seeds 0 --min-update 1500
scripts/summarize_training_logs.py --mode dev_1m --methods ea_rg_mappo single_graph mappo happo --seeds 0 --out-csv results/dev1m_seed0_1500update_summary.csv
```
