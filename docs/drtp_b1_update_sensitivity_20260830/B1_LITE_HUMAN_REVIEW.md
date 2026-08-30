# B1-Lite human review

**Decision:** `UPDATE_RELIABILITY_MECHANISM_NO_GO`.

## Scope and provenance

The reviewed product is `DRTP-B1-UPDATE-SENSITIVITY-LITE-V1` from the 320
completed, frozen 64-update continuations of the 40 paired 0.5M source
checkpoints.  It uses no new environment episode (`environment_episodes = 0`).
The stopped 64,000-episode endpoint evaluation is excluded; its partial rows
are not evidence.

The decision is about the proposed *DRTP-specific short-horizon update
sensitivity* mechanism.  It does not alter the factual outcomes of any prior
cohort and does not establish that MARL optimisation is generally reliable.

## Frozen criteria not met

The original B1 mechanism gate required all of the following: a replicated
adverse/catastrophic DRTP signature in at least two cohorts, presence by update
16, excess over paired UTR on at least two primary metrics, weak positive
controls, held-out B5 replication, and a later endpoint consequence.  B1-Lite
cannot satisfy the endpoint requirement because the full tape evaluation was
aborted for compute and is explicitly excluded.  More importantly, its
update-level evidence does not form the required precursor signature.

At update 16, the DRTP-minus-UTR median actor-delta cosine distance was
negative for catastrophic seed 2403 (-0.1338) and only +0.0192 for
catastrophic seed 3001.  Their policy-JS differences were respectively
+0.0211 and +0.0005.  Thus the two catastrophic source seeds do not share a
large, time-leading, DRTP-specific two-metric signature.

The held-out adverse B5 seed 3605 had positive actor and policy-JS differences
at update 16 (+0.2402 and +0.0397), but this pattern was absent in the 2400
catastrophic seed and weak in the 3000 catastrophic seed.  At update 64, 3001
did show elevated actor divergence (+0.3004) and policy JS (+0.0538), whereas
2403 instead had lower actor divergence than its UTR control (-0.2722).  This
is a seed-specific pattern, not a reproducible mechanism.

Across all six adverse DRTP seeds, the mean DRTP-minus-UTR actor-divergence
difference was only +0.0165 at update 16 (median -0.0231); the corresponding
policy-JS difference was +0.0134 (median +0.0075).  Branch-level KL, value
loss, advantage-scale, and training-reward dispersions were mixed rather than
consistently elevated in adverse DRTP seeds.

## Interpretation and boundary

The rollout-stream perturbation produces substantial policy/parameter
variation for both UTR and DRTP.  The minibatch negative control is generally
near zero through update 16, as expected from the one-full-rollout-minibatch
configuration.  Neither fact identifies an Original-DRTP-specific failure
mechanism.

No Reliable-DRTP, update guard, threshold change, seed replacement, or new
stabilisation candidate is scientifically authorised from B1.  The B-line must
not return to local sampler/rollback/probe/selector patching based on these
data.
