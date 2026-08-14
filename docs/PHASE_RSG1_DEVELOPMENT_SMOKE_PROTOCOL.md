# Phase RSG-1 — Development Smoke Protocol

## Authorization

RSG-TC-0 passed. This protocol authorizes exactly nine development runs:

| Method | Seeds | Budget |
|---|---|---:|
| MAPPO | 1501, 1502, 1503 | 200,192 env steps each |
| matched Single-Graph | 1501, 1502, 1503 | 200,192 env steps each |
| RSG-TC | 1501, 1502, 1503 | 200,192 env steps each |

No canonical seed, formal test result, old Full result, resume, early stopping,
checkpoint promotion, seed exclusion, or protocol change is allowed.

## Training contract

- 4 environments × 64 rollout steps × 782 updates;
- final checkpoint only;
- same frozen S2 observation, reward, failure, and geometry settings;
- no consistency loss, robustness auxiliary loss, Role-Gate, or new module;
- no in-training evaluation used for selection.

## Evaluation contract

Each final checkpoint is evaluated on the same paired episode IDs
`340000–340099` under nominal and relay-failure conditions. Evaluation uses
deterministic actions, `max_steps=260`, `min_success_step=260`, relay failure at
step 44 for 80 steps, and the frozen S2 information boundary.

Primary quantities are computed per training seed:

\[
J_N,\quad J_F,\quad \Delta J=J_N-J_F.
\]

Secondary quantities include success-at-horizon, collision, timeout,
constraint violation, path switching, direct/relay path fractions, task-support
availability, legal information availability, cache age, distance, and control
effort.

RSG-TC additionally records descriptive `b_ij` telemetry by relation multi-hot
combination, nominal/failure condition, and pre/post-failure phase. Telemetry
does not affect action selection or evaluation.

## Frozen retention gates

RSG-TC continues only if every mandatory gate passes:

1. Mean nominal ratio to SG is at least `0.90`.
2. Mean failure score is at least `0.90` of SG.
3. Mean `ΔJ` is lower than SG.
4. At least 2/3 seeds have lower `ΔJ`, and pooled direction agrees.
5. Collision, timeout, and constraint-violation rates are no more than 0.05
   absolute above SG.
6. Relation/state-stratified bias telemetry is non-zero and distinguishable.
   For each RSG-TC seed, compute the mean bias for every observed relation
   combination and the nominal/pre-failure versus failure/post-failure cells.
   A seed passes this telemetry gate if the largest-minus-smallest observed
   cell mean is greater than `1e-4` **or** the absolute nominal/pre-failure
   versus failure/post-failure mean difference is greater than `1e-4`. The
   pooled RSG-TC bias standard deviation must also exceed `1e-4`, and at least
   2/3 RSG-TC seeds must pass the per-seed condition. Zero or effectively
   uniform bias does not support the RSG-TC mechanism claim.

MAPPO and SG are retained as controls regardless of the RSG-TC decision. A
failed RSG-TC gate produces `RSG-1 NO-GO` and ends new-network screening.
