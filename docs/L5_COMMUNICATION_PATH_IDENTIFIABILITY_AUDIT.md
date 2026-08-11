# L5 communication-path identifiability audit

## Scope

`COMMUNICATION_PATH_IDENTIFIABILITY_AUDIT_V1` is a method-independent,
development-only audit. It ran no learning algorithm and made no architecture,
reward, dynamics, or task-protocol change. The frozen L4 conditions were held
fixed: communication-range scale `0.5`, packet dropout `0.3`, and message delay
`8` steps.

The audit used eight scripted episode seeds (`900000`–`900007`) only to reveal
the communication system's realised legal evidence paths before any relay
failure experiment is contemplated.

## Questions and measurements

For every receiver/sender pair and time step, the raw record captures:

1. physical communication reachability;
2. actual delivered/cache-valid sender-status packets;
3. sender packets carrying a fresh cache-valid target claim; and
4. recipient target-cache provenance paths containing the Relay.

The three critical realised links were `Scout -> Relay`, `Relay -> Attacker`,
and direct `Scout -> Attacker`.

For the requested counterfactual, the exact scripted action sequence was replayed
with Relay communication disabled. This leaves motion, target motion, and the
mission terminal condition unchanged; it therefore isolates communication from
physics. Legal-information effect is then evaluated by provenance erasure:
remove exactly Relay-origin sender evidence and target claims whose recorded path
contains Relay, while retaining all other delivered records unchanged.

## Results

Across `2580` receiver/sender step records:

| Quantity | Scout -> Relay | Relay -> Attacker | Scout -> Attacker |
| --- | ---: | ---: | ---: |
| Physical-link availability rate | 0 | 0 | 0 |
| Delivered status-packet records | 0 | 0 | 0 |
| Fresh target-claim records | 0 | 0 | 0 |

There were also:

* `0` recipient target-cache paths containing Relay;
* `0` Relay-origin legal sender-status records;
* `0` Relay-origin fresh target-claim records.

The fixed-action Relay-communication-disabled replays were exact for all eight
episodes: maximum Blue and target position error was `0.0`, terminal outcome
matched, and the termination horizon matched.

Consequently, Relay-provenance erasure changes no recorded actor legal
information set in this L4 trajectory population.

## Verdict

`L5_BLOCKED__RELAY_CAUSAL_ROLE_NOT_IDENTIFIED`

The immediate reason is geometric/topological, not a learning failure: neither
`Scout -> Relay` nor `Relay -> Attacker` becomes physically reachable in the
frozen L4 scripted population. There is therefore no observed relay forwarding
path for a relay failure to remove.

No L5 training is authorized. There are only two scientifically coherent
follow-up choices, requiring a separate author decision:

1. end the difficulty ladder at limited-range, dropout, and delay, and do not
   make relay-failure claims; or
2. redesign and freeze a *relay-identifiable task protocol* first, then prove
   actual `Scout -> Relay -> Attacker` delivered/cache-valid provenance and
   retained scripted mission reachability before testing any relay failure.

The raw audit records are intentionally retained as generated artifacts at
`results/l5_communication_path_identifiability_audit/` and are not source
controlled.
