# Post-MSR SVA + OGS Final Algorithm Decision Report

## 1. Scope and final status

This report completes the zero-training SVA and OGS stages specified by
`POST_MSR_SANITY_OOD_GAP_SCAN_AND_FINAL_ALGORITHM_DECISION.md`.

- Implementation commit: `bcaa040ad8fb47cc6a935f7a5c5e943243e6bcda`
- Branch: `codex/relation-aware-single-graph-v1`
- OGS archive: `D:/File/Downloads/post_msr_ogs_parallel_results.tar.gz`
- OGS archive SHA256: `E2882FF22D21B658664157C3FA01E1D6D9E1C40ABB0D4461B404A6BF930410D9`
- OGS execution: six parallel checkpoint/seed workers, 7,200/7,200 raw episodes
- New training: **not started**
- ENMM/new architecture/new loss/canonical seeds/formal five-seed training: **not started**

Final decision: **SVA-1, O2, Route B direction only**. The next algorithm direction is
DRTP-SG-MAPPO, but it was not implemented or trained in this stage.

## 2. SVA absolute checkpoint audit

The six existing 1M-step checkpoints were evaluated under the previously archived
MSR tape. The MSR tape (`380000–380099`) has hash
`b403239d849cc9d80730c34248483fff77407d53111010d747649e0b89270d01`.

| group | seed | J_nominal | J_failure | Delta_J | exposure |
|---|---:|---:|---:|---:|---:|
| fl_nominal_expert | 1801 | 103.712179 | 34.921951 | 68.790228 | 1.000 |
| fl_nominal_expert | 1802 | 22.510347 | 10.384699 | 12.125648 | 1.000 |
| fl_f0_expert | 1801 | 80.724363 | 65.558993 | 15.165370 | 1.000 |
| fl_f0_expert | 1802 | 38.479867 | 63.387111 | -24.907243 | 1.000 |
| mixed50_sg | 1801 | 91.941832 | 104.633138 | -12.691306 | 0.990 |
| mixed50_sg | 1802 | 183.381681 | 171.978675 | 11.403006 | 1.000 |
| pooled nominal expert | — | 63.111263 | 22.653325 | 40.457938 | 1.000 |
| pooled F0 expert | — | 59.602115 | 64.473052 | -4.870937 | 1.000 |
| pooled Mixed-50 | — | 137.661757 | 138.305907 | -0.644150 | 0.995 |

The empirical reference values are:

\[
J_N^\star=63.111263,\qquad J_F^\star=64.473052.
\]

The MSR normalization was:

\[
C_N=J_{N,\mathrm{Mixed}}/J_N^\star=2.181255,
\]
\[
C_F=J_{F,\mathrm{Mixed}}/J_F^\star=2.145174,
\]
\[
C_{\min}=\min(C_N,C_F)=2.145174.
\]

`C_N` and `C_F` exceed 2 because the Mixed-50 absolute scores are high on the MSR
tape while the specialist reference scores, especially the seed-1802 nominal
specialist reference, are low. The SVA replay and configuration checks found no
tape, evaluator, checkpoint-loading, reward, horizon, information-boundary, or
aggregation mismatch. Therefore these ratios are reference-sensitive diagnostics,
not a standalone superiority claim.

## 3. SVA decision

**SVA-1 — valid high Mixed-50 performance.**

- evaluator/configuration semantics: PASS;
- common checkpoint/evaluator loading: PASS;
- deterministic replay maximum absolute difference: `5.11668622e-06`;
- numerical tolerance: `1e-4`;
- specialist cross-tape relative change: `0.108174`, below the 20% SVA-2 threshold;
- training started: NO;
- ENMM started: NO.

The OGS stage was therefore authorized without retraining.

## 4. OGS tape and completeness

The OGS used a fresh development-only tape:

- episode IDs: `410000–410099`;
- 100 paired base IDs reused across all 12 conditions;
- 10 unseen OOD conditions plus nominal and seen F0 anchors;
- OGS tape hash: `4717edead23cdaae84ea62486214707a9a1ddd40d93a4035490afbca51176b63`;
- raw rows: `7,200` (`6 checkpoints × 12 conditions × 100 episodes`);
- per-seed rows: `72`;
- pooled rows: `36`;
- canonical: false;
- final canonical significance testing: not performed.

The OGS tape hash is intentionally different from the MSR `380000–380099` tape hash.

## 5. Mixed-50 seed 1801: all 12 conditions

| condition | J | D=J_nominal-J | R=J/J_F0_seen | collision | timeout | exposure |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 90.699 | 0.000 | 0.877 | 0.130 | 0.870 | 0.000 |
| f0_seen_44_80 | 103.365 | -12.667 | 1.000 | 0.050 | 0.930 | 0.990 |
| timing_28_80 | 103.725 | -13.027 | 1.003 | 0.110 | 0.840 | 1.000 |
| timing_36_80 | 106.234 | -15.535 | 1.028 | 0.040 | 0.930 | 0.990 |
| timing_52_80 | 99.285 | -8.587 | 0.961 | 0.050 | 0.930 | 0.990 |
| timing_60_80 | 96.410 | -5.711 | 0.933 | 0.040 | 0.910 | 0.990 |
| duration_44_40 | 106.490 | -15.792 | 1.030 | 0.180 | 0.800 | 0.990 |
| duration_44_60 | 109.063 | -18.364 | 1.055 | 0.060 | 0.920 | 0.990 |
| duration_44_100 | 79.837 | 10.861 | 0.772 | 0.020 | 0.910 | 0.990 |
| duration_44_120 | 76.975 | 13.724 | 0.745 | 0.050 | 0.900 | 0.990 |
| compound_28_120 | 74.764 | 15.935 | 0.723 | 0.030 | 0.910 | 1.000 |
| compound_60_120 | 78.107 | 12.592 | 0.756 | 0.020 | 0.970 | 0.990 |

## 6. Mixed-50 seed 1802: all 12 conditions

| condition | J | D=J_nominal-J | R=J/J_F0_seen | collision | timeout | exposure |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 181.043 | 0.000 | 1.029 | 0.040 | 0.880 | 0.000 |
| f0_seen_44_80 | 175.966 | 5.077 | 1.000 | 0.050 | 0.820 | 0.990 |
| timing_28_80 | 171.439 | 9.604 | 0.974 | 0.000 | 0.910 | 1.000 |
| timing_36_80 | 175.101 | 5.942 | 0.995 | 0.030 | 0.830 | 1.000 |
| timing_52_80 | 177.896 | 3.147 | 1.011 | 0.050 | 0.840 | 0.990 |
| timing_60_80 | 176.973 | 4.070 | 1.006 | 0.040 | 0.850 | 0.990 |
| duration_44_40 | 174.247 | 6.796 | 0.990 | 0.010 | 0.900 | 0.990 |
| duration_44_60 | 172.742 | 8.300 | 0.982 | 0.040 | 0.860 | 0.990 |
| duration_44_100 | 173.814 | 7.228 | 0.988 | 0.040 | 0.840 | 0.990 |
| duration_44_120 | 175.360 | 5.683 | 0.997 | 0.020 | 0.870 | 0.990 |
| compound_28_120 | 175.702 | 5.341 | 0.999 | 0.010 | 0.790 | 1.000 |
| compound_60_120 | 177.660 | 3.383 | 1.010 | 0.010 | 0.910 | 0.990 |

## 7. Pooled OGS scores

### Anchors

| condition | J | D | R | collision | timeout | exposure |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 135.871 | 0.000 | — | 0.085 | 0.875 | 0.000 |
| f0_seen_44_80 | 139.665 | -3.795 | 1.000 | 0.050 | 0.875 | 0.990 |

### Timing OOD

| condition | J | D | R | collision | timeout | exposure |
|---|---:|---:|---:|---:|---:|---:|
| timing_28_80 | 137.582 | -1.711 | 0.989 | 0.055 | 0.875 | 1.000 |
| timing_36_80 | 140.668 | -4.797 | 1.011 | 0.035 | 0.880 | 0.995 |
| timing_52_80 | 138.591 | -2.720 | 0.986 | 0.050 | 0.885 | 0.990 |
| timing_60_80 | 136.691 | -0.821 | 0.969 | 0.040 | 0.880 | 0.990 |

### Duration OOD

| condition | J | D | R | collision | timeout | exposure |
|---|---:|---:|---:|---:|---:|---:|
| duration_44_40 | 140.369 | -4.498 | 1.010 | 0.095 | 0.850 | 0.990 |
| duration_44_60 | 140.903 | -5.032 | 1.018 | 0.050 | 0.890 | 0.990 |
| duration_44_100 | 126.826 | 9.045 | 0.880 | 0.030 | 0.875 | 0.990 |
| duration_44_120 | 126.167 | 9.703 | 0.871 | 0.035 | 0.885 | 0.990 |

### Compound OOD

| condition | J | D | R | collision | timeout | exposure |
|---|---:|---:|---:|---:|---:|---:|
| compound_28_120 | 125.233 | 10.638 | 0.861 | 0.020 | 0.850 | 1.000 |
| compound_60_120 | 127.883 | 7.987 | 0.883 | 0.015 | 0.940 | 0.990 |

## 8. OOD robustness summary

| quantity | seed1801 | seed1802 | pooled |
|---|---:|---:|---:|
| J_F0_seen | 103.365243 | 175.965579 | — |
| J_OOD_mean | 93.089101 | 175.093379 | 134.091239 |
| J_OOD_worst | 74.764059 | 171.438668 | 123.101364 |
| R_OOD_mean | 0.900584 | 0.995043 | 0.947814 |
| R_OOD_worst | 0.723300 | 0.974274 | 0.848787 |

The pooled numerical thresholds for O1 are met (`R_OOD_mean=0.947814 ≥ 0.90`,
`R_OOD_worst=0.848787 ≥ 0.80`). However, the full O1 condition also requires
stable seed behavior and no meaningful safety deterioration. Seed1801 has a
consistent long-duration/compound gap (`R=0.745–0.756` for duration 100/120 and
`R=0.723–0.756` for compound conditions), while seed1802 remains near the seen-F0
reference. Seed1801 also reaches collision rate `0.180` at duration 40 versus
`0.050` at its seen F0 anchor. This is not a complete collapse, but it is a
meaningful seed-conditional OOD gap.

## 9. Safety and mechanism summary

- Constraint violation is `0.0` for every pooled Mixed-50 condition.
- Failure exposure is `0.990–1.000` across OOD conditions; no post-hoc exposure
  filtering was applied.
- Pooled collision ranges from `0.015` to `0.095`; the largest pooled value is
  the short-duration condition, with a higher seed-1801 value of `0.180`.
- Pooled timeout ranges from `0.790` to `0.940`, so timeout remains common and is
  not a reliable standalone success claim.
- Topology/path telemetry shows direct-path use after failure at approximately
  `0.363–0.426` for timing conditions, `0.235–0.418` for duration conditions, and
  `0.402–0.403` for compound conditions in the pooled Mixed-50 summaries.
- Task-support fraction rises with later/longer perturbations in several pooled
  conditions, reaching `0.510` for `compound_60_120`; route-switch counts remain
  nonzero. These are consistent with communication-path reconfiguration, but the
  OGS archive contains aggregate path telemetry rather than a new full edge-trace
  mechanism proof.

## 10. O1/O2/O3 and Route decision

### OGS classification: **O2 — moderate OOD gap**

Reason:

1. pooled mean retention is strong;
2. pooled worst retention remains above the nominal O1 numerical threshold;
3. nevertheless, one development seed shows a stable, condition-specific loss on
   long-duration and compound perturbations;
4. that seed also shows a short-duration collision increase;
5. there is no complete collapse, so O3 is not supported.

### Final algorithm decision: **Route B direction**

Freeze exactly one future direction:

> **DRTP-SG-MAPPO — Distributionally Robust Topology-Perturbation SG-MAPPO**

This is a direction only. No DRTP contract was written and no DRTP code or training
was started in this stage. Before any future training, a separate method contract
must freeze topology groups, robust objective, nominal-competence constraint,
parameter count, 1,000,192-step budget, development/held-out seeds, tapes, and
retention criteria. Full, RSG-TC, CTP, ENMM, Schedule D, reward changes, environment
changes, and canonical/formal training remain closed or unauthorized.

## 11. Required stop condition

SVA and OGS are complete. This report is the stopping point required by the plan.
No new training, new algorithm implementation, canonical evaluation, OOD extension,
ablation, or formal five-seed experiment was started.
