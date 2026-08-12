# Recovery Endpoint Protocol v2

Status: **FROZEN for Phase 2 evidence repair**

Frozen on: 2026-08-12

This protocol defines episode-level endpoint semantics before any re-evaluation. It does not alter training, reward, observation, communication, failure timing, checkpoint selection, or evaluation scenarios.

## Primary strict recovery endpoint

```text
pre_failure_chain_established == True
AND chain_lost_after_failure == True
AND post_failure_chain_recovered_after_loss == True
```

## Time definitions

- `t_failure`: failure onset step.
- `t_loss`: first step at or after `t_failure` at which a previously established chain is no longer closed.
- `t_recovery`: first step after `t_loss` at which the chain satisfies the stable-closure rule for the required hold window.
- `delta_t_loss_to_recovery = t_recovery - t_loss` for strict recovery events.
- `event = 1` for strict recovery; otherwise `event = 0`.
- `censor_time`: available observation duration after `t_loss` when strict recovery is not observed.

Episodes without a valid pre-failure chain or without a valid `t_loss` are reported as separate cohorts and are not silently treated as right-censored strict recovery episodes.

## Secondary operational endpoint

Retain the legacy quantity as a separate endpoint:

```text
post-failure first chain establishment/closure from failure onset
```

It must not be called strict re-establishment recovery.

## Required episode-level schema

Every re-evaluation row must contain at least:

```text
method, seed, episode, scenario, checkpoint_update, checkpoint_sha256,
pre_failure_chain_established, chain_lost_after_failure, t_failure, t_loss,
post_failure_chain_recovered_after_loss, t_recovery,
delta_t_loss_to_recovery, post_failure_chain_first_established,
event, censor_time, post_failure_first_chain_step, success, collision, timeout
```

## Reporting rules

1. No episode may be excluded because its result is unfavorable.
2. Episodes without pre-failure establishment are a separate descriptive cohort.
3. Episodes with pre-establishment but no loss are maintained-chain episodes, not strict recovery events.
4. Episodes with loss but no re-closure are right-censored at available follow-up.
5. Risk-set construction, stable hold window, censoring rule, and all tau values must be recorded in provenance.
6. The primary endpoint cannot be changed after inspecting results.

## Survival estimands

For the strict risk set, report event proportion, Kaplan–Meier curve, RMST at preregistered tau values, seed-level effects, hierarchical bootstrap intervals, and counts of non-risk-set cohorts. Legacy onset-based RMST is secondary and must be renamed consistently.
