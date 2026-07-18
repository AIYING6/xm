# Post-Gate-1 Five-Seed Launch Plan

Last updated: 2026-07-18

## Objective

Prepare the first paper-facing five-seed formal experiment for the communication-feasible 3DOF bottleneck dropout-relay protocol.

Core claim to test:

> Under strict intermittent sensing, packet loss, delayed communication, and relay-node communication failure, the multi-relation role graph improves kill-chain recovery over a single union graph and no graph.

## Current Evidence Gate

Completed development diagnostics:

| Diagnostic | Methods | Seeds | Main result |
|---|---|---:|---|
| 20-update post-Gate-1 | `single`, `multi_relation` | 3 | recovery `33.3%` vs `93.3%` |
| 60-update post-Gate-1 | `single`, `multi_relation` | 3 | recovery `43.3%` vs `93.3%` |
| 60-update safety-selected | `no_graph`, `single`, `multi_relation` | 3 | recovery `31.7%`, `38.3%`, `98.3%` |

The development gate is passed for planning formal expansion. It is not final paper evidence because it uses only three independent training seeds and small validation/test episode counts.

## Formal Method Set

Use three methods in the first five-seed formal run:

- `no_graph`;
- `single`;
- `multi_relation`.

Do not add GAT, 5v2, JSBSim, missile, or self-play until this run is complete.

Reason:

- `multi_relation` vs `single` answers whether multi-relation role/task communication is better than a single union graph.
- `multi_relation` vs `no_graph` answers whether message-passing structure is necessary.
- Adding more baselines before this gate will increase runtime without fixing the current evidence bottleneck.

## Seeds

Formal seeds:

```text
0 1 2 3 4
```

Current source availability:

| Method | Seed 0 | Seed 1 | Seed 2 | Seed 3 | Seed 4 |
|---|---|---|---|---|---|
| `no_graph` | available | available | available | missing | missing |
| `single` | available | available | available | missing | missing |
| `multi_relation` | available | available | available | missing | missing |

Seeds `3` and `4` are the blocker before five-seed formal launch.

## Source-Checkpoint Policy

Use a single predefined policy. Do not selectively repair only weak seeds.

Recommended policy:

1. Keep current seeds `0, 1, 2` as development-proven sources for the first formal attempt.
2. Generate seeds `3, 4` with the same source-generation path and budget.
3. If seed `3` or `4` collapses during source generation, do not replace only that seed after seeing formal test results. Either:
   - retain the collapsed seed and report variance; or
   - restart source generation for all five seeds under a new predefined budget.

This is less perfect than retraining all sources from scratch, but it is practical. The key is that any deviation must be decided before formal final-test evaluation.

## Training Protocol

Post-Gate-1 continuation:

```text
updates = 60
save_interval = 10
num_envs = 1 or 2
rollout_steps = 32
lr = 5e-5
entropy_coef = 0.001
target_policy = straight
strict_target_sensing = true
agent_target_info_bottleneck = true
communication_dropout_random = [0.00, 0.30]
message_delay_random = [0, 2]
node_failure_random_prob = 1.0
node_failure_start = 40
node_failure_duration = 80
```

Formal checkpoint selection:

```text
validation episodes = 50 per method/seed/checkpoint
test episodes = 100 per selected method/seed checkpoint
validation base seed = 750000
test base seed = 760000
max_selection_collision_rate = 0.0
```

Checkpoint selection score:

```text
eligible if validation collision_mean <= 0.0
score = 1000 * recovery + 100 * success - recovered_only_recovery_steps
```

If all validation checkpoints for one method/seed violate the collision threshold, the run should fail instead of silently selecting an unsafe checkpoint.

## Canonical Command Shape

After seed `3` and `4` sources exist, launch with:

```powershell
$PY = "D:/Anaconda/envs/.conda/envs/cac/python.exe"

& $PY scripts/run_3d_strict_sensing_formal_protocol.py `
  --seeds 0 1 2 3 4 `
  --graph-encoders no_graph single multi_relation `
  --updates 60 `
  --num-envs 1 `
  --rollout-steps 32 `
  --save-interval 10 `
  --target-policy straight `
  --strict-target-sensing `
  --agent-target-info-bottleneck `
  --communication-dropout-random-min 0.00 `
  --communication-dropout-random-max 0.30 `
  --message-delay-random-min 0 `
  --message-delay-random-max 2 `
  --node-failure-random-prob 1.0 `
  --node-failure-start-random-min 40 `
  --node-failure-start-random-max 40 `
  --node-failure-duration-random-min 80 `
  --node-failure-duration-random-max 80 `
  --scenarios dropout030_relay_failure `
  --validation-episodes 50 `
  --test-episodes 100 `
  --validation-base-seed 750000 `
  --test-base-seed 760000 `
  --max-selection-collision-rate 0.0 `
  --source-checkpoint-kind actor_critic_latest.pt `
  --out-dir results/intercept_3d_gate1_dropout030_bottleneck_5seed_formal
```

## Required Outputs

The formal run must produce:

- validation checkpoint summary;
- validation selected checkpoints;
- final test episode metrics;
- final test checkpoint summary;
- seed-aware statistics:
  - `multi_relation` vs `single`;
  - `multi_relation` vs `no_graph`;
- seed-level appendix table;
- collision and constraint-violation audit;
- one representative recovery timeline case.

## Decision Rules

Proceed toward manuscript main results if:

- `multi_relation - single` recovery delta remains positive for at least four of five seeds;
- hierarchical bootstrap lower bound for recovery delta remains above zero;
- `multi_relation` collision rate is not higher than baselines after validation safety selection;
- no method has hidden flight-envelope violations;
- final test was not used for checkpoint or hyperparameter decisions.

If the five-seed result weakens:

- do not tune on the test split;
- inspect validation curves and seed-level failures;
- decide whether to open a new development protocol for reward/safety tuning or source retraining;
- keep the current three-seed evidence as development evidence only.

## Immediate Next Step

Generate or locate seed `3` and `4` source checkpoints for:

- `no_graph`;
- `single`;
- `multi_relation`.

Until these source checkpoints exist, the five-seed formal run cannot start.

