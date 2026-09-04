# RACG-PPO C1 falsification contract (not yet authorized)

## Scope

C1, if separately authorized, uses only the five already-seen UTR source states 2201--2205. It performs exact same-rollout ordinary-PPO versus RACG-PPO mechanism comparisons. It is not a policy-performance experiment.

## Required pre-freeze before any C1 execution

The exact formula for reliability \(\rho\), the seven-dimensional robust proposal, numerical tolerance and all thresholds must be committed before reading C1 outcomes. No alternatives may be tried sequentially on these five states.

## Hard mechanism gates

1. Exact fixed-exposure paired batches in all five source states.
2. Material non-ordinary correction in at least 3/5 states; otherwise the method has no actuation.
3. Worst certificate-group surrogate harm smaller than ordinary PPO in at least 4/5 states.
4. Overall certificate surrogate retained in at least 4/5 states.
5. No zero-step rejection path; the complete pre-Adam actor direction (including entropy) must satisfy the frozen lower bound every epoch, and realized post-Adam parameter displacement must be nonzero.
6. Wall time no more than 4x Sync-UTR and peak memory within 10 GB.
7. No formal, independent or held-out evaluation tape.

Failure of any core gate closes this candidate. It does not authorize threshold relaxation, a second C1 formula, fresh-seed training or RACG-v2.

Passing C1 would authorize only a separately preregistered three-seed development experiment. It would not establish performance or cross-seed reliability.
