# C1 frozen contract: stable collection with group-weighted actor PPO

## Question

With the **same fixed-stratified training rollout**, does bounded, lagged
failure-group weighting improve the local actor surrogate for the most
TD-stressed group without materially harming the nominal surrogate or causing
an unstable PPO update?

This is not an end-to-end policy-performance study and it does not establish a
new algorithm.

## Frozen source and branches

- Sources: completed `utr_sg` runtime checkpoints for seeds 2201--2205 at
  update 3907.
- Collection: the existing fixed-stratified topology sampler.  It has no
  adaptive sampler state or feedback from difficulty to exposure.
- Shared prelude: one ordinary-PPO update produces lagged per-group mean
  absolute TD-residual scores.
- Branch A: resume the exact prelude runtime and perform one ordinary-PPO
  update.
- Branch B: resume the exact same prelude runtime, replay the exact same
  rollout, and change only the actor PPO policy term through the frozen group
  weights.

The common prelude converts the historical UTR checkpoint to standard PPO for
both branches.  C1 therefore makes no claim that this is a performance
continuation of the original T1 conditioned-actor UTR run.

## Candidate rule

- Nominal graphs always receive weight 1.
- Only failure graphs are reweighted.
- Score: lagged, training-only, per-graph mean absolute TD residual for each
  failure group.
- Strength: 0.25; bounds: [0.75, 1.25].
- Failure weights are frequency-normalized to have mean 1 in the following
  fixed-stratified rollout.
- Critic loss, entropy term, optimizer, PPO clipping, reward, environment and
  collection semantics remain ordinary PPO.

The C1-only post-update actor forward is diagnostic only: it consumes no
environment interaction and does not affect training, the sampler, or the
weights.

## Information boundary

No formal, independent, or held-out evaluation tape is read.  No evaluation
episode is run.  The training-only `condition_group` metadata is excluded from
the actor/critic inputs.  No final seed-quality label, future trajectory data,
or performance-based selection is used.

## Gate

`C1_PASS` requires all five exact batch pairs, non-uniform weight actuation in
each pair, at least 4/5 high-lagged-TD group surrogate improvements, nominal
non-harm in at least 4/5 seeds (and no seed below -0.005), and weighted
post-update actor KL at most 0.02 in every seed.  Otherwise the outcome is
`C1_NO_GO`.

Neither verdict authorizes C2, long training, a parameter sweep, or any
change to Mainline A.

## Method boundary

The construction follows PPO's clipped-surrogate update framework
([Schulman et al., 2017](https://arxiv.org/abs/1707.06347)) while using a
bounded group-aware weighting idea only as a local optimization audit.  It is
not group DRO: it neither treats episodes as independent training seeds nor
claims cross-seed risk optimization.
