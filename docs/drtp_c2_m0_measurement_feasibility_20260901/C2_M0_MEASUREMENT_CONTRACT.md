# C2-M0 measurement feasibility contract

**Protocol:** `C2-M0-MEASUREMENT-FEASIBILITY-V1`
**Status:** `C2_M0_FEASIBLE`
**Scope:** source-only, zero training and zero evaluation.

## Purpose

Determine whether a future *diagnostic-only* fresh-seed experiment could collect the measurement layers absent from C2-D1 without evaluation leakage or training control. M0 does not create a new algorithm, alter C2, select checkpoints, or authorize a follow-up run.

## Frozen proposed measurement interface

- Training remains ordinary UTR and the already-frozen group-weighted candidate; telemetry is write-only.
- `group_credit_telemetry=True` only every `32` updates: `61` observation updates across `1953` updates.
- Emit `427` per-group rows and `1281` actor/critic conflict-pair rows per trajectory.
- `failure_aware_telemetry=True` records already chosen actions, role-labelled path/support state and outcome windows; it does not request a second actor forward pass.
- Runtime checkpoints are fixed at `125k (update 488), 250k (update 976), 375k (update 1464), 500k (update 1953)`. Any later milestone evaluation would require a separate explicit authorization and must never select a checkpoint.
- Formal, independent and held-out evaluation tapes are excluded from training and telemetry.

## Required future preflight before any diagnostic training

1. Demonstrate telemetry-on versus telemetry-off trajectory equivalence through a fixed short technical replay or prove it via the existing default-off/write-only invariant.
2. Measure wall-clock and disk overhead. M0 has **not** measured either; no claim of a numeric cost bound is made here.
3. Verify save/resume retains telemetry writer state and milestone runtime state.
4. Freeze the future analysis rule before observing fresh final outcomes. No threshold sweep, classifier, or online control is permitted.

## Actionability boundary

Only a repeated, temporally leading signal may later motivate **one** matching minimal intervention. Gradient conflict could motivate an actor-only conflict projection; persistent group contribution domination could motivate bounded contribution normalization. Neither is designed, implemented, or authorized by M0. Role-level divergence alone is localization evidence, not an intervention prescription.

## Result

`C2_M0_FEASIBLE` means the interface is structurally capable of collecting the missing evidence. It is not evidence that a mechanism exists or that the group-weighted method should continue.
