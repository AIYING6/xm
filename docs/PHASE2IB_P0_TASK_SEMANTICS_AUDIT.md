# Phase 2IB P0 Task-Semantics Audit

**Protocol:** `PHASE2IB-RDT-V1`  
**Status:** PASS for P0 only  
**Training status:** no training started  
**Canonical data/checkpoints:** not used

## What was implemented

The opt-in `relay_dependent_task=True` configuration adds a bounded task
semantics layer to `UAVIntercept3DEnv`.  It requires
`strict_target_sensing=True` and `agent_target_info_bottleneck=True`; all
legacy configurations continue with `relay_dependent_task=False`.

In the new mode:

1. An attacker/interceptor cannot obtain direct radar target detection.
2. Its target cache is usable only when fresh and its recorded path contains
   the frozen relay ID 1.
3. A bypass cache such as `[0, 2]` is rejected rather than replacing a valid
   relay-routed cache.
4. While relay 1 is inside the configured failure window, an otherwise fresh
   attacker cache requiring that relay is not actionable.  It remains stored
   solely for path provenance and becomes usable again only after the relay
   failure window ends.
5. `relay_dependency_eligible_t` exposes the pre-result diagnostic state:
   attack geometry, scout detection, and relay-required attacker information.

No rewards, flight dynamics, terminal conditions, success definition,
historical recovery endpoint, or canonical evaluation protocol were changed.

## Executed checks

| Check | Result | Evidence |
| --- | --- | --- |
| Configuration guard | PASS | Relay-dependent mode without strict sensing and per-agent bottleneck raises `ValueError`. |
| Role sensing policy | PASS | Identical valid geometry yields `False` for attacker direct radar and `True` for scout radar. |
| Cache provenance policy | PASS | `[0,2]` is rejected; `[0,1,2]` is accepted and usable. |
| Fault semantics | PASS | A valid `[0,1,2]` attacker cache is usable before the fault, unavailable during the relay-1 fault window, and usable after it. |
| Legacy 3D environment smoke | PASS | `scripts/smoke_test_intercept_3d_env.py` completed 15 episodes. |

The exact semantic-audit payload was:

```json
{
  "attacker_cache_path": [0, 1, 2],
  "attacker_information_before_failure": true,
  "attacker_information_during_relay_failure": false,
  "attacker_information_after_relay_failure": true,
  "pass": true,
  "training_started": false,
  "canonical_data_used": false
}
```

## Interpretation and remaining gate

P0 establishes that the new task has a causal information-path mechanism that
the prior task lacked.  It does **not** establish that the required state is
reachable under fixed transparent controllers, that a post-fault loss occurs
in ordinary rollouts, or that EA-RG-MAPPO has an advantage.  The next permitted
action is a separately frozen P1 transparent-controller feasibility protocol
with timestep traces and no learned policies.  Phase 3A remains **NO-GO**.
