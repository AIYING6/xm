# NP1R physical opportunity-cost formalization

Status: `NP1_NO_GO__RESPONSIBILITY_CHOICE_NOT_PHYSICALLY_STABLE`

NP1R froze a weight-free lexicographic cost:

1. failure versus neutralization;
2. median neutralization completion step;
3. fresh sensing restoration latency;
4. takeover displacement.

No weights were tuned and no post-hoc scenario labels were used.  G1--G3
served as the calibration set and G4--G6 were held out for validation.

The validation did show different candidate winners (`G4: R2`, `G5: R1`,
`G6: R1`), but outcome stability across seeds failed.  In particular, G4/R1
was not consistently feasible (1/4 neutralized), while other assignments were
stable.  Thus the cost rule cannot yet make a reliable physical prediction of
which responsibility takeover is preferable.

## Verdict

`NP1_NO_GO__RESPONSIBILITY_CHOICE_NOT_PHYSICALLY_STABLE`

This closes the dynamic-capability responsibility-decision line under the
current 3DOF task.  No CTRR, NP2 baseline training, or further NP1R tuning is
authorized.  The result is a construct-level negative finding: multiple
candidate responsibilities exist, but their physical choice is not stable
enough to support a learning-algorithm claim.

Artifacts:

* `results/np1r_physical_opportunity_cost_formalization/NP1R_OPPORTUNITY_COST_REPORT.json`
* `results/np1r_physical_opportunity_cost_formalization/NP1R_OPPORTUNITY_COST_MANIFEST.json`
* `scripts/run_np1r_physical_opportunity_cost_formalization.py`

