# Phase TP-1 — Schedule C Audit Report

## Final decision

Schedule C completed technically, but **CTP-C is not selected**. Its pooled nominal score, failure score, and robustness degradation are all worse than the matched Single-Graph reference. The TP-1 curriculum route therefore receives **NO-GO for further curriculum continuation**. TP-2 remains **NO-GO** and was not started.

This is a tuning/development result only. It does not use canonical seeds or support a headline paper claim.

## Evidence and protocol integrity

- Archive: `phase_tp1_schedule_c_results.tar.gz`
- Archive SHA256: `F5D8005F3BCD70B7FF813F705D957074C917BEF3F26729B81863196A62D2CCCB`
- Arm: CTP-C only; seeds `1601,1602`
- Completed cells: `2/2`
- Budget: `300,032 env steps` per cell = `4 × 64 × 1172`
- Architecture: matched Single-Graph, `116,728` trainable parameters
- Training: from scratch; fixed final checkpoint; no resume, early stopping, or checkpoint promotion
- Evaluation tape: tuning tape `350000–350049`
- Failure: frozen F0, relay agent `1`, onset `44`, duration `80`
- Failure exposure: `1.00` for both CTP-C seeds
- Canonical seeds/results: not used
- Schedule B/D and TP-2: not started
- Schedule C hash: `558c59ccb554ecd168319fd6958705b40be9fda03ba804024b78f79a0bf3a529`

Both manifests report `completed`, `1172` training-log updates, `resume=false`, `early_stopping=false`, and `checkpoint_promotion=false`.

## CTP-C per-seed results

| Seed | J_nominal | J_failure | Delta_J | Collision failure | Timeout failure | Constraint violation | Failure exposure |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1601 | 42.4527 | 20.8387 | 21.6140 | 0.00 | 1.00 | 0.00 | 1.00 |
| 1602 | 51.9796 | 36.1302 | 15.8494 | 0.06 | 0.94 | 0.00 | 1.00 |
| **Pooled mean** | **47.2161** | **28.4844** | **18.7317** | **0.03** | **0.97** | **0.00** | **1.00** |

## CTP-C versus matched SG

Round-A matched SG pooled values were `J_nominal=61.6606`, `J_failure=53.8262`, and `Delta_J=7.8345`.

| Metric | CTP-C | Matched SG | CTP-C / SG | Interpretation |
|---|---:|---:|---:|---|
| J_nominal | 47.2161 | 61.6606 | 0.7657 | CTP-C is 23.43% lower |
| J_failure | 28.4844 | 53.8262 | 0.5292 | CTP-C is 47.08% lower |
| Delta_J | 18.7317 | 7.8345 | — | degradation increases by 10.8972, or 139.09% |

The robustness result is not a valid positive signal: CTP-C has substantially worse nominal competence and a larger absolute failure degradation. Its lower failure score is not evidence of robustness.

## Schedule A versus Schedule C

Schedule A pooled values were `J_nominal=63.7621`, `J_failure=50.3774`, and `Delta_J=13.3848`.

| Metric | CTP-A | CTP-C | CTP-C / CTP-A | Interpretation |
|---|---:|---:|---:|---|
| J_nominal | 63.7621 | 47.2161 | 0.7405 | Schedule C is 25.95% lower |
| J_failure | 50.3774 | 28.4844 | 0.5654 | Schedule C is 43.45% lower |
| Delta_J | 13.3848 | 18.7317 | — | degradation increases by 5.3469, or 39.95% |

The per-seed comparison is inconsistent: Schedule C slightly reduces Delta_J for seed 1601 (`2.36%`) but increases it sharply for seed 1602 (`242.16%`). The pooled result favors Schedule A over Schedule C, but neither curriculum has demonstrated an advantage over matched SG.

## Safety and exposure

All CTP-C episodes were exposed to the fixed failure condition. Constraint violation remained zero. CTP-C had a pooled collision rate of `0.03` versus `0.00` for matched SG, while timeout rates were `0.97` versus `1.00`. Safety does not rescue the performance result.

## TP-1 selection verdict

```text
schedule_c_complete = TRUE
schedule_c_protocol_valid = TRUE
ctp_c_selected = FALSE
matched_sg_retained_as_reference = TRUE
schedule_a_selected = FALSE
tp1_curriculum_selection = NO-GO
tp2_started = FALSE
```

The correct scientific conclusion is that Schedule C did not improve topology-robust training under the frozen protocol. Do not change the environment, reward, failure semantics, tape, seeds, or checkpoint rule to pursue a more favorable result. Any future method or curriculum would require a new separately authorized protocol; this TP-1 result cannot be silently promoted to canonical evidence.

## Evidence locations

- Machine-readable CTP-C result: `archival/results/phase_tp1_schedule_c_cloud_20260814/results/phase_tp1_schedule_c/SCHEDULE_C_RESULT.json`
- Per-seed CTP-C summary: `archival/results/phase_tp1_schedule_c_cloud_20260814/results/phase_tp1_schedule_c/schedule_c_per_seed_summary.csv`
- Round-A decision: `archival/results/phase_tp1_round_a_cloud_20260814/results/phase_tp1_round_a/ROUND_A_DECISION.json`
