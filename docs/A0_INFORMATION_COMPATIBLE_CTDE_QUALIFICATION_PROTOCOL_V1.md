# A0 Information-Compatible CTDE qualification (v1)

Status: `A0_INFORMATION_COMPATIBLE_CTDE_QUALIFICATION__NO_IMPLEMENTATION__NO_TRAINING`

## Question

The current L4 actor contract is recipient-specific: an Attacker may use its
own physical state and target information obtained from current local sensing
or a delivered, cache-valid packet.  The training-only MAPPO critic instead
receives `share_obs`, which includes global teammate state and the simulator's
global last-detected target estimate.  The estimate may have been updated by a
teammate even while the Attacker has no legal target evidence.

A0 asks whether this difference creates a material *critic-signal mismatch* in
the existing frozen L4 policies.  It does **not** assume that a new estimator
will improve performance.

## Frozen A0 counterfactual

For frozen L4 checkpoints `8901` and `8902` and frozen episode seeds
`890000..890031`, select each decision state satisfying:

1. `last_detected_target` exists globally; and
2. the Attacker has no fresh/cache-valid target evidence.

At each selected state, retain the physical simulator state and all actor
inputs.  Substitute only an alternative in-domain value for the global
`last_detected_target` estimate used by `share_obs`, then assert byte-exact
invariance of the Attacker observation, recipient graph node/edge tensors,
roles, adjacency, and relation adjacency.  The altered state is never stepped.

Record the central value shift and the corresponding one-step TD-residual
counterfactual while holding the observed reward, action, and next-state value
fixed.  This is a diagnosis of critic dependence on actor-unavailable global
information, not an environment or policy intervention.

## Phenomenon gate

The mismatch phenomenon is material only if **both** checkpoints have at least
20 selected states, 100% actor-input invariance, and median absolute critic
value shift at least 0.10 of the selected-state standard deviation of central
values.  TD sign-conflict frequency is reported descriptively, not used as a
performance endpoint.

## Candidate rejected-by-default formulation

The proposed expression

`A_legal(I_i, a_i) = E[A_central | I_i^legal, a_i]`

is a conditional projection.  Before any implementation, it must be shown to
be mathematically and operationally different from (i) a local/history critic,
(ii) a history-state critic, (iii) ROLA-style local advantage, and (iv)
ordinary critic distillation/control-variate constructions.  A0 treats an
equivalence to any of these existing lines as a novelty kill condition.

## Prohibitions

No policy/critic architecture, training objective, reward, environment,
checkpoint, episode population, or actor information contract may change.
No training, pilot, or performance comparison is allowed.
