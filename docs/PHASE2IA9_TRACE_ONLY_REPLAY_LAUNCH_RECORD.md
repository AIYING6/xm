# Phase 2IA9 failure-dependency trace-only replay launch record

**Status:** frozen before replay outputs.  
**Protocol:** `PHASE2IA9-FDP-V1`  
**Purpose:** classify the information path at the existing P1 support trigger
and relay-1 failure; not to estimate recovery or compare controllers.

## Frozen replay

- controllers: `structural_oracle`, `legal_observation`;
- new audit-only seeds: `801`, `802`, `803`;
- 100 deterministic episodes per controller × seed (600 total);
- all environment settings, two-step `chain_support_t` trigger, relay 1
  failure target, next-step failure timing, and 80-step duration exactly match
  P1;
- no policy checkpoint, learning, optimizer, training, canonical data, result
  selection, or intervention modification.

Only the Phase2IA9 read-only source/path fields are added to the trace. The
replay must not infer a new fault target or rerun after inspecting path counts.

## Classification output

For each support trigger and active-failure timestep, classify attacker support
as `DIRECT_BYPASS`, `CACHE_BYPASS_NO_RELAY1`, `RELAY1_REQUIRED_CACHE`,
`MIXED_OR_INDETERMINATE`, or `NO_ATTACKER_INFORMATION`. Classification is
descriptive; no class is a pass/fail performance result.

The command is intentionally unavailable until the trace-only executor and
static guard are committed. After execution an independent auditor may close
only the dependency classification, not P1/P2 or training gates.
