# Minimum external evidence plan

This is a plan only. It authorizes no implementation or training.

## Smallest credible comparison set

1. Plain corrected SG-MAPPO;
2. UTR;
3. naive legal-event randomization;
4. one adaptive sampler: PLR;
5. one robust optimizer: Group-DRO **or** batch-CVaR/EPOpt, chosen before execution.

All arms must use the corrected role-specific learner, identical action masks, reward,
transitions, fault time, environment-step budget, fresh paired training seeds, and an
evaluation tape unavailable to training. The sampler or optimizer must use training-only
signals. The training seed—not episode—is the independent unit.

## Required decision dimensions

- nominal success and safety;
- each predefined topology group, including worst-group performance;
- collision and timeout separately;
- held-out structural faults not in the collection support;
- 4/6/8-UAV scale transfer if the manuscript claims a framework rather than one benchmark;
- wall-clock, environment-step, and parameter/forward-pass overhead.

No candidate can be removed, reweighted, or reconfigured after seeing development outcomes.
The current saturated UTR endpoint is not a reason to relax this plan; it makes above-UTR
method discrimination harder and increases the value of held-out/scale evidence.

