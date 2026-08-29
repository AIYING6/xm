# Stable-v2 D6 sampler-feedback forensic contract

## Scope

D6 is a zero-training, read-only forensic analysis of the completed D5 pilot:
`UTR / Original DRTP / DRTP-KLB × seeds 3201--3203 × 0.5M`.

It may read only the D5 final evaluation CSV, the three Original DRTP and three
DRTP-KLB training logs, and their sampler logs. It must not create an
environment, evaluate a checkpoint, alter a checkpoint, select a checkpoint,
modify a sampler, or start training.

Mainline A is out of scope. D5 development seeds and D6 outputs must not be
merged into Mainline-A formal or independent-cohort statistics.

## Scientific question

Does the D5 record support the limited temporal pattern

\[
\text{KLB actor intervention}
\rightarrow
\text{paired sampler-}q\text{ divergence}
\rightarrow
\text{more non-uniform sampling and poorer D5 endpoint outcome}?
\]

This is **not** a test of the cause of Original DRTP seed sensitivity. It is
only a forensic test of why the KLB candidate can worsen an otherwise matched
trajectory.

## Frozen evidence and criteria

For each seed, D6 records the first KLB trigger, the first paired sampler
divergence, KLB-versus-Original mean distance from uniform, and final paired
robust-mean gain. The temporal-feedback pattern is supported only when all
three seeds satisfy all of the following:

1. the first sampler divergence follows the first KLB trigger;
2. mean sampler distance from uniform is greater under KLB than Original DRTP;
3. KLB's final paired robust-mean gain is no greater than Original DRTP's.

Passing this pattern authorizes **only** a PP-DRTP design audit: a future
candidate may estimate group difficulty from balanced, paired, training-only
probe rollouts rather than the exposure-dependent training stream. It does not
authorize implementation, hyperparameter selection, cloud training, a
checkpoint evaluation, or a claim that sampler feedback is the cause of
Original DRTP instability.

If any required D5 artifact is incomplete or any criterion is not satisfied,
the decision is `D6_NO_GO_NO_NEW_CANDIDATE_AUTHORIZED`.
