# DRTP submission figure and table plan

All values must be generated from frozen aggregation CSVs. A/B are separate in every primary display.

## Figures

| Figure | Purpose | Required design | Evidence status |
|---|---|---|---|
| Fig. 1. DRTP framework | Explain the contribution before results | Frozen condition support → nominal/failure split → group EMA deficit → bounded `q` update → unchanged MAPPO learner; visually mark that only reset allocation changes | ready |
| Fig. 2. UTR, DRTP and PLR-style mechanism map | Distinguish allocation mechanisms without claiming a universal winner | Five-row matrix: sampling object, signal, topology semantics, nominal anchor, probability constraints | ready |
| Fig. 3. Main A/B paired endpoints | Establish repeated cohort-level evidence | Two paired seed panels, separate A/B; third panel shows paired deltas; timeout and collision remain separate | ready once source CSV is staged |
| Fig. 4. Frozen OOD | Show bounded transfer beyond the training mixture | Structural and parameter-shift paired delta panels, A/B separated | ready once source CSV is staged |
| Fig. 5. PLR-style matched comparison | Show external-comparator boundary | A and B side-by-side distributions plus timeout; no pooled winner visual | ready once source CSV is staged |
| Fig. 6. Six-UAV cross-scale | Test the larger-team protocol | UTR/DRTP paired results and condition breakdown | pending; do not render before formal completion |

## Tables

| Table | Content | Main-text rule |
|---|---|---|
| Table 1 | Environment, role topology, condition groups, fixed support, training budget, endpoint tape | Include exact protocol rather than generic environment prose. |
| Table 2 | A/B UTR-versus-DRTP main endpoint | Mean, median, minimum, SD, nominal return, success, timeout, collision, paired positive count. |
| Table 3 | Frozen structural and parameter OOD | Condition family, endpoint return, mean paired delta, lower-tail delta, timeout, collision. |
| Table 4 | PLR-style matched comparison | A/B independently; table caption explicitly says cohort-dependent comparison. |
| Table 5 | Runtime and computational overhead | Parameters, wall-clock per 1M steps, peak memory, sampler overhead, hardware. |
| Table 6 (optional) | 6-UAV cross-scale endpoint | Only after final frozen aggregation exists. |

## Caption rules

1. State `n=5 independently trained policies per cohort` in each primary table caption.
2. State that A/B pooled quantities, if shown, are descriptive only.
3. Do not use a synthetic safety score; collision and timeout are separate fields.
4. Do not put development-only EGTR or GA-EGTR results in the main results figures.
