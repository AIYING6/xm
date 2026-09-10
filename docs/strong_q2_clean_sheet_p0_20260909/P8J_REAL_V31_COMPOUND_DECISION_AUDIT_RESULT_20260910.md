# P8J native V3.1 compound-decision audit

## Decision

`REAL_V31_COMPOUND_DECISION_GAP_STOP`.

The ACFID topic is closed on the current native six-UAV task. No policy was
trained and no method was implemented during this audit.

## Native counterfactual design

The audit used `SustainedSupportTopologyV31UAVEnv`, eight native legal task
edges, three independent communication random streams, and all 28 two-edge
combinations. At the post-fault state it enumerated all 729 six-agent joint
actions. Every action was evaluated from an exact runtime clone and followed by
the same deterministic actor-legal continuation. Single-edge and nominal value
vectors formed an additive decision predictor; the true compound rollout
provided the paired regret target.

## Frozen gate results

- Native runtime cloning and exact 729-action enumeration: pass.
- All primitive failures are native legal edges: pass.
- Compound oracle recoverability: 28.57%, inside the frozen 10–90% range.
- Decision-relevant compound cases: 10.71%, below the frozen 20% minimum.
- Median additive-action regret: 0.000, below the frozen 0.02 minimum.
- Mean additive-action regret: 0.01984 (descriptive only).

The recoverability result rules out global task failure as the explanation for
the stop. Instead, most compound failures do not alter the preferred recovery
joint action beyond the nominal-plus-single approximation. The available task
therefore does not supply a broad decision-level interaction gap capable of
supporting the proposed central claim.

## Consequence

P8I showed no learned ACFID advantage on mechanically selected development
pairs. P8J independently shows that the native V3.1 substrate contains too few
material additive-decision failures. Together these results close the current
ACFID topic. Increasing training budget, reducing thresholds, selecting the
high-regret fault pairs, or changing environment coefficients after inspection
would not be an acceptable repair.

The next clean-sheet search must exclude ACFID-style compound-fault interaction
decomposition unless a different, externally defensible task provides the gap
without coefficient tuning.
