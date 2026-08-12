# Phase 2IA4 Role-Gate efficacy report

## Frozen protocol status

The prescribed DEVELOPMENT_ONLY training completed for exactly two frozen
arms (`full_gate`, `no_role_gate`) and three development seeds (101, 202, 303),
at the fixed 1,000,192 environment steps per run. Fixed final checkpoints were
used for validation. No canonical seeds, canonical test results, checkpoint
promotion, seed exclusion, early stopping, or resume was used in this decision.

The recovered cloud training archive SHA256 is:

`e220e91ba1d560de266ff665e654dce7fb3371b6fc45ecdfbce092736538ff4c`.

Checkpoint/config hashes and the cloud-source provenance limitation are
recorded in `PHASE2IA4_TRAINING_COMPLETION_AUDIT.md`. In particular, the cloud
package did not contain `.git`; it is bound by archive, configuration, and
checkpoint hashes rather than an asserted exact source commit.

## Fixed-final validation and V0

The validation package contains 1,200 raw episodes and 24 timestep trace
files: 2 arms × 3 seeds × 4 frozen failure timings × 50 episodes. Independent
timestep reconstruction exactly matched evaluator endpoint fields (0
mismatches), so the V0 decision does not rely on a summary-only calculation.

| Arm | Strict risk set (C+D) | Required minimum | V0 |
|---|---:|---:|---|
| full_gate | 0 | 40 | FAIL |
| no_role_gate | 0 | 40 | FAIL |

Neither arm had a strict-risk episode in any seed or scenario. Thus all five
pre-registered V0 conditions fail. The evidence cannot estimate a strict
post-loss recovery contrast.

## Pre-registered decision

**ROLE-GATE EFFICACY: NOT ESTIMABLE DUE TO RISK-SET FAILURE**

This is intentionally neither `KEEP ROLE-GATE` nor `REMOVE ROLE-GATE`. The
retention rule cannot be applied because its required strict endpoint
population is absent. Auxiliary training telemetry or operational/success
metrics must not override V0.

**ROLE-GATE RETENTION: UNRESOLVED**
**ARCHITECTURE FREEZE: NO-GO**
**PHASE 3A: NO-GO**

## Minimal next action

Do not modify the frozen endpoint and do not inspect canonical performance to
resolve this. Prepare a separate protocol amendment that makes the strict
pre-failure-established → observed-loss population observable before any new
development runs. The amendment must be reviewed and committed independently;
it must state failure timing/eligibility instrumentation and a pre-result
adequacy gate. No conclusion about whether the Role-Gate should be retained can
be made until that new protocol passes V0.
