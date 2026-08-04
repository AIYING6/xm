# v1.5 Evaluation Metrics Protocol (frozen)

**Freeze date:** 2026-08-04
**Status:** Frozen **before** any v1.5 formal validation run and before any
v1.5 model selection. Hashed below; the hash must be recorded in the v1.5
change-control and must not change without a new protocol freeze.

## 1. Motivation

The v1.4 diagnostic revealed that `post_failure_chain_recovered_mean` averages
over **all** episodes, including episodes that finish **before** the node
failure occurs (`pre_failure_success`). Such episodes are counted as
recovered=0, which systematically penalises methods that complete the task
before exposure. This protocol therefore separates task-efficiency metrics from
failure-recovery metrics and requires them to be **reported jointly**, never in
isolation.

## 2. Two-layer evaluation structure

### Layer A — task efficiency (unconditional)

```text
unconditional_success_rate   : fraction of all episodes with task success
pre_failure_success_rate     : fraction of episodes completed successfully
                               before the failure step (no exposure)
time_to_success              : steps to task success (unconditional)
collision_rate               : fraction of episodes with a collision
```

### Layer B — failure recovery (conditioned on exposure)

```text
failure_exposure_rate                : fraction of episodes that reached the
                                       failure step (exposed)
recovery_rate_given_exposure         : exposed AND chain re-closed  /  exposed
time_to_recovery_given_exposure      : steps from failure to chain re-closure,
                                       exposed and recovered only
```

## 3. Mandatory joint reporting

- `recovery_rate_given_exposure` must **always** be reported together with:
  - the counts `recovered / exposed`;
  - the exposure sample size `N_exposed`;
  - per-seed values (training seed is the independent replication unit);
  - a confidence interval (e.g. exact binomial / stratified bootstrap).
- When `N_exposed` is small (< 10), the rate must be flagged as
  **"estimate unstable"**; percentages must not be compared across methods with
  different exposure rates.
- No single metric from Layer A or B may be reported alone as the method's
  headline claim; the joint block is the unit of reporting.

## 4. Freeze rules

- This protocol is frozen before any v1.5 formal validation and before any
  v1.5 model selection.
- It must not be modified in response to v1.5 validation/test results.
- Any change requires a new protocol version with its own hash and
  change-control entry.

## 5. Relationship to v1.4

- The v1.4 frozen selection rule (legacy weighted score, collision gate 0.0,
  larger-update tie-break) is **unchanged**; the exposure metrics are an
  additional diagnostic/reporting layer, not a selection rule.
- v1.4 selected checkpoints are already locked and are not re-selected.

## 6. Document hash

The frozen document SHA256 is recorded externally (no self-reference) in
`V1_5_EVALUATION_METRICS_PROTOCOL.md.sha256` stored next to this file. The hash
must be entered into the v1.5 change-control before any v1.5 formal validation.
