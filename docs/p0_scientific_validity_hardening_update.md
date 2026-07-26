# P0 Scientific Validity Hardening Update

Generated: 2026-07-24

## Purpose

Start the mandatory P0 gate from `docs/FINAL_Q1_SINGLE_PAPER_PLAN.md`.

The goal is to prevent the formal Q1/Q2 experiment package from relying on actor-side information that would not be available under decentralized execution.

## Changes Completed

### 1. Explicit 3DOF Role-Identity Schema

Added exported schema constants in `envs/uav_intercept_3d_env.py`:

```text
OBS3D_ROLE_IDENTITY_SLICE = slice(24, 28)
NODE3D_ROLE_IDENTITY_SLICE = slice(11, 16)
```

The previous actor no-role ablation used `slice(22, 26)`. That was incorrect for the 3DOF actor observation layout because it removed communication/attack capability features and only part of the role one-hot block.

`algorithms/ri_gmappo/simple_ri_gmappo.py` now imports the role-identity slices from the environment schema instead of hardcoding them.

### 2. Removed Global Attack-Hold Progress from Actor Graph Inputs

The 3DOF graph edge feature no longer includes normalized `attack_hold / attack_hold_steps`.

`attack_hold` remains valid in:

- centralized critic shared observation;
- environment success logic;
- `info` metrics and evaluation summaries.

It is no longer part of actor graph edge features.

This changes the 3DOF edge feature dimension:

```text
EDGE3D_FEAT_DIM: 18 -> 17
```

### 3. Test Coverage Added/Updated

Updated the no-role-identity test to:

- check the exported observation role slice;
- verify role features are zeroed;
- verify capability fields around the role slice are not accidentally removed.

Added a graph-boundary test:

```text
test_actor_graph_does_not_include_global_attack_hold_progress
```

It verifies that changing global `attack_hold` does not change actor graph node features, edge features, adjacency, or relation adjacency.

### 4. Full Actor Observation Schema

Added `OBS3D_FIELD_NAMES` in `envs/uav_intercept_3d_env.py`.

The test suite now verifies:

- schema length equals `env.obs_dim`;
- role fields are exactly `role_scout`, `role_relay`, `role_attacker`, `role_interceptor`;
- scout, relay, and attacker one-hot values occupy the exported role slice.

### 5. Actor-Logit Information Boundary Tests

Added two stronger actor-forward tests:

- changing global `attack_hold` does not change actor logits;
- changing an unreachable agent's target cache does not change attacker logits.

These tests directly compare policy logits instead of only comparing raw observations or graph tensors.

## Verification

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe -m pytest tests/test_gate1_communication_feasibility.py -q
```

Result:

```text
24 passed
```

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/smoke_test_intercept_3d_env.py
```

Result:

```text
episodes: 15
```

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/train_ri_gmappo.py --env-name 3d_intercept --graph-encoder multi_relation --updates 1 --num-envs 1 --rollout-steps 8 --eval-episodes 1 --eval-interval 1 --save-interval 1 --hidden-dim 32 --intent-coef 0.0 --out-dir results/p0_attack_hold_boundary_train_smoke
```

Result:

```text
training log: results/p0_attack_hold_boundary_train_smoke/train_log.csv
```

## Interpretation

This is a breaking scientific-validity change for old 3DOF actor checkpoints because the graph edge feature dimension changed from 18 to 17.

Therefore:

- old pre-hardening checkpoints remain useful for development comparison only;
- formal Q1/Q2 claims must use checkpoints trained after this P0 hardening;
- old `no_role_identity` results that used the wrong observation slice must not be used as paper-facing evidence.

## Remaining P0 Work

- Add a short paper-facing metric/schema note if needed.
- Freeze the P0 environment/config hash when committing this change.
- Proceed to P1 training-protocol standardization.
