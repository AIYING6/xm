# CV-DRTP D1 local technical report

**Status:** `CV_DRTP_D1_LOCAL_TECHNICAL_PASS — CLOUD_TRAINING_NOT_AUTHORIZED`.

## Scope

This is a rollout-free implementation audit of the frozen CV-DRTP design. It
does not establish empirical benefit, authorize a cloud run, or modify
Mainline A.

## Implemented boundary

`counterfactual_critic_enabled=False` is the default. In this mode no Q
network is constructed and the historical actor, scalar V critic, optimizer
and PPO loss path remain unchanged.

When enabled, the scalar V branch remains responsible only for the existing
bootstrapped-return/GAE target. A centralized Q branch receives legal
centralized state, role and sampled joint discrete action. For focal agent
`i`, the actor advantage is the detached finite-action baseline
`Q_i(s,a_i,a_-i) - sum_a pi_i(a|o_i) Q_i(s,a,a_-i)`. The Q branch has no
actor input, sampler input, reward change, rollout intervention or evaluation
information.

## Local checks passed

Executed with `D:/Anaconda/envs/.conda/envs/cac/python.exe`:

```text
tests/test_cv_drtp_d1.py                         4 passed
tests/test_drtp_stable_v2_kl_guard.py             5 passed
```

The checks establish:

1. Vectorized action enumeration equals an explicit finite-action reference.
2. Default-off repeated PPO updates are bitwise parameter-equivalent.
3. The enabled Q branch receives an update and reports Q loss, advantage
   dispersion, Q spread and local branch wall-clock telemetry.
4. A saved enabled checkpoint restores model and optimizer state such that the
   next fixed-minibatch PPO update matches uninterrupted execution exactly.
5. Existing post-step policy-guard behavior remains unchanged.

## Remaining boundary

No environment interaction or training has occurred. A future cloud package
must repeat its own integrity/preflight checks before any authorized pilot;
that pilot must use the separately frozen two-cohort 0.5M gate in the D0
contract. No pilot, parameter search or CV-DRTP-v2 is authorized by this
report.
