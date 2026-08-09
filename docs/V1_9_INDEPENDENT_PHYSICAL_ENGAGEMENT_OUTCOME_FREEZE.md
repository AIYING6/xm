# v1.9 Independent Physical Engagement Outcome Freeze

**Status: `SECONDARY_CONSTRUCT_VALIDITY_OUTCOME_FROZEN__D2_NOT_AUTHORIZED`.**

## Scope

The v1.9 primary endpoint remains unchanged: time from relay-failure onset to
first stable legal task-chain establishment, reported by RMTE80/RMTE220 and
its complete-follow-up outcome decomposition. This document adds a secondary,
evaluator-defined task-level construct-validity endpoint. It is not used for
checkpoint selection, does not replace RMTE, and does not authorize D2/F1/F2.

The current simulator has no target capture, target neutralization, weapon, or
mission-completion transition. It must therefore not be described as physical
capture or interception completion. It does contain all kinematic state needed
to define a narrower independent physical outcome: sustained safe engagement
readiness.

## Frozen event: sustained physical engagement readiness

For attacker/interceptor vehicle \(a\), at simulator step \(t\), define the
true-state physical predicate \(Q_a(t)=1\) only when all conditions hold:

1. `attack_range_min(a) <= ||p_target - p_a|| <= attack_range_max(a)`;
2. line-of-sight heading error is at most `attack_cone(a)`;
3. absolute altitude difference is at most 1,600 m; and
4. radial closure is strictly greater than -30 m/s.

All quantities are computed by the evaluator from true simulator kinematics:
blue/target positions, velocities, headings, speeds, and flight-path angles.
The values are the pre-existing environment physical engagement constants for
the attacker role (currently 1,400--5,200 m range, 50-degree cone, 1,600 m
altitude separation, and -30 m/s closure threshold). No threshold was chosen
from an R2 policy result.

Let \(Q(t)=\max_a Q_a(t)\) across eligible attacker/interceptor vehicles. The
event time \(T_{PE}\) is the first step after failure onset at which \(Q(t)=1\)
for `L=4` consecutive simulator steps. `L=4` is the already frozen stable
window length; the evaluator maintains its own physical counter and never
reads `attack_hold` or `chain_closed`.

This is named **sustained physical engagement readiness**, not capture,
interception completion, or mission success.

## Independence and safety contract

The evaluator may not read `chain_closed`, `attack_hold`, communication
adjacency, communication-derived reachability, packet/cache fields, sensing
availability, actor observation, graph features, relation masks, gate values,
or method identity. It does not call the environment's task-chain predicate.

The physical envelope is safely distinct from collision: the attacker's lower
engagement range (1,400 m) exceeds the 120-m collision radius. A deterministic
counterexample has a valid physical engagement geometry while tracking,
communication, cache validity, and task-chain closure are all absent. Hence
the physical predicate is evaluator-defined and not reconstructed from the
communication/task-chain machinery. It is not expected to be statistically
independent of task-chain establishment: a completed task chain uses an attack
window as one necessary component. The required distinction is **definition
and information independence**, not a claim of zero empirical association.

## Secondary estimand and reporting

For `tau in {80, 220}`, define

\[
  RMPE_\tau = E[\min(T_{PE},\tau)].
\]

Lower RMPE is favorable. If no sustained physical engagement readiness occurs
by \(\tau\), including after collision, constraint violation, or active
non-establishment, the episode contributes \(\tau\). Report at each horizon:

1. sustained physical engagement-readiness incidence;
2. terminal-failure incidence before physical readiness; and
3. active without physical readiness at the horizon.

This is the same complete-follow-up convention as RMTE but is a distinct
secondary outcome. It cannot enter validation selection or change the primary
comparison hierarchy.

Future reporting must show the association with task-chain establishment
without treating it as causal proof: the paired 2x2 episode table, conditional
incidences `P(PE by tau | establishment by tau)` and
`P(establishment by tau | PE by tau)`, and paired differences between methods.
The hierarchical unit remains formal training seed followed by matched
evaluation episode; no episode-level pseudo-replication is permitted.

## Deterministic evidence and remaining boundary

`scripts/audit_p1_independent_mission_outcome_v1_9.py` passes five tests:
the predicate's true-state-only inputs; valid engagement without a task chain;
each physical threshold's necessity; an evaluator-owned four-step stability
counter; and disjoint safe-engagement/collision radii.

This supports a scientifically definable secondary physical engagement outcome
in the present 3DOF simulator. It does **not** support a claim of target
capture, target neutralization, actual interception completion, or mission
completion. Those events do not exist in the current physics and must not be
invented as labels.
