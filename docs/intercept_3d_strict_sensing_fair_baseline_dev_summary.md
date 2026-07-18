# Strict-Sensing Fair Baseline Development Summary

Result directory: `results/intercept_3d_strict_sensing_fair_baselines_dev2`

This is a development-budget diagnostic, not a paper result. Its purpose is to check whether `no_graph`, `single`, and `multi_relation` can be trained and evaluated under the same strict-sensing protocol before launching a five-seed formal run.

| Split | Scenario | Method | Seeds | Success | Recovery | Recovery steps | Tracking | Connectivity | Timeout |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| validation | relay_failure | multi_relation | 2 | 0.0% | 0.0% | inf | 1.5% | 1.2% | 50.0% |
| validation | relay_failure | no_graph | 2 | 0.0% | 0.0% | inf | 0.0% | 24.7% | 100.0% |
| validation | relay_failure | single | 2 | 0.0% | 0.0% | inf | 5.1% | 28.4% | 100.0% |
| test | relay_failure | multi_relation | 2 | 0.0% | 0.0% | inf | 1.5% | 1.2% | 50.0% |
| test | relay_failure | no_graph | 2 | 0.0% | 0.0% | inf | 0.0% | 25.0% | 100.0% |
| test | relay_failure | single | 2 | 30.0% | 30.0% | 5.67 | 32.1% | 24.3% | 70.0% |

## Decision Rule

- If all methods have zero recovery, increase BC budget before increasing PPO updates.
- If `no_graph` is clearly worse and `single`/`multi_relation` are stable, expand to a longer 300-update diagnostic.
- If `single` catches `multi_relation`, keep the result and use it to tune scenario difficulty rather than forcing the claim.
- Do not tune on the final test split.
