# Strict-Sensing Fair Baseline Development Summary

Result directory: `results/intercept_3d_fair_staged_source_dev_seed0/stage4_strict_smoke`

This is a development-budget diagnostic, not a paper result. Its purpose is to check whether `no_graph`, `single`, and `multi_relation` can be trained and evaluated under the same strict-sensing protocol before launching a five-seed formal run.

| Split | Scenario | Method | Seeds | Success | Recovery | Recovery steps | Tracking | Connectivity | Timeout |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| validation | relay_failure | multi_relation | 1 | 0.0% | 0.0% | inf | 6.7% | 15.0% | 100.0% |
| validation | relay_failure | single | 1 | 0.0% | 0.0% | inf | 7.6% | 4.8% | 93.3% |
| test | relay_failure | multi_relation | 1 | 0.0% | 0.0% | inf | 4.8% | 15.0% | 100.0% |
| test | relay_failure | single | 1 | 0.0% | 0.0% | inf | 8.2% | 5.0% | 100.0% |

## Decision Rule

- If all methods have zero recovery, increase BC budget before increasing PPO updates.
- If `no_graph` is clearly worse and `single`/`multi_relation` are stable, expand to a longer 300-update diagnostic.
- If `single` catches `multi_relation`, keep the result and use it to tune scenario difficulty rather than forcing the claim.
- Do not tune on the final test split.
