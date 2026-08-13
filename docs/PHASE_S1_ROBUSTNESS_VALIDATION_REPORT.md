# Phase S1 Robustness Task Validation Report

**Protocol:** `PHASE-S1-RV-V1`  
**Status:** `S1-INFEASIBLE`  
**Training:** not started  
**Canonical data/checkpoints:** not used

## Executive result

The paired transparent replay found a repeatable mission-score degradation
under Relay failure, but the full S1 gate did not pass because failure exposure
was not complete in every cell. Legal-information availability did not degrade
in the same direction; it slightly increased under the failure condition.
Therefore the new robustness task is not yet ready for S2 freeze or S3 MARL
training.

## Cell results

| Controller | Seed | D_J | D_I | Failure exposure | Dynamic range | Cell |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| structural_oracle | 1401 | 0.0392 | -0.0051 | 0.95 | PASS | PASS by executor cell rule |
| structural_oracle | 1402 | 0.0399 | -0.0077 | 0.95 | PASS | PASS by executor cell rule |
| structural_oracle | 1403 | 0.0395 | -0.0036 | 0.88 | PASS | PASS by executor cell rule |
| legal_observation | 1401 | 0.0915 | -0.0305 | 0.93 | PASS | PASS by executor cell rule |
| legal_observation | 1402 | 0.0906 | -0.0290 | 0.91 | PASS | PASS by executor cell rule |
| legal_observation | 1403 | 0.0955 | -0.0282 | 0.94 | PASS | PASS by executor cell rule |

`D_J` was positive in every cell, with mission-score degradation between
approximately 3.9% and 9.6%. This is a meaningful preliminary task signal.
However, the manifest-level S1 decision required failure exposure above 0.99
in every cell, so the overall status is `S1-INFEASIBLE`.

## Gate decisions

### S1-G1 Nominal feasibility — PASS with limitation

Both transparent controllers completed paired nominal replays with
non-degenerate mission scores and legal-information telemetry. The nominal
condition is usable as a paired baseline, although success was not the primary
metric and most episodes timed out under the transparent protocol.

### S1-G2 Failure exposure — FAIL

Relay failure was active in most, but not all, paired failure episodes. Cell
exposure rates ranged from 0.88 to 0.95, below the pre-execution manifest
threshold of 0.99. This prevents claiming that every paired episode received
the intended failure perturbation.

### S1-G3 Measurable degradation — PARTIAL PASS

Mission score degraded consistently in every cell. The primary information
degradation was not observed: `D_I` was negative in every cell because legal
information availability was slightly higher in the failure replay. This
means the failure changed mission performance without establishing a clean
information-availability decrease under this action-tape design.

### S1-G4 Dynamic range — PASS for mission score

The mission-score effect was neither null nor catastrophic. Raw nominal and
failure scores retained substantial variation, and the observed degradation
was moderate. This gate passes for `D_J`, not for a multi-metric claim.

### S1-G5 Information legality — PASS for recorded scope

The executor recorded direct sensing, cache paths, communication edges,
task-chain occupancy, message age, failure exposure, and bypass telemetry. No
canonical data or training result was read. The negative `D_I` result is kept
as evidence, not reinterpreted as information robustness.

## Scientific interpretation

S1 supports a bounded statement:

> Under the paired transparent action-tape replay, Relay failure was associated
> with moderate mission-score degradation, but the perturbation was not exposed
> in every cell and did not produce a corresponding legal-information-
> availability decrease.

It does not yet support the stronger causal chain:

```text
Relay failure -> information degradation -> task-support degradation
               -> mission-performance degradation
```

The mission-performance component is visible; the information component is
not cleanly established by this protocol.

## Decisions

- S1 overall: **NO-GO / INFEASIBLE**.
- S2 environment/metric freeze: **not authorized**.
- S3 MARL smoke: **not authorized**.
- Phase 3A training: **NO-GO**.
- Role-Gate: **UNRESOLVED**.
- No threshold, endpoint, seed set, or failure definition is changed after
  observing the result.

The next action, if the robustness line is continued, requires a separately
frozen S1 amendment that explains the incomplete exposure and the counter-
intuitive `D_I<0` result. Otherwise the project should retain mission-score
degradation as a bounded diagnostic finding and avoid claiming information-
mediated robustness.
