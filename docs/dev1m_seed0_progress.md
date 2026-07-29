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
| EA-RG-MAPPO | 3907 | 100.00% | complete | 0.00 h |
| Single-Graph MAPPO | 3907 | 100.00% | complete | 0.00 h |
| MAPPO/no-graph | 3907 | 100.00% | complete | 0.00 h |
| HAPPO | 3907 | 100.00% | complete, post-correction rerun aligned | 0.00 h |

These ETA values are rough runtime diagnostics, not experiment results.

The earlier HAPPO-style run reached 2300 updates, but it used the pre-correction sequential PPO-style loss. It is now historical diagnostic evidence only. The formal HAPPO baseline restarted under `runs/happo_standard/` with the sequential joint-ratio-corrected surrogate and has now caught up to the other three seed-0 methods.

## Early Monitor Signals

The early online eval uses only 5 episodes and must not be treated as final evidence.

Current observations:

- MAPPO/no-graph reached `eval_success_rate=0.4` at update 500.
- EA-RG-MAPPO reached `eval_success_rate=0.6` at update 1700, `0.4` at updates 900, 1500, and 1600, and `0.2` at updates 800, 1100, and 1400.
- Single-Graph reached `eval_success_rate=0.4` at update 1800 after remaining at 0 through update 1700.
- The earlier HAPPO-style monitor reached `eval_success_rate=0.2` at update 1100 and `0.4` at update 1600, but those values are not formal HAPPO evidence after the correction.
- Corrected HAPPO reached update 3907. The online 5-episode monitor reached `eval_success_rate=0.4` at update 900 and returned to `0.0` at later monitored checkpoints, so it remains a noisy training monitor rather than evidence.
- Single-Graph remained at `eval_success_rate=0.0` through update 1300.
- No non-finite training values were detected outside the allowed unused `eval_intent_acc` column.

The 1000-update audit is recorded in:

```text
docs/dev1m_seed0_1000update_audit.md
```

The 2300-update output audit passed for EA-RG-MAPPO, Single-Graph, MAPPO/no-graph, and the historical pre-correction HAPPO-style run:

```text
results/dev1m_seed0_2300update_summary.csv
```

At update 2300, the online 5-episode monitor showed:

| Method | Eval Success | Eval Timeout | Avg Distance |
|---|---:|---:|---:|
| EA-RG-MAPPO | 0.0 | 1.0 | 30708.76 |
| Single-Graph MAPPO | 0.0 | 1.0 | 28763.21 |
| MAPPO/no-graph | 0.0 | 1.0 | 22786.01 |
| HAPPO | 0.0 | 1.0 | 30790.41 |

The corrected four-method 3907-update output audit passed and wrote:

```text
results/dev1m_seed0_3907update_summary.csv
```

Next required stage:

```text
validation checkpoint sweep
```

All four seed-0 methods completed the dev-1M training budget. Formal comparison still requires validation checkpoint selection before any test-split claim.

## Validation Sweep Progress

The validation sweep path is now resumable and chunk-safe. A resume-key bug in
`scripts/evaluate_3d_checkpoint_sweep.py` was fixed so completed checkpoint rows
are keyed by split, scenario, graph encoder, three ablation settings, seed, and
checkpoint update. The same chunk interface is available for HAPPO via
`--max-new-evals`.

Current EA-RG-MAPPO seed-0 validation status:

| Method | Seed | Split | Scenario | Episodes/checkpoint | Completed checkpoints | Total checkpoints |
|---|---:|---|---|---:|---:|---:|
| EA-RG-MAPPO | 0 | validation | relay_failure strict-sensing | 50 | 48 | 48 |
| Single-Graph MAPPO | 0 | validation | relay_failure strict-sensing | 50 | 48 | 48 |
| MAPPO/no-graph | 0 | validation | relay_failure strict-sensing | 50 | 47 | 47 |
| HAPPO | 0 | validation | relay_failure strict-sensing | 50 | 40 | 40 |

The current validation-selected checkpoints are:

| Method | Update | Success | Recovery | Recovery steps | Collision | Selection score |
|---|---:|---:|---:|---:|---:|---:|
| EA-RG-MAPPO | 1600 | 0.94 | 0.94 | 19.7447 | 0.00 | 1014.26 |
| Single-Graph MAPPO | 3907 | 0.82 | 0.82 | 19.2927 | 0.00 | 882.707 |
| MAPPO/no-graph | 3800 | 0.62 | 0.62 | 17.8065 | 0.00 | 664.194 |
| HAPPO | 900 | 0.14 | 0.14 | 67.2857 | 0.00 | 72.7143 |

The full EA-RG-MAPPO seed-0 validation sweep confirms that the late 5-episode
online training monitor can miss strong mid-training checkpoints. No test-split
claim should be made until validation selection is completed for all seed-0
methods and the selected checkpoints are frozen. The completed Single-Graph
sweep shows a strong baseline, which is useful for paper credibility; the
current validation gap is `+12 pp` success/recovery in favor of EA-RG-MAPPO.
The completed MAPPO/no-graph sweep selects update 3800. The current validation
ordering is monotonic with graph expressiveness: MAPPO/no-graph `0.62`,
Single-Graph `0.82`, and EA-RG-MAPPO `0.94` success/recovery. This is promising,
but it remains seed-0 validation evidence until test-split and multi-seed checks
are run.
The completed HAPPO sweep selects update 900 and remains much weaker than the
graph-based methods on strict-sensing relay-failure recovery. The seed-0
validation-selected summary is recorded in:

```text
docs/dev1m_seed0_validation_selection_summary.md
results/paper_config_runs/dev_1m/checkpoint_sweeps/seed0_validation_selected_summary.csv
```

## Held-Out Test Progress

The seed-0 held-out test split is complete for the four validation-selected
checkpoints. Test uses base seed `220000`, 100 matched episodes per method, the
same strict-sensing relay-failure scenario, and no checkpoint reselection.

| Method | Selected update | Test success | Test recovery | Recovery steps | Timeout | Collision |
|---|---:|---:|---:|---:|---:|---:|
| EA-RG-MAPPO | 1600 | 0.89 | 0.89 | 18.9663 | 0.11 | 0.00 |
| Single-Graph MAPPO | 3907 | 0.80 | 0.80 | 19.4875 | 0.20 | 0.00 |
| MAPPO/no-graph | 3800 | 0.60 | 0.60 | 17.8667 | 0.40 | 0.00 |
| HAPPO | 900 | 0.08 | 0.08 | 79.8750 | 0.92 | 0.00 |

The held-out test preserves the validation ordering:

```text
EA-RG-MAPPO > Single-Graph MAPPO > MAPPO/no-graph > HAPPO
```

This is a strong seed-0 protocol signal, but it is not a final paper claim until
seeds 1/2 are trained, validation-selected, and tested under the same procedure.

Detailed outputs:

```text
docs/dev1m_seed0_heldout_test_summary.md
results/paper_config_runs/dev_1m/test_eval/seed0_heldout_test_summary.csv
```

## Multi-Seed Expansion

Seeds 1 and 2 have been launched for all four methods under the unchanged
`dev_1m` protocol. A 20-update startup chunk was completed for each run to verify
that the manifest commands, output paths, checkpointing, and HAPPO standard
baseline path all work before committing more training budget.

| Method | Seed 1 update | Seed 2 update | Target updates |
|---|---:|---:|---:|
| EA-RG-MAPPO | 3907 | 3907 | 3907 |
| Single-Graph MAPPO | 3907 | 3907 | 3907 |
| MAPPO/no-graph | 3907 | 3907 | 3907 |
| HAPPO | 3907 | 3907 | 3907 |

All eight runs successfully completed the full 3907-update target and passed the
training-output audit. A log summary was written to:

```text
results/dev1m_seed1_seed2_3907update_summary.csv
```

Next action: run validation checkpoint selection for seeds 1/2, then held-out
test evaluation. Do not use the final online 5-episode monitor as the paper
result; seed 0 already showed that validation-selected mid-training checkpoints
can be much stronger than the last online monitor.

## Seeds 1/2 Validation Sweep Progress

EA-RG-MAPPO validation selection for seeds 1/2 is complete. Each seed has 50
saved checkpoint snapshots and was evaluated with 50 matched validation
episodes per checkpoint under the unchanged strict-sensing relay-failure
protocol. Current status:

| Method | Seed | Completed validation checkpoints | Total checkpoints | Current best success/recovery |
|---|---:|---:|---:|---:|
| EA-RG-MAPPO | 1 | 50 | 50 | 0.34 |
| EA-RG-MAPPO | 2 | 50 | 50 | 0.48 |

Seed 1 validation selection is complete. The selected checkpoint is update 2200
with `0.34` success/recovery, `9.41176` mean recovery steps, and zero collision.
Seed 2 validation selection is complete. The selected checkpoint is update 3800
with `0.48` success/recovery, `25.25` mean recovery steps, and zero collision.

The multi-seed EA-RG-MAPPO validation result is substantially weaker than seed 0
(`0.94` validation success/recovery). This is a stability warning, not yet a
paper conclusion. The next required step is to run the same seeds 1/2 validation
selection for Single-Graph MAPPO, MAPPO/no-graph, and HAPPO before judging
relative method quality or deciding whether the training protocol needs another
controlled adjustment.

Single-Graph MAPPO validation selection for seeds 1/2 is complete under the
same protocol. Current status:

| Method | Seed | Completed validation checkpoints | Total checkpoints | Current best success/recovery |
|---|---:|---:|---:|---:|
| Single-Graph MAPPO | 1 | 50 | 50 | 0.24 |
| Single-Graph MAPPO | 2 | 50 | 50 | 0.44 |

Seed 1 is complete and currently selects update 40 with `0.04` success/recovery,
`78.5` mean recovery steps, and zero collision under the existing selection
score. Its highest observed validation success/recovery is `0.24`, so the
selection-score behavior should be reviewed after all methods are swept. Seed 2
is complete and selects update 40 with `0.44` success/recovery, `23.4545` mean
recovery steps, and zero collision.

MAPPO/no-graph validation selection for seeds 1/2 has started under the same
protocol. Current status:

| Method | Seed | Completed validation checkpoints | Total checkpoints | Current best success/recovery | Best zero-collision success/recovery |
|---|---:|---:|---:|---:|---:|
| MAPPO/no-graph | 1 | 50 | 50 | 0.98 | 0.98 |
| MAPPO/no-graph | 2 | 0 | 50 | n/a | n/a |

MAPPO seed 1 is complete and selects update 2400 with `0.98` success/recovery,
`20.1224` mean recovery steps, and zero collision. Earlier nonzero
success/recovery checkpoints with nonzero collision were correctly excluded by
the zero-collision checkpoint-selection rule, but the final seed-1 result is a
major warning: the no-graph baseline can solve this validation split in at least
one seed. Before making method claims, complete MAPPO seed 2 and then audit
whether the no-graph actor path has any unintended information advantage or
whether the current strict-sensing task is too easy for some initialized runs.

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
