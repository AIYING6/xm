# v1.9 PCRF-R2 — Two-Source Theory and Protocol Freeze

**Status: CONCEPTUAL_AND_PROTOCOL_FREEZE; G0-R2 theory/comparator release is
recorded separately.  PCRF-R1 is terminated.**

This document is the author-authorized successor to the three-relation
PCRF-R1 line.  It freezes the R2 scientific object and the implementation
contract necessary to test it.  The novelty kill-check and final theory/
comparator conditions are now closed in
[G0-R2 final freeze](V1_9_G0_R2_FINAL_THEORY_COMPARATOR_FREEZE.md).  That
release still authorizes no code or GPU work by itself.

## 1. Author decision and scientific scope

G0-R1 established that Task-Support has no independent legal support, feature,
or intervention relative to delivered Communication.  It is therefore removed
from the headline architecture.  Task/role information may remain only as a
shared actor-legal **context** feature; it is not an evidence relation and
must be identically available to every comparator.

The R2 question is deliberately narrower and falsifiable:

> Under recipient-specific actor information, does preserving *direct local
> perception* and *delivered/cache-valid communication* as distinct evidence
> sources, with conflict-conditioned fusion, improve time to stable task-chain
> establishment over a single graph that receives exactly the same raw fields?

No third relation, Role-Pair gate, unrestricted union residual, or additional
dynamic fusion module is part of R2.

## 2. Mandatory source-separated actor contract

R2 has exactly two evidence sources for receiver \(i\):

\[
G_i^P=\{x_i^{self},\;m_i^P,\;\widehat y_i^{direct},\;q_i^{direct}\},
\qquad
G_i^C=\{x_i^{self},\;m_{ij}^C,\;p_{j\to i}^{delivered},\;
\text{age}_{ij},\;\text{confidence}_{ij}\}_{j\ne i}.
\]

`P` is a direct local sensing claim about the target, including its direct
availability mask and direct-sensing quality.  `C` contains only packets that
were actually delivered and remain cache-valid, including their snapshot target
claim, sender/provenance, generation/delivery timing, age, and confidence.
Pending, dropped, expired, invalid, or undelivered packets are absent/zeroed
before C construction.

The shared context \(z_i^{ctx}\) may contain receiver self state, own role,
local task state, local attack availability, and fixed vehicle capability.  It
must contain **no target estimate, no target-cache estimate, no packet-derived
target age/confidence, and no teammate payload**.  This prevents a source from
bypassing the factorization through a common observation encoder.

This restriction is necessary because the current pre-R2 `obs` path merges a
fresh direct target cache and a delivered target cache into the same target
fields.  That existing path is historical implementation evidence only; it is
not a valid R2 source contract.

## 3. R2 representation and exact neutral condition

Let `mP` and `mC` denote legal source-availability masks, and let \(F_P,F_C\)
be separate factor encoders.  R2 is

\[
h_i^P=m_i^P F_P(G_i^P),\qquad h_i^C=m_i^C F_C(G_i^C),
\]

\[
c_i=[a_i^P-a_i^C,\;d_{PC},\;\operatorname{age}_C,\;1-\operatorname{confidence}_C],
\]

\[
\ell_i=\beta+\Delta(c_i)-\Delta(0),\qquad
w_{ir}=\frac{m_i^r\exp(\ell_{ir})}{\sum_{s\in\{P,C\}}m_i^s\exp(\ell_{is})}
\quad\text{when }m_i^P+m_i^C>0,\qquad h_i=w_{iP}h_i^P+w_{iC}h_i^C.
\]

Here \(\beta\) is a learned, receiver-invariant two-logit baseline with no
dynamic input.  The only allowed dynamic descriptor fields are source
availability difference, a masked content disagreement \(d_{PC}\) between a
direct target claim and delivered target claim(s), delivered-message age, and
delivered-message confidence.  `dPC` is **not** an adjacency Jaccard score:
P and C have different endpoint types, so such a score would be structurally
confounded rather than an evidence disagreement.

The exact neutral state is `aP-aC=0`, `dPC=0`, `ageC=0`, and
`confidenceC=1`; it yields \(\Delta(c_i)=0\) exactly.  If exactly one source
is legal, its fusion weight is exactly one and the unavailable source is zero.
If neither is legal, \(h_i=0\) and action selection uses only
\(z_i^{ctx}\); no missing target/teammate state may be reconstructed.

## 4. Comparator information contract

| Method | Receives exactly the same legal raw inputs | Representation-only difference |
|---|---|---|
| PCRF-R2 | `z_ctx`, source-tagged direct P claims, source-tagged delivered C packet claims, masks, age/confidence, geometry, role/task context | separate P/C encoders plus availability-masked baseline/deviation fusion |
| wider single graph | the same source-tagged P/C claims, masks, packet fields, geometry, and context | one shared encoder on `P union C`; no factor-specific encoder/fusion |
| matched-information non-graph | the same raw P/C/context fields before deterministic source-preserving pooling | no graph message passing |

The single graph must retain source identity and every conflict-relevant raw
field.  It may learn to use them; withholding them would create information
asymmetry rather than a representation comparison.  An input-hash/provenance
audit must compare all three pre-encoder tensors before any R2 launch.

## 5. Preregistered mechanism states

These are diagnostic states, not selected performance cells:

1. **agreement:** direct P and fresh C agree; \(\Delta\) should return to the
   baseline response;
2. **fresh P / stale C:** a delivered C claim is old or low-confidence and its
   content differs from direct P;
3. **P unavailable / C valid:** only C may supply target evidence;
4. **C unavailable / P valid:** only P may supply target evidence.

Every method receives the same packet process and no method receives an
extra source.  All frozen diagnostic cells and failures are reported; these
diagnostics never replace nominal primary evidence.

## 6. R2 D0 requirements (not yet implemented or run)

An independent D0-R2 suite must pass before D1-R2:

1. R5 actor-boundary tests remain 14/14 or are superseded by stricter R2 tests;
2. P and C each have legal states that change while the other remains fixed;
3. source content, masks, and common context have no P/C bypass;
4. `c=0` gives `Delta=0` exactly after learning updates;
5. unavailable communication cannot restore teammate or target truth;
6. unavailable perception cannot restore target truth;
7. single-source degeneration gives unit weight to the sole available source;
8. legal change to content disagreement, age, or confidence changes the
   deviation and gives it nonzero gradient; and
9. PCRF-R2, single graph, and non-graph pass raw-input parity/hash checks.

## 7. Statistical and execution locks still required

The primary comparator is PCRF-R2 versus wider single graph.  The primary
endpoint remains time from failure onset to first `K=4` stable legal
task-chain establishment.  Any future restricted-time estimand must code
absorbing collision/constraint terminal events as no establishment by \(\tau\),
not ordinary early right censoring.  Hierarchical bootstrap resamples training
seeds, then matched evaluation episodes.

Before F1, author must freeze the practical margin \(\delta_{min}\), seed rule
(direct 8 or direction-neutral 5-to-8 precision expansion), validation
selector, new confirmatory episode bank, endpoint adequacy bounds, all F1
budget parameters, and the `PCRF-Delta0` mechanism control.  These values may
not be inferred from D1/D2/F1 performance.

## 8. Release sequence and No-Go rules

```text
R2 conceptual/protocol freeze (this document)
  -> verified R2 novelty kill-check (completed, narrowed claim)
  -> G0-R2 final protocol release (completed)
  -> separately authorized source-separated R2 implementation + D0-R2
  -> D1-R2 engineering gate
  -> matched three-method D2
  -> F1 -> untouched F2 -> diagnostics -> graded OOD
```

Stop the R2 line without a headline superiority claim if: source separation
cannot be implemented without actor-information leakage; the novelty
kill-check finds a method matching the complete R2 object; input parity fails;
the primary PCRF-R2 versus single-graph contrast fails its frozen practical
criterion; or the conflict/`Delta0` mechanism predictions fail.  No result
permits adding a third relation merely to rescue the story.
