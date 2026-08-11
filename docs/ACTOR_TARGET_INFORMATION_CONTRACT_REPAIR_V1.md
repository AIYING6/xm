# Actor target-information contract repair v1

## Frozen execution semantics

For the repaired multi-agent communication ladder, an actor may receive target
state only through one of two sources:

1. current legal local sensing by that same recipient; or
2. an actually delivered, cache-valid target packet with recorded sender/path
   provenance.

If neither source is present, changing global truth or
`last_detected_target_*` must not alter that actor's observation. Global target
state may remain in `share_obs` for the centralized critic only; it must not
enter an actor input.

The repaired configuration is `strict_target_sensing=true` and
`agent_target_info_bottleneck=true`. Cache age equal to the frozen maximum is
legal; maximum age plus one is excluded.

## Scope and requalification

This is an actor-contract repair only. It does not alter mission physics,
continuous guidance, action semantics, reward, horizon, role-specific heads,
or algorithm.

L1–L4 results generated with `agent_target_info_bottleneck=false` remain
development diagnostics but are not strict recipient-specific communication
evidence. The next permitted computation is only L1 corrected-contract
requalification using the original L1 role-specific-head seeds and evaluation
episodes. L2–L5 remain unauthorized.
