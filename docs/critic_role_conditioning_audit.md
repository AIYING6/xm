# Critic Role-Conditioning Audit

Last updated: 2026-07-19

## Issue

The external project-content review correctly identified a potential consistency problem: the 3DOF environment uses heterogeneous roles and role-specific reward components, while the centralized critic previously consumed only `share_obs`.

If two blue agents share the same centralized state but have different task roles, a role-agnostic critic can fit an ambiguous value target.

## Change

`RIGMAPPOAgent` now appends a one-hot encoding of each blue agent's role to the centralized critic input:

```text
critic_input[i] = concat(share_obs[i], one_hot(role[i]))
```

The actor input path is unchanged. The role-conditioned critic is used only for CTDE value estimation during training and bootstrap value computation.

Old checkpoints remain partially loadable because the existing matching loader expands compatible two-dimensional tensors and initializes the new critic input columns to zero.

## Validation

Passed:

```bash
D:/Anaconda/envs/.conda/envs/cac/python.exe -m py_compile algorithms/ri_gmappo/simple_ri_gmappo.py tests/test_gate1_communication_feasibility.py
D:/Anaconda/envs/.conda/envs/cac/python.exe -m pytest tests/test_gate1_communication_feasibility.py -q
```

Result:

```text
15 passed
```

## Boundary

This change fixes a value-function conditioning issue. It is not a new claimed paper contribution and must not be described as an execution-time information channel.

The next hardening task is to make `no_role_identity` a true role-removal ablation by ensuring role labels are removed consistently from actor graph inputs, node features, and role-pair message paths.
