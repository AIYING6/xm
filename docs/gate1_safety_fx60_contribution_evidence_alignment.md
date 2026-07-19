# Gate 1 Safety Fixed-Update-60 Contribution-Evidence Alignment

Last updated: 2026-07-19

## Purpose

This document maps the active manuscript contributions to the exact evidence that supports them. It is intended to prevent overclaiming and to guide later manuscript revisions.

## Contribution Alignment Table

| Manuscript contribution | Evidence status | Main support | How to write it | What not to claim |
|---|---|---|---|---|
| Strict-sensing 3DOF heterogeneous UAV kill-chain recovery task | Supported | `paper_latex_3d_en/sections/03_problem.tex`; `paper_latex_3d_en/sections/05_experiments.tex`; Fig. `fig:gate1_safety_fx60_mechanism` | A 3v1 3DOF task is constructed to study post-failure kill-chain recovery under limited communication and intermittent sensing. | Do not claim full 4v2 red-blue combat or 6DOF operational fidelity. |
| Multi-relation role graph with perception, communication, and task-support relations | Supported | Method section; main comparison table `tab:gate1-safety-fx60-main`; full vs single/no-graph bootstrap table | Separating relation semantics improves recovery compared with no-graph and single-graph baselines. | Do not claim every relation channel is individually decisive. |
| Role-pair-conditioned message propagation | Strongly supported | `no_role_pair_gate` ablation; table `tab:gate1-safety-fx60-ablation`; bootstrap table `tab:gate1-safety-fx60-bootstrap` | Removing role-pair gating reduces recovery from `88.6%` to `64.8%`, with a positive seed-aware recovery interval. | Do not claim role-pair gating is the only necessary mechanism. |
| Dynamic task-support relation | Supportive but mixed | `no_task_support` ablation; table `tab:gate1-safety-fx60-ablation`; seed-level recovery list | Removing task-support lowers mean recovery from `88.6%` to `64.8%`, but the seed-aware interval crosses zero. | Do not describe this ablation as statistically decisive. |
| Robust post-failure recovery under relay failure | Strongly supported | Main table; seed-aware deltas; mechanism curves; representative case | Full method achieves `88.6%` recovery versus `53.2%` single-graph and `21.8%` no-graph under matched fixed-budget evaluation. | Do not generalize to all communication and sensing failures. |
| Safety-compatible behavior | Supported in current scenario | Collision metrics in main and ablation tables | Full method has zero test collisions in the fixed-update-60 relay-failure evaluation. | Do not claim formal flight safety certification. |
| Failure-aligned mechanism explanation | Supported | `results/gate1_safety_fx60_mechanism/`; `docs/gate1_safety_fx60_mechanism/failure_aligned_mechanism_summary.md` | The full method preserves higher tracking and accumulates recovery faster despite connectivity collapse. | Do not use one representative case as standalone proof. |
| Topology curriculum / randomized topology training | Training protocol only | Method section; `docs/gate1_safety_fx60_no_curriculum_decision.md` | Use as a training protocol that exposes policies to communication variation and node failure. | Do not claim isolated curriculum causality unless `no_curriculum` is completed. |

## Recommended Contribution Wording

Use three paper contributions:

1. We formulate a strict-sensing 3DOF heterogeneous UAV kill-chain recovery task with relay-node communication failure and post-failure recovery metrics.
2. We propose a multi-relation role graph policy with perception, communication, task-support relations, and role-pair-conditioned message propagation for decentralized actors.
3. We provide a five-seed fixed-budget evidence chain showing improved relay-failure recovery over no-graph and single-graph baselines, supported by seed-aware bootstrap, mechanism ablations, and failure-aligned analysis.

## Components Classification

| Component | Classification | Paper handling |
|---|---|---|
| Multi-relation graph | Claimed method contribution | Main method and baseline comparison |
| Role-pair message gate | Claimed method contribution | Primary mechanism ablation |
| Task-support relation | Method component | Supportive ablation, cautious wording |
| Strict target sensing | Experimental realism constraint | Core scenario setting |
| Target-cache TTL/confidence | Environment hardening | Mention in protocol, not innovation |
| Proximity safety penalty | Training support | Mention as safety auxiliary, not innovation |
| BC warm start | Training aid | Do not claim as innovation |
| Reward shaping | Training aid | Do not claim as innovation |
| Topology randomization/curriculum | Training protocol | Do not claim isolated causality yet |
| Fixed update-60 checkpointing | Evaluation protocol | State clearly to avoid selection ambiguity |

## Current Evidence Gaps

- No `no_curriculum` ablation.
- No 4v2 red-blue scenario.
- No online missile closure.
- No high-fidelity radar model.
- No 6DOF JSBSim replay validation.
- No mild maneuvering target result promoted into the current paper package.

These gaps are acceptable only if the manuscript remains framed as a 3DOF mechanism study.
