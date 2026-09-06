# DRTP final-paper terminology ledger

| Canonical term | First-use definition | Do not substitute with |
|---|---|---|
| Uniform Topology Replay (UTR) | The matched uniform topology-condition sampling baseline | uniform baseline; random curriculum |
| Dynamic Robust Topology Prioritization (DRTP) | Adaptive training exposure allocation across frozen topology-failure groups | universal stabilizer; guaranteed robust policy |
| Original DRTP | The frozen DRTP implementation evaluated in the final A/B cohorts | EGTR; GA-EGTR |
| topology condition | One frozen nominal or failure-group condition used at environment reset | level, unless referring specifically to PLR literature |
| perturbed return | Frozen-endpoint return aggregated under the specified perturbed condition set | reward, unless referring to a rollout reward |
| robustness benefit | Higher perturbed return under the matched frozen endpoint protocol | universal robustness |
| reliability profile | Mean, median, lower-tail, seed dispersion and safety outcomes considered jointly | proof of zero variance |
| training cohort | One independently seeded set of five training seeds, analyzed separately | pooled replicate |
| fixed endpoint | The policy checkpoint at exactly 10,000,128 environment steps | best checkpoint |
| PLR-style comparator | Independently implemented Prioritized Level Replay-style topology-condition replay comparator | PLR reproduction |
| cross-scale six-UAV study | Matched UTR versus DRTP evaluation on the 2-scout/2-relay/2-terminal task | direct proof of all-scale generalization |

## Statistical notation

- `n=5` denotes independent **training seeds** within one cohort.
- A and B are reported separately for confirmatory interpretation; any pooled `n=10` view is descriptive only.
- `Δ = DRTP − comparator` is a paired seed-level endpoint difference under the same cohort and condition protocol.

