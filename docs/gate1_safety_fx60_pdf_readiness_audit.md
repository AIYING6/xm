# Gate 1 Safety Fixed-Update-60 PDF-Readiness Audit

Last updated: 2026-07-19

## Scope

Checked the active English manuscript rooted at:

- `paper_latex_3d_en/main.tex`
- `paper_latex_3d_en/sections/01_introduction.tex`
- `paper_latex_3d_en/sections/02_related_work.tex`
- `paper_latex_3d_en/sections/03_problem.tex`
- `paper_latex_3d_en/sections/04_method.tex`
- `paper_latex_3d_en/sections/05_experiments.tex`
- `paper_latex_3d_en/sections/06_discussion.tex`
- `paper_latex_3d_en/sections/07_conclusion.tex`

Generated table fragments included in the recursive check:

- `results/gate1_safety_fx60_paper_tables/main_results_latex.tex`
- `results/gate1_safety_fx60_paper_tables/ablation_results_latex.tex`
- `results/gate1_safety_fx60_paper_tables/seed_aware_deltas_latex.tex`
- `results/gate1_safety_fx60_model_costs/model_costs_latex.tex`

## Static Results

Recursive LaTeX-entry check from `main.tex` found:

- missing citations: none;
- unused BibTeX entries: none;
- missing references: none;
- duplicate labels: none;
- missing `\input{...}` files: none;
- missing graphics: none.

## Table Layout Risk

Five paper-facing tables are currently included:

| Table | Purpose | Layout status |
|---|---|---|
| `tab:gate1-safety-fx60-main` | main fixed-update-60 comparison | protected with `\resizebox{\textwidth}{!}{...}` |
| `tab:gate1-safety-fx60-timing` | early-vs-nominal relay-failure timing generalization | protected with `\resizebox{\textwidth}{!}{...}` |
| `tab:gate1-safety-fx60-ablation` | mechanism ablations | protected with `\resizebox{\textwidth}{!}{...}` |
| `tab:gate1-safety-fx60-bootstrap` | seed-aware bootstrap deltas | protected with `\resizebox{\textwidth}{!}{...}` |
| `tab:gate1-safety-fx60-model-cost` | model size and actor latency | protected with `\resizebox{\textwidth}{!}{...}` |

The resize protection is intentional because the bootstrap confidence-interval table and ablation seed-recovery column are likely to exceed page width without scaling.

## Figure Layout Risk

Included figures exist under `results/figures/`:

- `intercept_3d_task_scene.png`
- `intercept_3d_multi_relation_graph.png`
- `gate1_safety_fx60_mechanism_curves.png`
- `gate1_safety_fx60_representative_case_timeline.png`

The mechanism and representative-case figures are included at `0.98\textwidth` in `figure*` environments. This is acceptable for a single-column article draft, but the final journal template may require conversion to ordinary `figure` or width adjustment after PDF rendering.

## Compilation Status

`pdflatex` is not installed in the current environment, so full PDF compilation and visual page inspection were not performed.

When LaTeX becomes available, run the equivalent of:

```bash
cd paper_latex_3d_en
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Then inspect:

- whether all tables stay inside page margins;
- whether figure floats appear near their first references;
- whether captions remain readable after table scaling;
- whether bibliography entries render correctly;
- whether the abstract, contribution list, experiment tables, discussion, and conclusion retain the same fixed-budget evidence boundary.

## Fixes Applied

- `scripts/build_gate1_safety_fx60_paper_tables.py` now emits resized LaTeX tables for the main result, mechanism ablations, and seed-aware bootstrap deltas.
- `scripts/report_3d_model_costs.py` now emits a resized LaTeX table for the model-cost report.
- Regenerated all paper-facing LaTeX table fragments.
- Integrated the model-cost table into `paper_latex_3d_en/sections/05_experiments.tex`.
- Integrated the fixed-checkpoint early-vs-nominal timing-generalization table into `paper_latex_3d_en/sections/05_experiments.tex`.

## Remaining Risks

- Actual float placement cannot be verified without a compiled PDF.
- The current article class is a draft container, not a final target-journal template.
- If a two-column journal template is later selected, wide tables and `figure*` placement must be rechecked under that template.
