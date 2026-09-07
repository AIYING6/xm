# DRTP submission figure and table plan

All values must be generated from frozen aggregation CSVs. A/B are separate in every primary display.

## Figures

| Figure | Purpose | Required design | Evidence status |
|---|---|---|---|
| Fig. 1. DRTP overall framework | Explain the contribution before results | Frozen condition support → nominal/failure split → group EMA deficit → bounded `q` update → unchanged MAPPO learner; visually mark that only reset allocation changes | ready |
| Fig. 2. Topology failure and training-exposure mechanism | Explain why failure groups carry more structure than anonymous levels | Role graph, failed node/onset/duration semantics, nominal anchor, and within-group frozen-member sampling | ready |
| Fig. 3. UTR vs DRTP training process | Distinguish uniform, generic priority, and topology-semantic allocation | UTR / PLR-style / DRTP probability-update paths; include sampler `q` trajectories only from frozen logs and label this as process evidence, not a policy-performance curve | ready once sampler logs are staged |
| Fig. 4. Main robustness comparison | Answer RQ1 with repeated cohort-level evidence | Two paired seed panels, separate A/B; third panel shows paired deltas; timeout and collision remain separate | ready once source CSV is staged |
| Fig. 5. OOD/generalization results | Answer RQ3 under bounded shifts | Structural and parameter-shift paired delta heatmap/panels, A/B separated | ready once source CSV is staged |
| Fig. 6. Six-UAV cross-scale validation | Answer RQ4 at larger scale | UTR/DRTP paired results and condition breakdown | pending; do not render before formal completion |

## Tables

| Table | Content | Main-text rule |
|---|---|---|
| Table 1 | Experimental settings | Environment, role topology, condition groups, fixed support, training budget, endpoint tape, and matched controls. |
| Table 2 | A/B UTR-versus-DRTP main endpoint | Mean, median, minimum, SD, nominal return, success, timeout, collision, paired positive count. |
| Table 3 | PLR-style matched comparison | A/B independently; table caption explicitly says cohort-dependent comparison. |
| Table 4 | 6-UAV cross-scale endpoint | Only after final frozen aggregation exists. |
| Table 5 | Component ablation | Keep as a clearly marked placeholder unless a frozen ablation protocol is formally executed. |
| Supplementary Table S1 | UTR/PLR-style/DRTP mechanism comparison | Sampling object, adaptation signal, topology semantics, nominal reference, update rule, and constraints. |
| Supplementary Table S2 | Frozen structural and parameter OOD | Condition family, endpoint return, mean paired delta, lower-tail delta, timeout, collision. |

## Caption rules

1. State `n=5 independently trained policies per cohort` in each primary table caption.
2. State that A/B pooled quantities, if shown, are descriptive only.
3. Do not use a synthetic safety score; collision and timeout are separate fields.
4. Do not put development-only EGTR or GA-EGTR results in the main results figures.
