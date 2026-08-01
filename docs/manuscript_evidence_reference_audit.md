# Manuscript Evidence Reference Audit

Generated: 2026-08-02T01:40:10

Purpose:

```text
Check that Chinese and English LaTeX manuscripts actually reference the evidence required by the claim-evidence matrix.
This audit checks manuscript markers only; it does not compile PDFs.
```

## Summary

```text
references_checked = 51
failures = 0
C1 = 9
C2 = 4
C3 = 6
C4 = 4
C5 = 6
C6 = 6
C7 = 6
C8 = 4
C9 = 6
```

## Rows

| Claim | Lang | Type | Manuscript | Status | Notes |
|---|---|---|---|---|---|
| C1 | en | table_input | `paper_latex_en/sections/05_experiments.tex` | ok | Final 300-episode main table is included. |
| C1 | en | figure | `paper_latex_en/sections/05_experiments.tex` | ok | Final success-rate figure is included. |
| C1 | en | figure | `paper_latex_en/sections/05_experiments.tex` | ok | Final collision-rate figure is included. |
| C1 | en | budget_marker | `paper_latex_en/sections/05_experiments.tex` | ok | Main evaluation budget is explicitly stated. |
| C1 | en | value_marker | `paper_latex_en/sections/05_experiments.tex` | ok | Key low-collision value is stated. |
| C1 | zh | table_input | `paper_latex/sections/05_experiments.tex` | ok | Final 300-episode main table is included. |
| C1 | zh | figure | `paper_latex/sections/05_experiments.tex` | ok | Final success-rate figure is included. |
| C1 | zh | figure | `paper_latex/sections/05_experiments.tex` | ok | Final collision-rate figure is included. |
| C1 | zh | budget_marker | `paper_latex/sections/05_experiments.tex` | ok | Main evaluation budget is stated in Chinese manuscript. |
| C2 | en | table_input | `paper_latex_en/sections/08_appendix_experiments.tex` | ok | Seed-paired descriptive interval table is included. |
| C2 | en | boundary_marker | `paper_latex_en/sections/08_appendix_experiments.tex` | ok | Seed-paired interval boundary is stated. |
| C2 | zh | table_input | `paper_latex/sections/08_appendix_experiments.tex` | ok | Seed-paired descriptive interval table is included. |
| C2 | zh | boundary_marker | `paper_latex/sections/08_appendix_experiments.tex` | ok | Seed-paired interval boundary is stated. |
| C3 | en | table_input | `paper_latex_en/sections/08_appendix_experiments.tex` | ok | Communication-dropout table is included. |
| C3 | en | figure | `paper_latex_en/sections/08_appendix_experiments.tex` | ok | Communication-dropout collision figure is included. |
| C3 | en | budget_marker | `paper_latex_en/sections/08_appendix_experiments.tex` | ok | Dropout diagnostic budget is stated. |
| C3 | zh | table_input | `paper_latex/sections/08_appendix_experiments.tex` | ok | Communication-dropout table is included. |
| C3 | zh | figure | `paper_latex/sections/08_appendix_experiments.tex` | ok | Communication-dropout collision figure is included. |
| C3 | zh | budget_marker | `paper_latex/sections/08_appendix_experiments.tex` | ok | Dropout diagnostic budget is stated. |
| C4 | en | table_input | `paper_latex_en/sections/08_appendix_experiments.tex` | ok | Aggregate robustness table is included. |
| C4 | en | boundary_marker | `paper_latex_en/sections/08_appendix_experiments.tex` | ok | Aggregate summary boundary is stated. |
| C4 | zh | table_input | `paper_latex/sections/08_appendix_experiments.tex` | ok | Aggregate robustness table is included. |
| C4 | zh | boundary_marker | `paper_latex/sections/08_appendix_experiments.tex` | ok | Aggregate summary boundary is stated. |
| C5 | en | table_input | `paper_latex_en/sections/08_appendix_experiments.tex` | ok | Radius interpolation table is included. |
| C5 | en | figure | `paper_latex_en/sections/08_appendix_experiments.tex` | ok | Radius interpolation collision figure is included. |
| C5 | en | boundary_marker | `paper_latex_en/sections/08_appendix_experiments.tex` | ok | Interpolation boundary is stated. |
| C5 | zh | table_input | `paper_latex/sections/08_appendix_experiments.tex` | ok | Radius interpolation table is included. |
| C5 | zh | figure | `paper_latex/sections/08_appendix_experiments.tex` | ok | Radius interpolation collision figure is included. |
| C5 | zh | boundary_marker | `paper_latex/sections/08_appendix_experiments.tex` | ok | Interpolation boundary is stated. |
| C6 | en | table_input | `paper_latex_en/sections/08_appendix_experiments.tex` | ok | Target-speed robustness table is included. |
| C6 | en | figure | `paper_latex_en/sections/08_appendix_experiments.tex` | ok | Target-speed collision figure is included. |
| C6 | en | budget_marker | `paper_latex_en/sections/08_appendix_experiments.tex` | ok | Target-speed robustness budget is stated. |
| C6 | zh | table_input | `paper_latex/sections/08_appendix_experiments.tex` | ok | Target-speed robustness table is included. |
| C6 | zh | figure | `paper_latex/sections/08_appendix_experiments.tex` | ok | Target-speed collision figure is included. |
| C6 | zh | budget_marker | `paper_latex/sections/08_appendix_experiments.tex` | ok | Target-speed robustness budget is stated. |
| C7 | en | table_input | `paper_latex_en/sections/08_appendix_experiments.tex` | ok | Edge-feature masking table is included. |
| C7 | en | figure | `paper_latex_en/sections/08_appendix_experiments.tex` | ok | Edge-feature masking delta figure is included. |
| C7 | en | boundary_marker | `paper_latex_en/sections/08_appendix_experiments.tex` | ok | Edge masking boundary is stated. |
| C7 | zh | table_input | `paper_latex/sections/08_appendix_experiments.tex` | ok | Edge-feature masking table is included. |
| C7 | zh | figure | `paper_latex/sections/08_appendix_experiments.tex` | ok | Edge-feature masking delta figure is included. |
| C7 | zh | boundary_marker | `paper_latex/sections/08_appendix_experiments.tex` | ok | Edge masking boundary is stated. |
| C8 | en | boundary_marker | `paper_latex_en/sections/06_discussion.tex` | ok | LAG/JSBSim extension boundary is stated in discussion. |
| C8 | en | extension_marker | `paper_latex_en/sections/06_discussion.tex` | ok | LAG/JSBSim future-extension context is stated. |
| C8 | zh | boundary_marker | `paper_latex/sections/06_discussion.tex` | ok | LAG/JSBSim extension boundary is stated in Chinese discussion. |
| C8 | zh | extension_marker | `paper_latex/sections/06_discussion.tex` | ok | LAG/JSBSim future-extension context is stated. |
| C9 | en | boundary_marker | `paper_latex_en/sections/05_experiments.tex` | ok | Intent diagnostic boundary is stated in experiments. |
| C9 | en | value_marker | `paper_latex_en/sections/05_experiments.tex` | ok | Intent balanced-accuracy diagnostic value is stated. |
| C9 | zh | boundary_marker | `paper_latex/sections/05_experiments.tex` | ok | Intent diagnostic boundary is stated in Chinese experiments. |
| C9 | zh | value_marker | `paper_latex/sections/05_experiments.tex` | ok | Intent balanced-accuracy diagnostic value is stated. |
| C9 | en | boundary_marker | `paper_latex_en/sections/06_discussion.tex` | ok | Intent branch is excluded as a main contribution in discussion. |
| C9 | zh | boundary_marker | `paper_latex/sections/06_discussion.tex` | ok | Intent branch is excluded as a main contribution in Chinese discussion. |

## Use Boundary

```text
Passing this audit means required evidence markers are present in manuscript sources.
It does not guarantee final PDF layout quality or journal-specific formatting.
```
