# Phase 2IA5 amendment: eligibility-triggered failure diagnostic

**Amendment ID:** `PHASE2IA5-ETF-V1`  
**Status:** frozen DEVELOPMENT_ONLY amendment; no training is authorized by this document.  
**Branch:** `scientific_recovery_v2`  
**Predecessor:** Phase 2IA4 V0 risk-set adequacy failure.

## 1. Motivation and boundary

Phase 2IA4 used four fixed clock-time relay failures and correctly found a
zero strict-risk set in both arms. Independent timestep reconstruction showed
that this was not an evaluator error: most episodes had not established the
required chain before the fixed fault was observed. The relevant question is
therefore currently confounded between:

1. whether the policy can establish the pre-failure chain; and
2. conditional on such a chain, whether it recovers after the relay fault.

This amendment creates a **development diagnostic only** that separates those
two properties without changing the strict recovery definition. It is not a
canonical evaluation protocol, not a headline result, and cannot be used to
replace Phase 3A evidence.

## 2. Unchanged invariants

The following remain fixed:

- arms: `full_gate` and `no_role_gate` only;
- development seeds: `101`, `202`, `303` only;
- strict endpoint: `pre_failure_chain_established AND chain_lost_after_failure
  AND post_failure_chain_recovered_after_loss`;
- primary duration: `delta_t_loss_to_recovery = t_recovery - t_loss`;
- relay identity, failure duration (80 steps), observation, communication,
  reward, architecture, training configuration, and fixed-final checkpoint
  rule;
- no canonical seed, test scenario, result, survival headline analysis,
  checkpoint promotion, resume, early stopping, or seed exclusion.

No existing Phase 2IA4 raw output is overwritten.

## 3. Eligibility-triggered failure semantics

For each fresh deterministic development episode, evaluation starts with no
relay fault. Let `chain_closed(t)` be the already-frozen evaluator chain
predicate. Define an eligibility trigger at the first timestep `t*` for which
`chain_closed(t*-3), ..., chain_closed(t*)` are all true. The four-step hold is
pre-specified to match the existing `attack_hold_steps=4` persistence unit; it
was not selected from this amendment's results.

If this trigger occurs, relay agent 1 fails beginning at timestep `t* + 1` for
the fixed 80 steps. The pre-failure state is therefore observed, and ordinary
post-failure strict loss/recovery accounting begins at that activation step.

If no trigger occurs by timestep 220, or the episode terminates before it,
the episode is labelled `not_eligible_before_cap`; no fault is injected and it
is outside the strict-risk set. This is a first-class feasibility outcome, not
a censored recovery and not a failure of recovery. Fault injection is therefore
conditional on the same observable predicate for each arm, while each arm's
eligibility rate is retained rather than hidden.

This timing change is deliberately isolated here. It must not be retrofitted
onto any historical or canonical result.

## 4. Fixed diagnostic evaluation suite

The first action is a **checkpoint-only E0 feasibility evaluation**, using the
six archived Phase 2IA4 final checkpoints. It creates no new checkpoints and
starts no training.

- 100 deterministic episodes per arm × seed (600 episodes total);
- `target_policy=straight`, communication dropout `0.30`, message delay `2`,
  and all remaining Phase 2IA4 evaluation settings unchanged;
- development episode ID:

  ```text
  510000 + 10000 * seed + episode_index
  ```

  IDs are deliberately paired across arms and are unique with `(arm, ID)`.
- raw episode records and timestep trace records are mandatory;
- all evaluations use the fixed final actor/critic checkpoint supplied by the
  Phase 2IA4 completion audit.

## 5. E0 pre-result gate

E0 is assessed independently for each arm. It passes only when all are true:

1. at least 40 of 300 episodes become fault-eligible;
2. eligible episodes occur in at least two development seeds;
3. at least two seeds each contribute at least 10 eligible episodes;
4. at least one eligible episode has an observed post-failure chain loss; and
5. raw/trace coverage is complete and independently reconstructed endpoint
   fields match evaluator fields exactly.

E0 measures whether strict recovery can be observed at all. It does not use
success, return, operational first establishment, telemetry, or a performance
contrast as a substitute. If E0 fails in either arm, Role-Gate retention stays
`UNRESOLVED`; no Role-Gate efficacy conclusion and no further Phase 2IA5
training may be started automatically.

## 6. Consequences after E0

If E0 passes in both arms, a separate pre-result document must freeze any
subsequent development training budget and the V1 strict-risk adequacy rule
before that training can begin. That document may not alter this endpoint,
eligibility trigger, seed set, arm set, or checkpoint rule in response to E0
outcomes.

If E0 fails, the next action is a root-cause audit of the failed E0 condition,
not broader architecture search, seed expansion, endpoint substitution, or
canonical training.

## 7. Current decision

This amendment authorizes only the implementation and smoke validation of an
E0 executor. It does **not** authorize E0 execution until that executor has a
separate audit, deterministic replay test, schema test, and a committed launch
record. Phase 3A remains **NO-GO**.
