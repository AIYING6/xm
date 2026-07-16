# AGENTS.md

## Project Overview

This repository studies heterogeneous UAV cooperative decision-making under limited communication and intermittent sensing.

Current research line:

- Phase-1 baseline: 2D heterogeneous UAV pursuit/interception.
- Phase-2 target: 3DOF heterogeneous UAV cooperative interception with sensing, communication, message age, and attack-window metrics.
- Main method: `EA-RG-MAPPO-S` = Edge-Aware Role Graph MAPPO + staged topology/curriculum training.

Core directories:

- `envs/`: simulation environments and graph adapters.
- `algorithms/`: MAPPO, GAT-MAPPO, and RI/EA-RG-MAPPO implementations.
- `scripts/`: training, evaluation, plotting, smoke tests, and reproducibility gates.
- `results/`: generated experiment outputs, checkpoints, tables, figures, and audits.
- `docs/`: project state, paper drafts, evidence chain, and reproducibility documentation.
- `paper_latex/`, `paper_latex_en/`: Chinese and English LaTeX manuscripts.

## Engineering Rules

- Do not delete or rewrite the existing 2D evidence chain to make new 3DOF work pass.
- Keep rules, masks, reward shaping, demonstrations, ELO, and JSBSim as auxiliary mechanisms, not primary claimed innovations.
- Prefer adding a new environment or adapter over breaking an existing training/evaluation interface.
- Preserve the standard environment interface:
  - `reset() -> obs, share_obs, graph_obs`
  - `step(actions) -> obs, share_obs, graph_obs, rewards, dones, infos`
- For new environments, include a smoke test before connecting training.
- For new result CSVs, add schema, provenance, and artifact-gate entries when the file becomes part of the maintained evidence chain.
- Keep project memory in repository files, not in chat history.

## Validation

Use the configured `cac` environment when available:

```bash
D:/Anaconda/envs/.conda/envs/cac/python.exe
```

Minimum checks after environment or evidence-chain changes:

```bash
python scripts/smoke_test_env.py
python scripts/smoke_test_intercept_3d_env.py
python scripts/build_paper_assets.py
python scripts/check_reproducibility_artifacts.py
```

If a change only touches documentation, run the smallest relevant generator/check instead of full training.

## Completion Standard

A task is complete only when:

- the intended code or document change is present;
- relevant smoke tests or gates pass;
- maintained docs are updated when project state changes;
- the final response states what changed, what was verified, and any remaining risk.
