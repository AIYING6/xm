# True No-Role-Identity Ablation Audit

Last updated: 2026-07-19

## Issue

The earlier `graph_input_ablation=no_role_identity` path zeroed the explicit role tensor before role embedding and role-pair message gating, but the 3DOF actor still received explicit role one-hot fields inside:

- local actor observation columns `22:26`;
- graph node feature columns `11:16`.

That made the ablation weaker than its name implied.

## Change

For `graph_input_ablation=no_role_identity`, the RI actor now removes:

- explicit local-observation role indicators;
- explicit graph-node role indicators;
- role embeddings and role-pair gate role inputs.

It still preserves true heterogeneous platform capability fields such as speed, radar range, communication range, attack range, and energy. This is intentional: the ablation removes role labels, not the physical heterogeneity of the aircraft.

## Validation

Passed:

```bash
D:/Anaconda/envs/.conda/envs/cac/python.exe -m py_compile algorithms/ri_gmappo/simple_ri_gmappo.py tests/test_gate1_communication_feasibility.py
D:/Anaconda/envs/.conda/envs/cac/python.exe -m pytest tests/test_gate1_communication_feasibility.py -q
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/train_ri_gmappo.py --env-name 3d_intercept --graph-encoder multi_relation --graph-input-ablation no_role_identity --num-envs 1 --rollout-steps 8 --updates 1 --hidden-dim 16 --role-dim 4 --intent-dim 4 --eval-interval 1 --eval-episodes 1 --device cpu --out-dir results/critic_role_no_role_smoke
```

Result:

```text
16 passed
1-update 3DOF PPO smoke completed
```

## Next Decision

Old `no_role_identity` experiment results should be considered pre-hardening evidence. A small fixed-protocol rerun is required before this ablation can be used in the paper.
