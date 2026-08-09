# v1.9 Research Canon

This file records hard constraints and evidence boundaries. Subsequent v1.9
writing must not silently upgrade a hypothesis to a result.

## Literature facts

1. Graph networks provide relational inductive biases, but their usefulness is
   contingent on structure matching the problem rather than on graph use by
   itself (Battaglia et al., 2018, [arXiv:1806.01261](https://arxiv.org/abs/1806.01261)).
2. Partial observability and limited communication are intrinsic MARL
   difficulties; information sharing can be necessary, but it also makes the
   information structure part of the algorithmic problem (Omidshafiei et al.,
   2017, [arXiv:1703.06182](https://arxiv.org/abs/1703.06182); Liu & Zhang,
   2023, [arXiv:2308.08705](https://arxiv.org/abs/2308.08705)).
3. Relation-specific graph convolution is established prior art, so a v1.9
   contribution cannot rest on merely having multiple adjacency matrices
   (Schlichtkrull et al., 2018, *Modeling Relational Data with Graph
   Convolutional Networks*).
4. Existing communication mechanisms are condition-dependent rather than
   universally optimal; standardized, realistic robustness comparisons remain
   important (Wittner, 2026, [arXiv:2601.12886](https://arxiv.org/abs/2601.12886)).

## Project facts

1. v1.8 established a recipient-specific actor contract: unavailable teammate
   truth, pending/dropped packets, invalid endpoint geometry, and critic/shared
   state are excluded before actor feature construction.
2. R5 boundary tests passed 14/14. This is a scientific-integrity prerequisite,
   not an algorithmic novelty claim.
3. R6.5 showed perception, communication, and task-support masks are not
   identical. However, task-support was a strict subset of communication in the
   audited rollout family; 40% of communication edges lacked task support.
4. R6.5 found the union residual material but not dominant in its fixed audit.
   It remains a structural risk, not evidence of an advantage.
5. R6.5 found near-zero Role-Pair gate variation in the pilot. Role-Pair is not
   supported as a headline innovation on current evidence.
6. The current v1.8 formal repair run is not complete and cannot support a
   method-performance claim until its immutable selection artifacts have passed
   the specified gate.

## Definitions

- **Legal actor information:** receiver-local state/sensing plus packets that
  have actually been delivered and remain cache-valid, including their age,
  confidence, and provenance masks.
- **Relation conflict:** a time/receiver state in which perception evidence,
  delivered communication evidence, and task relevance do not induce the same
  usable-neighbor set or reliability.
- **Mechanism evidence:** evidence that the proposed pathway activates under
  its stated condition, changes the representation, and is necessary for the
  predicted effect against matched alternatives.
- **Primary endpoint:** time from failure onset to first stable task-chain
  establishment, with the stable window and censoring specified before formal
  evaluation.

## Forbidden claims

- “Multi-relation is universally superior.”
- “Role information is innovative” without a distinct role-conditioned
  mechanism and necessity evidence.
- Any superiority claim based only on MAPPO/HAPPO, unmatched actor information,
  selected OOD cells, or uncensored outcomes.
- Any causal explanation inferred solely from a final RMST difference.

## Unresolved claims

- Whether a conflict-conditioned factorization has an advantage over a
  parameter-matched single graph under matched legal information.
- Which relation conflicts occur often enough in realistic UAV episodes to
  matter for the nominal population.
- Whether the new mechanism improves learning stability, final establishment,
  or neither.
