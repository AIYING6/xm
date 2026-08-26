# PAPER-Q2 External Comparator Audit

**Decision:** `E2 — NO_FAIR_EXTERNAL_COMPARATOR`
**Training started:** no.

| method | nearest_relevance | same_problem_estimand | same_actor_information_boundary | same_action_and_learner_contract | architecture_or_objective_change_required | implementation_ready_under_frozen_contract | scientifically_relevant | fair_drop_in | decision | source |
|---|---|---|---|---|---|---|---|---|---|---|
| TAPE (AAAI 2024) | topology-aware cooperative MARL | no | no demonstrated drop-in mapping | no | yes | not established | yes, positioning only | no | do not train | https://ojs.aaai.org/index.php/AAAI/article/view/29699 |
| M3DDPG (AAAI 2019) | robust multi-agent learning under changing opponents | no | no demonstrated drop-in mapping | no; minimax DDPG differs from frozen MAPPO | yes | not established | yes, positioning only | no | do not train | https://ojs.aaai.org/index.php/AAAI/article/view/4327 |

TAPE is directly relevant as topology-aware cooperative MARL, but its topology/action/task semantics do not provide a drop-in implementation for the frozen heterogeneous Scout–Relay–Attacker relay-failure estimand. M3DDPG is directly relevant as robust MARL, but its minimax DDPG learner and opponent-variation framing are incompatible with the frozen MAPPO actor and information boundary. Implementing either would alter the scientific comparison rather than add a fair comparator.

Therefore no `PAPER_Q2_EXTERNAL_COMPARATOR_TRAINING_CONTRACT.md` is created, and no external-comparator training is authorized. The manuscript must state that the main empirical ablation is the capacity- and exposure-matched UTR versus DRTP comparison.
