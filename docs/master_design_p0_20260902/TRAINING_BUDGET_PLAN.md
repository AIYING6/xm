# Training budget plan

| Stage | purpose | indicative environment steps | stop rule |
|---|---|---:|---|
| semantic smoke | implementation only | <=1M total | graph/reachability failure |
| pilot | direction on fresh seeds | ~15M | no pre-frozen performance signal |
| development | select one candidate through development only | ~20M | weak or unsafe candidate |
| mature replication | separate two 5-seed cohorts at 2M | ~60M | cohort reversal |
| confirmatory | winner vs required comparators at 3M | ~90M | no Level-2 reliability evidence |
| OOD/scale/ablation | claim completion | ~25--50M | failed claim boundary |

Total full programme: approximately **210--236M environment steps**, plus fixed-tape evaluations. Estimate wall-clock only after an isolated main-scale throughput smoke test; a single 3080 Ti and 50 GB data disk are not adequate evidence for this full programme. Plan for staged cloud execution, checkpoint/telemetry compression, and at least several hundred GB of durable storage. Maximum concurrency is a hardware-calibrated safety parameter, never a scientific result.
