# Strict-Sensing Fair Baseline Development Summary

Result directory: `results/intercept_3d_strict_sensing_fair_60update_dropout030_diag`

This is a development-budget diagnostic, not a paper result. Its purpose is to check whether `no_graph`, `single`, and `multi_relation` can be trained and evaluated under the same strict-sensing protocol before launching a five-seed formal run.

| Split | Scenario | Method | Seeds | Success | Recovery | Recovery steps | Tracking | Connectivity | Timeout |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| validation | dropout030_relay_failure | multi_relation | 3 | 90.6% | 90.6% | 5.68 | 91.9% | 32.1% | 9.4% |
| validation | dropout030_relay_failure | single | 3 | 79.4% | 79.4% | 5.03 | 82.6% | 32.0% | 20.6% |
| test | dropout030_relay_failure | multi_relation | 3 | 96.7% | 96.7% | 5.91 | 97.2% | 32.4% | 3.3% |
| test | dropout030_relay_failure | single | 3 | 88.3% | 88.3% | 5.45 | 90.2% | 31.7% | 11.7% |

## Decision Rule

- If all methods have zero recovery, increase BC budget before increasing PPO updates.
- If `no_graph` is clearly worse and `single`/`multi_relation` are stable, expand to a longer 300-update diagnostic.
- If `single` catches `multi_relation`, keep the result and use it to tune scenario difficulty rather than forcing the claim.
- Do not tune on the final test split.
