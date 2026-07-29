# Post-Loss Reclosure Training Development Summary

Last updated: 2026-07-29

## Purpose

The previous stability runs showed that fixed step-40 relay-failure training can produce broad recovery, but strict delayed/late recovery remains zero. This note records the first successful development route for post-loss recovery.

## Code Changes

New optional environment/training controls were added with backward-compatible defaults:

- `min_success_step`: prevents an episode from terminating as success before a specified step.
- `post_loss_chain_reclosure_reward_weight`: adds a one-time reward when the kill chain is re-closed after it has been lost during node failure.
- `post_loss_chain_reclosure_min_step`: delays that one-time reward until a minimum absolute step.

These controls are exposed through:

- `envs/uav_intercept_3d_env.py`
- `algorithms/ri_gmappo/simple_ri_gmappo.py`
- `scripts/train_ri_gmappo.py`
- `scripts/evaluate_ri_gmappo_3d.py`
- `scripts/evaluate_3d_checkpoint_sweep.py`

`scripts/pretrain_ri_gmappo_3d_bc.py` now also supports relay-failure parameters and `min_success_step`, so behavior-cloning data can include post-failure recovery trajectories instead of ending before the failure event.

Validation:

- Python compile passed for all modified files.
- One-update recovery-training smoke passed.
- Recovery-BC smoke passed.

## Reachability Check

A temporary geometric-controller reachability check used:

- Strict sensing and target-information bottleneck enabled.
- Communication dropout `0.30`.
- Message delay `2`.
- Relay node failure.
- `min_success_step=80`.
- Four frozen scenarios: early, standard, delayed, late.

Geometric policy mode comparison:

| Mode | Early recovery | Standard recovery | Delayed recovery | Late recovery | Collision tendency |
|---|---:|---:|---:|---:|---:|
| direct | 1.00 | 1.00 | 0.75 | 0.75 | high, about 0.25 |
| lead | 1.00 | 1.00 | 0.35 | 0.35 | high, about 0.50 |
| offset | 1.00 | 1.00 | 0.90 | 0.90 | lower, about 0.10 |

Decision: use `offset` geometric demonstrations for recovery-oriented BC.

## Failed or Weak Routes

1. Random failure start alone:
   - Failure start sampled in `[25,100]`.
   - Suite success/recovery/delayed-recovery/collision: `0.400/0.200/0.000/0.000`.
   - Not sufficient.

2. Direct recovery BC:
   - BC-only produced weak delayed signal under one split but was not robust.
   - PPO improved early/standard recovery but delayed/late stayed zero.

3. Delayed-focused direct BC:
   - Failure start sampled in `[55,70]`.
   - Did not solve delayed/late recovery and introduced minor collision.

4. Offset BC without balanced loss:
   - Demonstration quality was high, but deterministic BC policy collapsed to zero recovery.
   - Indicates action-distribution imbalance matters.

## Successful Seed-0 Route

Behavior cloning:

- Output: `results/paper_config_runs/stability_dev/recovery_bc_offset_balanced_seed0/ea_rg_mappo`
- Episodes: `60`
- Epochs: `10`
- Graph encoder: `multi_relation`
- Geometric policy mode: `offset`
- Balanced loss: enabled
- Attacker action weight: `2.0`
- Failure start sampled in `[25,70]`
- `min_success_step=80`
- Demonstration success rate: `0.90`
- Final action accuracy: about `0.436`

BC-only evaluation on 20 episodes per scenario:

| Scenario | Success | Recovery | After-loss recovery | Collision |
|---|---:|---:|---:|---:|
| early | 0.55 | 0.55 | 0.55 | 0.00 |
| standard | 0.50 | 0.65 | 0.65 | 0.00 |
| delayed | 0.40 | 0.40 | 0.35 | 0.00 |
| late | 0.35 | 0.35 | 0.35 | 0.05 |

PPO fine-tuning:

- Output: `results/paper_config_runs/stability_dev/ea_rg_mappo_seed0_offset_balanced_recovery_bc_ppo_h64`
- Updates: `60`
- Checkpoints swept: `20,40,50,60`
- Validation episodes: `10` per scenario/checkpoint
- Selection: suite-level delayed recovery, `selection_success_weight=0`
- Evaluation uses `min_success_step=80`

Best checkpoint:

- Selected update: `40`
- Suite success/recovery/after-loss/delayed/collision:
  - `0.625/0.675/0.675/0.450/0.000`

Selected-checkpoint scenario metrics:

| Scenario | Success | Recovery | After-loss recovery | Delayed recovery | Collision |
|---|---:|---:|---:|---:|---:|
| early | 0.50 | 0.50 | 0.50 | 0.10 | 0.00 |
| standard | 0.60 | 0.80 | 0.80 | 0.30 | 0.00 |
| delayed | 0.70 | 0.70 | 0.70 | 0.70 | 0.00 |
| late | 0.70 | 0.70 | 0.70 | 0.70 | 0.00 |

## Interpretation

This is the first development result that directly supports the paper's recovery claim:

- The environment can express delayed/late post-loss recovery.
- The old BC source was not aligned with the recovery task.
- Balanced offset demonstrations plus conservative PPO create a nonzero and practically meaningful delayed-recovery signal.
- The best PPO checkpoint is not the latest checkpoint; checkpoint selection remains necessary.

This is still seed-0 development evidence only. It should not be used as final paper evidence until matched baselines and additional seeds are trained under the same recovery-oriented protocol.

## Next Steps

1. Expand the successful route to seeds `1` and `2` for EA-RG-MAPPO-S.
2. Repeat the exact same BC and PPO protocol for Single-Graph MAPPO.
3. If Single-Graph is competitive, add MAPPO/no-graph and HAPPO under the same protocol.
4. Freeze the recovery-oriented validation/test protocol before any formal multi-seed test.
5. Use the selected update around `40` as the first budget reference, then compare with longer budgets only if validation shows continued improvement.
