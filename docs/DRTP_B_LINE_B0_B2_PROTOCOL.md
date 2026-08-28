# DRTP B-Line B0--B2 Protocol

## Separation from the submission line

This is an independent mechanism-exploration line.  It must not revise the
claims, pooled statistics, checkpoints, or submission schedule of the frozen
DRTP application manuscript.  A negative B-line result changes neither the
formal 2301--2305 cohort facts nor the independently reported 2401--2405
reversal.

## B0 — frozen question and prohibited actions

The sole question is:

> Why can the unchanged DRTP sampler produce opposite final UTR--DRTP
> directions across training cohorts?

Candidate chain, not an accepted explanation:

`EMA/difficulty -> q -> sampled exposure -> behavior/path/geometry -> task support -> outcome`.

Until a mechanism gate is passed, the following are prohibited:

- changing DRTP, UTR, PPO, reward, environment, topology semantics, or actor
  information;
- implementing a stable-DRTP variant or combining multiple stabilizers;
- new 10M training, confirmatory training, checkpoint promotion, seed deletion,
  or seed substitution;
- presenting correlations in q/PPO logs as a causal mechanism.

The failed 2601--2603 Mechanism V1 cloud run is permanently
`TECHNICAL_INVALID`: its run directories were labelled 2601--2603 but the
materialized `config.seed`/telemetry seed was 1901.  It is excluded from all
B-line evidence and is not silently repaired or reused.

## B1 — historical divergence-timing audit

Inputs are only the frozen 2301--2305 and 2401--2405 archives already used by
the cohort-reversal forensic audit.  B1 may reconstruct update-indexed sampler
and PPO records, but it cannot infer unlogged environment behavior.

Current B1 status: `TIMING_UNRESOLVED_FROM_EXISTING_LOGS`.

The existing 781,260 PPO rows and 1,580 sampler windows establish neither a
pre-registered behavioral divergence threshold nor synchronized behavior
outcomes.  Therefore no 0--1M, 1--2M, or later window may be called the first
causal divergence time.  This is a valid B1 result, not a reason to loosen
future mechanism gates.  Any future pilot budget must be frozen prospectively
after telemetry-readiness work; it cannot be justified as a recovered fact
from these archives.

## B2 — read-only telemetry readiness requirements

Telemetry must be an output-only sink and must not alter policy, critic,
sampler, reward, termination, observations, or any RNG stream.  It must record:

1. sampler state: q, nominal/group EMA, difficulty, selected group/member and
   actual exposure;
2. PPO diagnostics: loss, policy/value loss, entropy, KL, clip fraction,
   explained variance, advantage statistics and gradient norm when available;
3. failure-relative behavior: position, velocity, heading/gamma, pairwise
   geometry, action and policy entropy;
4. legal information/topology: legal edges, direct/relay/no-path state, scout
   detection, attacker information validity, cache source/freshness, task
   support and attack-window state;
5. outcome: true reward components, cumulative reward, completion, collision,
   timeout, constraint violation and termination reason.

Two levels are mandatory: every episode has a summary; event windows cover
`tau=-20..+60`.  Nominal episodes use the frozen matched pseudo-onset 44.

Before any B3 pilot, all checks must pass:

- telemetry OFF/ON exact trajectory equivalence under a stochastic policy,
  including action sequence, reward, termination, sampler state and PPO update;
- actor/critic information-boundary and reward/failure-semantics invariance;
- parallel environment isolation, missing-value handling and bounded storage;
- save/reload at a mid-window boundary with byte-identical subsequent telemetry
  and training state;
- provenance assertion that requested seed, `cfg.seed`, sampler seed, runtime
  RNG seed and telemetry seed are identical for every run.

Failure of any item is `TELEMETRY_TECHNICAL_FAIL`; it authorizes a telemetry
repair only, not mechanism training.

### B2 completion record

`B2_TECHNICAL_PASS` was obtained in a short CPU stochastic-policy audit.  The
telemetry-on and telemetry-off executions produced identical 256-transition
action/reward/termination traces, PPO and sampler CSV rows, and final model
SHA256.  A mid-window runtime save/reload also reproduced the next update with
the complete model/optimizer/environment/RNG/sampler/telemetry state exactly.
The detailed acceptance record is
`docs/DRTP_B_LINE_B2_TELEMETRY_ACCEPTANCE.md`.  This technical PASS does not
authorize B3 by itself.

## Future gates (not yet authorized)

Only a later B3 authorization may launch a short cloud UTR/DRTP paired pilot.
A mechanism GO requires all of: time precedence, a same-direction pattern in
at least 2/3 DRTP seeds, weaker/absent paired UTR pattern, and a contiguous
three-layer `sampler/exposure -> behavior/support -> outcome` chain.  Otherwise
the B line stops at `MECHANISM_NO_GO` and no algorithm modification is allowed.
