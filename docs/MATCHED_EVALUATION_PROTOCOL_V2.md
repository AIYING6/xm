# Matched evaluation protocol v2

Canonical evaluation requires an explicit episode tape keyed by `(scenario_id, paired_episode_id)`. A tape must bind initial UAV state, target initialization/trajectory realization, dropout/delay masks, failure node/time, environment noise, and scenario ID. Every method consumes the same tape and may not mutate it with policy RNG.

## Current status

The current environment uses seed-derived RNG streams (`rng` and `dropout_rng`) but does not yet persist/replay a complete exogenous tape. Therefore paired evaluation is not yet proven. Gate E remains NO-GO until tape generation, replay, cross-method identity, and stable episode-ID tests pass.
