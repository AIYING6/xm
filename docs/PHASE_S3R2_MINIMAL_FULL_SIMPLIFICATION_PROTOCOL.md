# Phase S3-R2 Minimal Full Simplification Protocol

**Protocol ID:** `PHASE-S3-R2-V1`  
**Status:** FROZEN BEFORE TRAINING  
**Artifact class:** DEVELOPMENT_ONLY

## Purpose

S3-R1 established that the three unexposed episodes were genuine
pre-failure collisions, not evaluator errors. S3-R2 tests one narrowly
defined architecture hypothesis: whether the relation-conditioned Role-Gate
is responsible for the unstable nominal competence of the existing Full arm.

This is a one-component ablation. It is not a new architecture search and it
does not reopen S2.

## Frozen intervention

The only architecture change is:

```text
graph_encoder = multi_relation
role_gate_mode = none
```

The following remain unchanged from S2 and the original S3 contract:

- Perception, Communication, and Task-Support relation channels;
- union/global residual branch and its weight;
- MAPPO optimizer, learning rate, PPO settings, rollout length, environment
  count, reward, observation legality, geometry, target, and failure timing;
- hidden dimension 64, role dimension 8, intent dimension 8;
- no resume, no initialization checkpoint, no early stopping, no checkpoint
  promotion, and fixed final checkpoint only.

## Training contract

- one arm: `simple_full_no_role_gate`;
- development seeds: `1501`, `1502`, `1503`;
- 782 updates × 4 environments × 64 rollout steps = **200,192 environment
  steps per seed**;
- no canonical seeds, canonical test, or headline result;
- all three runs must be completed; no seed exclusion.

The training configuration retains the frozen S2 terminal field
`min_success_step=1000`. The known zero-success diagnostic is not silently
changed during training. Evaluation additionally reports the separate
development-only `success_at_horizon` field at step 260, as defined by S3-R.

## Evaluation contract

Each fixed final checkpoint is evaluated on the same 100 nominal/failure pairs
with episode IDs `340000–340099`, already used by S3-R. The nominal/failure
pair differs only by Relay-1 failure at step 44 for 80 steps. Existing MAPPO,
Matched Single-Graph, and Full results are not overwritten.

The primary diagnostic remains:

```text
Delta_J = J_nominal - J_failure
```

`J_nominal` must always be inspected together with `Delta_J`; a lower score
drop caused by low nominal competence is not a robustness advantage.

## Pre-registered screening rule

S3-R2 is a development screen, not a superiority test. The simplified Full
passes the architecture screening target only if all conditions hold:

1. all three runs complete with finite final PPO diagnostics and matching
   final-checkpoint manifests;
2. shared-tape, nominal/failure pairing, deterministic replay, and exposure
   provenance pass; natural pre-failure collisions remain included;
3. its seed-level mean nominal score is not more than 10% below the frozen
   Matched Single-Graph mean, using the comparator's absolute mean as the
   denominator;
4. `Delta_J` is lower than Matched Single-Graph in at least two of the three
   seeds and in the across-seed mean;
5. the apparent lower `Delta_J` is not accompanied by a negative nominal score
   in a seed where Matched Single-Graph has positive nominal score.

Failure of condition 3 means the multi-relation encoder remains suspect and
requires an encoder-level diagnosis. Failure of condition 4 means no
robustness signal is established. No condition authorizes canonical training.

## Decision boundary

```text
PASS -> candidate for a separately reviewed S4 architecture freeze
NO-GO -> multi-relation encoder diagnosis; no further blind training
INCONCLUSIVE -> integrity or deterministic replay failure
```

Role-Gate is not restored or expanded by this protocol. Phase 3A remains
`NO-GO` unless separately authorized after review.
