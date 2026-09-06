# DRTP stabilization: A-cohort interpretation and evidence governance

**Status:** `A_COMPLETE_B_FROZEN_CONTINUATION`
**Date:** 2026-09-06

This addendum governs interpretation only. It does not alter the frozen
algorithm, `alpha = 0.75`, seeds, tape, environment, reward, PPO settings, or
endpoint protocol.

## A cohort is valid

All 20 ten-million-step trajectories and all 14,000 fixed endpoint episodes
completed. The original automatic aggregation stopped because the CSV writer
inferred fields from a UTR row and did not accept anchored-sampler telemetry
fields. Reaggregation used the existing completed evaluation files only; it
did not train, evaluate, select a checkpoint, or change a result.

The A-cohort perturbed-return summary (five independent training seeds) is:

| Method | Mean | Worst seed | Sample SD |
|---|---:|---:|---:|
| UTR | 177.02 | 79.75 | 64.53 |
| Original DRTP | 216.66 | 191.49 | 23.48 |
| EGTR | **226.13** | **203.92** | **15.86** |
| Global-Anchored EGTR, `alpha=.75` | 210.82 | 128.64 | 46.73 |

Thus, **EGTR is the A-cohort preferred method**. Global-Anchored EGTR is not
selected over EGTR from A alone. It nevertheless exceeds UTR in all five
paired perturbed-return comparisons: `+0.68`, `+62.72`, `+52.04`, `+4.64`, and
`+48.89`.

The local concern is narrow: the anchored method did not preserve EGTR's
A-cohort lower tail, particularly for seed `78015` (EGTR `203.92`; anchored
`128.64`). The bounded anchor was actively and correctly applied, so this is
an outcome finding rather than an implementation failure.

## Meaning of `CONFIRMATION_WEAK`

`CONFIRMATION_WEAK` is a **cohort-local evidence label**, not a route-closing
instruction. Its only warranted reading is:

> The A cohort does not establish Global-Anchored EGTR, `alpha=.75`, as a
> final method preferred over EGTR.

It does not establish that DRTP is closed, that EGTR failed, that the anchored
method is ineffective relative to UTR, or that `alpha=.75` is cross-cohort
unreliable. It does not cancel Cohort B.

## Frozen next step: independent Cohort B

Cohort B (`78021--78025`, tape IDs `781000--781099`) remains the planned
independent test of whether the A method ordering is cohort-specific. UTR,
Original DRTP, EGTR and Global-Anchored EGTR remain exactly frozen. No alpha
change, new gate, sampler revision, GA-v2, or post-hoc root-cause programme is
authorized before B completes.

After B, select the paper's principal method from the full evidence profile:
mean and median return, seed-wise consistency, lower tail and catastrophic
outcomes, nominal behavior, OOD performance and safety. A method need not win
every seed or every metric. A and B must remain separate inferential cohorts;
any pooled ten-seed value is descriptive only.

The maintained machine-readable version is
`configs/drtp_stabilization_evidence_governance_20260906.json`.
