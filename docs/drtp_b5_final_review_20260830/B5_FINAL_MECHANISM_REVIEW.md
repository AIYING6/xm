# DRTP B5 final human mechanism review

**Decision:** `B5_MECHANISM_NO_GO`.

## What the experiment established

At 1M, Original DRTP exceeds paired UTR on `J_pert_mean` in 4/5 training seeds. The seed-level mean and median gains are 22.789 and 39.685, but the minimum gain is -53.441 and the sample SD is 49.780. Thus B5 preserves evidence of high-return potential while independently reproducing substantial training-seed risk.

The milestone directions are non-monotonic. Seeds 3601--3603 are adverse at 750k and recover by 1M, seed 3604 remains positive, and seed 3605 ends adverse. Failure-versus-nominal value residuals, TD residuals, normalized advantages, actor/critic gradient norms, nominal--failure gradient conflicts, and group-stratified training behavior do not form one direction-consistent precursor that repeats in at least two final adverse DRTP seeds and is absent from paired UTR.

## Frozen-gate outcome

All six frozen requirements were conjunctive. None can rescue the failed 2/5 adverse-seed replication requirement: only seed 3605 is paired-adverse at 1M. The changing signs across 250k, 500k, 750k, and 1M also prevent a continuous time-leading optimization-to-behavior-to-outcome chain. Because no complete candidate signature exists, neighboring-threshold robustness is not satisfied rather than retrospectively redefining a signal.

Accordingly, failure-group-conditioned credit assignment is **not supported as a stable actionable mechanism** by B5. No DRTP patch, Stable-v2, continuation, seed replacement, or performance-driven rerun is scientifically authorized under this contract.

## Statistical boundary

The independent unit is the training seed (`n=5` per arm). Update-by-group rows, gradient-pair rows, and episodes are technical repetitions used for descriptive time alignment only. No episode-level or update-level pseudo-replication, null-hypothesis test, or invented p-value is used.

## Project consequence

This decision does not modify mainline A and does not negate DRTP's observed upper-tail or mean gains. It closes the specific B5 credit-assignment mechanism route. A future optimization-reliability study would require a newly framed project and independent evidence; it must not be presented as an authorized continuation of B5.
