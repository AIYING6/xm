# Strict-Sensing Fair Baseline Development Summary

Result directory: `results/intercept_3d_strict_sensing_fair_30update_diag`

This is a development-budget diagnostic, not a paper result. Its purpose is to check whether `no_graph`, `single`, and `multi_relation` can be trained and evaluated under the same strict-sensing protocol before launching a five-seed formal run.

| Split | Scenario | Method | Seeds | Success | Recovery | Recovery steps | Tracking | Connectivity | Timeout |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| validation | relay_failure | multi_relation | 3 | 96.9% | 96.9% | 5.36 | 97.4% | 44.0% | 3.1% |
| validation | relay_failure | no_graph | 3 | 34.7% | 34.7% | 4.94 | 25.6% | 19.9% | 65.3% |
| validation | relay_failure | single | 3 | 90.8% | 90.8% | 4.95 | 92.3% | 43.8% | 9.2% |
| test | relay_failure | multi_relation | 3 | 95.0% | 95.0% | 5.99 | 95.7% | 42.8% | 5.0% |
| test | relay_failure | no_graph | 3 | 36.7% | 36.7% | 6.08 | 26.1% | 20.6% | 61.7% |
| test | relay_failure | single | 3 | 90.0% | 90.0% | 5.42 | 91.5% | 43.1% | 10.0% |

## Decision Rule

- If all methods have zero recovery, increase BC budget before increasing PPO updates.
- If `no_graph` is clearly worse and `single`/`multi_relation` are stable, expand to a longer 300-update diagnostic.
- If `single` catches `multi_relation`, keep the result and use it to tune scenario difficulty rather than forcing the claim.
- Do not tune on the final test split.
