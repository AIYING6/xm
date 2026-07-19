# Gate 1 Safety Fixed-Update-60 Method-Component Audit

Last updated: 2026-07-19

## Purpose

This audit classifies each major project component according to how it should appear in the active manuscript. The goal is to keep the contribution claim narrow and defensible.

## Component Classification

| Component | Classification | Current manuscript location | Evidence | Required wording |
|---|---|---|---|---|
| Strict-sensing 3DOF relay-failure task | Experimental task contribution | Problem, Experiments | Fixed-update-60 main comparison | Claim as the task setting and evaluation protocol. |
| Post-failure kill-chain recovery metrics | Experimental/evaluation contribution | Problem, Experiments | Main table, mechanism curves | Claim as task-specific evaluation metrics. |
| Multi-relation graph with perception/communication/task-support relations | Method contribution | Method | Main comparison, ablations | Claim as core method. |
| Role-pair-conditioned message propagation | Method contribution | Method | `no_role_pair_gate` ablation | Claim as core mechanism; strongest ablation support. |
| Task-support relation | Method component | Method | `no_task_support` ablation | Claim as part of method, but describe ablation as supportive/mixed. |
| Centralized critic / decentralized actor | Standard MARL setup | Method, Related work | Established MAPPO framing | Present as setup, not novelty. |
| Target-cache TTL/confidence | Environment hardening | Problem/Experiments if needed | Gate 1 tests and strict protocol | Mention as realism/hardening, not novelty. |
| Graph target hiding under strict sensing | Environment hardening | Experiments if needed | Gate 1 tests | Mention as information-boundary enforcement, not novelty. |
| Post-step message/failure timing | Environment hardening | Protocol docs; optional in paper | Gate 1 tests | Mention only if discussing reproducibility. |
| Proximity safety penalty | Training auxiliary | Experiments | Collision audit/safety route | State as safety auxiliary, not innovation. |
| Behavior cloning warm start | Training aid | Method only if necessary | Existing source policy | Keep out of contributions. |
| Reward shaping | Training aid | Method only if necessary | Training implementation | Keep out of contributions. |
| Topology randomization/curriculum | Training protocol | Method, Discussion | No `no_curriculum` ablation | Describe as training protocol; do not claim isolated causality. |
| Fixed `update_0060` checkpoint rule | Evaluation protocol | Experiments | Current paper package | State clearly; do not mix with validation-selected results. |
| Failure-aligned curves | Analysis method | Experiments | Mechanism figure | Use as explanation, not as independent performance metric. |
| Representative matched case | Qualitative illustration | Experiments | Median-positive case rule | Use only as interpretation. |

## Required Manuscript Guardrails

- Contribution list should contain only three items:
  1. strict-sensing 3DOF kill-chain recovery task;
  2. multi-relation role graph with role-pair-conditioned message propagation;
  3. five-seed fixed-budget evidence chain.
- Do not list topology curriculum, BC warm start, reward shaping, safety penalty, TTL/confidence caches, or post-step timing as contributions.
- Use `no_role_pair_gate` as the primary mechanism ablation.
- Use `no_task_support` as supportive evidence with seed heterogeneity.
- State the fixed checkpoint rule wherever the main result is introduced.

## Current Manuscript Status

Checked and aligned:

- `paper_latex_3d_en/main.tex`
- `paper_latex_3d_en/sections/01_introduction.tex`
- `paper_latex_3d_en/sections/04_method.tex`
- `paper_latex_3d_en/sections/05_experiments.tex`
- `paper_latex_3d_en/sections/06_discussion.tex`
- `paper_latex_3d_en/sections/07_conclusion.tex`

Remaining paper-quality work:

- Related work still needs stronger citation coverage for graph MARL, communication-limited MARL, and UAV air-combat decision learning.
- Method section still needs fuller equations and implementation details before submission.
- Problem section may need a formal metric definition block for recovery, chain closure, tracking, and attack window.
