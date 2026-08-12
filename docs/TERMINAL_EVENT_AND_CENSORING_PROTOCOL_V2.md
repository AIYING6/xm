# Terminal event and censoring protocol v2

The strict endpoint remains `pre-established -> loss -> recovered` and duration remains `t_recovery - t_loss`.

| Condition | Classification | Strict risk set? |
|---|---|---|
| fixed horizon before eligible loss | administrative right-censoring | only if cohort was eligible |
| timeout after eligible loss | administrative right-censoring at horizon | yes |
| collision before recovery | adverse terminal non-recovery / competing event sensitivity | yes, sensitivity treats worst-case |
| mission failure / target escape | adverse terminal non-recovery / competing event sensitivity | yes, sensitivity treats worst-case |
| mission success before eligible loss | descriptive-only non-event | no |
| pre-failure termination | outside strict risk set | no |
| post-failure loss without recovery | adverse terminal non-recovery | yes |
| maintained chain without loss | outside strict duration risk set | no |
| no pre-failure establishment | outside strict risk set | no |

The primary analysis uses administrative censoring only for eligible episodes that remain observable through the horizon. A preregistered safety sensitivity reclassifies policy-induced early collision, mission failure, and target escape after eligibility as adverse non-recovery rather than benign censoring. This rule is fixed before any canonical result.
