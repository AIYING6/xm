# T7 — Final Method Design Review

## Candidate class examined

The narrowest possible candidate was **state-conditional support-response
calibration**: retain the exact SG backbone and PPO, compare an actor's policy
with the same legal support tuple present versus locally masked, and regulate
the resulting action-distribution TVD toward a legal state-dependent target.

It would add no execution-time privileged information. The paired forward pass
would have approximately doubled actor-forward activation cost during training,
with no necessary parameter increase; inference parameters and latency would
remain unchanged. A parameter-matched control would still be required if any
new head were introduced.

## Why no final method is specified

The design depends on `\tau(x)`, the appropriate magnitude of sensitivity in a
legal state. T7's offline premise audit rejects the only available legal
reference, support quality. There is no actor-legal target scale; using reward,
future continuity, global path, or future topology would violate the execution
boundary, while using an arbitrary constant/range would be generic sensitivity
regularization.

Consequently, the candidate has no valid loss, calibration operator, or
inference rule. Defining one anyway would violate both the T7 mathematical
requirement and the anti-generic-method restriction.

## Stability audit

Forcing response magnitude without an identified target risks saturated
policies, excessive action switching, response to noisy cache fields, and PPO
instability. This is especially inappropriate after the DRTP/TCR instability
history. No adaptive sampling, gradient surgery, bilevel procedure, adversarial
objective, or high-gain sensitivity forcing is proposed.

## Required future controls, if a legitimate target were discovered elsewhere

The frozen conceptual controls would be: no-calibration SG/UTR; generic
conditioning (gate/FiLM); simple increase-sensitivity regularizer; and a
parameter-matched SG. These are recorded only to explain the burden a future
method would face; they do not authorize any algorithm or experiment.
