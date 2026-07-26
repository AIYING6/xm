# Current Requirements

Last updated: 2026-07-24

## Research Target

The project target is one Q1-level submission attempt, while preserving a realistic Q2 fallback if the expanded evidence chain is not strong enough.

The controlling plan is `docs/FINAL_Q1_SINGLE_PAPER_PLAN.md`. If older requirements conflict with that file, follow `docs/FINAL_Q1_SINGLE_PAPER_PLAN.md`.

The current core problem is:

> Heterogeneous UAV kill-chain recovery under limited communication, intermittent sensing, and key functional-node disruption.

The current main claim should remain focused:

> A perception-communication-task-support multi-relation role graph improves post-failure kill-chain recovery probability and robustness under strict intermittent sensing.

For the Q1 attempt, this claim must be upgraded from a graph-structure result to a communication-feasible mission-chain resilience result. The final implementation sequence is recorded in `docs/FINAL_Q1_SINGLE_PAPER_PLAN.md`.

## Scope Boundary

Do not immediately expand into a large all-in-one system. The near-term work should not prioritize:

- full 4v2/5v2 self-play;
- ELO as a contribution;
- full 6DOF retraining;
- online missile closed-loop training;
- high-fidelity radar modeling;
- JSBSim training for every baseline.

These can be later validation or enhancement modules after the 3DOF main evidence is stable. A small 4v2/5v2 rule-red extension and small LAG/JSBSim replay are now required Q1-supporting supplements, but they must not become full new training projects.

## Immediate P0 Requirements

Before any million-step training:

- replace magic-number observation slices with a documented observation schema;
- verify or correct the `no_role_identity` actor observation slice;
- remove global attack-chain progress from actor graph inputs;
- keep attack-chain progress available to centralized critic and metrics;
- add actor information-boundary tests;
- mark pre-hardening results that violate these rules as development evidence only.

## Current Implementation Goal

First make the 3DOF strict-sensing relay-failure line solid:

- `no_graph`: MAPPO-style no-message-passing baseline;
- `single`: single union-graph GAT-MAPPO baseline;
- `multi_relation`: proposed EA-RG-MAPPO-S baseline;
- same behavior-cloning initialization protocol;
- same PPO topology curriculum;
- same validation checkpoint selection;
- same disjoint test split;
- seed-aware statistics.

## Immediate Next Work

Q1 priority:

> Do not expand to 5v2 or launch five-seed formal training until Gate 1 in `docs/Q1_EXECUTION_PLAN.md` passes.

Gate 1 focuses on information realism:

- actor-side information isolation;
- task-support edges cannot bypass physical communication;
- graph direction convention;
- real delayed message delivery;
- communication-subsystem failure wording and metrics;
- CTDE separation between actor and critic.

The current bottleneck dropout-relay protocol remains the mechanism baseline and must be used as a regression target after Gate 1 changes.

The fair-baseline path now has a meaningful three-seed development diagnostic. Using existing `single` / `multi_relation` sources and newly trained `no_graph` sources, strict-sensing relay-failure test recovery was:

- `multi_relation`: `100.0%`;
- `single`: `93.3%`;
- `no_graph`: `40.0%`.

Therefore the next step is:

> Choose the formal `no_graph` source policy, then run a longer strict-sensing fair checkpoint-budget diagnostic before launching a five-seed formal run.

The current result is strong enough to justify moving forward, but it is not yet a final paper result because the strict-sensing fine-tuning budget and evaluation episode count remain small.

Seed-aware bootstrap has already been run for this three-seed diagnostic. It strongly separates `multi_relation` from `no_graph`, but only weakly separates `multi_relation` from `single`, so the near-term paper claim should be conservative.

A 50-episode source audit confirmed that `no_graph` seed 2 is genuinely weak. Formal reporting must avoid selectively replacing that seed after seeing test results; either retain all seeds and report variance, or retrain all `no_graph` seeds with one stronger standardized budget.

The 30-update diagnostic keeps this interpretation: `multi_relation` is clearly better than `no_graph`, while `single` remains close. Before five-seed formal training, identify a harder but still feasible strict-sensing setting that avoids saturation of `single`.

Checkpoint-only probes show that simply making the scenario harder is not enough. `weaving_mild` is too hard, reduced communication range remains saturated for graph methods, and radar dropout does not separate `multi_relation` from `single`. The next improvement should make task-support relations necessary, not just increase generic difficulty.

The best current scenario candidate is `communication_dropout0.30 + relay_failure + strict_target_sensing`. It separates `multi_relation` from both `single` and `no_graph` in checkpoint-only probing. Before making paper claims, checkpoint selection must be rerun with dropout-relay validation episodes and disjoint dropout-relay test episodes.

The first dropout-relay validation/test diagnostic has now been run. It still separates graph methods from `no_graph`, but it does not strongly separate `multi_relation` from `single` at 30 updates. The next evidence-building step should be a longer dropout-relay training/checkpoint diagnostic or a clearer task-support bottleneck, not immediate five-seed formal expansion.

The 60-update dropout-relay diagnostic improves the average `multi_relation - single` recovery delta only modestly and still has a confidence interval crossing zero. Therefore the project should now prioritize task-support bottleneck design over brute-force seed expansion.

The first agent target-information bottleneck probe produced a separated `multi_relation` vs `single` signal. Treat this as the current highest-priority quality-improvement route, but rerun validation selection with the bottleneck enabled before making paper claims.

Bottleneck-enabled validation selection and disjoint testing now preserve the separated signal. The next formalization step is to add `no_graph` under the same protocol, then expand to five seeds only after the three-method ordering is stable.

The three-method bottleneck protocol now has a stable development ordering: `no_graph < single < multi_relation`. This is the current best candidate for Q2-level main evidence. Five-seed expansion should use this frozen protocol, not the earlier straight relay-failure setup.

## Paper-Quality Upgrade Path

1. Stabilize the 3v1 strict-sensing relay-failure experiment.
2. Complete fair `no_graph` / `single` / `multi_relation` baselines.
3. Expand to five independent training seeds.
4. Add recovery-process explanation figures and seed-aware statistics.
5. For Q1 ambition, add a rule-based escort or jammer so the problem becomes adversarial kill-chain disruption, not only internal relay failure.
6. Add unseen disruption generalization.
7. Add JSBSim / LAG / missile-envelope replay as final feasibility validation, not as the main training backend.

## Claim Discipline

Do not claim reward shaping, rules, ELO, or curriculum scheduling alone as the main innovation.

Main contribution candidates:

- strict-sensing kill-chain recovery task definition;
- perception-communication-task-support multi-relation role graph;
- role-pair-conditioned message passing;
- topology curriculum as a supporting training mechanism;
- recovery probability, restricted recovery time, message age, tracking, and chain-closure metrics.

## Current Risk

The project is not yet at final paper-experiment quality. The main risks are:

- fair baselines are not yet trained at formal budget;
- current `no_graph` baseline is newly added and one source seed is weak;
- long-step convergence is not yet known;
- current Q1-level environmental complexity is insufficient without adversarial escort/jamming or stronger generalization evidence.
