# PAPER-Q2-P1 Comparator Decision

**Decision: `E2 — NO_FAIR_EXTERNAL_COMPARATOR`**  
**Training:** none authorized or started.

## Audit question

The current internal ladder is: standard MAPPO/graph references where contract-valid, matched Single-Graph UTR, and DRTP adaptive topology-perturbation weighting. The central controlled comparison is UTR versus DRTP because both use the same seven groups, 50% nominal anchor, SG architecture, PPO, environment, reward, actor boundary, budget, and evaluation contract; only the group-weight controller differs.

## Why no external drop-in is fair

- TAPE is topology-aware cooperative policy-gradient work, but its topology/action/task semantics do not implement the frozen heterogeneous Scout–Relay–Attacker relay-failure event.
- Robust MARL/M3DDPG addresses opponent-policy or adversarial variation with a different learner and continuous-control contract, not a drop-in CTDE comparator for this task.
- Distributionally robust Q-learning/DRRL papers are not multi-agent CTDE policy comparators and do not provide a directly reproducible actor under the frozen information boundary.
- Recent UAV relay MARL papers optimize communication, power, covert transmission, or connectivity restoration objectives rather than this mission-level relay-node topology perturbation estimand.

Forcing any of these into the environment would change the scientific problem or the fairness contract. The correct response is to strengthen related work and disclose that the comparison is an internal, capacity- and topology-group-matched ladder.

## Final manuscript handling

Do not add a comparator zoo. State explicitly that external methods were reviewed but no fair drop-in was identified. If a reviewer later requires one, create a separately frozen training request; P1 does not authorize it.
