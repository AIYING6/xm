# Atomic novelty audit

| Atomic component | Precedent pressure | Independent novelty claim? | Required boundary |
|---|---|---:|---|
| Uniform randomized training environments | High: domain randomization is established | No | Describe as a baseline/protocol |
| Sampling a finite set of training instances | High: PLR and curriculum work treat this as a generic collection decision | No | Do not call the sampler new |
| Robust optimization over scenario groups | High: EPOpt and group-DRO exist | No | External comparison is needed before robustness claims |
| Role-aware graph MARL | High | No | Present as an implementation choice unless a distinct architecture is introduced |
| Physical/legal/recoverability-constrained topology fault taxonomy | Moderate | Possibly | Must show the taxonomy excludes degenerate/illegal cases and changes the task |
| Assignment-observation formulation for Scouts and Terminals | Moderate | Possibly as formulation detail | It repairs ambiguity; do not market it as an algorithm |
| Fixed, equal group exposure including nominal anchor | Low as a systems protocol, high as generic idea | Only in combination with benchmark semantics | “Structured topology randomization,” never “novel randomization algorithm” |

**Bottom line:** there is no support for an “UTR algorithm” claim. There is a defensible
research opportunity only if the benchmark semantics and a fair evidence package show why
structure-aware exposure is a practically useful baseline for this problem.

