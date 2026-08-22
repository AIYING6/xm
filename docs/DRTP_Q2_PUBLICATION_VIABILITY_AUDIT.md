# DRTP Q2 Publication-Viability Audit

**Date:** 2026-08-22  
**Type:** zero-training retrospective audit  
**Historical decision preserved:** `DRTP_Q2_LIMITATION_ONLY`  
**Audit outcome:** `CONDITIONAL_PAPER_VIABLE_WITH_EXPLICIT_SEED_SENSITIVITY`

## 1. Purpose and boundary

This audit asks a different question from the historical stability gate:

> After reporting every available seed honestly, do the historical paired
> results still show a sufficiently strong average and median performance
> signal for a conventional Q2 paper?

It does **not** rewrite the historical DRTP development `NO-GO` or held-out
`HELD_OUT_FAIL`. It does not authorize new training, new seeds, new tapes,
checkpoint selection, threshold changes, or a new DRTP validation campaign.

The development and held-out datasets use different budgets and protocols.
They are therefore reported separately first. The five-seed cross-set summary
is descriptive and must not be presented as one homogeneous confirmatory
experiment.

## 2. Historical paired data

The five available paired seed comparisons are:

- development, 3M endpoint: seeds 1901 and 1902;
- held-out v2, 10M endpoint: seeds 2001, 2002, and 2003.

No seed is removed because it is unfavorable. Seed2002 remains the adverse
case and is shown in full.

## 3. Per-seed paired improvements

Each improvement is `DRTP - UTR`; positive is favorable for return metrics.

| Metric | 1901 | 1902 | 2001 | 2002 | 2003 | Win count | Mean | Median | Worst degradation | SD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `J_nominal` | 40.794 | 6.908 | 149.059 | -16.254 | 50.650 | 4/5 | 46.231 | 40.794 | -16.254 | 63.390 |
| `J_F0` | 133.589 | -21.687 | 104.265 | -113.951 | 29.804 | 3/5 | 26.404 | 29.804 | -113.951 | 99.467 |
| `J_OOD_mean` | 131.498 | -5.785 | 107.200 | -88.126 | 26.305 | 3/5 | 34.218 | 26.305 | -88.126 | 88.629 |
| `J_OOD_worst` | 130.631 | 7.552 | 92.626 | -97.100 | 23.688 | 4/5 | 31.479 | 23.688 | -97.100 | 87.658 |

The requested 3/5 criterion is met for F0 and OOD mean, and the stronger 4/5
criterion is met for nominal and OOD worst. Mean and median improvements are
positive for every return metric. However, dispersion is large and the worst
seed degradation is severe.

## 4. Safety audit

### 4.1 Development evidence

At the 3M pooled endpoint, DRTP had lower failure collision and timeout rates
than UTR (collision `0.0014` vs `0.0136`; timeout `0.5600` vs `0.8086`), with
zero constraint violations. This pooled safety signal does not erase the
seed1902 per-condition timeout breach (`+0.19` relative to UTR under
`compound_60_120`) that caused the historical development retention `NO-GO`.

### 4.2 Held-out evidence

| Metric, DRTP - UTR | Seed 2001 | Seed 2002 | Seed 2003 | Interpretation |
|---|---:|---:|---:|---|
| timeout | -0.4563 | +0.3919 | -0.0909 | lower in 2/3; catastrophic increase at 2002 |
| collision | +0.0037 | +0.0036 | +0.0164 | higher in all 3 held-out seeds |

Constraints remained zero in the cited held-out audit. Thus safety is not
uniformly improved: timeout is usually lower but can catastrophically worsen,
and collision is not favorable in the held-out set.

## 5. The seed2002 limitation

Seed2002 is not a removable outlier. At the 10M held-out endpoint:

- `J_F0`: `72.970` versus UTR `186.921` (`-113.951`);
- `J_OOD_mean`: `88.835` versus UTR `176.961` (`-88.126`);
- `J_OOD_worst`: `53.597` versus UTR `150.697` (`-97.100`);
- timeout: `0.9064` versus UTR `0.5145` (`+0.3919`).

The correct paper interpretation is not “DRTP consistently outperforms.” It is:

> DRTP yields substantial average gains across topology perturbations, while
> training initialization can materially change robustness and safety outcomes.

## 6. Publication-viability judgment

Under the proposed ordinary-Q2 descriptive standard:

- **Mean improvement:** positive for nominal, F0, OOD mean, and OOD worst.
- **Median improvement:** positive for all four return metrics.
- **Win count:** at least 3/5 for every robustness return metric; 4/5 for OOD worst.
- **Nominal competence:** no overall collapse; 4/5 favorable.
- **Safety:** mixed, not uniformly favorable; the adverse timeout and collision
  records must be reported, not hidden.
- **Reliability claim:** seed-stable superiority is not supported.

Therefore the historical data can support a **carefully bounded, performance-
and-reliability-oriented paper narrative**, but not a stable-algorithm claim.
This is a publication-viability judgment, not a retrospective conversion of
the algorithm-development gate into `PASS`.

## 7. Required paper positioning

### Permitted positioning

> DRTP substantially improves average robustness under relay-induced topology
> perturbations, with positive median paired gains in the available historical
> seed audit, but exhibits non-negligible sensitivity to training
> initialization.

### Prohibited positioning

- “DRTP consistently outperforms UTR across random seeds.”
- “DRTP is reliably superior.”
- “DRTP is seed-stable.”
- Reporting pooled means without the full seed table and adverse-seed analysis.

The paper must show all five paired seed results, win counts, paired mean and
median, worst degradation, dispersion, timeout, collision, and the complete
seed2002 case.

## 8. Recommended next work

No new algorithm search is recommended. If the paper proceeds with DRTP, the
remaining work should be publication-facing only: a strong external
comparator, a preregistered and transparently reported ablation, OOD
decomposition, scalability, seed-level statistics, and compute-cost analysis.
Any new confirmatory training would require a separate authorization and must
not be described as repairing the historical DRTP stability failure.

## 9. Final status

\[
\boxed{\texttt{DRTP\_Q2\_LIMITATION\_ONLY\ remains\ the\ historical\ algorithm\ decision}}
\]

\[
\boxed{\texttt{CONDITIONAL\_PAPER\_VIABLE\_WITH\_EXPLICIT\_SEED\_SENSITIVITY}}
\]

The second label describes paper positioning only. It does not alter the
historical `NO-GO`/`HELD_OUT_FAIL`, does not authorize training, and does not
claim that DRTP is a stable or universally superior method.
