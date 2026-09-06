# DRTP final figure contract

## Core conclusion

Original DRTP repeatedly improves cohort-level perturbed return relative to matched UTR under frozen endpoint evaluation, while its reliability and safety profile must be interpreted from the complete seed-level distributions.

## Figure plan

| Figure | Evidence role | Required source data | Status |
|---|---|---|---|
| Fig. 1 | Hero: A/B paired UTR-versus-DRTP endpoint comparison | seed-level perturbed return, nominal return, timeout, collision | ready for rendering once CSV is staged |
| Fig. 2 | Generalization: held-out structural and parameter OOD | fixed OOD per-seed-condition summary | source available after final staging |
| Fig. 3 | External comparison: PLR-style replay | matched A/B endpoint summaries for UTR, DRTP and PLR | pending cloud run |
| Fig. 4 | Cross-scale evidence: six-UAV endpoint comparison | 6-UAV per-seed-condition endpoint summary | pending cloud run |

## Figure 1 visual contract

- Archetype: quantitative grid.
- Backend: Python / matplotlib.
- Panel A: cohort A paired seed-level perturbed return.
- Panel B: cohort B paired seed-level perturbed return.
- Panel C: paired `DRTP − UTR` deltas by cohort, with zero reference line.
- Panel D: collision and timeout paired deltas, kept separate.
- Show every retained seed; points for a seed are connected across methods.
- Export SVG, PDF and 600-dpi TIFF, with a source-data CSV copied to the output folder.

## Review-risk control

The hero figure must not pool A and B as the primary panel, hide seed-level values, or imply all-seed dominance. It must not encode collision and timeout into one synthetic safety score.

