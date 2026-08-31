# Intervention Utility P0 readiness report

**Decision:** `HISTORICAL_EXACT_COUNTERFACTUAL_NOT_FEASIBLE`

P0 was a read-only audit of `drtp_klr_final_replication_p3_05m_results.tar.gz`. It did not restore a checkpoint, run an environment, evaluate a policy, modify DRTP, or authorize Selective-KLR.

## What the archive establishes

- The complete frozen trigger population contains **60** `post-step KL > 0.02` events across seeds 3701--3710 and 78,106 attempted guarded actor steps.
- Per-seed event counts are 7, 5, 1, 8, 7, 3, 6, 9, 4 and 10. These events are within-seed technical repetitions, not 60 independent scientific replications.
- The archive retains 30 runtime state files, but all are `250k`, `500k`, or `latest` milestones.
- It contains **zero** trigger-linked pre-update runtime snapshots. Thus a historical accept-versus-rollback branch would not start from the same actor, critic, optimizer, environment, rollout, RNG, and minibatch state.

The audit also confirms that the current implementation has the building blocks for a future prospective study: actor/Adam transaction snapshots, full model/optimizer transaction snapshots, environment runtime capture, and Python/NumPy/Torch RNG capture. Those capabilities are not evidence that historical branches can be reconstructed after the fact.

## Scientific consequence

The observed fact that KLR helped some final seeds and harmed others is sufficient to reject unconditional rollback. It is **not** evidence that a short-horizon accept-versus-rollback utility test can predict which intervention is beneficial. That proposition remains untested.

## Only valid next study, if separately authorized

A future `P1_PROSPECTIVE_INTERVENTION_UTILITY_AUDIT` must be instrumented at the trigger instant during a new, explicitly exploratory trajectory:

1. Let the official trajectory follow Original DRTP; KL is an alarm only, not an automatic rollback.
2. At every frozen `post-step KL > 0.02` alarm, atomically save the complete pre-trigger state and the attempted post-update actor state.
3. Spawn accept and rollback **shadow** branches from that same state, each with copied actor/critic/optimizer/sampler/environment/RNG state and an identical future seed schedule.
4. Use a pre-frozen short continuation and a disjoint training-only paired probe to compare branch utility. Shadow rollouts and probes must never enter the official PPO buffer or the formal evaluation tape.
5. Record all additional branch/probe interactions. A later selector cannot claim equal interaction cost without these records.
6. Analyse every alarm, not retrospectively selected good/bad examples. Training seed, rather than alarm event, remains the replication unit.

P1 must be an observational shadow audit: it does **not** permit selecting a branch for the official trajectory, changing PPO, or training a Selective-KLR policy. Only if it shows a time-leading, cross-seed, out-of-sample separation between helpful and harmful rollback events may one minimal selector be designed under a separate contract.

## Required authorization boundary

P0 authorizes nothing further. The next decision is whether to authorize prospective trigger-snapshot instrumentation and shadow branches. It must specify fresh seeds, branch horizon, training-only probe, maximum trigger handling cost, integrity tests, and GO/NO-GO thresholds before any cloud trajectory begins.
