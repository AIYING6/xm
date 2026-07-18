# 3DOF English LaTeX Draft

This directory is the separate 3DOF manuscript path for the heterogeneous UAV kill-chain recovery study.

It does not replace the older 2D LaTeX drafts in `paper_latex/` or `paper_latex_en/`.

## Main File

```text
main.tex
```

## Current Scope

- 3DOF scout-relay-attacker cooperative interception.
- Multi-relation role graph policy.
- Relay-failure kill-chain recovery as the main claim.
- Task-support and role-pair-gate ablations as mechanism evidence.
- Strict intermittent sensing as a budget-labeled scenario-depth pilot.

## Figures

The draft uses generated figures from:

```text
../results/figures/
```

The maintained figure inventory is:

```text
../docs/intercept_3d_manuscript_figures.md
```

## Static Check

From the repository root:

```bash
python scripts/check_latex_project.py
```

PDF rendering is not guaranteed in the Codex runtime because a TeX distribution may be unavailable.
