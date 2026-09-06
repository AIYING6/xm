# DRTP final claim--evidence matrix

This is the single authority for wording the final manuscript. It prevents a
strong cohort-level result from being rewritten as a universal per-seed or
safety claim. A pending row is a placeholder, not permission to infer a result.

| Candidate claim | Required evidence | Current evidence state | Permitted wording |
|---|---|---|---|
| DRTP improves robustness versus UTR | Completed fresh cohorts A and B at the fixed 10M endpoint | available | “DRTP showed repeated cohort-level robustness benefits over matched UTR.” |
| DRTP generalizes to unseen structures | Frozen structural held-out endpoint in both cohorts | available | “DRTP retained a positive cohort-level advantage under the evaluated structural shifts.” |
| DRTP is not merely generic prioritized replay | Matched PLR-style A/B experiment | pending | Do not claim before the external comparison completes. |
| DRTP transfers to a larger team | Frozen 6-UAV cross-scale endpoint | pending | Do not claim before the 6-UAV experiment completes. |
| Every seed improves | Per-seed dominance in every completed cohort and condition | unsupported | **Prohibited.** |
| DRTP uniformly improves safety | Consistent collision and timeout improvements for all relevant endpoints | unsupported | **Prohibited.** |
| DRTP eliminates cohort sensitivity | Evidence from more than the two completed fresh cohorts and an explicit stability analysis | unsupported | **Prohibited.** |

## Evidence boundary

- The independent unit is a training seed, not an evaluation episode.
- Cohorts A and B are reported separately. Any pooled ten-seed quantity is descriptive only.
- The main method is **Original DRTP**. EGTR and GA-EGTR are development evidence, not substitute main methods.
- Historical reversal cohorts belong in the Supplementary Material as scope and reproducibility context; they do not license post-hoc changes to the final protocol.

