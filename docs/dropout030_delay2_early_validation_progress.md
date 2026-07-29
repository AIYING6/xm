# Dropout030 Delay2 Early Relay-Failure Validation Progress

Last updated: 2026-07-28

## Purpose

The `dropout030_delay2_relay_failure` scenario did not separate
EA-RG-MAPPO from Single-Graph MAPPO. The next candidate stress scenario is:

```text
dropout030_delay2_relay_failure_early
```

This tests the same strict-sensing, dropout, delay, and relay-failure setting,
but moves the relay failure earlier so policies have less time to establish a
stable information chain.

## Current Progress

Regular MAPPO-family checkpoint sweep:

```text
results/paper_config_runs/dev_1m/checkpoint_sweeps/dropout030_delay2_relay_failure_early_seed0_2_validation/
```

Current coverage:

| Method | Seed | Completed Checkpoints |
| --- | ---: | ---: |
| MAPPO/no-graph | 0 | 47 |
| MAPPO/no-graph | 1 | 50 |
| MAPPO/no-graph | 2 | 50 |
| Single-Graph MAPPO | 0 | 47 |
| Single-Graph MAPPO | 1 | 50 |
| Single-Graph MAPPO | 2 | 50 |
| EA-RG-MAPPO | 0 | 48 |
| EA-RG-MAPPO | 1 | 50 |

EA-RG-MAPPO seed0 and seed1 are now covered, but seed2 is still missing.
Therefore the current result is still not valid for final method comparison.

Current partial selected checkpoints for MAPPO/no-graph:

| Seed | Selected Update | Success/Recovery | Collision |
| ---: | ---: | ---: | ---: |
| 0 | 3400 | 0.62 | 0.00 |
| 1 | 3060 | 0.48 | 0.00 |
| 2 | 3907 | 0.00 | 0.00 |

Current selected checkpoint for Single-Graph MAPPO:

| Seed | Selected Update | Success/Recovery | Collision |
| ---: | ---: | ---: | ---: |
| 0 | 1800 | 0.60 | 0.00 |
| 1 | 200 | 0.32 | 0.00 |
| 2 | 2560 | 0.66 | 0.00 |

Aggregate validation-selected results so far:

| Method | Mean Success/Recovery | Min | Max | Collision Mean |
| --- | ---: | ---: | ---: | ---: |
| MAPPO/no-graph | 0.3667 | 0.00 | 0.62 | 0.00 |
| Single-Graph MAPPO | 0.5267 | 0.32 | 0.66 | 0.00 |
| EA-RG-MAPPO | 0.5000 | 0.28 | 0.72 | 0.00 |

Interpretation: early relay failure has not eliminated the no-graph baseline.
At least two MAPPO/no-graph seeds still find non-trivial zero-collision
solutions. The completed no-graph mean success/recovery is `0.3667`.
Single-Graph MAPPO is stronger than no-graph in the completed baseline set,
with mean success/recovery `0.5267` and no zero-success seed. EA-RG-MAPPO seed0
is weaker (`0.28`) than both no-graph seed0 (`0.62`) and Single-Graph seed0
(`0.60`), but EA seed1 is strong (`0.72`) and exceeds Single-Graph seed1
(`0.32`). The early-failure scenario remains uncertain and depends heavily on
EA seed2.

Do not promote this scenario to held-out testing until EA-RG-MAPPO seed2 is
evaluated.

## Final Validation Decision

EA-RG-MAPPO seed2 has now been evaluated and the regular MAPPO-family validation
sweep is complete. See:

```text
docs/dropout030_delay2_early_validation_summary.md
```

Final validation aggregate:

| Method | Mean Success/Recovery |
| --- | ---: |
| MAPPO/no-graph | 0.3667 |
| Single-Graph MAPPO | 0.5267 |
| EA-RG-MAPPO | 0.4733 |

Decision: do not promote this scenario to held-out testing as the final main
scenario because EA-RG-MAPPO does not beat Single-Graph MAPPO.

HAPPO early-scenario sweep is also partial:

```text
results/paper_config_runs/dev_1m/checkpoint_sweeps/dropout030_delay2_relay_failure_early_happo_seed0_2_validation/
```

Current coverage:

| Method | Seed | Completed Checkpoints |
| --- | ---: | ---: |
| HAPPO | 0 | 40 |
| HAPPO | 1 | 19 |

## Resume Command

Run this command repeatedly until it reports no new evaluations and writes a
complete `validation_selected_checkpoints.csv`.

```powershell
cd C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav

& "D:\Anaconda\envs\.conda\envs\cac\python.exe" scripts/evaluate_3d_checkpoint_sweep.py --split validation --seeds 0 1 2 --graph-encoders no_graph single multi_relation --scenarios dropout030_delay2_relay_failure_early --episodes 50 --eval-batch-size 8 --base-seed 140000 --target-policy straight --strict-target-sensing --agent-target-info-bottleneck --target-prior-position 10000.0 0.0 5000.0 --graph-relation-ablation none --graph-message-ablation none --graph-input-ablation none --max-target-message-age-steps 80 --min-target-confidence 0.2 --no-graph-root results/paper_config_runs/dev_1m/runs/mappo --single-root results/paper_config_runs/dev_1m/runs/single_graph --multi-root results/paper_config_runs/dev_1m/runs/ea_rg_mappo --checkpoint-glob actor_critic_update_*.pt --device cpu --out-dir results/paper_config_runs/dev_1m/checkpoint_sweeps/dropout030_delay2_relay_failure_early_seed0_2_validation --max-selection-collision-rate 0.0 --resume
```

HAPPO resume command:

```powershell
cd C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav

& "D:\Anaconda\envs\.conda\envs\cac\python.exe" scripts/evaluate_happo_checkpoint_sweep.py --split validation --seeds 0 1 2 --scenarios dropout030_delay2_relay_failure_early --episodes 50 --eval-batch-size 8 --base-seed 140000 --target-policy straight --strict-target-sensing --agent-target-info-bottleneck --target-prior-position 10000.0 0.0 5000.0 --max-target-message-age-steps 80 --min-target-confidence 0.2 --happo-root results/paper_config_runs/dev_1m/runs/happo_standard --checkpoint-glob happo_update_*.pt --device cpu --out-dir results/paper_config_runs/dev_1m/checkpoint_sweeps/dropout030_delay2_relay_failure_early_happo_seed0_2_validation --max-selection-collision-rate 0.0 --resume
```

## Decision Rule

Only after both sweeps complete:

1. compare validation-selected checkpoints across MAPPO/no-graph,
   Single-Graph MAPPO, EA-RG-MAPPO, and HAPPO;
2. require zero-collision selected checkpoints;
3. check whether EA-RG-MAPPO improves both mean recovery and worst-seed
   recovery relative to Single-Graph and no-graph baselines;
4. if EA is not clearly stronger, do not keep modifying the scenario. Move to
   training-budget and PPO-stability analysis instead.
