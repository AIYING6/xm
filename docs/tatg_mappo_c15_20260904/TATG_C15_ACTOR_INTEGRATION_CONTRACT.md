# TATG-MAPPO C1.5 — actor-integration contract

## Scope

C1.5 is an actor-boundary and runtime-state audit only. `TATGMemoryActor` composes a copied, unchanged `RIActor` with either CETM or the parameter-matched generic current-snapshot GRU control. `simple_ri_gmappo.py`, the centralized critic, environment, rewards, sampler and PPO runner remain untouched.

The wrapper retains the copied snapshot policy head solely to expose its frozen policy-input boundary during this audit; its temporal head supplies the candidate logits. It is therefore not yet a production training actor. Any future runner integration must remove the inactive duplicate path while preserving the exact zero-memory initialization tested here.

## Candidate interface

The existing snapshot actor produces its ordinary final policy-input vector. CETM produces the frozen local transition memory. The candidate action logits are then:

```text
logits_i,t = TemporalHead(concat(snapshot_policy_input_i,t, m_i,t))
```

The temporal head copies every pre-existing policy-head parameter and initializes only the new memory columns to zero. Therefore, at reset, when `m=0`, the wrapper must return bit-identical logits to the copied legacy snapshot actor.

The generic control has the same copied actor, the same temporal head dimensions and the same added actor parameter count. It differs solely in using the current legal topology state at every step instead of a transition residual.

## Decision boundary

Pass requires exact reset equivalence, a synthetic legal-transition wiring check, capacity equality, exact wrapper state continuation and no edit to legacy actor/critic source.

Pass authorizes only a separately frozen rollout/PPO-interface preflight. It does not authorize environment rollouts, PPO updates, training, evaluation, checkpoint selection or cloud execution.
