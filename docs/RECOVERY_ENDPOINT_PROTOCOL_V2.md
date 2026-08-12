# Recovery endpoint protocol v2

This endpoint is frozen for canonical confirmatory evaluation. It must not be changed after inspecting results.

## Primary strict endpoint

An episode enters the primary cohort only when all three conditions are true:

```text
pre_failure_chain_established
AND chain_lost_after_failure
AND post_failure_chain_recovered_after_loss
```

For this cohort:

```text
t_loss = first post-failure time at which the established chain is lost
t_recovery = first subsequent time at which the post-failure chain is re-established
delta_t_loss_to_recovery = t_recovery - t_loss
event = 1 if the strict recovery occurs by censor_time; otherwise event = 0
```

Episodes without a pre-failure chain, without a post-failure loss, or without a post-loss recovery opportunity are not silently treated as slow recoveries. They are recorded with explicit cohort flags and excluded from the strict duration cohort according to the pre-registered cohort table.

## Secondary operational endpoint

The secondary endpoint is post-failure first chain establishment/closure from failure onset. It is retained for operational interpretation and must not replace the primary strict endpoint.

## Frozen episode schema

`pre_failure_chain_established`, `chain_lost_after_failure`, `t_failure`, `t_loss`, `post_failure_chain_recovered_after_loss`, `t_recovery`, `delta_t_loss_to_recovery`, `post_failure_chain_first_established`, `event`, and `censor_time` are required episode-level fields. Missing values are not imputed. A schema validator must fail closed when required fields or provenance identifiers are absent.

## Provenance rule

The endpoint definition, cohort counts, raw episode rows, derived survival rows, and every checkpoint must be linked by method, seed, config SHA, checkpoint SHA, evaluation protocol, and code snapshot. Historical files that do not satisfy this contract remain legacy evidence.
