# Final Single-Paper Scope

Last updated: 2026-07-24

## Controlling Update

The controlling final plan is now:

> `docs/FINAL_Q1_SINGLE_PAPER_PLAN.md`

If this older scope file conflicts with `docs/FINAL_Q1_SINGLE_PAPER_PLAN.md`, follow `docs/FINAL_Q1_SINGLE_PAPER_PLAN.md`.

The important update is:

- the project still produces one paper;
- the target is now Q1 attempt with Q2 fallback;
- the 3DOF 3v1 strict-sensing relay-failure task remains the main statistical evidence;
- HAPPO is a priority external strong baseline attempt for Q1 credibility;
- 4v2/5v2 rule-red and LAG/JSBSim replay are Q1-supporting supplements, not full new training projects;
- P0 scientific-validity hardening must precede any million-step formal training.

## Decision

This project will produce one paper, not a sequence of loosely connected papers.

The paper should be written as a high-quality Q2 submission candidate with a Q1 stretch target. The project should not keep expanding indefinitely. All future experiments must either strengthen the current paper's evidence chain or be rejected.

## Final Paper Target

Recommended title direction:

> Multi-Relation Role Graph Reinforcement Learning for Heterogeneous UAV Kill-Chain Recovery under Limited Communication and Intermittent Sensing

Chinese working title:

> 有限通信与间歇感知条件下异构无人机杀伤链恢复的多关系角色图强化学习方法

Core research question:

> When heterogeneous UAVs lose reliable sensing and a key relay node fails, can a perception-communication-task-support multi-relation role graph improve cooperative kill-chain recovery compared with no-graph, single-graph, and capacity-matched graph baselines?

## Final Claim Boundary

The paper may claim:

- a strict-sensing 3DOF heterogeneous UAV kill-chain recovery task;
- target-information bottleneck and relay-node failure as the main stressor;
- a multi-relation role graph separating perception, communication, and task-support relations;
- role-pair-conditioned message passing as the main mechanism;
- better recovery, tracking, timeout, and safety behavior than no-graph, single-graph, and parameter-matched single-graph baselines;
- mechanism evidence from ablations, seed-aware statistics, failure-aligned curves, and representative cases.

The paper must not claim:

- complete 4v2/5v2 red-blue air combat;
- full 6DOF training;
- real online missile/radar closed-loop validation;
- self-play or ELO as a contribution;
- topology curriculum as a primary contribution;
- `weaving_mild` as a final main result unless a revised protocol later passes its acceptance gate.

## Final Experiment Package

### Required Main Evidence

Already available and should be polished:

- Gate 1 fixed-update-60 main comparison:
  - `no_graph`;
  - `single`;
  - `multi_relation`.
- Five training seeds.
- 100 matched test episodes per seed.
- Strict sensing.
- Target-information bottleneck.
- `dropout030_relay_failure`.
- Seed-aware hierarchical bootstrap.
- Zero-collision reporting.

### Required Baseline Credibility

Already available and should be reported:

- no-graph MAPPO-style baseline;
- single-graph baseline;
- parameter-matched single-graph capacity-control baseline;
- model size and CPU inference latency.

### Required Mechanism Evidence

Use as paper-facing evidence:

- no-role-pair-gate ablation;
- hardened no-role-identity ablation;
- failure-aligned mechanism curves;
- representative median-rule recovery case.

Use as supporting evidence, not decisive proof:

- no-task-support relation ablation;
- no-curriculum diagnostic;
- scout-failure and delayed scout-failure diagnostics.

### Optional Scenario-Depth Evidence

`nominal weaving_mild` is currently diagnostic only.

Current frozen-protocol result:

- `no_graph`: 0.0% success;
- `single`: 14.0% success;
- `multi_relation`: 42.7% success.

Decision:

- do not expand this result to five seeds;
- do not tune on the `609000` test split;
- include only as a limitation or diagnostic if useful;
- do not use it as a main table.

### Optional Realism Supplement

For this single paper, the preferred realism supplement is a small LAG/JSBSim replay or interface-level feasibility check, not full 4v2/5v2 training.

Rationale:

- full 4v2/5v2 would open a new project and delay the paper;
- JSBSim replay, if feasible, can improve credibility without retraining all baselines;
- if LAG/JSBSim remains blocked, state it as future work and do not weaken the current paper.

Allowed supplement:

- replay one or a few successful 3DOF policy trajectories through a higher-fidelity interface;
- check command feasibility, altitude/speed envelopes, and attack-window consistency;
- use it as qualitative/appendix support only.

Not allowed:

- train all baselines in JSBSim;
- claim 6DOF validation without real reset/step evidence;
- add online missile/radar as a new main experiment.

## Stop Conditions

The experimental part is considered sufficient for the single paper when:

- Gate 1 main result tables are finalized;
- mechanism ablations and baseline credibility tables are finalized;
- failure-aligned figures and case study are finalized;
- manuscript claim wording matches the evidence boundary;
- reproducibility checks pass;
- PDF can be compiled and visually inspected;
- adviser/manual review does not identify a fatal missing baseline.

Do not add experiments merely because they are interesting.

## Recommended Final Execution Plan

### Phase A: Paper Package Closure

Priority: mandatory.

Tasks:

1. finalize English manuscript around the Gate 1 claim;
2. polish abstract, introduction, method, experiments, discussion, and conclusion;
3. make all tables and figures paper-facing;
4. remove outdated 2D or development-only claims from the active manuscript;
5. add data/code availability, funding, conflict-of-interest, and author placeholders;
6. choose target journal and migrate template;
7. compile PDF and inspect layout;
8. run final automated checks.

### Phase B: Final Evidence Audit

Priority: mandatory.

Tasks:

1. verify every numerical claim appears in exactly one source table;
2. build a final claim-to-evidence matrix;
3. mark each experiment as main, mechanism, supporting, diagnostic, or future work;
4. ensure `weaving_mild`, JSBSim, missile, radar, and 4v2 wording stays inside limitations/future work unless new evidence is added.

### Phase C: Optional Realism Check

Priority: optional.

Only run if Phase A and Phase B are stable.

Preferred route:

1. inspect current LAG/JSBSim blocker;
2. run minimal reset/step if data/submodule becomes available;
3. replay one representative policy command sequence;
4. report as qualitative feasibility only.

If this takes more than about one to two weeks, stop and submit without it.

## Final Quality Positioning

Q2 minimum route:

- Gate 1 main package plus strong writing and clean statistics.

Q1 stretch route:

- Gate 1 main package plus very polished mechanism explanation and, if feasible, a small realism supplement.

The final paper should be judged by evidence quality, not by system size.
