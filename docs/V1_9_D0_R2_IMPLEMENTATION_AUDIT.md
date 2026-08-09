# v1.9 D0-R2 Implementation and Identifiability Audit

**Status: `D0_R2_PASS__D1_R2_NOT_AUTHORIZED`.**

**Scope:** source-separated PCRF-R2 implementation and deterministic integrity
tests only.  No GPU, training, checkpoint selection, held-out evaluation, OOD,
ablation, or performance comparison was run.

## Implemented contract

The recipient graph now emits a separate R2 contract for every actor:

- `P`: receiver direct target sensing only, with a direct target claim only
  when that receiver currently senses it;
- `C`: only recipient-delivered, cache-valid sender packet snapshots; pending,
  dropped, expired, invalid, and undelivered packets are excluded before C
  tensor construction;
- source-free `context`: self/task/role/vehicle context with target-relative,
  direct-detection, inbound-connectivity, message-age, and target-cache fields
  zeroed before actor use.

PCRF-R2 has two independent P/C graph encoders, no union residual, no
Task-Support input, and no Role-Pair gate.  Its two-logit baseline is separate
from the four-field legal conflict deviation
`[availability_difference, content_disagreement, C_age, C_uncertainty]`.
The deviation is implemented as `Delta(c) - Delta(0)` exactly.  `single_r2`
and `matched_nongraph_r2` consume the same raw P/C/context tensors; only their
representation differs.

The historical Task-Support-containing chain auxiliary loss is forcibly
disabled for all R2 encoder labels, preventing an implicit third relation from
entering R2 through gradient flow.

## Deterministic test results

| Gate | Result | Evidence |
|---|---|---|
| Existing recipient-specific boundary regression | PASS 14/14 | `scripts/test_actor_boundary_v1_8.py` |
| P-only/C-only source intervention invariance | PASS | changing one source leaves the other branch representation unchanged |
| Exact neutral condition | PASS | after arbitrary correction parameters, `Delta(0)` subtraction yields exact zero delta |
| Baseline/conflict separation | PASS | baseline is two receiver-invariant logits and unchanged under conflict-input intervention |
| Single-source degeneration | PASS | P-only gives `[1,0]`; C-only gives `[0,1]` |
| Legal conflict responsiveness and gradient | PASS | disagreement/age change the delta; correction receives nonzero gradient |
| Historical common-input bypass | PASS | R2 actor output is invariant to altered legacy `obs/node/edge` tensors |
| Unavailable-source exclusion | PASS | changing unavailable P or C payload tensors cannot change actor output |
| Simulator-global truth counterfactual | PASS | changing an undelivered teammate's true state cannot change R2 actor output |
| No third-relation / union / Role-Pair residue | PASS | R2 source contract and modules contain none |
| Comparator raw-input parity | PASS | PCRF-R2, `single_r2`, and `matched_nongraph_r2` execute from the same source-tensor hash |
| Primary comparator capacity feasibility | PASS | PCRF-R2 hidden 128: 169,977 params; single-R2 hidden 147: 170,784 params; relative gap 0.47% |
| Batched actor contract | PASS | recipient-view flattening preserves the R2 source contract |
| 3DOF environment smoke | PASS | 15 episodes; no new interface break |

`scripts/test_pcrf_r2_d0_v1_9.py` reports **12/12 PASS**.  Together with the
continuing 14/14 actor-boundary regression, this satisfies the authorized D0
integrity and identifiability scope.

## Interpretation and stop rule

This audit establishes that the frozen R2 object is implementable without the
identified source and global-truth bypasses.  It is **not** evidence that
PCRF-R2 is useful, learns stably, improves any endpoint, or outperforms the
single graph.  The next possible decision is whether to authorize D1-R2
engineering-only runs.  D2, F1, confirmatory held-out evaluation, diagnostics,
and OOD remain blocked.
