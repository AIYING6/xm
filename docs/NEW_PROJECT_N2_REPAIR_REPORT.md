# N2 reward-repair report

**Verdict:** `N2_REPAIR_NO_GO__TASK_LEARNABILITY_NOT_ESTABLISHED`.

This was the single authorized N2 repair. It is development-only evidence and
does not authorize N3, formal training, cloud execution, OOD or a new method.

## Repair fidelity

The only changed factor was
`mission_progress_shaping_enabled=True`. The added term was

`0.25 * (0.99 * Phi(next_state) - Phi(state))`,

with `Phi` composed only of physical relative distance progress, line-of-sight
heading alignment, relative closing velocity, and the existing true
four-transition commit-hold fraction. The following were unchanged: N0
mission transition, action space, actor information contract, terminal outcome
taxonomy and priority, target escape, horizon 360, `RMTN180`, vanilla no-graph
MAPPO, seeds `7201/7202`, 60 updates, rollout and PPO settings.

Deterministic reward sanity passed 5/5; N0, N1 and actor-boundary regressions
remained 7/7, 4/4 and 14/14.

## Re-test result

The same 48 paired evaluation seeds were used for each controller. The two
repair checkpoints completed 60 updates and produced complete raw outputs.

| Controller | Episodes | RMTN180 | Neutralization by 180 | Terminal failure by 180 |
|---|---:|---:|---:|---:|
| random no-commit | 48 | 180.0 | 0.0% | 97.9% |
| scripted legal heuristic | 48 | 180.0 | 0.0% | 100.0% |
| repair MAPPO seed 7201 | 48 | 180.0 | 0.0% | 100.0% |
| repair MAPPO seed 7202 | 48 | 180.0 | 0.0% | 100.0% |
| pooled repair MAPPO | 96 | 180.0 | 0.0% | 100.0% |

The repair therefore did not produce a non-zero learning signal under the
frozen short N2 budget. It neither surpassed random nor approached the N1
oracle ceiling. The result cannot support a claim that the task is learnable,
and it cannot justify changing the policy architecture.

## Project decision

The new mission project stops at
`N2_REPAIR_NO_GO__TASK_LEARNABILITY_NOT_ESTABLISHED`. No additional reward
shaping, action-space change, horizon change, target-policy change, seed
replacement, longer training or cloud run is authorized by this gate.

The remaining scientifically defensible choices are to archive this task as a
negative learnability result or to propose a separately reviewed new task-level
protocol change with a new N0/N1/N2 chain. N3 method selection is not entered.
