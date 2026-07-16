# English LaTeX Paper Draft

This directory contains an English LaTeX draft for the EA-RG-MAPPO-S paper.

## Main File

```text
main.tex
```

## Source Scope

The English draft is converted from the validated Chinese LaTeX manuscript and the English Markdown drafts under `docs/`.

It keeps the current evidence boundary:

```text
Validated: simplified 2D heterogeneous UAV pursuit under limited communication.
Not validated yet: full 6DOF air combat with missile, radar, and human-UAV teaming.
```

## Shared Assets

```text
Figures: ../results/figures/
Tables: ../results/latex_*.tex
Bibliography: ../paper_latex/references.bib
```

## Static Check

From the project root, run:

```bash
python scripts/check_latex_project.py
```

The checker validates both `paper_latex/` and `paper_latex_en/`.

English-specific consistency check:

```bash
python scripts/check_english_latex_consistency.py
```

This checks that the English draft keeps the required result markers, table/figure inputs, and evidence-boundary statements.

## Compile

Recommended command in an environment with a LaTeX distribution:

```bash
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

The current Codex runtime does not have `xelatex`, `latexmk`, or `bibtex` on PATH, so PDF rendering has not been verified here.
