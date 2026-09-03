# UTR: benchmark versus method decomposition

| Component | Nature | Claim status |
|---|---|---|
| Six-UAV role graph with Scouts, Relays, and Terminals | Task/benchmark design | Potentially publishable if semantics and baselines are established |
| Legal node/edge failure groups | Task/benchmark design | Potentially distinctive; must be documented independently of UTR |
| Recoverability-aware grouping (`R_*`, `C_*`) | Benchmark taxonomy | Potentially distinctive; requires causal/scripted validation and held-out testing |
| Role-local assignment cues | Observation/interface design | Necessary task formulation repair; not standalone algorithmic novelty |
| Corrected role-specific SG-MAPPO | Learner correctness | Required baseline, not novelty |
| Uniform draw across seven groups | Training protocol / baseline | Standard structured domain randomization |
| Fixed development tape and seed-level analysis | Experimental discipline | Credibility feature, not core method novelty |

The paper must not collapse these categories. The strongest honest unit of contribution is the
**topology-failure benchmark plus a transparent structured-randomization baseline**, not the
uniform sampler as a standalone MARL algorithm.

