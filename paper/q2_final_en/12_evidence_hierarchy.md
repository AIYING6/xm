# Evidence Hierarchy and Cohort Timeline

This source table is for conversion into a compact manuscript figure or supplementary table after a target journal and its template are selected. It makes the evidentiary roles explicit; it is not a new experiment and it does not pool cohorts.

## Evidence hierarchy

| Evidence layer | Frozen object | Independent unit | What it supports | What it cannot support |
| --- | --- | --- | --- | --- |
| Primary causal comparison | Formal paired UTR--DRTP cohort, seeds 2301--2305, 10M final checkpoints, tape 490000--490099 | Training seed | Under the matched protocol, adaptive DRTP reweighting improved the reported formal robustness endpoints relative to conditionally uniform UTR. | Stable superiority over other training cohorts or every non-uniform sampler. |
| External performance reference | MAPPO-NoGraph reference | Training seed | A non-graph, no-message external point of comparison. | A parameter-matched causal ablation or a fair leaderboard ranking. |
| Reliability boundary | Independent UTR/SNR/DRTP cohort, seeds 2401--2405, 10M final checkpoints, tape 500000--500099 | Training seed | The formal positive direction did not reproduce in this independent cohort; the paper's claims must remain cohort-bounded. | Erasure or reinterpretation of the completed formal result. |
| Evaluation-tape diagnosis | Formal and independent policies evaluated on both frozen tapes | Training seed | The sign reversal persists across the two fixed tapes, weakening evaluation-tape randomness as a sufficient explanation. | A causal explanation of the training-cohort reversal. |
| Additional unseen-member evaluation | Six onset--duration tuples excluded from the training support | Training seed | Post hoc descriptive performance on these held-out members. | Preregistered confirmatory strict OOD evidence. |
| Optimization and sampler telemetry | PPO and sampler logs from completed runs | Training seed | Exposure redistribution, protocol integrity, and descriptive time-aligned diagnostics. | A stable actionable causal mechanism. |
| Stabilization stress tests | TR, anchor, KL, probe, selector, and critic candidates | Training seed within each frozen contract | Simple local interventions did not reliably eliminate the observed lower-tail/cohort risk. | A solved reliability problem or a new main method. |

## Cohort timeline

| Stage | Cohort or artifact | Role in the manuscript | Reporting rule |
| --- | --- | --- | --- |
| Historical context | Earlier development and telemetry records | Motivates the reliability question and documents that no zero-training actionable mechanism was established. | Context only; never pooled with formal results. |
| Primary formal evidence | 2301--2305 paired UTR--DRTP, 10M | Main method comparison and primary tables/figures. | Report all five seeds and the final-checkpoint rule. |
| External reference | MAPPO-NoGraph | Non-causal architecture reference. | State unequal parameter and information inputs. |
| Independent reliability evidence | 2401--2405 UTR/SNR/DRTP, 10M | Mandatory boundary on the formal result. | Report separately; never combine with 2301--2305 as apparent \(n=10\). |
| Cross-tape evaluation | Both cohorts on both fixed tapes | Excludes a sufficient tape-only explanation for the sign reversal. | Descriptive diagnostic, not a new independent training cohort. |
| Additional unseen-member evaluation | Six post hoc excluded conditions | Supplementary generalization boundary. | Label as additional, post hoc, and non-confirmatory. |
| B-line stress tests | Stabilization studies | Supplementary negative-result/reliability evidence. | Do not present as methods, a leaderboard, or solved stabilization. |

## Claim map for the final manuscript

1. The Abstract, Introduction, Method, and primary Results may state the formal paired result and the bounded design rationale.
2. The Results and Discussion must state that the independent cohort reverses the direction, and that this prevents a claim of cross-cohort stable superiority.
3. Supplementary Information may provide exhaustive seed, safety, provenance, diagnostics, and stabilization-stress-test details without changing the main-method definition.
4. The release package must preserve all completed seeds, manifests, tapes, and unfavorable outcomes before any external anonymous-availability statement is made.
