# D0 theory and solver matrix

| Candidate | Natural unrestricted formulation | Standard methods that would already solve/approximate it | Nontrivial theory needed to pass | D0 evidence for that structure | Gate |
|---|---|---|---|---|---|
| A | Time-expanded multi-commodity flow + assignment + migration binary variables | MILP, min-cost flow special cases, rolling-horizon MPC, Lyapunov online control | A source-native interval/laminar capacity property yielding an integral relaxation, or a competitive ratio not subsumed by existing disruption-free migration/AoI scheduling | None | **Fail** |
| B | Distributed constraint optimization / version-state MDP with synchronization actions | Consensus auction, CBBA, event-triggered consensus, DCOP, CMDP | A version-feasibility conflict graph admitting a new minimal synchronization decomposition, approximation, or convergence theorem beyond consensus | The counterexample alone; no structural proof | **Fail / conditional** |
| C | Dynamic reconfiguration with state migration, switching cost, and recovery state | Dynamic programming, MILP, standard hysteresis, online control | A recovery-state graph property that yields bounded switching or an optimal threshold not already a handover/failback result | None | **Fail** |

## Theory standard

For D-line, a runtime bound for generic MILP is insufficient. A candidate must pre-commit to a theorem about feasibility, equivalence, approximation, competitive performance, bounded switching, a polynomial special case, or a parameterized result. D0 found no such theorem target that is both problem-specific and separated from the nearest-neighbor literature.
