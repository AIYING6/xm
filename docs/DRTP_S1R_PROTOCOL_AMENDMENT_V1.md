# DRTP S1-R Protocol Amendment v1

## Status

This document amends the concept-level S1-R protocol after the execution audit
reported `F_PROTOCOL_UNDERSPECIFIED`. The original v1 protocol and its audit are
preserved as historical records and are not rewritten.

This amendment performs protocol closure only. It does not run an evaluator,
load a checkpoint, create an environment, generate a tape, or start training.

## Closure decisions

- G and B are selected by machine-readable rules from the archived REL-A0
  `cell_summary`; no seed is manually forced.
- Selected G: seed `2001`.
- Selected B: seed `2002`.
- All five REL-A0 tapes are imported by hash; no new evaluation tape is made.
- TP50 is a deterministic audit subset: the first 10 episode IDs from each
  imported tape, 50 IDs total.
- All scientific budgets, milestone steps, RNG stream derivations, formulas,
  thresholds, schemas, stop conditions, and failure labels are frozen in
  `DRTP_S1R_PROTOCOL_V2_FROZEN.md` and the JSON contract.

## Historical boundary

`DRTP_S1R_PROTOCOL_EXECUTION_AUDIT.md` remains `F_PROTOCOL_UNDERSPECIFIED`.
That historical conclusion is not upgraded by this amendment. The v2 contract
is prospective and is the only contract that could authorize a later S1-R
technical smoke or scientific run.

## Required machine artifacts

- `artifacts/drtp_s1r_protocol_v2/frozen_contract.json`
- `artifacts/drtp_s1r_protocol_v2/gb_selection.json`
- `artifacts/drtp_s1r_protocol_v2/rng_tuples.json`
- `artifacts/drtp_s1r_protocol_v2/eval_manifest.json`
- `artifacts/drtp_s1r_protocol_v2/tp50_manifest.json`

## Current stop state

`TRAINING STARTED = NO`  
`EVALUATION STARTED = NO`  
`CHECKPOINTS CREATED = NO`  
`TELEMETRY SMOKE STARTED = NO`

The next action requires separate authorization after this amendment and its
static validation report are committed.
