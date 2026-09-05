# B-line P0.5 environment semantic audit contract

## Purpose

P0 established only a conditional toy counterexample: with a maximum consecutive route-outage contract and a `reconfigure_relay` action, two histories with the same current snapshot can require different decisions. P0.5 determines whether those exact assumptions belong to the existing UAV environments.

## Permitted evidence

- Existing environment source and fixed actor-interface source.
- Failure timing, message/cache freshness, actor observation and graph-observation boundaries, action masks, termination, reward, and existing action interfaces.
- Static source hashes and deterministic source-marker checks.

## Prohibited activity

- Environment, reward, termination, observation, or action-space changes.
- Solver design or implementation.
- Environment construction or stepping, PPO/RL, checkpoint loading, training, evaluation, tape access, seed selection, or parameter tuning.

## Required classification

Every finding must be one of:

1. `environment_native_semantics` — encoded in the current environment;
2. `legally_derivable_internal_state` — deterministically reconstructible only from actor-legal observations/history;
3. `newly_introduced_assumption` — not encoded in the present environment and therefore not usable to promote P0.

## Frozen decision rule

- `B_P05_SEMANTIC_PASS`: the exact P0 continuity constraint and action interface are native, actor-legal or legally derivable, and make feasibility or the preferred decision history-dependent.
- `B_P05_SEMANTIC_PARTIAL`: a native time-dependent information problem exists, but the exact P0 constraint/action pair does not map to the current environment.
- `B_P05_SEMANTIC_NO_GO`: neither native semantics nor legal history can support a history-sensitive decision distinction.

No verdict authorizes solver or P1 automatically.
