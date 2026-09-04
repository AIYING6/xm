# TATG-MAPPO C1 — implementation and exact serialization contract

## Scope

C1 implements only the frozen Causal Event-Triggered Topology Memory (CETM) in an isolated module. It does not modify `RIActor`, `RIGMAPPOAgent`, the centralized critic, the environment, rewards, UTR exposure, checkpoint-selection rule, or PPO.

## Frozen interface

For each blue actor and rollout environment, CETM accepts only the legal local structural vector frozen in P1.5:

```text
x_i,t = concat(R_comm[t][i, 0:n_blue], R_support[t][i, 0:n_blue], edge_age[t][i, 0:n_blue])
```

The existing relation convention is receiver–sender. No target row, another actor's receiver row, failure identifier or schedule, group label, centralized state, critic input, reward, return or evaluation tape is read.

The retained runtime state is exactly:

```text
(m_i,t, x_i,t-1, a_i,t-1)
```

It resets to zero/neutral action, is exported in a runtime-state dictionary, and must restore bit-exact continuation before policy integration may be considered.

## Matched control and decision

`SnapshotTopologyGRU` has the same GRUCell dimensions and parameter count as CETM. It processes the current topology vector on every step; CETM processes the transition residual and applies the frozen event gate. C1 uses synthetic graph tensors only and does not create an environment.

Pass: `TATG_C1_IMPLEMENTATION_SERIALIZATION_PASS` requires all local-scope, event-invariance, capacity, reset and exact-restoration checks.

Pass authorizes only a future separately frozen actor-integration audit. It does not authorize PPO, a rollout, cloud training, evaluation or a performance claim.
