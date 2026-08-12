# Phase 2I-A3 failure perturbation effectiveness

Among the 1,200 existing episodes, 22 were pre-established and maintained after failure; zero were classified as pre-established and lost, and zero were strict recovered/unrecovered risk-set episodes. The failure-effectiveness table is in `results/development/phase2ia3_riskset_audit/failure_effectiveness_summary.csv`.

This does not support R4 as the primary cause because the dominant issue is that the policies generally do not establish an eligible chain before failure. The retained episode summaries do not contain an edge-level alternate-path timeline; this is explicitly marked unavailable. The perturbation cannot be judged as a recovery perturbation for most episodes because no eligible chain existed to perturb.

No canonical failure protocol was changed.
