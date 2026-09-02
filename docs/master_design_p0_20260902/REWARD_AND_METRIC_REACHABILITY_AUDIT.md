# Reward and metric reachability audit

The existing 3-UAV reward cannot be copied mechanically: pairwise collision opportunities, connectivity averages and per-role bonuses change with N. P1 must define normalized quantities with invariant physical meaning.

| Quantity | required scale-safe definition | gate |
|---|---|---|
| mission progress | normalized target/intercept progress relative to scale-specific feasible geometry | attainable nominally |
| success | role-legal terminal neutralization under valid support path | feasible in R/C, impossible in I |
| collision | collision rate per UAV-pair exposure plus episode indicator | no automatic N penalty |
| communication | task-path availability/age, not dense all-pairs closure alone | respects directed support graph |
| role rewards | role-normalized contribution, bounded total magnitude | no reward inflation from copies |
| timeout | fixed physical mission deadline or normalized horizon | comparable within scale |

Before learner connection, deterministic scenario sweeps must establish reachable success, recoverable rerouting and impossible lower-bound semantics. This is a future design/smoke requirement, not a P0 experiment.
