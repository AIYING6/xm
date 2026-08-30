# B5 group credit telemetry dictionary

## Group file: `group_credit_telemetry.csv`

One row per PPO update × failure group. `status=NO_SAMPLES` is explicit missingness and must not be imputed.

| field family | meaning |
|---|---|
| return / rollout_value | GAE return target and rollout-time critic prediction |
| value_residual | return target minus rollout-time value prediction |
| td_residual | one-step reward + discounted next value − rollout value |
| raw_advantage | unnormalized GAE advantage |
| normalized_advantage | normalization across the full paired rollout, matching PPO |
| actor_gradient_norm | group PPO policy+entropy gradient norm; diagnostic only |
| critic_gradient_norm | group value-loss gradient norm; diagnostic only |

## Conflict file: `group_credit_gradient_conflicts.csv`

One row per observed update × unordered group pair. Negative dot product marks a conflict for that diagnostic objective; it is not itself a mechanism or an independent replicate.
