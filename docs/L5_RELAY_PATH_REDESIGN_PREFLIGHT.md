# L5 relay-path redesign preflight

## Blocking finding

`L5_RELAY_PATH_REDESIGN_BLOCKED__ACTOR_CONTRACT_INCONSISTENT`

The authorised redesign is limited to communication topology and geometry. It
cannot satisfy the required condition that Relay be an Attacker's *legal*
information path under the current L4 configuration, because that configuration
sets:

```text
strict_target_sensing = true
agent_target_info_bottleneck = false
```

In this environment, that combination makes each actor's target observation use
the environment-wide `last_detected_target_*` estimate once any detector has
seen the target. It does not require the recipient's direct detection, a
delivered sender packet, or a cache-valid target claim. Thus an Attacker can
receive target information outside `Scout -> Relay -> Attacker` packet/cache
provenance.

## Deterministic counterexample

`scripts/test_l5_relay_path_actor_contract_preflight.py` creates an L4 attacker
with all attacker caches invalid and no sender packets. Changing only the
environment-wide latest target detection changes the Attacker observation.
The test is deliberately an expected-failure preflight: it demonstrates that
the present contract cannot support a relay-only information claim.

## Decision boundary

No relay topology/geometry redesign and no L5 training may proceed under this
configuration. It would create the appearance of a relay path while retaining
an actor-visible non-packet bypass.

The next action needs separate author approval because it changes the execution
information contract, not merely topology:

1. freeze a recipient-specific L5 actor contract (for example, require each
   target estimate to arise from local sensing or a delivered, cache-valid
   target packet);
2. run the actor-boundary and packet-provenance regressions for that contract;
3. only then evaluate one topology/geometry redesign for actual
   `Scout -> Relay -> Attacker` provenance.

The earlier L0–L4 development outputs must remain labelled as development
evidence under their original contract; they cannot establish a relay-dependent
claim.
