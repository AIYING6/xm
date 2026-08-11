# H0 hybrid-action collapse identifiability audit

**Status:** `H0_COMPLETE__COMMIT_ACTION_SEMANTICALLY_DOMINATED__NO_NEW_ALGORITHM_PROBLEM`

## Scope

This was a read-only replay of eight existing corrected-contract development
checkpoints: two each from L1, L2, L3 and L4.  It used the same fixed eight
L4 evaluation seeds for every checkpoint.  No parameter update, environment
change, seed selection, or new training occurred.

## Finding

For all eight baseline checkpoints, including the role-specific vanilla MAPPO
baseline used in L1--L4:

* deterministic Attacker `engage_commit` was `1` on every replayed step;
* behavioural commit entropy was therefore `0` bits;
* turn and climb retained nonzero variation.

M2R's `Full-9601` has the same all-one commit behaviour.  `Full-9602` is the
opposite, all-zero commit pathology.  Thus the all-one pattern is not unique
to M0/M2R Full, while the all-zero pattern is method-specific in the available
evidence.

## Why this is not a new hybrid-action optimization problem

The mission transition only consumes `engage_commit` inside the true
neutralization envelope.  Outside that envelope, commit does not change
flight dynamics, safety dynamics, communication, or incur a separate cost;
inside it, commit is necessary for the four-step neutralization hold.
Consequently, under the frozen task interface, `commit=1` weakly dominates
`commit=0`.  A policy that always commits is therefore an expected consequence
of the action semantics, not evidence that the continuous/discrete PPO heads
have an independently identifiable optimization conflict.

The M2R all-zero arm remains a method-specific failure, but it cannot be used
to reframe the dominated commit action as a general algorithmic research gap.

## Decision

H0 does **not** authorize H1/H2 or another method repair.  The current UAV
platform's M0/M2R acquisition-conditioning line remains closed.  Any future
algorithm project must begin with an independently established scientific
problem rather than repackaging this action-interface artefact.
