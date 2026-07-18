# Strict-Sensing Fair Baseline Development Summary

Result directory: `results/intercept_3d_strict_sensing_fair_3seed_diag`

This is a development-budget diagnostic, not a paper result. Its purpose is to check whether `no_graph`, `single`, and `multi_relation` can be trained and evaluated under the same strict-sensing protocol before launching a five-seed formal run.

| Split | Scenario | Method | Seeds | Success | Recovery | Recovery steps | Tracking | Connectivity | Timeout |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| validation | relay_failure | multi_relation | 3 | 100.0% | 100.0% | 5.27 | 100.0% | 44.7% | 0.0% |
| validation | relay_failure | no_graph | 3 | 33.3% | 33.3% | 5.19 | 23.3% | 19.3% | 66.7% |
| validation | relay_failure | single | 3 | 92.7% | 92.7% | 4.94 | 94.3% | 44.1% | 6.7% |
| test | relay_failure | multi_relation | 3 | 100.0% | 100.0% | 5.60 | 100.0% | 44.0% | 0.0% |
| test | relay_failure | no_graph | 3 | 40.0% | 40.0% | 5.17 | 27.5% | 21.8% | 60.0% |
| test | relay_failure | single | 3 | 93.3% | 93.3% | 5.05 | 94.4% | 43.8% | 6.7% |

## Decision Rule

- If all methods have zero recovery, increase BC budget before increasing PPO updates.
- If `no_graph` is clearly worse and `single`/`multi_relation` are stable, expand to a longer 300-update diagnostic.
- If `single` catches `multi_relation`, keep the result and use it to tune scenario difficulty rather than forcing the claim.
- Do not tune on the final test split.
