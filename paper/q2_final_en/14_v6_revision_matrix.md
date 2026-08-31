# V6 reviewer-directed refinement matrix

This internal matrix records manuscript-level changes made after the V6 pre-submission review. It is not part of the main manuscript.

| Review concern | Revision made | Location |
| --- | --- | --- |
| The formal and independent cohorts were too far apart | Added an early evidence-strata table that reports their opposite directions before detailed results | English Section 5.1; Chinese Section 5.1 |
| Literature was too sparse | Expanded the verified reference set from 16 to 30, covering communication learning, adaptive training distributions, and fault-related UAV communication | English Sections 1 and 3; Chinese Sections 1 and 2 |
| Contributions were diffuse | Compressed contributions to task formulation, bounded reweighting, and reliability-aware evidence | English Section 1; Chinese Section 1.4 |
| Main text read like an audit report | Moved projection iteration and numerical-tolerance detail out of the method narrative; reduced gate labels in the historical timeline | English Section 4; Chinese Sections 4 and 5 |
| Stability exploration could be mistaken for a new method claim | Retained it only as a reliability stress-test boundary and directed detailed material to Supplementary Table S5 | English Discussion 6.3; Chinese Discussion 7.2 |
| Scope and limitations were scattered | Grouped them into four categories: task scope, comparison/mechanism identification, generalization/statistics, and training reliability/theory | Chinese Discussion 7.5; reflected throughout English Discussion 6.5 |

## Canonical terminology ledger

| Canonical term | First-use form | Do not use as a synonym |
| --- | --- | --- |
| DRTP | bounded adaptive topology-perturbation reweighting Single-Graph MAPPO (DRTP-SG-MAPPO) | Stable-DRTP, Reliable-DRTP, DRTP-v2 |
| UTR | Uniform Topology Randomization Single-Graph MAPPO (UTR-SG-MAPPO) | uniform baseline, random curriculum |
| formal cohort | prospective paired seeds 2301--2305 | confirmation cohort, pooled cohort |
| independent cohort | separately completed seeds 2401--2405 | validation seeds, extra five seeds |
| cross-perturbation endpoints | `J_pert,mean` and `J_pert,worst` | strict OOD endpoints |
| additional unseen-member evaluation | post hoc six-tuple training-excluded evaluation | confirmatory OOD evaluation |
| MAPPO-NoGraph | external performance reference | matched causal baseline |
