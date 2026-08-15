# DRTP Strict-Continuous 10M Execution Readiness Report

## Status

**READY TO LAUNCH ON CLOUD / NO HELD-OUT, CANONICAL, OR FOLLOW-ON TRAINING
AUTHORIZED.**

The proposed 3M→5M warm-restart training route is cancelled.  Its amendment
and runtime persistence implementation remain in the repository, but the
strict-10M study starts each of the four authorized trajectories from update
zero and never loads a legacy 3M checkpoint.

## Implemented controller

- `scripts/run_drtp_sg_strict_10m_single.py` launches only UTR/DRTP ×
  seeds 1901/1902, from scratch, for 39,063 updates (10,000,128 environment
  steps) with runtime-state persistence enabled from the initial invocation.
- `scripts/launch_drtp_sg_strict_10m_autodl.sh` launches the four trajectories
  in parallel, then evaluates every fixed half-million milestone using the
  frozen 420k tape and stops after aggregation.
- `scripts/run_drtp_sg_strict_10m_evaluation.py` evaluates all 20 milestones
  on the 12-condition paired development contract (96,000 episodes total).
- `scripts/aggregate_drtp_sg_strict_10m.py` reports full learning curves,
  1M/3M/5M/10M snapshots, first stable plateau, the 8M→9M→10M unresolved
  maturity condition, final 10M retention/safety gates, and no automatic
  held-out authorization.

## Technical verification

`scripts/verify_drtp_sg_strict_10m_contract.py` passed without training:

| check | result |
|---|---|
| four and only four authorized arms | PASS |
| 39,063 updates / 10,000,128 steps each | PASS |
| all 20 fixed 0.5M milestones | PASS |
| matched SG parameter count 116,728 | PASS |
| no legacy resume or warm restart | PASS |
| runtime persistence enabled from start | PASS |
| frozen topology sampler and S2 task configuration | PASS |
| only 420000–420099 development tape may be generated | PASS |
| held-out/canonical use | PROHIBITED |

The runtime-state implementation itself previously passed save→reload→next
update equality for both UTR and DRTP, including model, optimizer, environment,
RNG, sampler, and append-only logs.

## Launch boundary

This report authorizes the strict continuous development controller only.  It
does not authorize `430000–430099`, seeds 2001/2002/2003, canonical seeds 0–4,
new algorithms, parameter changes, post-hoc checkpoint selection, or extension
beyond 10M.  The sole final comparison is UTR versus DRTP at their common 10M
final checkpoints.
