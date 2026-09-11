# P40 topology-transfer value: pre-training novelty and identifiability gate

## Status

**NOT AUTHORIZED FOR TRAINING.** This record preserves the decision made before
any new environment, sampler, or long-horizon run is created.

## Candidate question

Given a fixed, finite library of legal topology-degradation conditions and a
fixed training budget, can training exposure be allocated according to the
*cross-condition transfer value* of each topology intervention, rather than its
current within-condition difficulty alone?

The question is narrower than generic domain randomization: the interventions
are discrete, information-legal communication/topology changes in a cooperative
task. It is nevertheless not novel merely because it changes the sampling
distribution.

## Why the first formulation is insufficient

The initial proposal, called topology intervention value allocation (TIVA),
would estimate a condition value and reweight reset-time sampling. That generic
description collides with established work on active domain randomization,
learned randomization distributions, and robust/minimax environment
distribution optimization. It cannot be launched as a distinct algorithmic
contribution on that basis alone.

Relevant collision sources:

- Active Domain Randomization selects informative environment variations from a
  predefined range using rollout discrepancies: Mehta et al., CoRL 2020,
  <https://proceedings.mlr.press/v100/mehta20a.html>.
- Monotonic Robust Policy Optimization jointly optimizes policy and sampling
  distribution for average and worst-case environment performance: Jiang et
  al., ICML 2021, <https://proceedings.mlr.press/v139/jiang21c.html>.
- Flow-based Domain Randomization learns a sampling distribution for robust
  robotic policies: Curtis et al., ICML 2025,
  <https://proceedings.mlr.press/v267/curtis25a.html>.

These sources are a novelty screen, not evidence about the local task.

## Only viable differentiator to audit

A new line remains potentially distinguishable only if it estimates a **directed
topology-transfer matrix**:

\[
T_{g \rightarrow h}=\text{out-of-fold change in endpoint proxy on condition }h
\text{ after a matched update induced by training condition }g.
\]

The sampler would then solve a coverage allocation problem over the *recipient*
conditions, rather than prioritize a source condition solely because it is hard,
low-return, or informative. This must use common-random-number probes and a
training-side validation split. The final OOD tape remains sealed and never
appears in a training update or allocation score.

This formulation is not yet a contribution. It earns a method contract only if
the gates below pass.

## Required zero-training gates

| Gate | Required observation | Failure consequence |
| --- | --- | --- |
| G1 task band | Nominal UTR learns above a prespecified floor; at least one fault condition degrades performance without global timeout collapse | Stop: no meaningful robustness allocation problem |
| G2 intervention heterogeneity | A matched, read-only update/probe audit shows non-constant rows of \(T\); uncertainty must be reported | Stop: all conditions are exchangeable for the proposed purpose |
| G3 decision relevance | Maximin coverage based on \(T\) selects a distribution materially different from uniform, DRTP difficulty weighting, and hardest-first | Stop: transfer scoring adds no decision |
| G4 leakage exclusion | Source/recipient probe split, random-number tape, and final OOD tape are disjoint and machine-audited | Stop: invalid generalization claim |
| G5 causal ablation | Predeclared arms can isolate transfer-aware allocation from difficulty weighting and random reweighting while holding policy, reward, support and budget fixed | Stop: mechanism cannot be identified |
| G6 literature distinction | Focused review finds no directly equivalent discrete structured-intervention transfer-matrix curriculum with the same allocation target | Stop or substantially reformulate |

## Minimum future causal design, conditional on all gates passing

1. UTR: uniform exposure over the frozen support.
2. DRTP: existing difficulty-driven bounded allocation.
3. Random-transfer control: identical update cadence and constraints, but
   source-to-recipient transfer labels permuted once before training.
4. Transfer-aware allocation: bounded maximin allocation driven by the audited
   training-side transfer matrix.

All arms must share the policy, PPO objective, observations, actions, reward,
environment transition, total exposure, nominal mass, seed registry, endpoint,
and final evaluation tape. Training seeds remain the independent unit.

## Claims allowed if the line passes

At most: the new allocation rule improved predeclared endpoint metrics under the
evaluated topology suite, and its transfer-matrix telemetry documented a
different allocation rationale from difficulty-only reweighting.

Not allowed: universal topology generalization, causal recovery of missing
information, safety guarantees, or a claim that any single matrix entry caused
the policy behavior.

## Immediate next action

Implement no method. First perform G1--G3 as a short, deterministic,
read-only-or-micro-update audit with a sealed final endpoint tape. The audit
must emit `P40_GATE_PASS` only when every gate is satisfied; otherwise it emits
`P40_STOP` and no long training may start.
