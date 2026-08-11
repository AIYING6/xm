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

## L1 corrected-contract requalification result

The requalification ran exactly the original development pairing: role-specific
heads, non-Attacker commit masking, seeds `8301` and `8302`, 60 updates, and
the frozen 32 evaluation seeds. The only changed variable was
`agent_target_info_bottleneck=false -> true`.

| Condition | Geometry entry | Neutralization | RMTN180 |
| --- | ---: | ---: | ---: |
| Corrected-contract seed 8301 | 59.38% | 34.38% | 135.78 |
| Corrected-contract seed 8302 | 18.75% | 15.63% | 160.50 |
| Random | 31.25% | 9.38% | 168.13 |
| Scripted | 100% | 100% | 53.59 |
| Oracle | 100% | 100% | 52.56 |

Both learned seeds have nonzero geometry entry, neutralization above the frozen
random reference, and RMTN180 below 180. The development verdict is therefore:

`L1_CORRECTED_CONTRACT_LEARNING_SIGNAL_RETAINED`

This is a requalification gate, not a performance claim. It permits a future
separate decision to rebuild L2, then L3 and L4, under the repaired contract.
It does not revalidate the old L2–L4 outputs or authorize L5.

## L2 corrected-contract range requalification result

The range-only requalification retained every frozen L2 setting except the
repaired target-information contract: range scale `0.5`, reliable packets,
no delay, role-specific actor heads, non-Attacker commit masking, continuous
guidance, aligned reward, 60 updates, seeds `8501` and `8502`, and 32 frozen
evaluation episodes.  The only changed variable relative to the historical L2
development rung was `agent_target_info_bottleneck=false -> true`.

| Condition | Geometry entry | Neutralization | RMTN180 |
| --- | ---: | ---: | ---: |
| Corrected-contract seed 8501 | 56.25% | 37.50% | 131.88 |
| Corrected-contract seed 8502 | 43.75% | 34.38% | 135.91 |
| Random | 28.13% | 0% | 180.00 |
| Scripted | 100% | 100% | 56.09 |
| Oracle | 100% | 100% | 52.72 |

Both learned development seeds retain nonzero geometry entry, neutralization
above the frozen random reference, and RMTN180 below the restriction horizon;
there were no collision or constraint-failure outcomes.  The frozen gate is:

`L2_CORRECTED_CONTRACT_RANGE_LEARNING_SIGNAL_RETAINED`

This is development-only requalification evidence, not a cross-condition
performance claim.  It restores the scientific eligibility of a separately
authorized, strict-contract L3 packet-dropout rung.  It does not authorize
L3 automatically, does not revalidate historical L3/L4 data, and does not
authorize delay, Relay-path redesign, a new algorithm, or formal training.
