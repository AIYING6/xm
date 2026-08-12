# Phase 2IA5 E0 executor audit

## Purpose

This audit covers the standalone checkpoint-only executor for protocol
`PHASE2IA5-ETF-V1`. It is a code and deterministic-rule audit only. It does
not start E0 evaluation, inspect canonical data, or train a policy.

## Required checks

- Only `full_gate` and `no_role_gate` are accepted.
- Only development seeds `101/202/303` are accepted.
- Development IDs follow `510000 + 10000 * seed + episode_index`, paired
  across arms but unique in combination with arm.
- Eligibility is exactly four consecutive `chain_closed` observations.
- The trigger must occur by step 220. At step 220 the eligibility window
  closes; a later chain hold does not activate a fault.
- When eligible, agent 1 fails at trigger step + 1 for exactly 80 steps.
- Existing fixed final checkpoints are loaded; no checkpoint selection,
  promotion, resume, or training path exists.
- Raw episode and timestep trace outputs refuse to overwrite existing E0 data.
- The executor requires explicit `--execute`; without it it fails closed.

## Decision

The static audit script `scripts/audit_phase2ia5_e0_executor.py` and unit
script `scripts/test_phase2ia5_e0_executor.py` must both pass before an E0
launch record is created. Passing this audit alone does not authorize E0
execution or new training.
