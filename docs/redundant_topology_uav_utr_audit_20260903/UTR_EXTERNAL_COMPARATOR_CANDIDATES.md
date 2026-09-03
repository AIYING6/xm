# External comparator candidates

| Candidate | Why it is relevant | Status under current interface | Minimum implementation boundary |
|---|---|---|---|
| Plain corrected SG-MAPPO | Establishes nominal-only reference | Already implemented | Same learner/budget; nominal collection only |
| Naive legal-event randomization | Tests whether topology taxonomy/equal group exposure matters | Fair with minimal adaptation | Predeclare a legal event-level support; same fault time, step budget, and no extra observation |
| PLR | Tests adaptive scenario sampling | Fair with minimal adaptation | Treat each frozen group or fixed event instance as a level; priorities use training-only rollout statistics |
| EPOpt / batch-CVaR | Tests worst-trajectory robust optimization | Fair with minimal adaptation | Same training support and steps; select worst fraction from training rollouts only; report effective sample reduction |
| Group-DRO | Tests worst-group objective | Fair with minimal adaptation | Use training group labels only; retain learner inputs and account for group-loss weighting |
| Learned structured communication / GIB-MARL | Tests a different communication architecture | Not a direct same-interface comparator | Use as contextual related work unless a separate architecture-comparison study is funded |

Static curriculum is not an external comparator. It is an already completed internal negative
ablation (`P3_P2_NO_SIGNAL`) and should be reported compactly, without treating it as evidence
of UTR’s external novelty.

