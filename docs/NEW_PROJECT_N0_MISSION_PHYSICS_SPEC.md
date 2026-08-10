# N0 specification: an independently defined standoff-neutralization mission

**Status:** `N0_MISSION_PHYSICS_IMPLEMENTATION_PASS__READY_FOR_N1_TASK_PROTOCOL`.

This document specifies a *new* task transition only.  It does not add an
algorithm, reward, training run, information feature, or paper performance
claim.

## N0 decision

The existing 3DOF simulator contains enough kinematic state to implement an
honest **abstract standoff-neutralization** event, but not to claim detailed
missile dynamics, sensor fire-control fidelity, or real-world kill probability.
The new task must use the former wording only.  It must never call the old
`attack_hold`, `chain_closed`, or physical-engagement-readiness predicate a
mission completion event.

## Existing physical substrate

The current model already evolves, at one-second intervals, true blue/target
position, velocity, heading, flight-path angle, energy, collision state and
altitude/world-boundary constraints.  The attacker already has a true-state
standoff envelope: range 1,400--5,200 m, heading error at most 50 degrees,
altitude separation at most 1,600 m, and radial closure above -30 m/s.  These
are valid inputs for an evaluator-owned transition; communication/cache values
and graph predicates are not.

## Proposed target lifecycle

The target has exactly one lifecycle state:

`ACTIVE -> NEUTRALIZED`.

`NEUTRALIZED` is a terminal simulator state.  It freezes the target dynamics,
marks the episode a mission completion, and ends the episode.  It is not an
observation value or a reward proxy.

## Proposed action and physical transition

Only an attacker/interceptor role can produce an effective additional binary
action `engage_commit`. It is a decision to initiate/maintain the abstract
standoff engagement; it conveys no information and does not expose evaluator
state. The existing flat discrete-action interface represents an attempted
commit by another role as the corresponding flight action with a no-op commit.

At step \(t\), evaluator-only eligibility for attacker \(a\) is

\[
E_a(t)=1
\]

only when all of the following are true from simulator kinematics:

1. `engage_commit[a] = 1`;
2. target range is 1,400--5,200 m;
3. attacker line-of-sight heading error is at most 50 degrees;
4. absolute altitude separation is at most 1,600 m; and
5. radial closure is greater than -30 m/s.

The evaluator owns a new `engage_commit_hold` counter.  It increments only
while some eligible attacker exists and resets otherwise.  On the first step
at which the counter reaches **4 consecutive simulator steps**, the target
transitions to `NEUTRALIZED`.

The numbers are inherited from the already-existing attacker geometry and
stable-window duration, not selected after any policy result.  They define a
lightweight, deterministic task abstraction.  The paper may call the outcome
*simulated standoff neutralization*; it may not claim a physical missile hit,
weapon exchange, or real operational kill probability.

## Strict independence from the old coordination endpoint

For a fixed true physical state and `engage_commit` actions, neutralization
must be invariant to changes in:

- `chain_closed` and `attack_hold`;
- sensing labels, packet delivery, cache contents, cache age/confidence;
- communication adjacency, graph relations, encoder outputs and method ID.

Conversely, a closed communication/task chain without `engage_commit` cannot
neutralize the target.  A valid standoff envelope without four committed
steps also cannot neutralize it.  These requirements prevent a renamed old
coordination predicate from becoming the new success label.

## Terminal-outcome precedence

At each transition, precedence is frozen as:

1. blue--target or blue--blue collision: terminal failure;
2. blue altitude/world-boundary constraint violation: terminal failure;
3. valid `NEUTRALIZED` transition: mission completion;
4. administrative episode horizon: active, unneutralized follow-up.

If collision and a putative neutralization condition co-occur on one step,
collision is failure.  This avoids awarding a mission completion for unsafe
contact.

The future N3 protocol must additionally decide whether target escape is a
distinct terminal failure or whether world-boundary handling keeps the target
in the mission area.  It must not leave this ambiguity to training code.

## Required deterministic N0 tests

Before any learning interface is connected, tests must demonstrate:

1. exactly four legal committed steps yield `NEUTRALIZED`;
2. three legal committed steps do not;
3. each geometry condition is necessary;
4. changing only `engage_commit` changes the event while the physical state is
   fixed;
5. changing only cache/communication/graph state cannot change the event;
6. `chain_closed=1` cannot by itself cause neutralization; and
7. a simultaneous collision blocks neutralization and is recorded as terminal
   failure.

## Evaluation boundary

The future primary outcome may be mission-completion incidence and restricted
mean time to neutralization, with terminal failure and active-unneutralized
outcomes reported separately.  Its horizon, failure exposure and analysis
population are deliberately **not** selected here; N3 must establish them from
method-blind task feasibility work before an algorithm is trained.

## N0 verdict

**PASS — implemented as an abstract standoff-neutralization task.** The
author-approved fidelity boundary is retained exactly: the simulator contains
neither a missile model nor a kill-probability claim. The implementation is
default-off for the legacy coordination environment. When enabled it adds only
the evaluator-owned target lifecycle and attacker/interceptor `engage_commit`
action semantics described above; it does not alter actor observations, graph
features, reward shaping, or any training protocol.

The deterministic N0 test suite passes all seven frozen conditions:
four-step completion; three-step non-completion; each geometry condition;
commit causality; cache/communication/graph invariance; old-chain
non-equivalence; and collision precedence. N0 is a simulator-physics pass,
not a validated benchmark or an authorized method study.
