# Domain-randomization equivalence audit

## Decision

`UTR_IS_A_STRUCTURED_DOMAIN_RANDOMIZATION_BASELINE`.

At the level of the learning rule, UTR is domain randomization: it samples a training condition
from a fixed distribution and applies ordinary PPO/MAPPO updates. Its differentiating
restriction is not a new optimization principle; it is the **support** of the randomization
distribution—seven predeclared topology failure equivalence classes with one nominal condition.

## Consequences

1. Do not claim that equal randomization itself is novel.
2. The manuscript may claim a *structured topology-randomization protocol* only when it
   accurately describes the fault-support construction and avoids implying adaptive robustness.
3. A method claim requires comparisons against unstructured/naive fault randomization and at
   least one established adaptive or robust alternative under a matched budget.
4. Benchmark value requires evidence that the classes are meaningful, legal, recoverable where
   intended, and not merely relabelled random faults.

