# Phase 2IA9 failure-dependency path-audit protocol

**Protocol ID:** `PHASE2IA9-FDP-V1`  
**Status:** instrumentation/audit only; no environment intervention, P1 rerun,
checkpoint evaluation, or training is authorized.

## Question

Phase2IA8 P1 established that relay-1 failure did not cause an observed loss
of `chain_support_t`. The next question is not whether to make the fault
stronger; it is whether relay-1 was ever necessary for the attacker's target
information at the frozen pre-failure support trigger.

## Frozen audit fields

At every timestep, emit these read-only fields for the existing attacker role:

- `attacker_direct_target_information_t`: any attacker directly detects target;
- `attacker_fresh_cache_information_t`: any attacker has fresh cached target
  information but no direct detection;
- `attacker_cache_source_ids_t`: deterministic semicolon-separated source IDs
  for fresh attacker caches;
- `attacker_cache_paths_t`: deterministic semicolon-separated source-to-
  receiver cache paths for fresh attacker caches;
- `attacker_cache_path_includes_relay1_t`: whether any fresh attacker cache
  path includes relay agent 1;
- `attacker_support_path_relay1_required_t`: true only when support holds,
  attackers have no direct target information, and every fresh attacker cache
  path includes relay 1.

These are explanatory telemetry. They do not change the support predicate,
cache rules, communication, sensing, failure, reward, success, or termination.

## Audit sequence

1. P0-style invariant test proves each field equals existing state/cache
   arrays and does not change a deterministic rollout.
2. Static audit proves no existing transition or decision condition references
   any new field.
3. Only after those gates pass, a separate launch record may authorize a
   **trace-only replay** of the already frozen transparent P1 controllers on
   new development seeds. The replay must reproduce the original P1 failure
   schedule exactly and must not be used to select another failure design.

## Interpretive constraint

This audit may classify relay dependence as absent, direct-sensing bypass,
alternate-cache-path bypass, relay-dependent, or indeterminate. It may not
itself change a failure target, suppress direct sensing, alter initial geometry,
or authorize learned-policy work. Any later relay-dependent task must be
justified in a separately reviewed scientific design amendment.
