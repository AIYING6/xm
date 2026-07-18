# Fair Staged Source Quality Audit

Result directory: `results/intercept_3d_fair_staged_source_dev_seed0`

| Stage | Method | Seed | Update | Success/Recovery | Timeout/Unrecovered | Avg steps/recovery steps |
|---|---|---:|---:|---:|---:|---:|
| stage2_nominal | multi_relation | 0 | 5 | 0.0% | 100.0% | 260.0 |
| stage3_curriculum | multi_relation | 0 | 5 | 0.0% | 100.0% | 260.0 |
| stage4_strict_validation | multi_relation | 0 | 3 | 0.0% | 100.0% | inf |
| stage2_nominal | single | 0 | 5 | 0.0% | 100.0% | 260.0 |
| stage3_curriculum | single | 0 | 5 | 0.0% | 100.0% | 260.0 |
| stage4_strict_validation | single | 0 | 3 | 0.0% | 100.0% | inf |

## Interpretation Rule

- If `stage2_nominal` success is zero, do not interpret strict-sensing results; the source policy has not learned the base interception task.
- If `stage2_nominal` succeeds but `stage3_curriculum` fails, tune topology/node-failure curriculum before strict fine-tuning.
- If both source stages are nonzero but strict validation is zero, then tune strict-sensing fine-tuning or scenario difficulty.
