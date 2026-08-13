# Phase S2 Freeze Implementation Clarification

**Status:** clarification before S3 launch; not a protocol amendment.

The frozen S2 environment contract already specified the `business_grounded_s1`
geometry and relay-dependent task semantics. This clarification makes both
existing requirements executable by adding explicit opt-in configuration fields:

- `business_grounded_geometry: true` fixes the initial blue positions to
  Scout `(-2000, -6000, 5000)`, Relay `(-2000, 0, 5000)`, and Attacker
  `(-2000, 6000, 5000)`, with zero initial headings and flight-path angles;
- `relay_dependent_task: true` activates the already frozen strict sensing and
  legal cache semantics.

No reward coefficient, communication range, failure onset/duration, target
process, metric definition, endpoint, seed set, or evaluation rule changed.
The defaults remain `false`, so the pre-existing environment behavior is
unchanged outside S3. The S3 runner is the only maintained launcher that
enables both fields.
