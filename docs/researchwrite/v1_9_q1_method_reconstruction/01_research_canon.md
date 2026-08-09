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
3. The v1.9 G0 read-only comparator audit found that, in the current
   recipient-specific implementation, the Task-Support and Communication masks
   are exactly equal in all 605 audited graph states.  A three independently
   meaningful relation claim is therefore not supported; this is a hard G0
   No-Go.  The author consequently terminated PCRF-R1 and authorized a
   two-source PCRF-R2 theory/protocol freeze; this is not a performance result.
4. The current pre-R2 common observation path can merge a receiver's direct
   target cache and delivered target-cache estimate.  A valid PCRF-R2 must
   remove this source-dependent target content from shared context and expose
   it only through source-tagged P/C branches.
5. R6.5 found the union residual material but not dominant in its fixed audit.
   It remains a structural risk, not evidence of an advantage.
6. R6.5 found near-zero Role-Pair gate variation in the pilot. Role-Pair is not
   supported as a headline innovation on current evidence.
7. The current v1.8 formal repair run is not complete and cannot support a
   method-performance claim until its immutable selection artifacts have passed
   the specified gate.
8. PCRF D0 static tests passed 5/5 and the D1 four-run CUDA engineering pilot
   reported `D1_ARTIFACT_GATE_PASS`. These are implementation and artifact
   checks only; they are not performance evidence.

## Definitions

- **Legal actor information:** receiver-local state/sensing plus packets that
  have actually been delivered and remain cache-valid, including their age,
  confidence, and provenance masks.
- **P/C conflict:** a time/receiver state in which direct local target evidence
  and delivered/cache-valid target evidence differ in availability, content,
  freshness, or confidence.  It is not a relation-adjacency Jaccard difference
  between different endpoint types.
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
- Whether source-separated direct P and delivered C inputs can be implemented
  without a common-observation bypass.
- Which P/C conflicts occur often enough in realistic UAV episodes to
  matter for the nominal population.
- Whether the new mechanism improves learning stability, final establishment,
  or neither.
