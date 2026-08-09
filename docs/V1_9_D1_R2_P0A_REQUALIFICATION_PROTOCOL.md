# D1-R2 P0-A Engineering Requalification Protocol

**Scope:** repair verification only; `performance_use_prohibited = true`.

The repaired pipeline is requalified with `pcrf_r2`, `single_r2`, and
`matched_nongraph_r2`, engineering seeds 9301 and 9302, 30 updates per run,
the unchanged 8-environment/128-rollout/4-PPO-epoch engineering configuration,
and real resume at update 10. These seeds are permanently excluded from F1.

Each validation point (updates 1, 10, 20, 30) must persist a snapshot, new
terminal-outcome event record, RMTE outcome decomposition, SHA256, commit,
protocol/method/seed provenance, and both resume segment logs. The gate checks
the source-separated R2 checkpoint path, finite training quantities, empty
stderr, record-summary recomputation, and the frozen RMTE selector.

The only successful state is:

`D1_R2_P0A_REQUALIFICATION_GATE_PASS__P0_R2_RED_TEAM_CONTINUES__D2_NOT_AUTHORIZED`.

No D1 value, rank, selected update, or curve may be used as a scientific result.
