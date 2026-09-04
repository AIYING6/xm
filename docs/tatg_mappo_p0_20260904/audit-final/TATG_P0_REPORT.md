# TATG-MAPPO P0 semantic and novelty audit

**Verdict:** `TATG_P0_FEASIBLE_FOR_P1_INFORMATION_GAP_PROBE`.

P0 only establishes that a new, actor-legal information-sufficiency question is technically testable. It makes no claim that the current actor is insufficient, that memory improves return, or that a recurrent policy should be implemented.

## Distinction from the closed DRTP stabilization programme

This route does not seek a bad-seed precursor, change the training sampler, change group weights, project gradients, blend policies or select a checkpoint. Its unit of analysis is the environment-level information available to a single decentralized actor during a topology transition, not a post-hoc association with seed outcomes.

## Static checks

- `snapshot_graph_actor_exists`: `True`
- `snapshot_actor_has_no_memory_module`: `True`
- `actor_receives_current_legal_graph_tensors`: `True`
- `actor_does_not_receive_failure_schedule`: `True`
- `dynamic_failure_transition_exists`: `True`
- `legal_temporal_proxies_exist`: `True`
- `fixed_exposure_baseline_exists`: `True`
- `runtime_state_persistence_exists`: `True`

## P1 boundary

P1 may use only fresh scripted, policy-neutral trajectories and legal actor tensors. It must compare a current snapshot with a fixed short history against a predeclared transition target, in two disjoint state cohorts. It must not use a learned policy, episode return, final quality label, checkpoint, or any evaluation tape. A P1 pass authorizes only an exact formula audit; a fail closes the entire TATG route before implementation.
