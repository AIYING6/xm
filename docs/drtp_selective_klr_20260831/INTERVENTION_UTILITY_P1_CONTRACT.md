# Selective-KLR Intervention Utility: P1 prospective shadow audit

**Status:** `INTERVENTION_UTILITY_P1_AUTHORIZED`  
**Selective-KLR training:** `NOT AUTHORIZED`  
**Mainline A:** `UNCHANGED`  
**Automatic continuation:** `NOT AUTHORIZED`

## Question

When the unmodified Original-DRTP PPO trajectory produces a post-step empirical KL alarm above `0.02`, does a deterministic short-horizon, training-only paired probe show that restoring the pre-update actor is better, worse, or practically indistinguishable from retaining the attempted actor update?

P1 measures the intervention utility at each alarm.  It does not train a selector and does not allow an alarm result to change the official trajectory.

## Frozen protocol

- Official trajectories: Original DRTP only, seeds 3801--3810. Cohorts A (3801--3805) and B (3806--3810) remain separate.
- Official budget: 1,953 updates / 499,968 environment steps per seed. Milestones 250k and 500k are descriptive only.
- Every `KL > 0.02` alarm is enrolled. No seed, alarm, threshold, branch horizon, or result may be selected after inspection.
- At each alarm the system preserves pre/post model and optimizer states, global and stream RNG state, environment state, sampler state, rollout tensor and minibatch order in a trigger-linked snapshot.
- `accept`: post-step actor. `rollback`: copied pre-step actor while retaining the same post-step critic, matching the historical KLR intervention semantic.
- Each branch runs the same four base IDs across the seven supported topology groups. Probe episodes are deterministic, training-only, and excluded from both the PPO buffer and every formal/held-out evaluation tape.
- The official actor is restored to the accepted post-step actor before training continues. Any model or optimizer mutation after a callback is a technical failure.

## Interpretation boundary

The primary shadow endpoint is the mean episode return over the six failure groups, with nominal return, collision, timeout and step count retained as secondary outcomes. The frozen practical margin is `7.874919837916801`; it is used only to classify probe differences as practically positive/negative/near-zero. Trigger rows are technical repetitions: the independent scientific unit is the training seed.

P1 returns only `INTERVENTION_UTILITY_P1_READY_FOR_REVIEW` or `INTERVENTION_UTILITY_NO_GO`. No automatic mechanism claim, selector design, Selective-KLR training, continuation, seed replacement or parameter adjustment is permitted.
