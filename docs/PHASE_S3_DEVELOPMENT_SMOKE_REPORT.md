# Phase S3 Three-Method Development Smoke Report

**Protocol:** `PHASE-S3-TMDS-V1` with cloud scheduling amendment `V1-A1`  
**Artifact class:** DEVELOPMENT_ONLY  
**Result:** **S3-NO-GO / S4 AND CANONICAL TRAINING NOT AUTHORIZED**

## Scope and provenance

This report audits the cloud result package `phase_s3_results.tar.gz` (SHA256
`C63D01532AA09C4173BE17E5B0746EF88D922D61A16B28FC5F99987A6FDD240D`).
The package is preserved under
`archival/provenance/phase_s3_cloud_a4f2076/` and contains all nine required
runs. Every run reports `completed`, exactly 200,192 environment steps, a
fixed-final-checkpoint-only rule, and a checkpoint SHA256 matching its manifest.
All runs used commit `a4f2076a38da86d528890f4fbdc8019bff4fb365`.

No canonical seeds, canonical evaluation, or Phase 3A training was used.

## Frozen S3 evidence

Each method × seed final checkpoint was evaluated on 100 nominal/failure pairs.
All failure-condition episodes were exposed. Seed-level means are:

| Method | Seed | `J_nominal` | `J_failure` | `Delta_J` |
|---|---:|---:|---:|---:|
| Full | 1501 | 12.160 | 8.259 | 3.901 |
| Full | 1502 | 38.160 | 14.137 | 24.023 |
| Full | 1503 | -15.396 | -23.035 | 7.639 |
| MAPPO | 1501 | 32.873 | 10.967 | 21.906 |
| MAPPO | 1502 | 16.716 | 10.050 | 6.666 |
| MAPPO | 1503 | 37.020 | 24.809 | 12.211 |
| Matched SG | 1501 | 33.306 | 19.167 | 14.139 |
| Matched SG | 1502 | 23.387 | 29.843 | -6.456 |
| Matched SG | 1503 | 50.893 | 36.743 | 14.150 |

`Delta_J = J_nominal - J_failure`; lower positive values indicate less observed
failure degradation, but cannot be interpreted independently of nominal
competence.

## Gate assessment

| S3 dimension | Result | Evidence |
|---|---|---|
| Learnability / numerical stability | PASS | All nine runs completed; final PPO losses, KL, gradients, and explained variance were finite. |
| Failure exposure and dynamic range | PASS as diagnostic | Exposure was 100%; non-null nominal/failure differences were observed. |
| Topology/path telemetry | PASS | During active failure, Relay edges were zero for all methods; direct/alternative paths and legal information remained observable. |
| Nominal competence of Full | FAIL | Full nominal score was below both MAPPO and Matched SG in seeds 1501 and 1503; seed 1503 was negative. |
| Coherent Full robustness signal | FAIL | Full had lower `Delta_J` than both comparators in seeds 1501 and 1503, but not 1502. Those same two apparent wins coincide with lower Full nominal score, so the result is compatible with low-competence pseudo-robustness. |
| Success diagnostic | UNINFORMATIVE | `min_success_step=1000` exceeds the frozen 260-step horizon, yielding zero success for all methods and conditions. |

## Mechanism observations

The expected topology intervention occurred: during active failure,
`Scout→Relay` and `Relay→Attacker` communication were zero. The direct
`Scout→Attacker` path remained possible. This continues to support the bounded
topology-reconfiguration task definition, but it does not explain a Full
advantage because no such advantage was established under non-degenerate
nominal competence.

## Execution-contract limitation discovered

Nominal/failure pairs are correctly matched **within** each method and seed.
However, the runner assigned different episode-ID ranges by method: MAPPO
`310000–310099`, Matched SG `320000–320099`, and Full `330000–330099`.
Therefore cross-method contrasts are not matched on identical evaluation tapes.
This did not invalidate within-method `Delta_J`, but it rules out treating
episode-level cross-method contrasts as paired evidence. This must be repaired
in any future separately frozen protocol.

## Decision and claim boundary

The S3 purpose was screening, not superiority proof. The required screening
condition—non-degenerate Full nominal competence plus a coherent Full
robustness signal relative to both MAPPO and capacity-matched Single-Graph—is
not met.

Accordingly:

```text
S3-NO-GO / S4 architecture work and Phase 3A canonical training are not authorized.
```

Do not remove seed 1503, reinterpret `Delta_J` alone as robustness, promote
the existing result to a manuscript claim, or change S2 settings in response to
these outcomes. Any next action requires a separately written decision protocol
that distinguishes the structural success-metric issue from the independent
question of Full nominal competence and uses identical cross-method evaluation
tapes.
