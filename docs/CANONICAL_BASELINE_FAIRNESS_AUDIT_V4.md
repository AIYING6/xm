# Canonical baseline fairness audit v4

The final architecture identities/config paths are:

1. `configs/canonical_v2/final_ea_rg_mappo_s.json`;
2. `configs/canonical_v2/mappo.json`;
3. `configs/canonical_v2/parameter_matched_single_graph.json`;
4. `configs/canonical_v2/final_ea_rg_mappo_s_no_union_residual.json`.

All methods will share the frozen environment, rewards, failure schedule, observation legality contract, seed set, training budget, rollout length, environment count, PPO settings, BC policy, curriculum difficulty exposure, validation-only selection, evaluation N, and evaluation tapes. Necessary differences are only graph encoder, capacity-controlled Single-Graph width, relation-conditioned gate in Full/no-union, and union residual multiplier.

**Status: architecture-bound PASS; end-to-end fairness remains contingent on the Phase 2H tape, config-manifest, and curriculum provenance blockers.**
