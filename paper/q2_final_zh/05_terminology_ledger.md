# 05 Terminology Ledger

| Canonical term | First-use definition | Prohibited or legacy variants | Decision |
|---|---|---|---|
| DRTP-SG-MAPPO | Distributionally Robust Topology-Perturbation Single-Graph MAPPO | DRTP Full, DRTP-Stable | Use full name once, then DRTP. |
| UTR-SG-MAPPO | Uniform Topology Randomization Single-Graph MAPPO | ordinary SG when referring to the matched training baseline | Use full name once, then UTR. |
| matched Single-Graph MAPPO | shared 116,728-parameter actor/critic backbone | wider SG, old matched-SG without contract label | Always state the contract when ambiguity exists. |
| relay-node failure | failure of the Relay role under frozen semantics | information blackout, relay disconnection unless proven | Failure does not imply no legal direct path. |
| topology/path reconfiguration | change in legal communication-path and task-support composition | information restoration, strict recovery | Primary mechanism term. |
| nominal condition | no injected relay failure | normal scene, clean scene | Use “nominal.” |
| canonical F0 | onset 44, duration 80 frozen canonical failure | default failure without definition | Define once with onset and duration. |
| OOD timing/duration/compound conditions | held-out perturbation families | unseen topology in universal sense | Scope to the frozen families. |
| `J_nominal` | mission score under nominal evaluation | nominal reward if the quantity is mission score | Keep symbol and definition stable. |
| `J_F0` | mission score under canonical F0 | failure reward | Keep symbol and definition stable. |
| `J_OOD_mean` | equal-contract mean over frozen OOD conditions | generalization score | Name the aggregation. |
| `J_OOD_worst` | worst frozen OOD condition score | worst-case robustness without scope | Always state frozen condition set. |
| training seed | independent statistical unit | episode as replicate | Never treat episodes as training replicates. |
| risk-set trigger validity | trigger success among episodes alive immediately before onset | all-episode exposure as evaluator validity | Overall outcomes still retain all episodes. |
| training-seed sensitivity | reproducible difference in final policy outcomes across training seeds | proven policy-basin divergence | Basin is only a candidate explanation. |
