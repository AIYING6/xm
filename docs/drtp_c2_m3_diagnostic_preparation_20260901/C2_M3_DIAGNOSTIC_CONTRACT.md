# C2-M3 telemetry-first diagnostic contract

**Status:** `M3_READY_FOR_AUTHORIZATION`; training is not authorized.

## Scientific question

Can a training-only measurement, recorded before performance divergence, repeatedly distinguish a group-weighted PPO trajectory helped by weighting from one harmed by weighting? This is a diagnostic experiment, not C2-v2 and not a new stabilizer trial.

## Frozen design

- Cohort A: 5101–5105; Cohort B: 5106–5110. The provenance scan found no source/configuration/document occurrence for these seeds.
- Arms: fixed-stratified UTR with ordinary PPO, and the frozen C2 group-weighted UTR candidate. No Original-DRTP reference arm is needed for this causal comparison.
- 1,953 updates / 499,968 environment steps per trajectory; 20 trajectories total.
- Fixed milestones: 125k, 250k, 375k, 500k. Later evaluation of every fixed checkpoint requires a separately frozen post-hoc tape and cannot select or promote a checkpoint.
- Training-only telemetry: group credit and failure-aware role behavior, each default-off except in this diagnostic contract; group credit every 32 updates. It cannot enter PPO, the sampler, reset selection or evaluation.

## Analysis and stop rule

Outcome labels are assigned only after all runs and all fixed checkpoint evaluations finish; they are never online inputs. Cohorts are analysed separately, with training seed—not update, group or episode—as the independent unit.

An actionable candidate requires, in **both** cohorts: at least two rescue and two harm seeds, a repeated training-only signal preceding checkpoint task divergence, and one signal-to-one-minimal-intervention mapping. Failure of any condition is `M3_NO_ACTIONABLE_MECHANISM`; no tuning, rerun, continuation or new algorithm follows automatically.

## Required preflight

The M2 measured overhead (about 4.3% wall-clock and 36.3 MB for 128 updates) must be recorded again on the chosen cloud image. Any trajectory-equivalence, writer, save/resume, disk or tape-isolation failure stops before scientific training.
