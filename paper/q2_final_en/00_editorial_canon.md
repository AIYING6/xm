# DRTP English Manuscript Editorial Canon

## Canonical title

**Bounded Adaptive Topology-Perturbation Reweighting for Relay-Failure UAV Coordination: Formal Gains and Training-Cohort Sensitivity**

## One-sentence argument

In a frozen three-UAV relay-failure coordination task, we evaluate bounded adaptive reweighting of predefined topology-perturbation groups against a parameter- and exposure-matched uniform baseline; the formal five-seed cohort shows consistent paired gains, whereas an independent cohort does not reproduce their direction, delimiting DRTP as a promising but not cross-cohort reliable empirical training strategy.

## Terminology ledger

| Canonical English term | First-use definition | Do not use |
| --- | --- | --- |
| DRTP-SG-MAPPO (DRTP) | bounded adaptive topology-perturbation reweighting Single-Graph MAPPO | distributionally robust DRTP; Stable-DRTP |
| UTR-SG-MAPPO (UTR) | Uniform Topology Randomization Single-Graph MAPPO | ordinary SG baseline |
| relay-node failure | frozen failure of the Relay role and its associated communication edges | information blackout; full disconnection |
| topology/path reconfiguration | change in the composition of legal communication paths and task support | information recovery |
| nominal condition | condition without an injected relay failure | clean scene; normal scene |
| canonical F0 | relay failure with onset 44 and duration 80 | default failure without definition |
| `J_pert,mean` | mean mission score across the ten frozen perturbation conditions | OOD mean; generalization score |
| `J_pert,worst` | minimum mission score in those ten frozen conditions | general worst-case robustness |
| additional unseen-member evaluation | post hoc evaluation on six excluded onset--duration tuples | preregistered OOD evaluation |
| training seed | independent statistical unit | episode replicate |
| training-cohort sensitivity | direction difference between completed training cohorts | proven basin mechanism |

## Non-negotiable claim boundary

The manuscript may claim the formal-cohort result and its protocol-level evidence. It must not claim stable superiority across training cohorts, universal robustness, a general distributionally robust optimization guarantee, strict OOD generalization, a causal mechanism for seed sensitivity, or that online adaptation is necessary relative to every fixed non-uniform distribution.

## English-source rule

`paper/q2_final_zh/main_zh.md`, its formal-result archive, and its supplementary source data are the only scientific sources for the new English manuscript. The pre-existing `paper_latex_3d_en/` EA-RG-MAPPO manuscript describes a different study and must not be reused as DRTP evidence or prose.
