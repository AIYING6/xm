# N2 Guidance-Level Task-Interface Repair Report

## Verdict

`N2_GUIDANCE_REPAIR_NO_GO__BENCHMARK_LEARNABILITY_NOT_ESTABLISHED`

This was the single authorized task-interface repair. It is development-only
and produces no paper performance evidence.

## Frozen change

The actor output was changed from the original 27 low-level flight actions to
9 turn/climb guidance commands (with the unchanged `engage_commit` extension,
18 total action values). A deterministic controller supplied the acceleration
command by tracking each vehicle's own midpoint speed. The controller used no
target state, global truth, communication state, graph state, or reward signal.

Unchanged: mission physics, four-step hold, failure precedence, target escape,
reward, actor information contract, RMTN180, episode horizon, evaluation seeds,
network, PPO budget, and `engage_commit` semantics.

## Development result

Two seeds were trained for the same 60 updates and evaluated on the same 48
fixed episode seeds as N2. Random guidance baseline and both learned policies
all had zero neutralization incidence by 180 steps and RMTE/RMTN contribution
equal to 180.

| controller | episodes | neutralization by 180 | RMTN180 | terminal failure by 180 |
|---|---:|---:|---:|---:|
| random guidance | 48 | 0.000 | 180.0 | 0.5625 |
| MAPPO guidance seed 7201 | 48 | 0.000 | 180.0 | 0.4792 |
| MAPPO guidance seed 7202 | 48 | 0.000 | 180.0 | 0.8958 |

The pooled learned result is 0/96 neutralizations and RMTE180=180.0. Thus
the repair did not establish a stable geometry-entry or mission-completion
learning signal. The increased active-unneutralized probability in seed 7201
does not meet the predefined GO condition and cannot be treated as evidence of
progress.

## Decision

The benchmark remains not learnable with transparent vanilla MAPPO under the
single authorized interface repair. Per the frozen decision rule, stop the new
mission line here. Do not add another task-interface repair, reward change,
training budget, network, or formal training stage.

Artifacts:

- `results/new_project_n2_guidance_repair/N2_GUIDANCE_REPAIR_MANIFEST.json`
- `results/new_project_n2_guidance_repair/summary.csv`
- `results/new_project_n2_guidance_repair/N2_GUIDANCE_REPAIR_VERDICT.json`
