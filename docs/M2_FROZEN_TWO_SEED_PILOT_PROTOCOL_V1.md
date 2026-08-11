# M2 frozen Full-versus-B1 two-seed pilot v1

**Status:** `M2_COLLECTOR_INTEGRATION_AND_FROZEN_TWO_SEED_PILOT_AUTHORIZED`

## Frozen execution matrix

| Item | Frozen value |
| --- | --- |
| Task | Corrected-contract L4: range scale 0.5, dropout 0.3, delay 8, horizon 180 |
| Methods | `full`, `b1` |
| Development training seeds | 9201, 9202 |
| Updates / seed | 60 |
| Rollout / PPO | Existing L4 configuration: 8 environments, 128 rollout steps, 4 PPO epochs |
| Evaluation seeds | 890000--890031, paired for all four runs |
| Actor information | Current local sensing or delivered/cache-valid target evidence only |
| Fixed controls | Reward, environment, continuous hybrid action, role heads, attacker-only commit mask, critic, history width, optimizer and all PPO settings |

## Collector contract

The collector carries explicit `target_state`, `self_state`, `previous_action`
and canonical `evidence_valid` for every environment-recipient timestep.  The
PPO replay buffer stores the pre-step history state and reuses it when scoring
the recorded action.  Target state resets on either episode termination or an
invalid evidence timestep.  The target-free self state cannot receive target
values, direct-detection, attack-window or cache freshness fields.

## Pre-launch gates

The launch is blocked unless the following pass on the committed source:

- M2 interface: 9 deterministic checks;
- collector expiry transition: nonzero target state -> zero on expiry ->
  nonzero after fresh legal evidence;
- recipient-specific target contract;
- actor boundary;
- continuous hybrid-action and role-specific-head regressions.

## Decision rule

For each training seed, compare Full with B1 on the paired 32 evaluation
episodes.  A seed has a mechanism improvement only when all three directions
hold: acquisition conditional on legal evidence increases, evidence-to-range
latency decreases, and `NO_ATTACK_RANGE_ACQUISITION` fraction decreases.

- **PASS:** both seeds improve the mechanism and at least one seed also has a
  better mission endpoint (neutralization higher or RMTN180 lower).
- **PARTIAL:** exactly one seed meets the mechanism criterion.  Analyse only
  these frozen records; do not add seeds, updates, or modules.
- **NO-GO:** neither seed meets the mechanism criterion, or B1 is equivalently
  or consistently better.

No interim curve, reward, final success rate, or resource utilisation can
change this protocol.  The pilot is development evidence only and cannot enter
the final paper's confirmatory results.
