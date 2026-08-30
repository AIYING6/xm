# DRTP B1 update-reliability mechanism contract

## Objective

B1 tests one mechanism and does not search for an algorithm: whether a frozen
Original-DRTP state that later produces a poor or catastrophic result is
already unusually sensitive to future rollout/update randomness. The model,
optimizer, DRTP q/EMA/window state, environment state, reward, PPO constants,
and actor information boundary are identical at each source checkpoint.

The causal manipulation begins only after the 0.5M runtime checkpoint. It
replaces either future rollout streams (environment, stochastic action, and
topology draws) or the minibatch stream. Each RNG branch is a technical
repetition. The source training seed remains the independent unit.

## Source cohorts

The experiment uses every paired UTR/Original-DRTP 0.5M runtime checkpoint in
four already-completed cohorts: 2301--2305, 2401--2405, 3001--3005, and
3601--3605. No source seed or checkpoint is selected after branch results are
seen. Historical final outcomes are used only to define source-state classes.

- 2400 and 3000 are discovery cohorts.
- 2300 is the stable/high-return control cohort.
- 3600 is the branch-result holdout replication cohort.

## Branch design

Each of the 40 source checkpoints receives four rollout-RNG branches and four
minibatch-RNG branches. Every branch runs exactly 64 PPO updates (16,384
environment interactions), with diagnostic snapshots after 1, 4, 16, and 64
updates. The total is 320 short branches and 5,242,880 environment steps.

The minibatch family is a preregistered negative control. The frozen PPO setup
uses a 4x64 rollout and `minibatch_graphs=256`, hence one complete-rollout
minibatch per epoch. Reordering all 256 samples should have negligible effect;
its inclusion tests implementation and numerical coupling rather than serving
as a plausible main mechanism.

## Evidence and gate

Primary readouts are cumulative actor-update direction dispersion, fixed-bank
policy-output divergence, and short fixed-tape endpoint dispersion. KL, critic
drift, explained variance, advantage statistics, training reward, collision,
and timeout are secondary time-aligned evidence.

`UPDATE_RELIABILITY_MECHANISM_PASS` requires every condition in
`configs/drtp_b1_update_sensitivity_freeze.json`. In particular, the same
time-leading signature must repeat in at least two adverse/catastrophic DRTP
seeds from at least two cohorts, exceed matched UTR, remain weak in good DRTP
controls, and reproduce in the held-out 3600 cohort. Leave-one-branch-out
analysis must not change the decision.

If any conjunctive condition fails, the result is
`UPDATE_RELIABILITY_MECHANISM_NO_GO`. No Reliable-DRTP design is then
authorized by B1.

## Current authorization boundary

This document freezes the scientific design only. It does not authorize cloud
execution or any algorithm modification. Mainline A is unchanged.
