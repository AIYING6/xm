# v1.9 Argument Map

## Scientific tension

Under realistic packet delay, loss, and relay failure, an agent may have local
perception, delivered teammate evidence, and task relevance that disagree. A
single graph can aggregate legal features, but it has no explicit requirement
to preserve which semantic source conflicts with which. Conversely, simply
splitting a graph into named relation channels does not establish a useful
inductive bias when the channels are redundant or bypassed by a union path.

## Central research question

**When legally available perception, delivered communication, and task demand
disagree, can a provenance-conditioned relation factorization improve stable
task-chain establishment relative to parameter-matched single-graph and
non-graph policies that receive exactly the same actor information?**

## Testable thesis

The candidate v1.9 method should help only when a receiver has measurable
relation conflict. It should remain approximately neutral when relations agree.
Its advantage must disappear when the conflict-conditioned fusion is ablated.

## Minimum candidate mechanism: PCRF

The design name is **Provenance-Conditioned Relation Factorization (PCRF)**.
It is a candidate, not an implemented method.

1. Construct three legal evidence factors at each receiver: local perception,
   delivered/cache-valid communication, and task-demand compatibility. Each
   factor is built after availability/provenance masking and cannot invent a
   missing packet or geometry.
2. Encode each factor separately with matched parameter budget.
3. Derive a receiver-local **conflict descriptor** only from legal quantities:
   factor availability, relation overlap/disagreement, packet age, confidence,
   and role/task compatibility. It contains no simulator-global truth.
4. Fuse factor representations with a conflict-conditioned simplex gate. The
   gate must have a recorded neutral state under agreement and a measurable,
   bounded change under disagreement. It replaces the unrestricted union
   residual as the proposed explanatory pathway.
5. Retain a parameter-matched single-factor/union comparator so any gain cannot
   be attributed to width or privileged fields.

This is distinct from “multi-relational GNN + Role Gate”: the claimed object is
the explicit, legal, measurable response to relation conflict. Static Role-Pair
gates are not part of the headline candidate unless a later audit shows a
nontrivial independent role effect.

## Supporting arguments and required refutations

1. **Information structure matters.** Delayed/lost communication changes what
   a receiver can lawfully know. *Refutation:* PCRF leaks sender truth or uses
   unavailable geometry; this is a P0 stop.
2. **Relation conflict is observable.** The environment can generate fixed
   states with local sensing, delivery, freshness, and task demand in conflict.
   *Refutation:* conflicts are absent/trivial, or their descriptors collapse to
   the single-graph input.
3. **Factorized fusion is necessary.** Under matched input and capacity, PCRF
   should show a primary advantage in the pre-specified conflict-relevant
   population and mechanism-aligned representation behavior. *Refutation:* no
   seed-consistent advantage, no gate response, or a single graph matches it.
4. **The claim has a boundary.** In relation-agreement episodes, no large
   advantage is required or claimed. *Refutation:* the method only helps via a
   change to unrelated information, reward, or optimization budget.

## Final move

The paper should conclude either that provenance-conditioned relation
factorization is useful under a specified class of relation conflict, or that
it is not. A truthful negative result stops this method line; it is not a cue
to add unmotivated modules.
