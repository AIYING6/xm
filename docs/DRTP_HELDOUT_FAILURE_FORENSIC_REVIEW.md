# DRTP Held-out Failure Zero-training Forensic Review

**Classification: C — no actionable cause / intrinsic seed sensitivity.**

This is a retrospective, zero-training review of the completed held-out v2
experiment. It does not revise the historical `HELD_OUT_FAIL`, promote an
intermediate checkpoint, exclude a seed, alter DRTP/UTR, or authorize a new
training stage.

## Scope and evidence

The primary failed case is DRTP-SG seed2002. Controls are held-out DRTP-SG
seeds2001/2003, held-out UTR-SG seed2002, and the completed development DRTP
seeds1901/1902. The review used final and 0.5M-spaced model checkpoints,
runtime states, sampler weight/EMA/difficulty logs, complete PPO training logs,
and the completed 430000--430099 final-checkpoint evaluation.

The independent unit is the training seed. The 100 evaluation episodes per
condition are repeated measurements of a trained seed, not independent method
replicates. Consequently, this report makes no p-value or population-level
superiority claim from the three held-out seeds.

## Integrity and boundary checks

All six held-out runs completed 39,063 updates (10,000,128 environment steps)
from scratch with strict continuous trajectories, no runtime resume or warm
restart, and complete runtime-state persistence. Each archived final model and
runtime-state SHA256 matches its run manifest. The final evaluation comprises
6 x 12 x 100 = 7,200 raw rows on the frozen held-out tape.

The retained milestone checkpoints are used below only for parameter-trajectory
forensics. No held-out intermediate-checkpoint scores existed in the frozen
confirmation contract; the final 10M checkpoint remains the sole confirmatory
result. Thus the exact *first held-out-score* divergence cannot be dated
without a new, retrospective evaluation and must not be inferred as if it had
been measured.

## Observed outcome failure

| Seed | Arm | J nominal | J F0 | J OOD mean | J OOD worst | Timeout | Exposure |
|---|---|---:|---:|---:|---:|---:|---:|
| 2001 | UTR | 99.223 | 102.603 | 91.713 | 77.737 | 0.935 | 1.000 |
| 2001 | DRTP | 248.282 | 206.868 | 198.913 | 170.363 | 0.478 | 0.964 |
| 2002 | UTR | 187.061 | 186.921 | 176.961 | 150.697 | 0.515 | 1.000 |
| 2002 | DRTP | 170.807 | 72.970 | 88.835 | 53.597 | 0.906 | 1.000 |
| 2003 | UTR | 194.740 | 197.038 | 196.390 | 186.628 | 0.886 | 1.000 |
| 2003 | DRTP | 245.390 | 226.842 | 222.695 | 210.316 | 0.795 | 0.978 |

The seed2002 reversal is genuine: it occurs with 100% failure exposure and is
therefore not attributable to a missed failure event. Relative to UTR seed2002,
DRTP seed2002 is lower by 113.951 on F0, 88.126 on OOD mean, and 97.100 on OOD
worst, while timeout is higher by 0.392.

## Timing of the observed training divergence

The earliest internal divergence appears by approximately 1M steps, not as a
late 9M--10M collapse. At the 1M-adjacent sampler update, seed2002 DRTP had
EMA nominal/F0/mean-other-group returns of 56.2/52.9/46.2, compared with
114.9/94.7/94.6 for UTR seed2002. By about 3M, DRTP seed2002 recovered to
181.1/159.5/152.2, and it later remained in an approximately 170--207 range.

This establishes an early, gradual internal learning deficit followed by
partial recovery. It does not establish the exact timing of the final held-out
F0/OOD failure, because per-milestone held-out evaluation was intentionally not
part of the confirmation protocol.

## Adaptive-weight and group-return audit

At the first 0.5M milestone, seed2002 already allocated the failure-group
weights as F0=0.07, TE=0.05, TL=0.09, DS=0.10, DL=0.34, and CP=0.35. Its
terminal distribution was F0=0.07, TE=0.22, TL=0.05, DS=0.05, DL=0.25, and
CP=0.35. Thus F0 was persistently de-emphasized while CP and DL were often at
or near the bounded maximum.

Across actual training selections, seed2002 received 1,424 F0 episodes versus
3,321 for UTR seed2002, while CP and DL received 6,588 and 5,186 episodes.
This is compatible with adaptive under-exposure of F0.

However, it is not an identifiable seed2002-only defect. Successful DRTP
seed2001 also finished with F0=0.07 and successful development seed1901
finished with F0=0.05, while held-out seed2003 allocated even more cumulative
CP/DL exposure than seed2002 and still achieved the best held-out DRTP result.
Therefore low F0 probability and CP/DL concentration are plausible correlates,
not a falsifiable single cause of the seed2002 failure.

The seed2002 group EMAs were low early but recovered: terminal training EMAs
were F0=187.6 and mean other-group EMA=187.4, close to UTR seed2002's
F0=192.4 and mean other-group EMA=187.2. The severe final held-out F0 gap is
therefore a generalization/outcome discrepancy not explained by a persistent
training-group return collapse.

## PPO and checkpoint-trajectory audit

No identifiable generic PPO instability was found. In the late 5M--10M phase,
DRTP seed2002 had mean value loss 0.510, gradient norm 4.69, approximate KL
0.00150, clip fraction 0.0137, and explained variance 0.974. These values are
comparable to UTR seed2002 (0.573, 4.76, 0.00164, 0.0155, and 0.970) and are
not more extreme than the successful DRTP seeds.

The maximum and 95th-percentile gradients for DRTP seed2002 (54.97 and 12.35)
were lower than those for successful DRTP seed2001 (147.47 and 22.11) and
seed2003 (113.86 and 19.09). KL and clip-fraction extrema likewise show no
seed2002-specific explosion. PPO diagnostics do not support classification B.

Checkpoint parameter displacement also provides no late-collapse signature.
The normalized 9.5M--10M model displacement was 0.149 for DRTP seed2002,
within the same order as held-out DRTP seed2001 (0.138), seed2003 (0.133), and
UTR seed2002 (0.144). The largest displacement
for all reviewed trajectories occurred in the initial 0.5M--1M interval.

## Timeout audit

The final held-out timeout deterioration is established (0.906 for DRTP versus
0.515 for UTR in seed2002). Training-time evaluation was disabled by contract,
and the training logs contain no per-episode timeout series. Its first onset
and temporal synchronization with PPO quantities are therefore not observable
from existing evidence. This is a data-boundary finding, not evidence that the
timeout increase began late in training.

## Failure-mechanism decision

No single major mechanism meets the requested standard of being both supported
by existing evidence and falsifiable without adding unplanned measurements:

- Early DRTP weight concentration and low F0 exposure are associated with the
  seed2002 failure, but occur in successful DRTP seeds as well.
- Generic PPO numerical instability is contradicted by the diagnostic ranges
  and checkpoint trajectory.
- A late parameter collapse is not supported.
- Timeout onset cannot be temporally localized with the recorded data.

The only defensible classification is **C — no actionable cause / intrinsic
seed sensitivity under the current adaptive-weighting protocol**.

## Required stop and route consequence

The current DRTP adaptive-weighting route should be permanently closed as a
paper-main-method candidate. No minimal stability fix is proposed because no
identifiable A/B mechanism was established. The historical held-out `FAIL`
remains unchanged; canonical training, five-seed confirmation, ablations, new
algorithms, and retraining remain unauthorized. Any later work must begin with
a separately authorized scientific-route decision, not an attempt to repair or
re-run this DRTP result.
