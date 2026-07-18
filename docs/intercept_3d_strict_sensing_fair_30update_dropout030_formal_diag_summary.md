# Strict-Sensing Fair Baseline Development Summary

Result directory: `results/intercept_3d_strict_sensing_fair_30update_dropout030_formal_diag`

This is a development-budget diagnostic, not a paper result. Its purpose is to check whether `no_graph`, `single`, and `multi_relation` can be trained and evaluated under the same strict-sensing protocol before launching a five-seed formal run.

| Split | Scenario | Method | Seeds | Success | Recovery | Recovery steps | Tracking | Connectivity | Timeout |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| validation | dropout030_relay_failure | multi_relation | 3 | 92.5% | 92.5% | 5.85 | 93.4% | 31.9% | 7.5% |
| validation | dropout030_relay_failure | no_graph | 3 | 30.0% | 30.0% | 5.00 | 20.1% | 14.1% | 70.0% |
| validation | dropout030_relay_failure | single | 3 | 79.7% | 79.7% | 5.04 | 83.0% | 31.8% | 20.0% |
| test | dropout030_relay_failure | multi_relation | 3 | 93.3% | 93.3% | 5.91 | 94.4% | 31.1% | 6.7% |
| test | dropout030_relay_failure | no_graph | 3 | 31.7% | 31.7% | 4.93 | 20.2% | 13.7% | 68.3% |
| test | dropout030_relay_failure | single | 3 | 86.7% | 86.7% | 5.43 | 88.6% | 31.6% | 13.3% |

## Decision Rule

- If all methods have zero recovery, increase BC budget before increasing PPO updates.
- If `no_graph` is clearly worse and `single`/`multi_relation` are stable, expand to a longer 300-update diagnostic.
- If `single` catches `multi_relation`, keep the result and use it to tune scenario difficulty rather than forcing the claim.
- Do not tune on the final test split.
