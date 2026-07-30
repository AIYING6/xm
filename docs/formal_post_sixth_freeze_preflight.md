# Formal Post-Sixth-Freeze Preflight

Last updated: 2026-07-30

## Purpose

This is a smoke/preflight record for the post-sixth-review formal protocol. It
verifies that the hardened zero-mask actor information boundary, hidden
local-attack edge removal, FreshRec metric changes, BC initialization, and PPO
training entry points are executable before launching the real 1M budget study.

These outputs are not paper evidence and must not be used for final validation
or held-out testing.

## Protocol

Common settings:

- strict target sensing enabled;
- agent target-information bottleneck enabled;
- communication dropout probability `0.30`;
- message delay `2`;
- failed blue agent `1`;
- randomized failure start `[25, 70]`;
- failure duration `80`;
- attack hold steps `4`;
- minimum success step `80`;
- safety proximity distance `2500`;
- safety proximity penalty weight `0.5`;
- validation monitor base seed `391000`.

Preflight outputs:

```text
results/paper_config_runs/formal_budget_post_sixth_freeze_preflight/
```

## Result

All five formal method families completed a minimal BC plus one-update PPO
preflight.

| Method | BC | PPO | Notes |
|---|---:|---:|---|
| MAPPO/no-graph | pass | pass | RI-GMAPPO training entry, `graph_encoder=no_graph`, hidden dim 64 |
| Single-Graph MAPPO | pass | pass | RI-GMAPPO training entry, `graph_encoder=single`, hidden dim 64 |
| Parameter-Matched Single-Graph MAPPO | pass | pass | RI-GMAPPO training entry, `graph_encoder=single`, hidden dim 96 |
| EA-RG-MAPPO-S | pass | pass | RI-GMAPPO training entry, `graph_encoder=multi_relation`, role-gate prior 0.4 |
| HAPPO | pass | pass | HAPPO BC and HAPPO PPO entry |

Additional checks completed in the same freeze pass:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe -m pytest tests/test_gate1_communication_feasibility.py -q
33 passed

D:/Anaconda/envs/.conda/envs/cac/python.exe -m py_compile envs/uav_intercept_3d_env.py scripts/evaluate_ri_gmappo_3d.py scripts/evaluate_3d_checkpoint_sweep.py scripts/evaluate_happo_checkpoint_sweep.py tests/test_gate1_communication_feasibility.py
passed

D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/smoke_test_intercept_3d_env.py
passed, 15 episodes
```

## Decision

The formal experiment entry points are ready for the 1M budget study from a clean
post-sixth-freeze root:

```text
results/paper_config_runs/formal_budget_post_sixth_freeze/
```

Because the zero-mask actor input and FreshRec definitions changed after earlier
training, all formal budget evidence must be regenerated under this root.

Next task:

1. Run BC for seeds `0 1 2` and all five methods under
   `formal_budget_post_sixth_freeze`.
2. Run 1M PPO budget, `977` updates, for the same methods and seeds.
3. Evaluate checkpoint snapshots on the four-scenario validation suite using
   `selection_metric=fresh_info_recovery`, `selection_group=suite`, and
   `selection_success_weight=0`.
4. Decide whether 2M is necessary before expanding to five formal seeds.
