# 6-UAV V2 task-discrimination screening findings

**Status:** protocol-design screening only; not manuscript evidence and not a
performance comparison.

## What was read

Three completed frozen UTR V2 endpoints (training seeds 69021–69023) were
replayed once per topology group under five declared candidate settings. No
policy weights, optimizer state, sampler, or source checkpoint was written.

## Observed screening pattern

| Candidate | Nominal success | Perturbed success | Interpretation |
| --- | ---: | ---: | --- |
| V2 reference | 1.000 | 1.000 | Ceiling; effective faults do not change the endpoint. |
| Moderate route, cache horizon 1 | 0.667 | 0.667 | Some nominal seed variation, but no topology-group separation. |
| Moderate route, distance 40, cache horizon 1 | 0.000 | 0.000 | The frozen policy no longer solves the nominal task. |
| Long route, cache horizon 5 | 0.000 | 0.000 | Nominal task is not learnable for the frozen endpoint. |
| Long route, cache horizon 2 | 0.000 | 0.000 | Nominal task is not learnable for the frozen endpoint. |

## Decision

The screen does not identify a valid task from geometry and cache-freshness
changes alone. In particular, an effective fault is insufficient: the current
failure family preserves alternate routes and/or cached support, so completion
does not require a policy to react to topology loss. Conversely, simply
increasing terminal travel distance moves the frozen policy outside its
learnable operating regime.

Therefore no 6-UAV V3 training protocol is authorized from this screening.
A future cross-scale experiment needs a separate task-dependence design review
that creates sustained, legal post-fault coordination demand while retaining
nominal solvability. It must then undergo a fresh zero-training calibration
before any UTR/DRTP training is started.
