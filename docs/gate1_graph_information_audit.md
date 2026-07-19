# Gate 1 Graph-Information Audit

Last updated: 2026-07-18

## Scope

This pass hardens actor-side graph information under `strict_target_sensing + agent_target_info_bottleneck`.

Actor local observations were already localized, but the shared graph target node could still contain a global last-detected target estimate. That is too easy to challenge in review, even if graph adjacency masks prevent many direct paths.

## Implemented

- `_get_graph_obs()` now uses `_target_state_for_graph_observation()`.
- In non-strict settings, graph behavior is unchanged.
- In strict bottleneck settings:
  - if at least one blue UAV directly detects the target at the current post-step, the graph target node uses the current target state;
  - if no blue UAV currently detects the target, the graph target node uses the fixed prior position with zero velocity;
  - stale global `last_detected_target_pos` is not exposed through the graph target node.
- Per-agent target-message information remains available through actor-local observation only when that agent has direct sensing or a fresh target cache.

## Tests

Added Gate 1 regression coverage for:

- changing only hidden global last-detected target state does not change strict-bottleneck graph node or edge features when no agent currently detects the target;
- direct current detection still allows the graph target node to reflect the current target state.

Verification run:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe -m py_compile envs/uav_intercept_3d_env.py tests/test_gate1_communication_feasibility.py
D:/Anaconda/envs/.conda/envs/cac/python.exe -m unittest tests.test_gate1_communication_feasibility
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/smoke_test_intercept_3d_env.py
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/evaluate_ri_gmappo_3d.py --allow-random-policy --episodes 1 --strict-target-sensing --agent-target-info-bottleneck ...
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/train_ri_gmappo.py --env-name 3d_intercept --graph-encoder multi_relation --strict-target-sensing --agent-target-info-bottleneck --updates 1 --num-envs 1 --rollout-steps 8 ...
```

Observed result:

```text
py_compile: pass
Gate 1 unit tests: 14 tests OK
3DOF environment smoke: 15 episodes OK
hardened graph evaluator smoke: pass
hardened one-update PPO train smoke: pass
```

## Remaining Risk

This is a first-pass hardening that removes the most visible stale-global-target graph shortcut. A stricter future implementation could provide per-agent ego graphs, but that would require changing rollout storage and actor interfaces. For the current Q1 route, the next practical step is a three-seed development rerun under the hardened protocol.
