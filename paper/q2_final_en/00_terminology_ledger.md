# English Terminology Ledger

| Canonical term | Use | Do not use |
| --- | --- | --- |
| DRTP-SG-MAPPO (DRTP) | Bounded adaptive topology-perturbation reweighting Single-Graph MAPPO | Distributionally Robust Topology-Perturbation; Stable-DRTP |
| UTR-SG-MAPPO (UTR) | Uniform Topology Randomization Single-Graph MAPPO | ordinary SG baseline when the matched training contract matters |
| relay-node failure | Frozen failure of the Relay role | information blackout; information restoration |
| topology/path reconfiguration | Change in legal communication-path and task-support composition | strict recovery of unavailable information |
| canonical F0 | Failure onset 44, duration 80 | default failure without definition |
| $J_{\mathrm{pert,mean}}$ | Mean mission score across the ten frozen, training-supported perturbation conditions | OOD/generalization score |
| $J_{\mathrm{pert,worst}}$ | Minimum mission score across the same ten frozen conditions | guaranteed worst-case robustness |
| additional held-out conditions | Six onset--duration members excluded from training support and evaluated post hoc | preregistered OOD confirmation |
| training seed | Independent statistical unit | episode replicate |
| training-cohort sensitivity | Observed change in outcome direction across separately trained cohorts | proven policy-basin mechanism |
| MAPPO-NoGraph performance reference | Same-task reference with different message input and parameter count | matched causal ablation or external leaderboard |
