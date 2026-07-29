# Dropout030 Delay2 Relay-Failure Protocol

Last updated: 2026-07-28

## Purpose

This protocol tests whether the multi-relation role graph improves kill-chain
recovery when relay failure is combined with packet loss and message delay.

The scenario is harder than `dropout030_relay_failure` because target
information must survive:

- strict target sensing;
- actor-side target information bottleneck;
- 30% communication dropout;
- 2-step message delay;
- relay UAV failure.

This is a candidate final stress scenario only if EA-RG-MAPPO beats
MAPPO/no-graph and Single-Graph MAPPO after validation-selected checkpoint
selection.

## Scenario Names

- `dropout030_delay2_relay_failure`
- `dropout030_delay2_relay_failure_early`
- `dropout030_delay2_relay_failure_delayed`
- `dropout030_delay2_relay_failure_late`

Start with the normal scenario. Use the early variant only if no-graph remains
too competitive.

## Validation Selection

Run validation selection first. Do not run held-out test until validation
selection finishes for all four methods.

Smoke checks have passed for both sweep scripts:

- regular MAPPO-family sweep: one EA-RG-MAPPO checkpoint, 2 episodes;
- HAPPO sweep: one HAPPO checkpoint, 2 episodes.

```powershell
cd C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav

& "D:\Anaconda\envs\.conda\envs\cac\python.exe" scripts/evaluate_3d_checkpoint_sweep.py --split validation --seeds 0 1 2 --graph-encoders no_graph single multi_relation --scenarios dropout030_delay2_relay_failure --episodes 50 --eval-batch-size 8 --base-seed 140000 --target-policy straight --strict-target-sensing --agent-target-info-bottleneck --target-prior-position 10000.0 0.0 5000.0 --graph-relation-ablation none --graph-message-ablation none --graph-input-ablation none --max-target-message-age-steps 80 --min-target-confidence 0.2 --no-graph-root results/paper_config_runs/dev_1m/runs/mappo --single-root results/paper_config_runs/dev_1m/runs/single_graph --multi-root results/paper_config_runs/dev_1m/runs/ea_rg_mappo --checkpoint-glob actor_critic_update_*.pt --device cpu --out-dir results/paper_config_runs/dev_1m/checkpoint_sweeps/dropout030_delay2_relay_failure_seed0_2_validation --max-selection-collision-rate 0.0 --resume

& "D:\Anaconda\envs\.conda\envs\cac\python.exe" scripts/evaluate_happo_checkpoint_sweep.py --split validation --seeds 0 1 2 --scenarios dropout030_delay2_relay_failure --episodes 50 --eval-batch-size 8 --base-seed 140000 --target-policy straight --strict-target-sensing --agent-target-info-bottleneck --target-prior-position 10000.0 0.0 5000.0 --max-target-message-age-steps 80 --min-target-confidence 0.2 --happo-root results/paper_config_runs/dev_1m/runs/happo_standard --checkpoint-glob happo_update_*.pt --device cpu --out-dir results/paper_config_runs/dev_1m/checkpoint_sweeps/dropout030_delay2_relay_failure_happo_seed0_2_validation --max-selection-collision-rate 0.0 --resume
```

## Decision Rule

Proceed to held-out testing if:

- EA-RG-MAPPO has the highest mean validation success/recovery;
- the EA-vs-no-graph gap is practically meaningful;
- no method has nonzero selected-checkpoint collision rate;
- seed-level results do not depend on a single lucky seed.

If MAPPO/no-graph is still competitive, do not use this scenario as the final
main claim. Repeat validation selection on
`dropout030_delay2_relay_failure_early`.

## Held-Out Test

Only run this after validation selection is frozen.

Use the validation `selected_checkpoints.csv` files as test inputs and keep a
separate test base seed. Do not use test results to retune selection rules.
