# Canonical baseline fairness audit v3

| Factor | Full | MAPPO | Single-Graph | No-Union | Status |
|---|---|---|---|---|---|
| 3DOF environment/failure protocol | same | same | same | same | specified |
| observation semantics | graph + local | no graph + local | single graph + local | graph + local | method-defined; legality audit pending |
| reward | same | same | same | same | specified |
| budget/rollout/env count | fixed | fixed | fixed | fixed | specified |
| optimizer/PPO/GAE/entropy/clip | must match | must match | must match | must match | config binding incomplete |
| BC initialization | same policy | same policy | same policy | same policy | provenance binding pending |
| curriculum | staged | equivalent difficulty required | equivalent difficulty required | equivalent difficulty required | unresolved |
| validation scenarios/selection | same | same | same | same | specified |
| evaluation N/tapes | same | same | same | same | tape not implemented |

No unexplained Full-only training advantage may remain. The planned Wave 1 launch is therefore not training-ready until optimizer/config/BC/curriculum manifests are bound per method and the evaluation tape exists.
