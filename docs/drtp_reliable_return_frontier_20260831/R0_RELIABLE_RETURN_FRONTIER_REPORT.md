# DRTP reliable-return frontier R0

**Status:** `R0_ZERO_TRAINING_COMPLETE — NO CANDIDATE PROMOTED`.

This is a post-hoc exploratory re-expression of completed pilots. It neither changes their original frozen gate decisions nor pools training cohorts. It authorizes no training, parameter selection, or Mainline-A modification.

## Reliability-first objective

The acceptable trade-off is deliberately stricter than ‘lower variance’: the candidate must retain a positive mean paired robust gain over UTR, have a non-negative worst paired gain, keep mean and upper-tail loss versus Original DRTP within the frozen measurement margin `epsilon_J = 7.875`, and not enlarge the paired-gain range.

## Archived-cohort screen

| Experiment | Candidate mean G | Candidate worst G | Mean loss vs Original | Upper-tail loss | Range reduced | Screen |
| --- | ---: | ---: | ---: | ---: | :---: | :---: |
| S1_TR | 5.159 | -21.382 | -9.029 | -11.869 | False | False |
| S2_ANCHOR | 4.711 | -8.834 | -8.581 | -1.137 | True | False |
| R1_CONSERVATIVE | -6.981 | -78.314 | 10.141 | -22.990 | False | False |
| D3_KLR | 33.067 | 28.449 | -23.252 | 9.420 | True | False |
| KLR_FINAL_A | 18.516 | -26.874 | 0.871 | -29.231 | False | False |
| KLR_FINAL_B | 9.976 | -37.110 | -15.989 | -58.609 | False | False |
| D5_KLB | -42.557 | -49.669 | 11.264 | 23.473 | True | False |
| P3_PP | 10.372 | -1.828 | -38.202 | -22.116 | True | False |
| P4_PP | 5.492 | -35.701 | 8.106 | 2.380 | False | False |

## Interpretation

No archived candidate passes the complete screen or is eligible for promotion. D3_KLR is the nearest early pilot row: it has positive mean and worst paired gains and a smaller range, but its observed upper-tail loss is `9.420`, exceeding the frozen `epsilon_J = 7.875`. More decisively, the completed KLR final replication fails in both independent cohorts: each cohort contains a newly catastrophic KLR seed and KLR enlarges gain range and sample SD. PP-DRTP's independent P4 cohort fails the downside and range requirements. Conservative-DRTP reverses in R1. Every other comparable candidate fails at least one reliability-first condition.

Thus the revised objective is scientifically viable, but none of the archived local-patch candidates supplies sufficient evidence that it achieves that objective. A future candidate must be designed from a new, independently supported mechanism and must be tested prospectively in two separate fresh-seed cohorts. This R0 audit does not authorize that candidate or any cloud run.

## Integrity boundary

The unit of evidence remains the training seed. Differences in seed sets, tapes, budgets, and candidate semantics make the archived rows unsuitable for pooled estimation or retrospective winner selection.
