# LaTeX Paper Draft

This directory contains a maintainable LaTeX draft for the EA-RG-MAPPO-S paper.

## Main File

```text
main.tex
```

## Compile

Recommended local command:

```bash
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

The draft uses `ctexart`, so XeLaTeX is recommended.

## Static Check

Before rendering, run:

```bash
python ../scripts/check_latex_project.py
```

This checks section inputs, figure paths, nested table inputs, citation keys, and labels without requiring a TeX installation.

## One-Command Paper Asset Build

From the project root, run:

```bash
python scripts/build_paper_assets.py
```

This regenerates lightweight paper assets from existing results and runs the validation gates. It does not retrain policies or rerun long evaluations.

## Notes

- Figures are loaded from `../results/figures/`.
- The final 300-episode table is loaded from `../results/latex_final_comm_300_table.tex`.
- The training/evaluation setting table is loaded from `../results/latex_training_settings_table.tex`.
- Runtime and checkpoint reports are stored in `../docs/runtime_environment_report.md` and `../docs/checkpoint_inventory.md`.
- References are stored in `references.bib`.
- This is a research draft, not a journal-specific template yet.
- Current Codex runtime check: `xelatex`, `latexmk`, and `bibtex` are not on PATH, so PDF rendering was not verified here.
- Static LaTeX project check passed in the current Codex runtime with 14 checked TeX inputs.
