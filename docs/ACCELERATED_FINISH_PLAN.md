# Accelerated Finish Plan

Last updated: 2026-07-22

## Objective

Finish the current UAV MARL paper package as quickly as possible without weakening the evidence chain.

The project should now stop broad exploration and move into finish mode.

## Frozen Core Claim

Under strict intermittent sensing, limited communication, target-information bottleneck, and relay/scout node failure, a multi-relation role graph with role-pair-conditioned message passing improves kill-chain recovery reliability compared with no-graph and single-graph baselines.

## Frozen Contribution Boundary

Primary contributions:

1. strict-sensing node-failure kill-chain recovery task and metrics;
2. multi-relation role graph;
3. role-pair-conditioned message passing.

Not primary contributions:

- topology curriculum;
- reward shaping;
- rule-based guidance;
- ELO/self-play;
- JSBSim/6DOF replay;
- missile model.

These can be mentioned as training support, future work, or implementation context only.

## Evidence Package To Keep

Main evidence:

- fixed-update-60 five-seed safety package;
- no-graph, single-graph, full multi-relation comparison;
- seed-aware bootstrap;
- zero-collision full-method result.

Mechanism evidence:

- role-pair gate ablation as the cleanest mechanism result;
- task-support relation as supportive only;
- role identity as reliability support;
- parameter-matched single graph as capacity-control credibility;
- no-curriculum diagnostic as a boundary against overclaiming;
- seed-level mechanism figures.

Scenario-depth evidence:

- early relay-failure timing generalization;
- nominal `weaving_mild` as supporting scenario-depth evidence;
- delayed scout-failure stressor as supplemental screen, not main table.

## Stop Conditions

Do not start new training or new scenario variants unless all are true:

- the gap is reviewer-critical;
- the existing evidence cannot answer it;
- the new run has a fixed protocol before evaluation;
- the run can be completed within a small bounded budget.

## Remaining Work

1. Manuscript consistency pass
   - align abstract, introduction, method, and experiments with the frozen contribution boundary;
   - remove or soften claims about curriculum;
   - make stressors supplemental.

2. Figure/table package
   - include main result table;
   - include mechanism ablation table;
   - include seed-level scatter and bootstrap forest;
   - include timing-generalization table;
   - include model-cost table.

3. Reproducibility package
   - list exact scripts and result paths;
   - record frozen checkpoints;
   - add command snippets for regenerating tables/figures;
   - run static consistency checks.

4. Final experimental audit
   - verify no mixed checkpoint-selection protocols are silently combined;
   - verify all seed counts and episode counts are labeled;
   - verify all claims have a matching table or figure.

5. Draft-to-submission pass
   - compile LaTeX when a TeX toolchain is available;
   - inspect PDF layout;
   - tighten related work and limitations;
   - prepare cover letter / response-ready limitations notes.

## Practical Completion Standard

The project is ready for submission preparation when:

- the fixed evidence package is internally consistent;
- all paper figures and tables are generated from scripts;
- main claims do not exceed seed-aware statistics;
- no new experiment is needed to defend the primary contribution;
- the manuscript compiles cleanly or has only environment-specific LaTeX-toolchain blockers.
