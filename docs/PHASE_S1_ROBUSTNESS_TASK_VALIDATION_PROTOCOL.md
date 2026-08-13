# Phase S1 Robustness Task Validation Protocol

**Protocol ID:** `PHASE-S1-RV-V1`  
**Status:** FROZEN BEFORE EXECUTION  
**Training:** prohibited

## Scientific question

Does the frozen relay-failure task produce a stable, measurable, non-
catastrophic degradation from nominal to failure conditions under legal
transparent control?

S1 does not test learned-policy superiority and does not require recovery.

## Paired conditions

Each deterministic episode is evaluated twice with the same controller,
development seed, initial UAV state, target realization, action sequence,
dropout stream, and horizon:

- `nominal`: no Relay-1 failure;
- `relay_failure`: Relay 1 failure at the frozen R2B trigger semantics.

Only the failure flag differs. Results are paired by
`(controller, seed, episode_id, condition)`.

Controllers are fixed to `structural_oracle` and `legal_observation`. S1 uses
development seeds `1401`, `1402`, and `1403`, 100 paired episodes per cell,
and no checkpoints or canonical seeds.

## Primary estimands

Only two metrics are primary:

1. **Mission degradation**

   ```text
   D_J = (J_nominal - J_failure) / max(|J_nominal|, epsilon)
   ```

   `J` is the transparent-controller episode mission score, with nominal and
   failure raw values reported alongside the normalized difference.

2. **Legal information degradation**

   ```text
   D_I = A_info_nominal - A_info_failure
   ```

   where `A_info` is the fraction of timesteps with fresh, legal attacker
   target information derived from cache/direct-sensing provenance.

Secondary metrics are task-chain availability, information age, robustness
ratio, success, collision, timeout, and constraint violation.

## Five gates

| Gate | Requirement |
| --- | --- |
| S1-G1 Nominal feasibility | Nominal episodes produce non-degenerate mission score, legal information, and task-chain occupancy; no hidden target state is used. |
| S1-G2 Failure exposure | Relay failure is active at the frozen time, Relay communication edges disappear, and failure telemetry is present. |
| S1-G3 Measurable degradation | At least one primary degradation (`D_J` or `D_I`) is positive with stable direction in each controller×seed cell. |
| S1-G4 Dynamic range | Failure is neither null (`D≈0`) nor catastrophic for every episode; both nominal and failure distributions retain measurable variance and non-degenerate task outcomes. |
| S1-G5 Information legality | Direct sensing, cache path, graph edges, message age, and task-support provenance are logged; no hidden/global target state enters controller observations. |

The exact numerical adequacy thresholds are fixed before execution in the
executor manifest. They cannot be chosen from observed outcomes.

## Required artifacts

The executor must write paired raw episode CSV, raw timestep provenance,
per-cell summary, metric manifest, bypass audit, and an S1 report. It must not
calculate survival/KM/RMST headline results and must not start MARL training.

## Decision rule

S1 PASS permits S2 metric/environment freeze and then S3 three-method
learnability smoke. S1 FAIL keeps training NO-GO and requires either a bounded
protocol amendment or closure of the proposed robustness task. Role-Gate is not
part of S1.
