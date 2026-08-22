# G0 Topology Legality and Feasibility Audit

## Actor-information and graph legality

All G0 conditions are instantiated through the existing environment config
before reset. The actor receives only the frozen decentralized observation and
graph tensors. It receives neither a topology ID, failure label, shortest path,
future link state, nor a global connectivity flag. Diagnostic topology labels
are written only after rollout for analysis.

The environment itself applies a configured directed deletion after ordinary
communication adjacency formation. Therefore every deletion respects
`A[receiver,sender]`; no evaluation adapter writes actor graph tensors.

## Physical interpretation

- `U1` represents loss of the Scout communication node, an untrained failure
  location, not an information-blackout claim.
- `U2` represents bilateral loss of the longest direct radio link while the
  Relay route remains.
- `U3` represents a direction-dependent link budget/interference loss, with
  Scout-to-Attacker delivery unavailable but the reverse link retained.
- `U4` and `U5` combine an untrained path constraint with an existing node
  failure to test legal path reconfiguration rather than timing alone.

The frozen business task retains attacker terminal sensing; none of U1–U5
asserts impossible mission completion or a unique Relay information role.
U6 is explicitly diagnostic-only because its post-onset graph may remove all
forward Scout-to-Attacker routes.

## Variable-size audit

`VARIABLE_SIZE_ZERO_SHOT_SUPPORTED = NO`. The trained actor/critic input
shapes, role identity tensors, and checkpoint parameterization are fixed for
three controllable blue agents. Evaluating four or five agents without
retraining would violate the frozen architecture contract, so variable-size
results are not part of G0.

## Evaluation validity

For node-failure cases, all episodes remain in unconditional performance and
safety denominators. Trigger correctness is evaluated among episodes alive at
the scheduled onset; pre-onset collisions remain policy outcomes, not
evaluator defects. No outcome-based episode exclusion is permitted.
