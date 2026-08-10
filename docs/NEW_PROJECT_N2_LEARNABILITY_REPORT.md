# N2 learnability check report

**Verdict:** `N2_LEARNABILITY_NO_GO__TASK_PROTOCOL_REPAIR_REQUIRES_NEW_AUTHORIZATION`.

This is a development-only task diagnostic. It is not a comparison between
algorithms and creates no paper performance result, candidate main method, or
authorization for cloud execution, N3, formal training, OOD, or ablations.

## Frozen pilot completed

The pilot followed `NEW_PROJECT_N2_LEARNABILITY_PROTOCOL.md` without a
checkpoint search:

- plain no-graph, shared-policy CTDE MAPPO only (`vanilla_mappo_n2`);
- development training seeds `7201` and `7202`, 60 updates each, four parallel
  environments, 128 rollout steps and four PPO epochs;
- final-update checkpoints only;
- a fixed 48-seed paired development bank (`730000`--`730047`);
- random no-commit and a scripted controller that reads only legal actor
  observations; and
- N1's scripted oracle only as the pre-existing reachability reference (97.9%
  neutralization), never as a learned-policy input, initializer or selector.

Raw development artifacts are intentionally untracked under
`results/new_project_n2_development_pilot/`.

## Outcome

| Controller | Episodes | RMTN180 | Neutralization by 180 | Terminal failure by 180 |
|---|---:|---:|---:|---:|
| random no-commit | 48 | 180.0 | 0.0% | 97.9% |
| scripted legal heuristic | 48 | 180.0 | 0.0% | 100.0% |
| vanilla MAPPO seed 7201 | 48 | 180.0 | 0.0% | 100.0% |
| vanilla MAPPO seed 7202 | 48 | 180.0 | 0.0% | 79.2% |
| pooled vanilla MAPPO | 96 | 180.0 | 0.0% | 89.6% |

The frozen N2 GO rule requires at least one learned neutralization, learned
neutralization above the random floor, and pooled RMTN180 below 180. All three
conditions failed. This result is sufficient to block N3; it is not evidence
that an alternative neural architecture would fail or succeed.

## Reward and information checks

Before the pilot, deterministic checks passed:

- N2 mission reward does not call communication, age, graph or attack-window
  proxy functions;
- changing only chain/cache/communication cannot alter mission reward;
- only frozen physical terminal outcomes alter terminal reward; and
- the training factory propagates the 54-action interface, 360-step horizon,
  35 km escape threshold and strict recipient-specific target contract.

N0, N1 and actor-boundary regression suites also remained green (7/7, 4/4 and
14/14 respectively).

The post-pilot read-only observability audit did **not** find an information
absence explanation. In the same frozen task, legal target-relative evidence
was available for roughly 0.67--0.76 of actor time steps across Scout, Relay and
Attacker roles; the attacker had positive direct-sensing exposure and more than
114 cache-confidence-positive steps per episode on average. The audit reads
only actor-observable fields and never target truth. Its raw output is under
`results/new_project_n2_observability_audit/`.

## Interpretation and permitted next decision

The task is physically reachable under N1's true-state oracle but is not
learnable by the prescribed transparent baseline at this small frozen pilot
budget. Since legal target evidence is frequently available, the current best
classification is **task/reward/control learnability inadequacy**, not a simple
actor-observability absence. Likely contributors must remain hypotheses until a
separately authorized task-protocol repair: sparse four-step commitment credit,
escape pressure, and the current physical-control curriculum.

No architecture change, extra training, seed replacement, reward tuning or
cloud run is authorized by this report. A future repair proposal must identify
one task-level cause, change only that cause, add deterministic tests, and
repeat N2 from a new development manifest before any method design begins.
