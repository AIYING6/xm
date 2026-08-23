# 02 Evidence Table

| Claim ID | Manuscript claim | Primary evidence | Status | Required boundary |
|---|---|---|---|---|
| C1 | Relay failure induces legal topology/path reconfiguration and mission degradation. | `docs/PHASE_S1B_TOPOLOGY_RECONFIGURATION_VALIDATION_REPORT.md` and S2 contracts | supported | Do not claim blackout or strict recovery. |
| C2 | DRTP isolates adaptive topology-group weighting relative to matched UTR. | DRTP method contract; `artifacts/paper_q2_closeout/efficiency_results.csv` | supported | Same architecture/exposure must be stated. |
| C3 | DRTP has positive historical mean and median paired return effects. | `final_seed_level_results.csv`; `final_reliability_results.csv` | supported descriptively | Keep 3M/10M strata separate. |
| C4 | DRTP is sensitive to training seed. | held-out seed2002; REL-A0 reports | supported | Present in main text, not supplement only. |
| C5 | Safety outcomes are mixed. | `final_main_results.csv`; held-out audit | supported | No uniform safety-improvement claim. |
| C6 | Evaluator validity should use the alive-at-onset risk set while overall performance retains all episodes. | Phase-C exposure forensic and v2 reviews | supported | Pre-trigger collisions remain policy outcomes. |
| C7 | No fair external drop-in comparator was identified. | `external_comparator_matrix.csv` | supported as audit outcome | Not evidence that no related work exists. |
| C8 | Results are limited to the frozen 3-UAV simulation. | environment and method contracts | supported | No scalability/deployment claim. |
| C9 | DRTP is stable, universally robust, or consistently superior. | none | prohibited | Delete rather than hedge. |
| C10 | A new prospective paired UTR/DRTP confirmation is required before upgrading DRTP beyond a historical seed-sensitive result. | `docs/DRTP_UTR_Q2_FORMAL_FIVE_SEED_CONFIRMATION_CONTRACT.md`; preflight artifact | authorized and frozen; result pending | Use seeds 2301–2305, common 10M final checkpoints, tape 490000–490099, and retain all outcomes. |

## Missing but non-blocking presentation inputs

- final journal name and article format;
- final author list, affiliations, and corresponding author;
- code/data availability wording;
- funding, conflict-of-interest, and author-contribution statements;
- final reference-manager library after citation verification.
