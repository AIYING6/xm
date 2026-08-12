# 3DOF English LaTeX Draft

This is the only maintained manuscript source for the 3DOF EA-RG-MAPPO-S study.

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

The maintained tables and figures are under `../results/`.

## Static Check

From the repository root:

```bash
python scripts/check_latex_project.py
```

PDF rendering is not guaranteed in the Codex runtime because a TeX distribution may be unavailable.
