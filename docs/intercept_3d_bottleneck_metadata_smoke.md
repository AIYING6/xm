# Bottleneck Protocol Metadata Smoke

Last updated: 2026-07-17

## Purpose

Verify that the bottleneck dropout-relay protocol is now machine-readable in new evaluation outputs, not only described by directory names and Markdown notes.

This is a schema smoke test, not an experiment result.

## Checks

Single-checkpoint evaluation:

```text
scripts/evaluate_ri_gmappo_3d.py
checkpoint = results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0060.pt
episodes = 1
scenario = dropout030_relay_failure equivalent settings
strict_target_sensing = True
agent_target_info_bottleneck = True
out_csv = results/intercept_3d_bottleneck_metadata_smoke.csv
```

Checkpoint-sweep evaluation:

```text
scripts/evaluate_3d_checkpoint_sweep.py
split = validation
seeds = [0]
graph_encoders = [multi_relation]
scenarios = [dropout030_relay_failure]
episodes = 1
checkpoint_glob = actor_critic_update_0060.pt
strict_target_sensing = True
agent_target_info_bottleneck = True
out_dir = results/intercept_3d_bottleneck_checkpoint_sweep_metadata_smoke
```

## Verified Output Columns

New episode-level CSVs include:

- `strict_target_sensing`
- `agent_target_info_bottleneck`

New checkpoint-sweep summary and selected-checkpoint CSVs include:

- `strict_target_sensing`
- `agent_target_info_bottleneck`

## Decision

The schema path is ready for the five-seed expansion. Existing older result CSVs may not contain these fields; do not silently mix old and new CSV schemas in a final paper table without either regenerating the affected rows or documenting the older protocol provenance.
