# N2 learnability and baseline protocol

**Status:** `N1_TASK_PROTOCOL_FROZEN__N2_LEARNABILITY_CHECK_AUTHORIZED__NO_MAIN_METHOD_DESIGN`.

N2 asks only whether the frozen N0/N1 task can be learned without exploiting an
old internal coordination proxy. It is not a competition among algorithms and
does not authorize a new network module, formal training, cloud execution, or
a paper performance claim.

## 1. Transparent reference ladder

| Reference | Purpose | Information boundary |
|---|---|---|
| `random_no_commit` | Non-completing floor; no effective engagement decision. | no privileged state |
| `scripted_legal_heuristic` | Transparent non-learning reference using only each recipient's legal observation and valid delivered cache. | actor contract only |
| `scripted_oracle` | Evaluator-only physical reachability ceiling from N1. It is never a learned baseline. | true simulator state, calibration only |
| `vanilla_mappo_n2` | Shared-policy, centralized-critic MAPPO with a plain MLP actor and **no graph encoder**. | actor contract only; critic training-only state |

The scripted oracle must not be used to imitate, initialize, label, or select
the learning baseline. The N2 learning baseline has no graph aggregation,
relation module, gate, task-chain auxiliary loss, intent loss, or method claim.

## 2. Frozen mission reward

The N2 environment activates the N0 mission transition and uses the following
team reward only:

\[
r_t=0.12\,\operatorname{clip}\left((\bar d_{t-1}-\bar d_t)/1000,-1,1\right)-0.01
\]

plus terminal additions `+5` for `NEUTRALIZED`, `-5` for `COLLISION`, `-4` for
`CONSTRAINT_FAILURE`, `-3` for `TARGET_ESCAPE`, and `-1` for `TIMEOUT`.
Distance is an evaluator-computed true physical potential; it does not enter an
actor feature. There is no reward term for sensing, packet delivery, cache age,
communication adjacency, graph relation, `chain_closed`, attack-window,
physical-engagement readiness, or `engage_commit` by itself. The legacy reward
remains unchanged when the mission extension is disabled.

## 3. Minimal development pilot

Before the pilot, use the frozen nominal environment:

- mission neutralization enabled; `engage_commit_hold_steps=4`;
- `target_escape_radius=35,000 m`; administrative horizon 360;
- primary evaluation endpoint `RMTN180` with the N1 outcome decomposition;
- `strict_target_sensing=True` and `agent_target_info_bottleneck=True`;
- delivered/cache-valid packet semantics from N1;
- no failure curriculum, no reward tuning, no graph input, no auxiliary loss.

The pilot uses exactly two development-only seeds and the following frozen
common budget. These seeds and episodes cannot become F1/F2 seeds.

| Item | Frozen N2 value |
|---|---:|
| training seeds | `7201`, `7202` |
| updates per seed | 60 |
| parallel environments | 4 |
| rollout steps | 128 |
| PPO epochs | 4 |
| actor/critic hidden size | 128 |
| learning rate | `3e-4` |
| evaluation episode seeds | `730000`--`730047` (48 paired episodes) |
| learning checkpoint | final update 60 only; no selection search |

The evaluation bank is generated and used only after both development runs
finish. Its paired use across the two learned checkpoints, the legal heuristic,
and the random floor is for diagnostics only, never formal evidence.

## 4. Reward-hacking audit

Deterministic tests must establish all of the following before any pilot:

1. the mission reward cannot call communication, message-age, graph or attack
   geometry proxy functions;
2. changing only chain/cache/communication fields cannot change mission reward;
3. only the frozen terminal outcomes change terminal reward; and
4. the 3DOF training factory propagates the mission horizon, escape radius,
   action cardinality and strict actor-information switches.

The terminal transition itself remains covered by N0/N1: no cache, graph,
chain or proxy manipulation can produce mission success without four true
kinematic committed transitions.

## 5. N2 GO / NO-GO rule

After the two-seed pilot, N2 may pass only if all of these are true on a
development-only evaluation bank fixed before the pilot:

1. vanilla MAPPO has neutralization incidence above the `random_no_commit`
   floor and at least one observed `NEUTRALIZED` episode;
2. its pooled `RMTN180` is below 180 (the endpoint is not universally
   saturated);
3. it remains at least 10 percentage points below the N1 oracle's 97.9%
   neutralization incidence, so the task is not at an immediate oracle ceiling;
4. terminal outcomes are recorded and no apparent improvement is bought by an
   unexplained increase in collision or constraint-failure incidence; and
5. no NaN, invalid action interface, actor-information deviation, or reward
   hacking audit failure occurs.

A failure is diagnostic, not an invitation to add an architecture. First
classify it as reward/task-protocol inadequacy (for example no terminal reward
delivery) or observability inadequacy (for example legal target information is
almost never available). Only a bounded repair to that identified task issue
may be proposed; it requires separate authorization. N2 does not authorize
F1, F2, OOD, ablation, or a headline method.
