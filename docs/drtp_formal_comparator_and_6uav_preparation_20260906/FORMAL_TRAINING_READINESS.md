# PLR external comparator and 6-UAV cross-scale formal-training readiness

**Status:** `PREPARED_NOT_AUTHORIZED_TO_LAUNCH`.

This preparation creates two independent, from-scratch formal experiment
contracts. It does not train, evaluate, inspect an endpoint, change the
frozen UTR/DRTP methods, or open another mechanism audit.

## 1. PLR-style external comparator

The comparator is an independent implementation of the published PLR replay
rule, not copied source code. A training level maps to one of the six frozen
DRTP failure groups (`F0`, `TE`, `TL`, `DS`, `DL`, `CP`). Nominal exposure
remains fixed at 0.50; for every selected failure group, the established
uniform draw among its pre-existing condition members remains unchanged.

The PLR learning-potential score is mean absolute, unnormalised GAE over a
vectorised T-step rollout fragment. PLR uses rank priority with temperature
0.10 plus a 0.10 staleness mixture. It changes reset selection only: not
observations, graph inputs, rewards, action masks, PPO loss, model capacity,
or the endpoint tape.

The formal cohort is `UTR / Original DRTP / PLR-style` × five fresh matched
seeds `79011–79015`, each at 10,000,128 steps. `79021–79025` are reserved,
unread independent replication seeds. The result can establish an external
sampler comparison; it cannot retrospectively alter the already frozen DRTP
claim.

## 2. Six-UAV cross-scale evidence

The cross-scale cohort is `UTR / Original DRTP` × five fresh matched seeds
`69011–69015`, each at 10,000,128 steps. It keeps the corrected six-UAV
role-separated learner and the frozen seven groups:

- nominal;
- `R_upstream`, `R_downstream`;
- `C_relay_node`, `C_balanced`, `C_cross`, `C_same_relay`.

UTR is uniform over these seven groups. DRTP retains the same group support,
fixed nominal mass `1/7`, failure onset, transitions, rewards, masks, role
assignment interface, learner, PPO, model capacity and endpoint tape; it may
only adapt the conditional distribution across the six non-nominal groups
from completed training returns. Seeds `69021–69025` are reserved for an
independent replication and are not part of the first formal cohort.

## 3. Decision discipline

The two packages are independent. Neither launches automatically when the
other finishes. Analyses will report all seeds and joint evidence: mean,
median, paired directions, lower tail, seed spread, collision and timeout.
No single development statistic can trigger an algorithm revision or closure.

The required zero-training gate is
`DRTP_PLR_AND_6UAV_PREFLIGHT_PASS`; a separate explicit launch authorization
is still required after the cloud packages are built and reviewed.
