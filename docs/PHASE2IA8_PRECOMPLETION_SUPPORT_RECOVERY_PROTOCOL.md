# Phase 2IA8 amendment: pre-completion support recovery

**Amendment ID:** `PHASE2IA8-PSR-V1`  
**Status:** design frozen; no implementation, training, evaluation, or
canonical result is authorized by this document.  
**Prerequisite audit:** `PHASE2IA7_TERMINAL_SEMANTICS_AUDIT.md`

## 1. Why a new protocol is necessary

In the present environment, `chain_closed` is a **terminal mission-completion
flag**, not a nonterminal pre-failure state:

```text
support_t := (attack window) AND (tracking) AND (attacker has target-information chain)
attack_hold_t := consecutive support_t count
chain_closed_t := attack_hold_t >= 4
success_t := chain_closed_t
terminal_t := success_t OR adverse terminal OR horizon
```

Therefore a strict recovery study that waits for `chain_closed` before
injecting failure is semantically impossible. Phase 2IA8 introduces a new
pre-completion endpoint for a **new research task**. It does not revise,
replace, or reanalyse any historical v2 strict-recovery result.

## 2. New primary state variable

At every simulator timestep, log the exact Boolean that the existing
environment uses to increment `attack_hold` in non-v16 mode:

```text
chain_support_t =
  (max attack_window > 0.5)
  AND (mean detected_by > 0.0)
  AND (_comm_has_chain_to_attacker() is true)
```

`chain_support_t` is an observable task-execution support condition. It is
not `chain_closed`, success, return, or an operational proxy. The existing
`chain_closed` and mission success fields remain logged as separate terminal
events.

## 3. Pre-completion strict recovery endpoint

The endpoint applies only to a fresh Phase 2IA8 dataset.

```text
pre_failure_support_established
AND support_lost_after_failure
AND post_failure_support_recovered_after_loss
```

Definitions:

- `pre_failure_support_established`: `chain_support_t=1` for the two timesteps
  immediately preceding fault activation;
- `t_failure`: the first active relay-failure timestep;
- `t_loss`: first timestep at or after `t_failure` with `chain_support_t=0`;
- `t_recovery`: first subsequent timestep with `chain_support_t=1`;
- `delta_t_loss_to_recovery = t_recovery - t_loss`;
- `event=1` only for a recovery before censoring; an eligible loss without
  recovery is retained as a non-event/censored or adverse-terminal case
  according to a separately frozen terminal-event protocol.

This is intentionally a new endpoint name and schema. It must never be
reported as the older `chain_closed` strict recovery endpoint.

## 4. Triggered failure schedule

The following schedule is frozen before any Phase 2IA8 result:

1. start with relay agent 1 healthy;
2. detect the first pair of consecutive `chain_support_t=1` timesteps;
3. fail relay agent 1 at the immediately following timestep for 80 steps;
4. close eligibility if no such pair occurs by step 220, or if an episode
   terminates first;
5. do not inject a fixed-time fallback fault for an ineligible episode.

This guarantees fault occurs before the terminal four-step `chain_closed`
condition can be completed, while preserving the same support semantics used
by the task. It does not change reward, observation, communication, dynamics,
roles, training budget, or the completed-mission terminal rule.

## 5. Planned development-only feasibility ladder

No learned-policy comparison is permitted initially.

### P0 instrumentation/invariance gate

Add `chain_support_t` to the timestep trace and prove it exactly equals the
pre-existing internal condition that advances `attack_hold`. Demonstrate that
logging does not change an unmodified rollout.

### P1 pre-completion mechanism probe

Use fixed transparent controllers under the exact existing task configuration
to verify that the two-step support predicate and triggered-failure machinery
are observable. P1 must use new development-only seeds and must keep oracle
and legal-observation controllers separate. No learned policy/checkpoint is
used.

### P2 frozen-checkpoint observability probe

Only if P0 and P1 pass, replay the six archived Phase2IA4 final checkpoints,
with no training, to estimate whether the new pre-completion population is
observable for both arms. A preregistered adequacy gate must be frozen before
this replay.

### P3 new development training consideration

Only after P0/P1/P2 all pass may a distinct proposal consider new development
training. It must separately freeze task label, endpoint schema, seeds,
budget, checkpoint rule, and retention analysis. It remains non-canonical
until Architecture Freeze passes.

## 6. Integrity constraints

- Historical Phase2IA2/IA4/IA5/IA6 results remain archival and cannot be
  transformed into Phase2IA8 evidence.
- No method/seed selection, reward adjustment, scenario tuning, endpoint
  substitution, or primary-outcome change may follow P1/P2 outcomes.
- `chain_support_t` must be computed within the environment and emitted before
  it is consumed by any evaluator; it cannot be reconstructed from success.
- Phase 3A remains **NO-GO** until a separately documented architecture and
  evidence decision.

## 7. Current authorization

This amendment authorizes only P0 implementation, unit/invariance tests, and
a separate P0 audit/launch record. It authorizes neither P1 execution nor any
training.
