# Strict-Sensing Fair Baseline Development Summary

Result directory: `results/intercept_3d_strict_sensing_mixed_source_seed0_diag`

This is a development-budget diagnostic, not a paper result. Its purpose is to check whether `no_graph`, `single`, and `multi_relation` can be trained and evaluated under the same strict-sensing protocol before launching a five-seed formal run.

| Split | Scenario | Method | Seeds | Success | Recovery | Recovery steps | Tracking | Connectivity | Timeout |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| validation | relay_failure | multi_relation | 1 | 100.0% | 100.0% | 6.90 | 100.0% | 42.4% | 0.0% |
| validation | relay_failure | no_graph | 1 | 48.0% | 48.0% | 4.79 | 34.1% | 25.3% | 52.0% |
| validation | relay_failure | single | 1 | 74.0% | 74.0% | 5.56 | 77.9% | 41.3% | 26.0% |
| test | relay_failure | multi_relation | 1 | 100.0% | 100.0% | 6.30 | 100.0% | 43.1% | 0.0% |
| test | relay_failure | no_graph | 1 | 30.0% | 30.0% | 5.67 | 25.8% | 17.9% | 70.0% |
| test | relay_failure | single | 1 | 100.0% | 100.0% | 5.80 | 100.0% | 43.6% | 0.0% |

## Decision Rule

- If all methods have zero recovery, increase BC budget before increasing PPO updates.
- If `no_graph` is clearly worse and `single`/`multi_relation` are stable, expand to a longer 300-update diagnostic.
- If `single` catches `multi_relation`, keep the result and use it to tune scenario difficulty rather than forcing the claim.
- Do not tune on the final test split.
