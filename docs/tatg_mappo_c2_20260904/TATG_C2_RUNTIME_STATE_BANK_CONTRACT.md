# TATG-MAPPO C2 — vectorized runtime-state-bank contract

## Scope

C2 implements and audits only a runner-neutral `TATGRuntimeStateBank`. It does not edit or execute `collect_rollout`, PPO, the environment, evaluation or checkpoint writer.

## Required lifecycle

The bank stores exactly one `(m, x_previous, a_previous)` state per vectorized rollout environment. After an actor call, the runner would record the sampled own action. When `np.all(dones)` is true for one environment slot, only that slot must reset from its newly reset legal graph. Other vectorized slots must retain their state exactly.

Its runtime payload is exactly:

```text
{"tatg_memory_state": {"memory", "previous_topology", "previous_action"}}
```

No evaluation information, group label, failure schedule, return or centralized critic state is included.

## Decision boundary

Pass requires isolated-slot behavior, exact completed-slot reset, exact serialization continuation, and confirmation that the legacy runner exposes explicit done/reset and runtime-checkpoint lifecycle points.

Pass authorizes only a separately frozen runner-integration preflight. It does not authorize environment steps, PPO, training, cloud execution, evaluation or a performance claim.
