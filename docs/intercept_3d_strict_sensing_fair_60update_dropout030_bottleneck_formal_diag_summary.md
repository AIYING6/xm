# Strict-Sensing Fair Baseline Development Summary

Result directory: `results/intercept_3d_strict_sensing_fair_60update_dropout030_bottleneck_formal_diag`

This is a development-budget diagnostic, not a paper result. Its purpose is to check whether `no_graph`, `single`, and `multi_relation` can be trained and evaluated under the same strict-sensing protocol before launching a five-seed formal run.

| Split | Scenario | Method | Seeds | Success | Recovery | Recovery steps | Tracking | Connectivity | Timeout |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| validation | dropout030_relay_failure | multi_relation | 3 | 81.7% | 81.7% | 6.75 | 84.5% | 28.4% | 18.3% |
| validation | dropout030_relay_failure | no_graph | 3 | 27.2% | 27.2% | 5.70 | 18.5% | 11.6% | 72.8% |
| validation | dropout030_relay_failure | single | 3 | 58.6% | 58.6% | 5.56 | 65.2% | 27.6% | 40.6% |
| test | dropout030_relay_failure | multi_relation | 3 | 95.0% | 95.0% | 5.77 | 95.8% | 31.9% | 5.0% |
| test | dropout030_relay_failure | no_graph | 3 | 25.0% | 25.0% | 5.07 | 17.3% | 11.6% | 75.0% |
| test | dropout030_relay_failure | single | 3 | 78.3% | 78.3% | 5.18 | 81.8% | 30.2% | 21.7% |

## Decision Rule

- If all methods have zero recovery, increase BC budget before increasing PPO updates.
- If `no_graph` is clearly worse and `single`/`multi_relation` are stable, expand to a longer 300-update diagnostic.
- If `single` catches `multi_relation`, keep the result and use it to tune scenario difficulty rather than forcing the claim.
- Do not tune on the final test split.
