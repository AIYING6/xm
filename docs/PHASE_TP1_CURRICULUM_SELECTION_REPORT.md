# Phase TP-1 — Round-A Curriculum Selection Report

## Decision

Round A is complete and technically valid. The pre-registered rule triggers **Schedule C**. Schedule B and Schedule C training have **not** been started.

This report is a development selection result only. It does not authorize canonical seeds, TP-2 confirmation, or formal paper claims.

## Protocol integrity

- Arms: matched SG and CTP-SG Schedule A.
- Seeds: `1601,1602` for both arms.
- Completed cells: `4/4`.
- Budget: `300,032 env steps` per cell, equal to `4 × 64 × 1172`.
- Checkpoint: fixed final update only; no resume, early stopping, promotion, or seed exclusion.
- Evaluation tape: paired IDs `350000–350049`.
- Failure condition: frozen F0, onset `44`, duration `80`, relay agent `1`.
- Failure exposure: `1.0` in all four cells.
- Canonical seeds and canonical results: untouched.
- Result archive SHA256: `31F3FAFE3EE45A3F2A08592B2E6DF551F4EDD193C889E7D6F5009F87A8C6839A`.

## Per-seed results

| Arm | Seed | J_nominal | J_failure | Delta_J | Collision failure | Timeout failure | Constraint failure |
|---|---:|---:|---:|---:|---:|---:|---:|
| SG | 1601 | 60.3692 | 48.6095 | 11.7596 | 0.00 | 1.00 | 0.00 |
| SG | 1602 | 62.9521 | 59.0428 | 3.9093 | 0.00 | 1.00 | 0.00 |
| CTP-A | 1601 | 61.6669 | 39.5295 | 22.1374 | 0.00 | 1.00 | 0.00 |
| CTP-A | 1602 | 65.8574 | 61.2253 | 4.6321 | 0.00 | 1.00 | 0.00 |

## Pooled Round-A comparison

| Metric | matched SG | CTP-A | CTP-A − SG / ratio |
|---|---:|---:|---:|
| J_nominal | 61.6606 | 63.7621 | +3.41% |
| J_failure | 53.8262 | 50.3774 | −6.41% |
| Delta_J | 7.8345 | 13.3848 | +70.83% |
| Collision failure | 0.0000 | 0.0000 | 0.0000 |
| Timeout failure | 1.0000 | 1.0000 | 0.0000 |
| Constraint failure | 0.0000 | 0.0000 | 0.0000 |

## Pre-registered selection logic

### Nominal competence

`mean J_nominal_CTP = 63.7621` is greater than `0.95 × mean J_nominal_SG = 58.5776`. Nominal competence is sufficient; Schedule B is not triggered.

### Failure robustness

CTP-A has lower pooled failure score (`50.3774` vs `53.8262`) and higher pooled degradation (`13.3848` vs `7.8345`). It therefore fails the Round-A robustness condition. Both CTP-A seeds have higher Delta_J than their SG counterparts.

### Safety

Collision, timeout, and constraint-violation rates are identical between SG and CTP-A in the pooled tuning evaluation. Safety does not trigger a rejection independently, but it also does not compensate for the failure-performance result.

## Frozen next-step decision

```text
nominal_sufficient = TRUE
failure_robustness_sufficient = FALSE
trigger = SCHEDULE_C
schedule_b_started = FALSE
schedule_c_started = FALSE
```

Schedule C is the only permitted next curriculum under the frozen TP protocol. No other schedule, hyperparameter, architecture, reward, environment, failure semantic, seed, tape, or checkpoint rule may be introduced. Schedule C must remain unstarted until its execution is separately authorized after this Round-A report.

Raw evidence is preserved under the archival result directory corresponding to the uploaded Round-A archive. The machine-readable source decision is `ROUND_A_DECISION.json`.
