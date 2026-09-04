# TGTR-PPO C1 final result

## Verdict

`TGTR_C1_NO_GO`

This is a training-only, same-rollout mechanism result. It is not a policy-performance evaluation and it used no formal, independent, or held-out evaluation tape.

## What was tested

Five completed UTR source states (2201--2205) supplied model and Adam states. For every source state, one deterministic 24 x 64 rollout contained 768 nominal graphs and 128 graphs from each of F0, TE, TL, DS, DL, and CP. Every group was split into fixed design and certificate streams. Matched ordinary PPO and TGTR consumed the same immutable rollout.

## Gate outcome

| Gate | Result | Evidence |
| --- | --- | --- |
| five exact complete batch pairs | PASS | all five batches contained the frozen seven-group counts |
| ordinary group-harm actuation | PASS | ordinary PPO harmed at least one certificate group in 4/5 states |
| TGTR certificate legality | PASS only by rejection | every proposed actor epoch was rejected, leaving a zero actor displacement |
| nonzero actor-step rate | FAIL | 0/5 states retained a nonzero final actor step; 20/20 epochs were zero steps |
| overall surrogate retention | FAIL | TGTR matched or exceeded ordinary in only 1/5 states because its accepted actor change was zero |
| cost | FAIL on local CPU | observed wall-time ratio was 8.81--9.68x; this is not the decisive failure because the nonzero-step and retention gates already failed |
| critic isolation | PASS | final critic parameters and Adam slots were copied from the matched ordinary transaction exactly |

At the smallest frozen backtracking scale (1/64), the worst certificate-group surrogate changes remained materially negative: approximately `-4.5e-6` to `-3.7e-5`, well beyond the fixed `1e-7` float32 tolerance. The zero-step outcome is therefore not a comparison-rounding artifact.

## Interpretation

The experiment validates the original diagnosis that a single ordinary PPO update can help the average while locally harming individual topology groups. However, the proposed design-to-certificate constraint does not generalize across the two fixed streams strongly enough to retain useful actor motion. The held-stream certificate turns TGTR into an actor freeze rather than a high-return stabilizer.

This rules out the frozen TGTR formulation. It does not justify relaxing the certificate after seeing the result, extending the backtracking grid, merging design and certificate streams, or starting the 0.5M fresh-seed pilot. Those changes would create a new post-hoc algorithm rather than validate this candidate.

## Project decision

- TGTR-PPO frozen candidate: closed.
- Fresh-seed 0.5M TGTR development: not authorized.
- Cloud repetition: not justified; the decisive mechanism gates are hardware-independent.
- Original DRTP/EGTR historical conclusions: unchanged.
- Next algorithm work, if continued, must return to mechanism design and cannot be presented as TGTR-v2.
