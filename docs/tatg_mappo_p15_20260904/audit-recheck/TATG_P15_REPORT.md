# TATG-MAPPO P1.5 formula, fairness and serialization audit

**Verdict:** `TATG_P15_FORMULA_FROZEN_FOR_C1_IMPLEMENTATION_AUDIT`.

CETM is frozen as an event-gated update of a local topology-transition residual. Its current-graph encoder and critic remain the existing snapshot components. The generic GNN+GRU control uses the same added GRUCell and head dimensions, but consumes a current topology vector rather than a transition residual and updates at every step.

The audit is algebraic only. It does not instantiate a neural policy, read a checkpoint, step an environment, fit a probe, calculate return or run PPO.

## Checks

- `candidate_is_transition_residual_not_snapshot_gru`: `True`
- `local_topology_input_is_receiver_row_only`: `True`
- `existing_edge_age_proxy_retained`: `True`
- `no_hidden_failure_or_critic_input`: `True`
- `zero_residual_memory_invariance`: `True`
- `nonzero_residual_can_update_memory`: `True`
- `generic_gru_control_is_capacity_matched`: `True`
- `transition_information_ablation_frozen`: `True`
- `critic_and_ppo_are_unchanged`: `True`
- `runtime_state_serialization_is_explicit`: `True`
- `no_legacy_stabilization_module`: `True`

A pass authorizes only a separate C1 implementation and exact-serialization audit. It does not authorize any training or performance claim.
