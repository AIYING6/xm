# Gate 1 Communication-Feasibility Audit

Last updated: 2026-07-18

## Purpose

Gate 1 is the Q1-readiness gate for information realism. It checks that the 3DOF actor path does not rely on target information that would be unavailable during decentralized execution.

## Completed in This Pass

Code changes:

- Graph convention is now enforced in the 3DOF task-support path as `A[receiver, sender] = 1`.
- Task-support relation edges now require delivered physical communication; they no longer act as an independent information channel.
- The union graph uses active task-support edges rather than potential role-support edges.
- `_has_target_information()` now follows receiver-sender communication direction.
- `_comm_has_chain_to_attacker()` now checks whether the attacker can receive from a sensing source under receiver-sender reachability.
- 3DOF actor construction disables global intent-context broadcasting. This prevents the target-node summary from being broadcast to every blue agent during decentralized execution.
- `message_delay_steps` now uses a real pending-message queue. A physical communication opportunity schedules a future delivery; the receiver-side communication edge is only written after the delay has elapsed.
- Each 3DOF blue agent now has a target-message cache with validity, position, velocity, source, generation step, delivery step, hop count, confidence, and propagation path.
- Target-message delivery updates the receiver cache only when the delayed message arrives.
- Newly received target messages are not forwarded again in the same communication update, so multi-hop propagation advances one hop per delay cycle.
- Task-chain closure now depends on an executor actually having target information, not just on transitive communication reachability.

Tests added:

- `tests/test_gate1_communication_feasibility.py`
  - graph attention direction;
  - task-support no-bypass;
  - disconnected attacker action logits unchanged when hidden target state changes.
  - delayed communication is unavailable before the configured future delivery step.
  - packet dropout prevents delayed-message queue insertion and delivery.
  - communication-subsystem failure drops queued delivery involving the failed node.
  - target-message cache propagation across a scout-relay-attacker chain advances one hop per delay cycle and records path/hop count.

Updated smoke:

- `scripts/smoke_test_intercept_3d_env.py` now uses the receiver-sender task-support convention.

## Verification

Passed:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe -m py_compile envs/uav_intercept_3d_env.py algorithms/ri_gmappo/simple_ri_gmappo.py scripts/evaluate_ri_gmappo_3d.py scripts/pretrain_ri_gmappo_3d_bc.py scripts/smoke_test_intercept_3d_env.py tests/test_gate1_communication_feasibility.py
D:/Anaconda/envs/.conda/envs/cac/python.exe -m unittest tests.test_gate1_communication_feasibility
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/smoke_test_intercept_3d_env.py
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/train_ri_gmappo.py --env-name 3d_intercept --updates 1 --num-envs 1 --rollout-steps 4 --eval-episodes 1 --eval-interval 1 --save-interval 1 --hidden-dim 16 --intent-coef 0.0 --target-policy straight --strict-target-sensing --agent-target-info-bottleneck --out-dir results/ri_gmappo_3d_gate1_smoke
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/train_ri_gmappo.py --env-name 3d_intercept --updates 1 --num-envs 1 --rollout-steps 4 --eval-episodes 1 --eval-interval 1 --save-interval 1 --hidden-dim 16 --intent-coef 0.0 --target-policy straight --strict-target-sensing --agent-target-info-bottleneck --message-delay-steps 2 --out-dir results/ri_gmappo_3d_gate1_delay_smoke
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/train_ri_gmappo.py --env-name 3d_intercept --updates 1 --num-envs 1 --rollout-steps 4 --eval-episodes 1 --eval-interval 1 --save-interval 1 --hidden-dim 16 --intent-coef 0.0 --target-policy straight --strict-target-sensing --agent-target-info-bottleneck --message-delay-steps 2 --out-dir results/ri_gmappo_3d_gate1_multihop_smoke
```

Short post-change compatibility diagnostic:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/evaluate_ri_gmappo_3d.py --checkpoint results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0060.pt --graph-encoder multi_relation --episodes 5 --base-seed 880001 --target-policy straight --strict-target-sensing --agent-target-info-bottleneck --communication-dropout-prob 0.30 --failed-blue-agent 1 --node-failure-start-step 40 --node-failure-duration-steps 80 --device cpu --out-csv results/intercept_3d_gate1_post_change_eval_smoke.csv --summary-md docs/intercept_3d_gate1_post_change_eval_smoke.md
```

Result:

- episodes: `5`;
- success: `100%`;
- post-failure recovery: `100%`;
- average steps: `46.0`.

This is only a compatibility smoke result. It must not be used as paper evidence.

Short three-method post-change diagnostic:

```text
results/intercept_3d_gate1_post_change_three_method_smoke/test_checkpoint_summary.csv
```

Setting:

- split: `test`;
- training seed: `0`;
- checkpoint update: `60`;
- episodes per method: `5`;
- scenario: `dropout030_relay_failure`;
- strict target sensing and agent target-information bottleneck enabled.

Result:

| Method | Success | Recovery | Timeout |
|---|---:|---:|---:|
| `no_graph` | `0%` | `0%` | `100%` |
| `single` | `60%` | `60%` | `40%` |
| `multi_relation` | `100%` | `100%` | `0%` |

Interpretation:

- the post-Gate-1 semantics are executable for all three methods;
- the expected development ordering remains visible in this tiny seed-0 smoke;
- this is not a statistically meaningful result and must not be used as paper evidence.

Three-seed post-change diagnostic:

```text
results/intercept_3d_gate1_post_change_3seed_diag/
docs/intercept_3d_gate1_post_change_3seed_diag_summary.md
```

Aggregate recovery:

- `no_graph`: `30.0%`;
- `single`: `26.7%`;
- `multi_relation`: `86.7%`.

Seed-aware `multi_relation - single` recovery delta is `+60.0 pp`, 95% CI `[+20.0, +93.3] pp`. This supports continuing the communication-feasible route, but it is still a checkpoint-reuse diagnostic.

Short retraining smoke:

```text
results/intercept_3d_gate1_post_change_retrain_smoke/
docs/intercept_3d_gate1_post_change_retrain_smoke_summary.md
```

After 3 continuation PPO updates from existing seed-0 checkpoints:

- `single`: `90.0%` recovery over 10 episodes;
- `multi_relation`: `100.0%` recovery over 10 episodes.

This confirms that post-Gate-1 training remains executable. It is not paper evidence.

Three-seed retraining diagnostic:

```text
results/intercept_3d_gate1_post_change_retrain_3seed_diag/
docs/intercept_3d_gate1_post_change_retrain_3seed_diag_summary.md
```

After 3 continuation PPO updates from existing checkpoints:

- `single`: `35.0%` recovery over 60 matched episodes;
- `multi_relation`: `95.0%` recovery over 60 matched episodes;
- seed-aware recovery delta: `+60.0 pp`, 95% CI `[+16.7, +90.0] pp`.

This is still a small development diagnostic, but it confirms that the new communication-feasible semantics remain trainable.

20-update retraining diagnostic with validation checkpoint selection:

```text
results/intercept_3d_gate1_post_change_retrain_20update_diag/
docs/intercept_3d_gate1_post_change_retrain_20update_diag_summary.md
```

Setting:

- methods: `single`, `multi_relation`;
- training seeds: `0, 1, 2`;
- continuation budget: `20` PPO updates;
- checkpoint snapshots: updates `5, 10, 15, 20`;
- validation episodes: `10` matched episodes per candidate checkpoint;
- test episodes: `20` matched episodes per selected seed/method checkpoint;
- scenario: `dropout030_relay_failure`;
- strict target sensing and agent target-information bottleneck enabled.

Validation-selected test result:

| Method | Recovery | Timeout | Tracking during failure | Connectivity during failure |
|---|---:|---:|---:|---:|
| `single` | `33.3%` | `65.0%` | `43.7%` | `18.3%` |
| `multi_relation` | `93.3%` | `6.7%` | `94.4%` | `30.8%` |

Seed-aware hierarchical bootstrap gives `multi_relation - single` recovery delta `+60.0 pp`, 95% CI `[+16.7, +91.7] pp`, and restricted mean recovery-step delta `-125.13`, 95% CI `[-189.58, -35.85]`.

This remains development evidence because it uses only three independent training seeds and a short continuation budget. It is strong enough to justify a longer post-Gate-1 diagnostic.

60-update retraining diagnostic with validation checkpoint selection:

```text
results/intercept_3d_gate1_post_change_retrain_60update_diag/
docs/intercept_3d_gate1_post_change_retrain_60update_diag_summary.md
```

Validation-selected test result:

| Method | Recovery | Timeout | Tracking during failure | Connectivity during failure |
|---|---:|---:|---:|---:|
| `single` | `43.3%` | `56.7%` | `51.4%` | `20.6%` |
| `multi_relation` | `93.3%` | `5.0%` | `95.3%` | `32.2%` |

Seed-aware hierarchical bootstrap gives `multi_relation - single` recovery delta `+50.0 pp`, 95% CI `[+15.0, +80.0] pp`, and restricted mean recovery-step delta `-110.57`, 95% CI `[-171.70, -42.23]`.

Risk note: one selected `multi_relation` seed had `5.0%` collision on the 20-episode test split, so the final protocol needs a validation-time collision rejection or penalty rule.

## Remaining Gate 1 Work

The following items are not complete yet:

- define a validation-time collision rejection or penalty rule before any five-seed formal run;
- decide how `no_graph` is included under the post-Gate-1 communication-feasible semantics;
- prepare five-seed formal expansion only after the baseline set and checkpoint-selection rule are frozen.

Boundary documentation is now maintained in `docs/actor_critic_observation_boundary.md`.

## Paper Impact

This pass improves the Q1 defensibility of the method because it closes two obvious reviewer objections:

- task-support edges can no longer transmit information without physical communication;
- target intent/context is no longer globally broadcast to all 3DOF actors.
- delayed communication is no longer treated as immediate delivery plus an age feature.
- target information now has an auditable sender path and hop count, which supports the paper's mission-chain recovery explanation.

Existing historical 3DOF results remain useful as development evidence, but formal Q1/Q2 results must be regenerated after Gate 1 is fully closed.
