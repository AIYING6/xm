# S0 final decision — two-shot stabilization readiness

## `S0_READY_FOR_S1_AUTHORIZATION`

S0 is complete and has stopped. No training trajectory, environment rollout,
optimizer update, checkpoint evaluation rerun, cloud job, parameter sweep, or
third candidate version was started.

## Frozen values

| Item | Frozen value |
|---|---:|
| S1 candidate | DRTP-TR |
| final L1 cap, delta | 0.02513300038143937 |
| delta source | pooled label-free P90 of 12,781 valid final post-projection original-DRTP movements |
| epsilon_J | 7.874919837916801 |
| epsilon source | P90 of 100 absolute paired cross-tape endpoint differences for the same checkpoint |
| practical downside margin | strictly greater than 7.874919837916801 J units |
| S2 candidate | Conservative-DRTP only |
| S2 uniform anchor | 0.20 |
| S1 seeds | 2901, 2902, 2903 |
| S1 tape hash | 2ff360d6e240f6f9e3b7a5b74dc56db54da601e391bc259a5a51719d83fa7461 |
| first budget | 9 × 499,968 = 4,499,712 environment steps |
| maximum safe cloud concurrency estimate | 9 on one 12-GB RTX 3080 Ti, with one CPU thread per process |

## Audit disposition

- The sampler source inventory is hash-recorded and was selected without
  good/bad cohort labels.
- Recorded original q movements exceed the P90 cap at 10% by definition. A
  forced-target replay activates the cap at 15.98%; this is expected because
  prior clipping displaces candidate q from later recorded targets. It is an
  algebra check, not a counterfactual learning claim.
- All forced-target replay outputs passed final L1, simplex, floor, and cap
  checks.
- The implementation audit passed exact inactive-TR recovery, steep-target
  activation, deterministic pre-adaptation RNG selection, mid-window
  save/resume, frozen constant checks, and candidate telemetry fields.
- Seed 2901--2903 provenance is clean for scientific use; the tape is a new,
  development-only namespace 530000--530099.

## What this authorization does and does not mean

It means the S1 protocol is mechanically prepared for a future, separately
authorized cloud launch. It does **not** mean DRTP-TR is effective, that q
volatility was a historical cause, or that any result supports a stable-DRTP
claim.

The next action requires explicit human authorization of exactly the frozen S1
training contract. Any result-driven change to delta, epsilon_J, the practical
margin, anchor, seeds, tape, budget, safety rule, or candidate count is
prohibited.
