# DRTP-Q2R Zero-Training Fair Review

**Date:** 2026-08-22  
**Review type:** retrospective, zero-training, no new evaluation tape  
**Final decision:** `DRTP_Q2_LIMITATION_ONLY`

## 1. Scope and immutable history

This review consolidates the existing DRTP evidence only. It does not train,
rerun, create a tape, alter a checkpoint, change a threshold, or reinterpret a
historical decision. The following historical conclusions remain unchanged:

- DRTP development retention: `NO-GO`.
- DRTP held-out v2: `HELD_OUT_FAIL`.
- TC-SAM development: `TC_SAM_DEV_FAIL`.
- No canonical seed was used in the evidence summarized below.

The review therefore cannot convert any previous `NO-GO` or `FAIL` into a
`PASS`.

## 2. Evidence included

| Evidence set | Seeds | Budget | Role | Source |
|---|---:|---:|---|---|
| DRTP development | 1901, 1902 | up to 3M | historical development evidence | [DRTP development performance report](DRTP_SG_MAPPO_DEVELOPMENT_PERFORMANCE_REPORT.md) |
| DRTP held-out v2 | 2001, 2002, 2003 | 10M | historical confirmation evidence | [DRTP held-out v2 audit](DRTP_HELDOUT_V2_AUDIT_REPORT.md) |

These sets use different budgets and evaluation protocols. Their descriptive
values are not pooled into a single inferential experiment. They are reviewed
together only to test whether the claimed DRTP advantage is stable enough to
justify another expensive prospective validation.

## 3. Development evidence at the common 3M endpoint

### 3.1 Pooled descriptive metrics

| Metric | UTR-SG | DRTP-SG | DRTP / UTR |
|---|---:|---:|---:|
| `J_nominal` | 147.157 | 171.007 | 1.162 |
| `J_F0` | 127.929 | 183.880 | 1.437 |
| `J_OOD_mean` | 120.607 | 183.464 | 1.521 |
| `J_OOD_worst` | 103.149 | 172.241 | 1.670 |
| failure collision rate | 0.0136 | 0.0014 | — |
| failure timeout rate | 0.8086 | 0.5600 | — |

This is a strong pooled signal, especially for OOD-worst performance. It is
not sufficient by itself to establish a robust method claim.

### 3.2 Paired seed evidence

| Metric | Seed 1901: UTR → DRTP | Seed 1902: UTR → DRTP | Frozen interpretation |
|---|---:|---:|---|
| `J_nominal` | 89.226 → 130.020 | 205.087 → 211.995 | both positive |
| `J_F0` | 59.997 → 193.586 | 195.862 → 174.175 | seed1902 fails; ratio 0.889 < 0.90 |
| `J_OOD_mean` | 59.602 → 191.100 | 181.613 → 175.828 | seed1902 direction negative |
| `J_OOD_worst` | 50.017 → 180.648 | 156.281 → 163.833 | both positive |

The timeout safety contract also failed at seed1902 under
`compound_60_120`: DRTP minus UTR timeout was `+0.19`, above the frozen
per-seed-condition ceiling of `+0.10`. Consequently the historical
development result correctly remains `NO-GO`.

## 4. Held-out v2 evidence at the common 10M endpoint

### 4.1 Paired per-seed metrics

| Seed | Method | `J_nominal` | `J_F0` | `J_OOD_mean` | `J_OOD_worst` | collision | timeout |
|---:|---|---:|---:|---:|---:|---:|---:|
| 2001 | UTR | 99.223 | 102.603 | 91.713 | 77.737 | 0.0527 | 0.9345 |
| 2001 | DRTP | 248.282 | 206.868 | 198.913 | 170.363 | 0.0564 | 0.4782 |
| 2002 | UTR | 187.061 | 186.921 | 176.961 | 150.697 | 0.0000 | 0.5145 |
| 2002 | DRTP | 170.807 | 72.970 | 88.835 | 53.597 | 0.0036 | 0.9064 |
| 2003 | UTR | 194.740 | 197.038 | 196.390 | 186.628 | 0.0145 | 0.8864 |
| 2003 | DRTP | 245.390 | 226.842 | 222.695 | 210.316 | 0.0309 | 0.7955 |

### 4.2 Held-out pooled descriptive metrics

| Metric | UTR-SG | DRTP-SG | DRTP / UTR |
|---|---:|---:|---:|
| `J_nominal` | 160.341 | 221.493 | 1.381 |
| `J_F0` | 162.187 | 168.893 | 1.041 |
| `J_OOD_mean` | 155.021 | 170.147 | 1.098 |
| `J_OOD_worst` | 138.354 | 144.758 | 1.046 |

The pooled means remain favorable, but the held-out stability decision was
`HELD_OUT_FAIL` because seed2002 is a genuine adverse realization under the
frozen protocol.

## 5. Seed consistency and catastrophic reversal

Across the five historical paired seeds, the direction counts are:

| Metric | DRTP favorable vs UTR |
|---|---:|
| `J_nominal` | 4/5 |
| `J_F0` | 3/5 |
| `J_OOD_mean` | 3/5 |
| `J_OOD_worst` | 4/5 |

These counts are descriptive only because the development and held-out sets
were run under different budgets/protocols. They nevertheless show the key
pattern: strong pooled values coexist with a repeated adverse-seed risk.

Seed2002 is the decisive failure case in the held-out set:

- `J_F0`: DRTP 72.970 versus UTR 186.921, a difference of `-113.951`.
- `J_OOD_mean`: DRTP 88.835 versus UTR 176.961, a difference of `-88.126`.
- `J_OOD_worst`: DRTP 53.597 versus UTR 150.697, a difference of `-97.100`.
- timeout: DRTP 0.9064 versus UTR 0.5145, an increase of `+0.3919`.

This is not a small variance effect that can be hidden by the pooled mean. It
is a method-level reliability limitation under the stated evidence contract.

## 6. Q2 fairness assessment

### Is DRTP usually strong or effectively gambling?

The evidence supports the narrower statement that DRTP can be very strong on
some seeds and protocols, but its benefit is not reliably reproduced across
training seeds. The available evidence does not justify calling it a stable
Q2 main method.

### Is another 5-paired-seed validation justified?

No. A new 5-paired-seed, 10M validation would cost approximately 100M new
environment steps (five UTR and five DRTP runs) and would be a new prospective
experiment. The present evidence already contains both a failed development
retention result and a failed held-out confirmation with a catastrophic
seed-level reversal. The expected scientific value of another expensive trial
is therefore insufficient relative to the remaining paper work.

### What can DRTP still support?

DRTP can be retained as a transparent descriptive comparison or limitation
case: adaptive topology weighting can produce large pooled gains, but those
gains are not seed-reliable under the current contract. It must not be framed
as the stable final algorithm, and no favorable checkpoint or seed may be
selected to replace the failed evidence.

## 7. Final decision

\[
\boxed{\texttt{DRTP\_Q2\_LIMITATION\_ONLY}}
\]

The DRTP algorithm-development route is closed. No DRTP-v2, new adaptive
weighting rule, SAM variant, new loss, new encoder, seed replacement, or
additional prospective DRTP validation is authorized by this review.

The recommended paper route is now the clean UTR-SG-MAPPO robustness paper,
using the already established relay-node failure, topology/path
reconfiguration, OOD, safety, evaluator-semantics, and seed-level evidence.
DRTP may appear only with its complete adverse-seed record as a limitation or
descriptive comparator.

## 8. Reproducibility statement

No training, evaluation rerun, tape generation, checkpoint modification, or
algorithm modification was performed for this review. All numbers above were
transcribed from the cited maintained reports; the historical `NO-GO` and
`HELD_OUT_FAIL` decisions are preserved verbatim.
