# L1 role-specific actor-head development report

## Scope and freeze

This was a development-only isolation experiment for the L1 coordination
bottleneck. It did not enter L2, N3, formal training, or paper evidence.
The only intended change relative to the failed L1 shared-actor pilot was
role-specific actor policy heads. Reliable communication, aligned physical
reward, continuous guidance actions, mission physics, horizon, PPO settings,
and evaluation seeds were retained. `engage_commit` was masked for Scout and
Relay because only the attacker/interceptor has that mission action.

Training seeds were 8301 and 8302; evaluation used 32 fixed development seeds.
The immutable machine-readable output is
`results/l1_role_specific_actor_development_v2/L1_VERDICT.json`.

## Development outcome

| policy | geometry entry | neutralized by 180 | mean RMTN180 |
|---|---:|---:|---:|
| role-specific seed 8301 | 32/32 | 31/32 | 56.16 |
| role-specific seed 8302 | 26/32 | 18/32 | 108.72 |
| random | 10/32 | 3/32 | 168.13 |
| scripted | 32/32 | 32/32 | 53.03 |
| oracle | 32/32 | 32/32 | 52.56 |

No collision or constraint-failure inflation was observed in these fixed
development episodes. Both learned seeds were above random on neutralization,
entered geometry, and left the all-horizon-saturated regime.

## Interpretation boundary

The result establishes a reproducible L1 learning signal under role-specific
actor heads and is consistent with heterogeneous shared-policy optimization
being a major bottleneck. It does **not** establish that role-specific heads
are a paper innovation, that they outperform a formal comparator, or that
communication failures are solved. The sample is development-only and must not
be promoted to F1/F2 evidence.

## Decision

`L1_ROLE_SPECIFIC_ACTOR_HEADS_ESTABLISH_LEARNING_SIGNAL`.

The next decision remains author-gated. Do not add packet loss, delay, relay
failure, a new method, or formal training automatically. If continuing, the
next protocol must first define a stronger role-conditioned comparator and a
pre-registered L2 progression; otherwise this result is sufficient to close
the learnability diagnosis.
