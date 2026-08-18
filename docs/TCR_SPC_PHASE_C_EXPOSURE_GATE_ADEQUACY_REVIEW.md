# TCR/SPC Phase-C Exposure-Gate Adequacy Review

- Review type: zero-training, zero-re-evaluation protocol review
- Historical Phase-C v1 decision: permanently retained as TECHNICAL INVALID
- Frozen forensic input: 18,000 raw records; 69 unexposed episodes; 69/69 natural pre-trigger collision; evaluator/trigger defects 0; unresolved 0
- Decision: B — ALL_EPISODE_EXPOSURE_GATE_CONFLATES_POLICY_TERMINATION_WITH_EVALUATOR_VALIDITY

## Scope and non-actions

This review does not train, re-evaluate, alter checkpoints, alter TCR/SPC/UTR, alter PPO, start 3M, use held-out or canonical seeds, delete episodes, or rewrite the Phase-C v1 decision.

The 69 pre-trigger collision episodes remain part of every performance and safety population.

## Frozen estimands

Let F_sched be all scheduled failure episodes for a method × seed × condition cell.

### Estimand 1: evaluation-trigger validity

Define the onset risk set:

R = { i in F_sched : i is alive immediately before the scheduled onset }.

Operationally, under the archived evaluator step semantics, this is the set with terminal_step >= scheduled_onset.

The trigger-validity quantity is:

V_trigger = number of episodes in R with failure active / |R|.

This quantity tests whether the evaluator/trigger works when an episode reaches the intervention boundary. If |R| = 0, trigger validity is not estimable for that cell and must be reported as such; it must not be silently treated as a successful or failed evaluator.

### Estimand 2: policy performance and safety

All scheduled failure episodes remain in the unconditional population:

all-episode J = sum(J_i for i in F_sched) / |F_sched|.

The same all-episode population is used for overall nominal/F0/OOD returns and safety reporting. Required diagnostics include:

- collision rate;
- pre-trigger collision rate;
- timeout rate;
- constraint-violation rate;
- fraction surviving to onset, |R| / |F_sched|;
- trigger exposure among onset survivors, V_trigger.

A pre-trigger collision is therefore a policy safety/performance outcome, not an evaluator failure.

## Answers to Q1–Q5

### Q1 — Does all-episode exposure conflate two quantities?

Yes.

exposed / all scheduled failures mixes:

1. whether a policy survives long enough to encounter the scheduled intervention; and
2. whether the evaluator correctly triggers the intervention after the episode reaches onset.

The forensic audit demonstrates the distinction: all 69 failures were scheduled, but all 69 terminated by collision before onset. The archived evidence contains no episode that survived to onset while failing to trigger. Thus the low all-episode exposure is not evidence of evaluator invalidity.

### Q2 — How should a pre-onset collision be interpreted?

As a policy outcome.

It is a collision before the scheduled failure, so it is relevant to safety, nominal competence, unconditional mission performance, and pre-trigger termination. It is not an evaluator defect because the scheduled failure had no opportunity to occur.

It must remain in the overall denominator and must never be deleted, censored, relabelled as exposed, or silently moved into a post-failure analysis.

### Q3 — Should conditional failure-robustness analysis use the onset risk set?

Yes.

Any claim specifically about response after the scheduled topology perturbation should use the onset risk set R, because only those episodes actually reach the perturbation boundary. The conditional analysis must report |R|, survival fraction, and trigger validity beside every conditional estimate.

The unconditional all-episode analysis remains mandatory and is not replaced by the risk-set analysis.

### Q4 — How do we prevent artificial improvement through pre-trigger termination?

The v2 contract must impose the following safeguards:

1. report all-episode nominal/F0/OOD performance and all safety metrics;
2. report pre-trigger collision and pre-trigger termination separately;
3. report onset-risk-set size for every method × seed × condition cell;
4. report V_trigger only among episodes in R;
5. never rank a method using conditional post-failure performance alone;
6. treat an empty or extremely small risk set as an estimand-adequacy warning, not as evidence of robustness;
7. preserve the original catastrophic-seed, safety, and seed-consistency rules;
8. require the same tape, checkpoints, conditions, and paired episode IDs for every method;
9. make every conditional aggregate auditable against the complete raw episode table.

A policy that collides before onset cannot obtain a free robustness advantage: its collision and pre-trigger termination remain visible in the unconditional result. Conditional analysis describes post-onset behavior; it does not erase the cost of failing to reach onset.

This review does not introduce a new favorable numerical threshold. Any future risk-set adequacy threshold must be frozen prospectively before a new authorized analysis and must apply symmetrically to all methods.

### Q5 — Must the original Phase-C v1 TECHNICAL_INVALID remain?

Yes.

The v1 result is an immutable historical conclusion under the v1 contract, whose all-episode exposure gate was not satisfied. The later estimand review does not retroactively change the v1 decision and does not convert it to GO.

## Decision

B — ALL_EPISODE_EXPOSURE_GATE_CONFLATES_POLICY_TERMINATION_WITH_EVALUATOR_VALIDITY

The original all-episode gate is not scientifically suitable as the sole technical-validity condition when policy termination can occur before scheduled onset.

A prospective v2 contract is therefore created. It changes only the exposure-validity estimand and diagnostic reporting contract; it does not change any algorithm, checkpoint, PPO setting, environment, reward, failure semantics, or historical result.

## Stop rule

After creating the prospective v2 contract, stop. No 1M re-analysis, 3M continuation, held-out evaluation, canonical evaluation, training, or algorithm modification is authorized by this review.

## Provenance

- docs/TCR_SPC_PHASE_C_FAILURE_EXPOSURE_FORENSIC_AUDIT.md
- docs/TCR_SPC_PHASE_C_1M_STABILITY_SCREEN_CONTRACT.md
- Historical Phase-C decision: TECHNICAL INVALID
