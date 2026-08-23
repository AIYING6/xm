# DRTP S1-R — Seed Reliability Causal Screen

## Frozen status

`PROTOCOL-ONLY / NO TRAINING AUTHORIZED`

REL-A0 is complete. It establishes reproducible training-seed-dependent final
policy outcomes and a genuine catastrophic seed, but it does **not** establish
policy-basin divergence, a specific RNG cause, or any other root-cause
mechanism. “Policy-basin divergence” remains a candidate hypothesis only.

The historical S1-A `F_TECHNICAL_INVALID` result and the REL-A0 result are
retained unchanged.

## Objective and scope

S1-R asks one narrow question:

> Which isolated random source, if any, can bidirectionally change the
> catastrophic-versus-favorable training outcome while all other sources and
> the method contract remain fixed?

S1-R is not a new algorithm search and does not authorize a long run,
DRTP-Stable implementation, or paper experiment.

## Frozen good/bad seed selection

Labels are assigned from the REL-A0 machine-readable multi-tape records, not
from historical impressions.

### Bad candidate B

A seed is a bad candidate only if, for each of F0, timing, duration, and
compound conditions, DRTP’s paired return difference relative to UTR is
unfavorable on at least 4 of the 5 tapes. The same seed must show no
evaluator-coverage defect. A consistent safety deterioration strengthens the
label but is not substituted for the primary return rule.

### Good candidate G

A seed is a good candidate only if it is favorable on at least 3 of the 4
failure families on at least 4 of the 5 tapes, has positive pooled paired
effects, and has no catastrophic reversal under the same primary-return rule.
Timeout and collision are retained as mandatory diagnostics; a seed with a
systematic safety penalty is not eligible as G.

If exactly one eligible G and one eligible B cannot be identified, S1-R stops
before causal training and reports `NO_ELIGIBLE_G_B_PAIR`.

Under the current REL-A0 data, seed2002 is the expected B candidate. G must be
selected by the frozen rule above and must not be chosen for aesthetic reasons.

## Telemetry opening gate

Before any causal run, a short technical smoke must create and then read back
real files containing, at minimum:

- per-agent position and velocity;
- sampled action;
- task stage/progress;
- dwell or stagnation counters;
- graph/topology/path state;
- failure-relative time and terminal reason;
- timeout precursor fields;
- PPO loss, entropy, KL, clip fraction, and gradient diagnostics;
- DRTP group weights, EMA/difficulty, and group-return state;
- fixed probe-state policy outputs;
- checkpoint milestone and reload metadata.

The gate requires field presence, finite and schema-valid values, nonempty
milestone persistence, and a successful save→reload→next-update deterministic
check. Missing or placeholder telemetry is `S1-R TECHNICAL FAIL` and blocks all
long runs.

## Bidirectional causal design

Only after a separate authorization may the isolated-source screen run. For
each candidate source (initialization, environment, action, minibatch, and
topology), use a crossed design with the same fixed exposure and PPO contract:

| direction | required test |
|---|---|
| rescue | B + favorable source stream → favorable outcome |
| reverse degradation | G + unfavorable source stream → unfavorable outcome |

The comparison must preserve all non-target random streams and use the same
training budget, checkpoint milestones, telemetry schema, and evaluation tape.
No source may be changed jointly with another source in the primary screen.

## S1-R evidence rule

A source becomes an `ACTIONABLE_CAUSAL_CANDIDATE` only if all three hold:

1. bidirectional rescue and reverse-degradation effects are both observed;
2. the effect is reproduced in the frozen primary performance metrics, not only
   in one episode or one diagnostic plot;
3. trajectory telemetry shows a consistent precursor pattern aligned with the
   performance split.

One-direction rescue alone is insufficient. The result must not be called a
root cause; RNG interactions and residual seed sensitivity remain possible.

If no source satisfies all three requirements, the only allowed conclusion is
`NO_ACTIONABLE_CAUSE`, after which seed-mechanism enhancement is closed and the
original DRTP-with-seed-sensitivity result is retained.

## Prohibitions

Until a separate authorization is issued, do not:

- train S1-R runs;
- implement DRTP-Stable or any new algorithm;
- change DRTP weighting, PPO, environment, reward, exposure, or information
  boundary;
- relabel seed2002, remove weak seeds, or promote an intermediate checkpoint;
- use held-out or canonical seeds;
- claim policy-basin divergence or a specific RNG source as established.

## Required output after separately authorized execution

`docs/DRTP_S1R_SEED_RELIABILITY_CAUSAL_SCREEN_REPORT.md`, containing the
telemetry gate, frozen G/B selection, bidirectional matrix, trajectory
precursors, and exactly one of `TECHNICAL FAIL`, `NO_ELIGIBLE_G_B_PAIR`,
`ACTIONABLE CAUSAL CANDIDATE`, or `NO ACTIONABLE CAUSE`.
