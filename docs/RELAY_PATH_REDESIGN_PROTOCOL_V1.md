# Relay information-path redesign protocol v1

**Status:** `RELAY_PATH_REDESIGN_AUTHORIZED__IDENTIFIABILITY_ONLY__NO_L5_TRAINING__NO_N3`

This development-only redesign gives the existing Scout, Relay, and Attacker a
physical two-hop communication geometry. It changes neither reward, mission
physics, actor architecture, packet/cache semantics, nor the recipient-specific
information contract.

At `communication_range_scale = 0.5`, the opt-in reset formation places Scout
and Relay 4.2 km apart, Relay and Attacker 4.2 km apart, and Scout and Attacker
8.4 km apart. Thus the existing pairwise range rule permits Scout-to-Relay and
Relay-to-Attacker delivery while blocking direct Scout-to-Attacker delivery.
All three start with equal speed, heading, and climb angle to avoid a one-step
topology artifact. The target begins at `(3500, -4200, 5000)`: it is initially
visible to Scout but outside Attacker radar range for the two delayed packet
hops. This is an environment geometry parameter, not an observation exception.

The only legal target route remains local sensing or delivered cache-valid
packets. Relay forwarding uses the existing target-cache propagation mechanism:
the expected Attacker cache provenance is `[Scout, Relay, Attacker]`. No
`relay_alive` condition may inject information into an actor.

Before any relay failure calibration or training, the deterministic audit must
show all of the following:

1. actual Scout-to-Relay and Relay-to-Attacker delivered/cache-valid target
   evidence;
2. no contemporaneous direct Scout-to-Attacker path for the relay-only record;
3. an Attacker observation containing relay-provenance target evidence;
4. an otherwise identical relay-disabled counterfactual with changed Attacker
   legal information but unchanged physical state trajectory; and
5. a feasible scripted/oracle task path with relay contribution before a future
   failure onset.

Passing this gate only yields `RELAY_PATH_IDENTIFIED__READY_FOR_L5_FAILURE_CALIBRATION`.
It does not authorize L5 training or any algorithm work.

## Completed identifiability audit

The deterministic, no-training audit used eight scripted/oracle episodes
(`910000`–`910007`) at range scale `0.5`, dropout `0.3`, and delay `8`. Every
episode produced relay-only Attacker evidence at steps `17`–`19`, before oracle
neutralization at step `43`. Disabling Relay communication changed Attacker's
legal observation in all eight paired replays while leaving blue/target physical
trajectories exactly identical. The scripted/oracle controller neutralized in
all eight active-Relay episodes. The resulting verdict is
`RELAY_PATH_IDENTIFIED__READY_FOR_L5_FAILURE_CALIBRATION`; L5 training remains
unauthorized.
