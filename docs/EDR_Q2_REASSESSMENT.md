# EDR-Q2 — Q2-Publishable Method Reassessment

## Scope

The historical EDR decision remains **`C — NO_GO`** under the prior Strong-Q2
novelty standard. This is a prospective reassessment under the author-approved
Q2-publishable standard; it does not reopen T3/T5/T7 or authorize code,
training, rollouts, tape creation, held-out, or canonical evaluation.

## Bounded method claim

EDR changes only neighbour aggregation in the existing SG actor:

\[
m_{ij}=A_{ij}\sigma(e_{ij})h_j,\qquad c_i=\frac{1}{C}\sum_j m_{ij},\qquad C=N_{max}=4.
\]

All score and payload parameters are reused from the matched SG. For a deleted
incoming edge `(i,k)`, every surviving contribution `m_ij, j != k` is unchanged
before downstream nonlinearity. EDR does not claim topology invariance,
information restoration, recovery, a new universal GNN, or guaranteed
robustness.

## Q2 review ledger

| Requirement | Finding | Status |
|---|---|---:|
| Current SG vulnerability | Softmax deletion rescales surviving messages. | PASS |
| Deletion locality | Fixed-normalized independent gates preserve survivor contributions. | PASS |
| Relay relevance | Real F0 removes Relay→Attacker while Scout→Attacker remains legal. | PASS |
| Actor legality | Existing legal local and graph inputs only. | PASS |
| Parameter fairness | Reused operator has 116,728 parameters, exactly matching SG. | PASS |
| Stability complexity | No feedback sampler, auxiliary target, or gradient surgery. | PASS |
| Novelty | Moderate, targeted, and honest; not foundational GNN novelty. | PASS at Q2 only |

## Reassessment result

**Q2_PUBLISHABLE_GO.** EDR is not a standalone graph-learning invention. It is
eligible as the targeted method component of a complete paper whose contribution
bundle includes legal Relay failure semantics, topology/path reconfiguration,
OOD robustness, safety, seed stability, and property-specific ablations.

A stable 10–20% robustness improvement with retained nominal competence and
lower timeout would be sufficient for a credible Q2 paper; no performance
doubling is required. This is a future falsifiable hypothesis, not a result.
