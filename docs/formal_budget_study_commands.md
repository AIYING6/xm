# Formal Budget Study Commands

Last updated: 2026-07-29

## Purpose

This document gives the command protocol for the common-budget study. It follows
`docs/formal_protocol_freeze.md` and should not introduce new tuning choices.

## Budget Mapping

With `num_envs=8` and `rollout_steps=128`, each update uses:

```text
8 * 128 = 1024 environment transitions
```

Budget candidates:

```text
1M  ~=  977 updates
2M  ~= 1954 updates
```

Budget-study seeds:

```text
0 1 2
```

Formal five-seed training after choosing `B*`:

```text
0 1 2 3 4
```

Validation base seed:

```text
391000
```

Final held-out test base seed:

```text
491000
```

## Output Root

After the 2026-07-29 shared actor-graph target-mask audit, clean formal-budget runs should
write to:

```text
results/paper_config_runs/formal_budget_post_graph_mask/
```

The older `results/paper_config_runs/formal_budget/` and
`results/paper_config_runs/formal_budget_post_audit/` directories are preserved
as development/continuity evidence only because their checkpoints were produced
before the final graph-mask protocol.

## Common BC Settings

For MAPPO/no-graph, Single-Graph MAPPO, Parameter-Matched Single-Graph MAPPO,
and EA-RG-MAPPO-S:

```powershell
& "D:/Anaconda/envs/.conda/envs/cac/python.exe" scripts/pretrain_ri_gmappo_3d_bc.py `
  --episodes 120 --epochs 20 --batch-size 256 `
  --hidden-dim <HIDDEN_DIM> --role-dim 8 --intent-dim 8 `
  --graph-encoder <GRAPH_ENCODER> `
  --role-gate-prior-strength <ROLE_GATE_PRIOR_STRENGTH> `
  --geometric-policy-mode offset --attacker-action-weight 2.0 `
  --seed <SEED> --target-policy straight `
  --strict-target-sensing --agent-target-info-bottleneck `
  --communication-dropout-prob 0.30 --message-delay-steps 2 `
  --failed-blue-agent 1 `
  --node-failure-start-random-min 25 --node-failure-start-random-max 70 `
  --node-failure-duration-steps 80 --attack-hold-steps 4 --min-success-step 80 `
  --device cpu `
  --out-dir results/paper_config_runs/formal_budget_post_graph_mask/<METHOD>/bc_seed<SEED>
```

For HAPPO:

```powershell
& "D:/Anaconda/envs/.conda/envs/cac/python.exe" scripts/pretrain_happo_3d_bc.py `
  --episodes 120 --epochs 20 --batch-size 256 `
  --hidden-dim 64 --role-dim 8 --intent-dim 8 `
  --geometric-policy-mode offset --attacker-action-weight 2.0 `
  --seed <SEED> --target-policy straight `
  --strict-target-sensing --agent-target-info-bottleneck `
  --communication-dropout-prob 0.30 --message-delay-steps 2 `
  --failed-blue-agent 1 `
  --node-failure-start-random-min 25 --node-failure-start-random-max 70 `
  --node-failure-duration-steps 80 --attack-hold-steps 4 --min-success-step 80 `
  --device cpu `
  --out-dir results/paper_config_runs/formal_budget_post_graph_mask/happo/bc_seed<SEED>
```

## Common PPO Settings

For MAPPO/no-graph, Single-Graph MAPPO, Parameter-Matched Single-Graph MAPPO,
and EA-RG-MAPPO-S:

```powershell
& "D:/Anaconda/envs/.conda/envs/cac/python.exe" scripts/train_ri_gmappo.py `
  --env-name 3d_intercept `
  --seed <SEED> --num-envs 8 --rollout-steps 128 --updates <UPDATES> `
  --hidden-dim <HIDDEN_DIM> --role-dim 8 --intent-dim 8 `
  --graph-encoder <GRAPH_ENCODER> `
  --role-gate-prior-strength <ROLE_GATE_PRIOR_STRENGTH> `
  --init-checkpoint results/paper_config_runs/formal_budget_post_graph_mask/<METHOD>/bc_seed<SEED>/actor_critic_latest.pt `
  --actor-lr 5e-5 --critic-lr 1e-4 `
  --clip-coef 0.1 --ppo-epochs 2 --target-kl 0.01 `
  --entropy-coef 0.003 --max-grad-norm 0.5 --critic-warmup-updates 20 `
  --eval-interval 100 --eval-episodes 5 --eval-base-seed 391000 `
  --save-interval 100 --save-snapshots `
  --target-policy straight `
  --strict-target-sensing --agent-target-info-bottleneck `
  --communication-dropout-prob 0.30 --message-delay-steps 2 `
  --failed-blue-agent 1 `
  --node-failure-start-random-min 25 --node-failure-start-random-max 70 `
  --node-failure-duration-steps 80 --attack-hold-steps 4 --min-success-step 80 `
  --post-loss-chain-reclosure-reward-weight 0.5 `
  --post-loss-chain-reclosure-min-step 80 `
  --safety-proximity-distance 2500 `
  --safety-proximity-penalty-weight 0.5 `
  --device cpu `
  --out-dir results/paper_config_runs/formal_budget_post_graph_mask/<METHOD>/ppo_seed<SEED>_<BUDGET>
```

For HAPPO:

```powershell
& "D:/Anaconda/envs/.conda/envs/cac/python.exe" scripts/train_happo_baseline.py `
  --seed <SEED> --num-envs 8 --rollout-steps 128 --updates <UPDATES> `
  --hidden-dim 64 --role-dim 8 --intent-dim 8 `
  --init-checkpoint results/paper_config_runs/formal_budget_post_graph_mask/happo/bc_seed<SEED>/happo_bc_latest.pt `
  --lr 5e-5 --clip-coef 0.1 --ppo-epochs 2 `
  --entropy-coef 0.003 --max-grad-norm 0.5 `
  --eval-interval 100 --eval-episodes 5 --eval-base-seed 391000 `
  --save-interval 100 --save-snapshots `
  --target-policy straight `
  --strict-target-sensing --agent-target-info-bottleneck `
  --communication-dropout-prob 0.30 --message-delay-steps 2 `
  --failed-blue-agent 1 `
  --node-failure-start-random-min 25 --node-failure-start-random-max 70 `
  --node-failure-duration-steps 80 --attack-hold-steps 4 --min-success-step 80 `
  --post-loss-chain-reclosure-reward-weight 0.5 `
  --post-loss-chain-reclosure-min-step 80 `
  --safety-proximity-distance 2500 `
  --safety-proximity-penalty-weight 0.5 `
  --device cpu `
  --out-dir results/paper_config_runs/formal_budget_post_graph_mask/happo/ppo_seed<SEED>_<BUDGET>
```

## Method Substitutions

| Method | `<METHOD>` | `<GRAPH_ENCODER>` | `<ROLE_GATE_PRIOR_STRENGTH>` | `<HIDDEN_DIM>` |
|---|---|---|---:|---:|
| MAPPO/no-graph | `no_graph` | `no_graph` | 0.0 | 64 |
| Single-Graph MAPPO | `single_graph` | `single` | 0.0 | 64 |
| Parameter-Matched Single-Graph MAPPO | `param_matched_single` | `single` | 0.0 | 96 |
| EA-RG-MAPPO-S | `ea_rg_mappo_s_gate_prior` | `multi_relation` | 0.4 | 64 |
| HAPPO | `happo` | not used | not used | 64 |

## Checkpoint Sweep

`--selection-metric fresh_info_recovery` means generation-based, after-loss,
continuous-window FreshRec. It does not count a pre-failure target observation
that is merely delivered after relay failure. Tie-break order is higher
FreshRec, lower collision, shorter fresh recovery time, higher success, and
earlier checkpoint update.

For MAPPO-style methods:

```powershell
& "D:/Anaconda/envs/.conda/envs/cac/python.exe" scripts/evaluate_3d_checkpoint_sweep.py `
  --split validation `
  --seeds 0 1 2 `
  --graph-encoders <GRAPH_ENCODER> `
  --scenarios dropout030_delay2_relay_failure_early dropout030_delay2_relay_failure dropout030_delay2_relay_failure_delayed dropout030_delay2_relay_failure_late `
  --episodes 50 --eval-batch-size 5 --base-seed 391000 `
  --target-policy straight `
  --strict-target-sensing --agent-target-info-bottleneck `
  --min-success-step 80 --attack-hold-steps 4 `
  --run-dir-template "ppo_seed{seed}_<BUDGET>" `
  --checkpoint-updates <CHECKPOINT_UPDATES> `
  --<ROOT_ARG> results/paper_config_runs/formal_budget_post_graph_mask/<METHOD> `
  --out-dir results/paper_config_runs/formal_budget_post_graph_mask/checkpoint_sweeps/<METHOD>_<BUDGET> `
  --selection-group suite `
  --selection-metric fresh_info_recovery `
  --selection-success-weight 0 `
  --delayed-recovery-min-step 80 `
  --device cpu --resume
```

Use:

- `--no-graph-root` for MAPPO/no-graph.
- `--single-root` for Single-Graph MAPPO.
- `--multi-root` for EA-RG-MAPPO-S.

For HAPPO:

```powershell
& "D:/Anaconda/envs/.conda/envs/cac/python.exe" scripts/evaluate_happo_checkpoint_sweep.py `
  --split validation `
  --seeds 0 1 2 `
  --scenarios dropout030_delay2_relay_failure_early dropout030_delay2_relay_failure dropout030_delay2_relay_failure_delayed dropout030_delay2_relay_failure_late `
  --episodes 50 --eval-batch-size 5 --base-seed 391000 `
  --target-policy straight `
  --strict-target-sensing --agent-target-info-bottleneck `
  --min-success-step 80 --attack-hold-steps 4 `
  --run-dir-template "ppo_seed{seed}_<BUDGET>" `
  --checkpoint-updates <CHECKPOINT_UPDATES> `
  --happo-root results/paper_config_runs/formal_budget_post_graph_mask/happo `
  --out-dir results/paper_config_runs/formal_budget_post_graph_mask/checkpoint_sweeps/happo_<BUDGET> `
  --selection-group suite `
  --selection-metric fresh_info_recovery `
  --selection-success-weight 0 `
  --delayed-recovery-min-step 80 `
  --device cpu --resume
```

Recommended checkpoint update candidates:

- 1M: `200 400 600 800 977`
- 2M: `400 800 1200 1600 1954`

## Budget Decision

After 1M validation:

- If all methods plateau and validation ranking is stable, choose `B*=1M`.
- If most methods are still improving or seed failures remain high, run 2M.

After 2M validation:

- Choose one common `B*`.
- Do not choose different budgets per method.
- Do not use the final held-out test to choose `B*`.
