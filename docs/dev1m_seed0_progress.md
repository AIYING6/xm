# Dev-1M Seed-0 Progress

Generated: 2026-07-24

## Current Stage

The first real development-budget training batch is running.

Mode:

```text
dev_1m
```

Target per run:

```text
3907 updates
1,000,192 environment steps
```

## Launched Jobs

| Method | Seed | Status |
|---|---:|---|
| EA-RG-MAPPO | 0 | running |
| Single-Graph MAPPO | 0 | running |
| MAPPO/no-graph | 0 | running |
| HAPPO | 0 | running |

## Latest Progress Snapshot

Updated after switching from unreliable detached background jobs to foreground resumable chunks:

| Method | Update | Progress | Active | Rough ETA |
|---|---:|---:|---|---:|
| EA-RG-MAPPO | 2200 | 56.31% | chunk complete | 2.27 h |
| Single-Graph MAPPO | 2200 | 56.31% | chunk complete | 2.23 h |
| MAPPO/no-graph | 2200 | 56.31% | chunk complete | 2.19 h |
| HAPPO | 2200 | 56.31% | chunk complete | 2.31 h |

These ETA values are rough runtime diagnostics, not experiment results.

## Early Monitor Signals

The early online eval uses only 5 episodes and must not be treated as final evidence.

Current observations:

- MAPPO/no-graph reached `eval_success_rate=0.4` at update 500.
- EA-RG-MAPPO reached `eval_success_rate=0.6` at update 1700, `0.4` at updates 900, 1500, and 1600, and `0.2` at updates 800, 1100, and 1400.
- Single-Graph reached `eval_success_rate=0.4` at update 1800 after remaining at 0 through update 1700.
- HAPPO reached `eval_success_rate=0.2` at update 1100 and `0.4` at update 1600.
- Single-Graph remained at `eval_success_rate=0.0` through update 1300.
- No non-finite training values were detected outside the allowed unused `eval_intent_acc` column.

The 1000-update audit is recorded in:

```text
docs/dev1m_seed0_1000update_audit.md
```

The 2200-update output audit passed and wrote:

```text
results/dev1m_seed0_2200update_summary.csv
```

At update 2200, the online 5-episode monitor showed:

| Method | Eval Success | Eval Timeout | Avg Distance |
|---|---:|---:|---:|
| EA-RG-MAPPO | 0.0 | 1.0 | 45366.77 |
| Single-Graph MAPPO | 0.0 | 1.0 | 60984.54 |
| MAPPO/no-graph | 0.0 | 1.0 | 22848.85 |
| HAPPO | 0.0 | 1.0 | 30661.40 |

## Execution Note

Detached background jobs were not reliable in the Codex sandbox. The active execution path is now:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/run_manifest_training_chunk.py --method <method> --seed 0 --chunk-updates 100 --python-exe D:/Anaconda/envs/.conda/envs/cac/python.exe
```

The chunk runner trims logs to the latest checkpoint before resuming, preserving a checkpoint-consistent training record.

As of the 1700-update chunks, the trainers also write full training-state checkpoints:

```text
actor_critic_training_state_latest.pt
happo_training_state_latest.pt
```

Future chunks prefer these files so optimizer state is restored when available. The 1600 to 1700 chunks still resumed from weights-only checkpoints because full training-state files did not exist before this code change. The 1700 to 1800 chunks confirmed optimizer-state restore on the real training path for all four methods.

Resume-smoke verification passed after update 1700:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe -m py_compile algorithms/ri_gmappo/simple_ri_gmappo.py scripts/train_happo_baseline.py scripts/run_manifest_training_chunk.py
```

Both temporary resume-smoke runs loaded optimizer state and completed one update under `results/resume_smoke/`.

## Monitor Command

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/check_training_progress.py --mode dev_1m --methods ea_rg_mappo single_graph mappo happo --seeds 0
```

## Next Gate

After all four seed-0 runs finish:

1. run `scripts/audit_training_outputs.py --mode dev_1m --methods ea_rg_mappo single_graph mappo happo --seeds 0`;
2. run validation sweeps only;
3. inspect validation-selected checkpoints and learning curves;
4. then decide whether to launch seeds 1 and 2 unchanged or adjust training protocol.
