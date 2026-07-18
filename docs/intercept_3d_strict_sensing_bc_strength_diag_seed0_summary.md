# Strict-Sensing Fair Baseline Development Summary

Result directory: `results/intercept_3d_strict_sensing_bc_strength_diag_seed0`

This is a development-budget diagnostic, not a paper result. Its purpose is to check whether `no_graph`, `single`, and `multi_relation` can be trained and evaluated under the same strict-sensing protocol before launching a five-seed formal run.

| Split | Scenario | Method | Seeds | Success | Recovery | Recovery steps | Tracking | Connectivity | Timeout |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| validation | relay_failure | multi_relation | 1 | 0.0% | 0.0% | inf | 5.2% | 15.1% | 100.0% |
| validation | relay_failure | single | 1 | 0.0% | 0.0% | inf | 9.9% | 8.4% | 100.0% |
| test | relay_failure | multi_relation | 1 | 0.0% | 0.0% | inf | 4.8% | 15.3% | 100.0% |
| test | relay_failure | single | 1 | 0.0% | 0.0% | inf | 9.6% | 8.4% | 100.0% |

## Decision Rule

- If all methods have zero recovery, increase BC budget before increasing PPO updates.
- If `no_graph` is clearly worse and `single`/`multi_relation` are stable, expand to a longer 300-update diagnostic.
- If `single` catches `multi_relation`, keep the result and use it to tune scenario difficulty rather than forcing the claim.
- Do not tune on the final test split.
