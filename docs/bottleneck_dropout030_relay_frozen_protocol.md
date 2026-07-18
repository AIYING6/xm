# Bottleneck Dropout-Relay Frozen Protocol

Last updated: 2026-07-17

## Purpose

This document freezes the current strongest 3DOF scenario-depth protocol before any five-seed expansion.

Main claim to test:

> Under strict/intermittent target sensing, 30% communication dropout, and relay-node failure, the multi-relation role graph improves post-failure kill-chain recovery over a single union graph and no graph.

This protocol should not be changed after five-seed training begins. If a new scenario or hyperparameter is needed, create a separate development protocol instead of editing this one.

## Frozen Scenario

Scenario name:

`dropout030_relay_failure`

Required environment switches:

- `target_policy=straight`
- `strict_target_sensing=True`
- `agent_target_info_bottleneck=True`
- `communication_dropout_prob=0.30`
- `failed_blue_agent=1`
- `node_failure_start_step=40`
- `node_failure_duration_steps=80`

Training-domain randomization for the current 60-update protocol:

- `communication_dropout_random_min=0.00`
- `communication_dropout_random_max=0.30`
- keep the existing strict-sensing, communication-range, delay, radar-dropout, and node-failure randomization settings from `scripts/run_3d_strict_sensing_formal_protocol.py` unless a new development protocol is explicitly opened.

## Frozen Methods

Report these as the main comparison set:

- `no_graph`
- `single`
- `multi_relation`

Fairness requirements:

- same training seeds;
- same environment settings;
- same source-checkpoint policy within each method family;
- same PPO budget;
- same validation checkpoint-selection episodes;
- same disjoint final-test episodes;
- same seed-aware statistics.

Do not replace only one weak seed after seeing final-test results. If the source policy is changed, retrain all affected seeds under a predefined rule and record the change in `docs/fair_baseline_source_policy.md`.

## Frozen Development Result

Current three-seed diagnostic:

`results/intercept_3d_strict_sensing_fair_60update_dropout030_bottleneck_formal_diag/`

Test recovery:

- `multi_relation`: `95.0%`
- `single`: `78.3%`
- `no_graph`: `25.0%`

Seed-aware deltas:

- `multi_relation - single`: `+16.7 pp`, 95% CI `[+6.7, +28.3] pp`
- `multi_relation - no_graph`: `+70.0 pp`, 95% CI `[+20.0, +100.0] pp`

This is still a development result because it uses three independent training seeds. It is strong enough to justify a five-seed formal run.

## Five-Seed Expansion

Recommended seeds:

`0 1 2 3 4`

Recommended final-test budget:

- validation: at least `50` matched episodes per training seed;
- final test: at least `100` matched episodes per training seed if runtime is acceptable;
- use disjoint validation and test base seeds.

Recommended fixed base seeds:

- validation base seed: `750000`
- test base seed: `760000`

Checkpoint selection:

- reject validation checkpoints whose collision rate exceeds the predefined threshold;
- for safety-critical formal runs, use `--max-selection-collision-rate 0.0`;
- among eligible checkpoints, select each method/seed checkpoint only on validation recovery and recovery-time score;
- do not inspect or tune on final-test performance;
- final test uses only selected checkpoints.

## Canonical Commands

Use the project Python environment:

```powershell
$PY = "D:/Anaconda/envs/.conda/envs/cac/python.exe"
```

Five-seed training command template:

```powershell
& $PY scripts/run_3d_strict_sensing_formal_protocol.py `
  --seeds 0 1 2 3 4 `
  --graph-encoders no_graph single multi_relation `
  --updates 60 `
  --num-envs 2 `
  --rollout-steps 32 `
  --save-interval 10 `
  --target-policy straight `
  --strict-target-sensing `
  --agent-target-info-bottleneck `
  --communication-dropout-random-min 0.00 `
  --communication-dropout-random-max 0.30 `
  --scenarios dropout030_relay_failure `
  --validation-episodes 50 `
  --test-episodes 100 `
  --validation-base-seed 750000 `
  --test-base-seed 760000 `
  --max-selection-collision-rate 0.0 `
  --out-dir results/intercept_3d_strict_sensing_fair_60update_dropout030_bottleneck_5seed_formal
```

If the command is run in stages, use the same arguments with `--train-only`, `--eval-only`, or `--test-only`.

## Formal Reporting Rules

Main table:

- task success;
- post-failure chain recovery;
- restricted mean recovery steps;
- tracking during failure;
- connectivity during failure;
- timeout;
- collision and flight-envelope violations.
- checkpoint-selection collision threshold and the number of validation checkpoints rejected by it, if any.

Statistics:

- training seed is the primary independent unit;
- use hierarchical bootstrap over training seeds and matched episodes;
- show seed-level points or a seed-level appendix;
- unrecovered episodes use restricted mean recovery time rather than recovered-only time.

Interpretation boundary:

- claim recovery robustness under strict/intermittent sensing and relay failure;
- do not claim full 6DOF air-combat autonomy from this result;
- JSBSim/LAG validation remains a later transfer/verifiability step, not part of this frozen main claim.
