# V8 branch-value task contract — 2026-09-14

## Status and evidence class

This note records a **development-only** task-identification repair.  It is
not paper evidence and must not be pooled with any earlier UAV or DRTP result.

## V7 G2 diagnosis

The frozen V7 plain-MAPPO development run (`83811–83813`) completed with
`V7_G2_NOT_YET_ESTABLISHED`.  All four public service-envelope profiles had
zero endpoint success and each policy selected reconstruction at both causal
decision stages.  The actor-decision mask was inspected: it correctly retained
only the relay's two causal actions in PPO.  The structural diagnosis is thus
not an ignored action or an invalid G0 controller.

The early authorisation action was uniformly correct across all four profiles:
it should retain the initial legal bridge.  Its benefit was delayed until a
later mission milestone, so V7 created a binary credit-assignment collapse
rather than a context-sensitive early choice.  This result forbids entropy,
learning-rate, bias, or seed sweeps on V7.

## V8 structural repair

V8 preserves the same plant, sensing and message transport, public envelope
observations, service reward, physical budget, route geometry, and safety
contract.  It changes only the macro decision interface:

1. Early authorisation is a compulsory public retain reservation.  It creates
   a legal service prerequisite but supplies no actor action or profile label.
2. At the public branch, both current- and future-value profiles must choose a
   route.  Retaining preserves authorised current service; reconstruction
   releases it and travels to the announced future route.
3. The correct branch action reverses by public envelope value: retain for
   current profiles and reconstruct for future profiles.  A mission cannot
   terminate before that branch decision.

This removes a uniform, delayed binary action while preserving a real
cooperative choice whose outcome changes legal task completion.

## G0 evidence

`scripts/audit_compositional_service_envelope_handoff_v8_g0.py` produced
`results/development/_v8_g0_branch_conflict_20260914/v8_g0_report.json` with
`V8_G0_BRANCH_VALUE_PASS` across six fixed seeds per profile:

- `current_compact` and `current_delayed`: always retain succeeds (1.0),
  always reconstruct fails (0.0);
- `future_fresh` and `future_durable`: always reconstruct succeeds (1.0),
  always retain fails (0.0);
- a public-envelope value rule succeeds in all four profiles.

The controller reads no profile identifier, target truth, peer-hidden state or
future manoeuvre truth.  It uses the same public envelope values emitted to
the actor.

## Frozen V8 G2 gate

`configs/commitment_handoff_v8_g2_freeze_20260914.json` fixes three
development seeds (`83911–83913`), 64 updates, four environments, 64 rollout
steps and 60 endpoint episodes per profile.  It is a capacity-controlled
plain MLP MAPPO gate with no graph encoder, candidate representation, sampler
or auxiliary loss.  A pass is required before any candidate-method pilot is
specified.

## G2 outcome and G2B interpretation boundary

The frozen three-seed run completed with `V8_G2_NOT_YET_ESTABLISHED`. At
fixed, profile-stratified endpoints, all three plain MLP policies selected
reconstruction for every profile. They succeeded in both future-value profiles
and failed in both current-value profiles. This is a failure of
profile-conditioned branch selection, not a failed G0 controller, missing
public context, ignored actor action, or missing profile coverage: the actor
receives the public envelope values, PPO retains only the causal relay action,
and training exposes one instance of each profile per rollout.

The original G2 pass rule incorrectly required the plain MLP to solve the
relation-value distinction reserved for the candidate method. That is stronger
than the stated baseline-grounding requirement and would make a successful
candidate representation unnecessary. The historical G2 report is retained
unchanged. `scripts/audit_compositional_service_envelope_handoff_v8_g2b.py`
adds a separate, non-overwriting interpretation audit:

- every baseline seed must have balanced endpoint success strictly between
  global failure and saturation;
- all four public profiles must be evaluated;
- relation-blind branch collapse is a **candidate target**, not a baseline win.

G2B can establish only an intermediate, non-saturated baseline and a concrete
public decision error. It cannot establish candidate efficacy, mechanism
identification, or paper evidence. Those remain gated by the matched pilot and
semantic-shuffle audit.

## G3 candidate-mechanism contract: public service-envelope relation value

The next development gate introduces one and only one candidate intervention:
at the V8 causal branch, the relay's binary logits are computed from the
already public current and future service envelopes. The candidate combines an
identical encoder of each three-field envelope with their directional
difference and product. It does not expose a profile identifier, a hidden
future state, a new observation channel, a graph encoder, an auxiliary loss,
or a sampler.

The ordinary control is a no-graph MLP with hidden width 66; the candidate
uses width 64 plus the relation head. At the frozen smoke-test construction,
the counts are 37,850 and 37,460 parameters respectively (1.04% difference).
The semantic-shuffle ablation preserves every parameter and input dimension
but permutes the future-envelope field correspondence inside the candidate
head. It is an ablation hypothesis, not a claimed result before its pilot.

Before any formal cohort is registered, the candidate must clear a 2--3 seed
development pilot against this capacity-matched ordinary control. The pilot
must show a behavioral difference at the causal branch and a non-ceiling,
non-global-failure endpoint pattern. It cannot establish robustness,
generalization, or semantic necessity; those require the separately frozen
formal control, aligned candidate, and shuffle arms.
