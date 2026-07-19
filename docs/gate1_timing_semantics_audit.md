# Gate 1 Timing Semantics Audit

Last updated: 2026-07-18

## Convention

The 3DOF environment now treats `info["step"]` as a post-step timestamp:

- reset state is step `0`;
- the first call to `env.step()` returns the state after step `1`;
- node-failure activation is evaluated at the returned post-step timestamp;
- delayed message delivery is evaluated at the returned post-step timestamp;
- per-step metrics in `info` describe the same returned post-step state.

This makes failure windows and message delays auditable from saved episode CSVs.

## Implemented

- `UAVIntercept3DEnv.step()` increments `step_count` before movement, sensing, communication, failure gating, and metric logging.
- A message queued at reset with `message_delay_steps=2` is delivered on returned step `2`, not step `3`.
- A failure window with `node_failure_start_step=1` and `node_failure_duration_steps=2` is active on returned steps `1` and `2`, then inactive on step `3`.
- `post_failure_recovery_metrics()` now preserves the legacy `post_failure_chain_recovered` field while also reporting:
  - `post_failure_chain_maintained`;
  - `post_failure_chain_recovered_after_loss`;
  - `post_failure_chain_unrecovered`;
  - `post_failure_first_chain_step`.

## Tests

Added Gate 1 regression coverage for:

- post-step `info["step"]` and node-failure boundary semantics;
- delayed message delivery under post-step timing;
- maintained/recovered-after-loss/unrecovered metric split.

Verification run:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe -m py_compile envs/uav_intercept_3d_env.py scripts/evaluate_ri_gmappo_3d.py tests/test_gate1_communication_feasibility.py
D:/Anaconda/envs/.conda/envs/cac/python.exe -m unittest tests.test_gate1_communication_feasibility
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/smoke_test_intercept_3d_env.py
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/evaluate_ri_gmappo_3d.py --allow-random-policy --episodes 1 ...
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/evaluate_3d_geometric_node_failure.py --seeds 0 --episodes 1 ...
```

Observed result:

```text
py_compile: pass
Gate 1 unit tests: 13 tests OK
3DOF environment smoke: 15 episodes OK
evaluator CSV smoke: pass
geometric CSV smoke: pass
```

## Remaining Gate 1 P0 Item

Actor observations are now local, but graph node/edge inputs still contain a shared estimated target state. The next P0 pass should replace actor-side graph target shortcuts with packet/ego-consistent graph information while keeping centralized critic access separate.

