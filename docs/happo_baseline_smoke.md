# HAPPO Baseline Smoke

Generated: 2026-07-24

## Purpose

Start the priority external strong-baseline requirement from `docs/FINAL_Q1_SINGLE_PAPER_PLAN.md`.

This smoke test checks whether a HAPPO-style baseline can be implemented without derailing the existing 3DOF EA-RG-MAPPO training code.

## Implementation

Created:

```text
scripts/train_happo_baseline.py
```

Current scope:

- 3DOF only;
- no-graph external baseline;
- one separate actor/critic module per blue UAV;
- sequential PPO update over agents;
- same environment interface and rollout collector as the existing MAPPO path;
- same strict-sensing, bottleneck, dropout, and relay-failure scenario knobs.

This is intentionally not a graph method. It is meant to be an external heterogeneous MARL baseline, not another ablation of EA-RG-MAPPO.

## Smoke Result

Direct smoke:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/train_happo_baseline.py --updates 1 --num-envs 1 --rollout-steps 8 --eval-episodes 1 --eval-interval 1 --save-interval 1 --save-snapshots --hidden-dim 32 --role-dim 4 --intent-dim 4 --strict-target-sensing --agent-target-info-bottleneck --communication-dropout-prob 0.3 --failed-blue-agent 1 --node-failure-start-step 40 --node-failure-duration-steps 80 --out-dir results/happo_baseline_smoke
```

Result:

```text
training log: results/happo_baseline_smoke/train_log.csv
```

Config-equivalent smoke:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/train_happo_baseline.py --seed 0 --target-policy straight --strict-target-sensing --agent-target-info-bottleneck --communication-dropout-prob 0.3 --message-delay-steps 0 --failed-blue-agent 1 --node-failure-start-step 40 --node-failure-duration-steps 80 --max-target-message-age-steps 80 --min-target-confidence 0.2 --hidden-dim 64 --role-dim 8 --intent-dim 8 --lr 0.00005 --entropy-coef 0.001 --updates 1 --num-envs 1 --rollout-steps 8 --eval-episodes 1 --eval-interval 1 --save-interval 1 --save-snapshots --device cpu --out-dir results/paper_config_runs/smoke/runs/happo/bc_ppo_seed0
```

Result:

```text
training log: results/paper_config_runs/smoke/runs/happo/bc_ppo_seed0/train_log.csv
```

## Command-Manifest Status

`configs/paper/happo.yaml` now records:

```text
implementation_status = smoke_train_passed_pending_formal_evaluator
```

`scripts/generate_paper_commands.py` now emits HAPPO training commands.

HAPPO validation/test sweep rows remain marked:

```text
ready_after_training
```

The HAPPO path uses a parallel evaluator and checkpoint sweep:

```text
scripts/evaluate_happo_3d.py
scripts/evaluate_happo_checkpoint_sweep.py
```

Both validation and test sweep smoke runs passed. The test sweep uses the validation `selected_checkpoints.csv`.

## Interpretation

HAPPO is no longer a pure blocker. The training and checkpoint-sweep smoke path is viable.

It is not yet paper-ready because it still needs development-budget training, validation checkpoint selection, and final matched test evaluation.

## Next Work

1. Include HAPPO in the first `dev_1m` development-budget command review.
2. Run HAPPO development training with the same validation/test split policy.
3. Compare HAPPO against MAPPO, Single-Graph, and EA-RG-MAPPO only after validation-selected test results are available.
