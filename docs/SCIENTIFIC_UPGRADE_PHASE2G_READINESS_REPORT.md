# Scientific upgrade Phase 2G readiness report

**Branch:** `scientific_recovery_v2`  
**Phase:** 2G — Historical Evidence Closure and Canonical v2 Readiness  
**Date:** 2026-08-12  
**Formal training launched in this phase:** No

## Executive decision

**Phase 3A / formal canonical training: NO-GO.**

Gate A1, Gate H, and Gate C0 are closed positively. Gate B1 remains NO-GO because an independent standard survival implementation has not executed in an available clean environment. This is an explicit technical/statistical blocker, not a license to weaken tolerance, disable SSL verification, or substitute the historical survival v1.1 code. No headline result is promoted.

## Gate table

| Gate | Meaning | Status | Evidence / reason |
|---|---|---|---|
| A1 | Scientific protocol, endpoint, sender/receiver semantics, and paper-code equivalence | PASS | `docs/PAPER_CODE_EQUIVALENCE_AUDIT_V2.md`, `docs/RECOVERY_ENDPOINT_PROTOCOL_V2.md`, audited Method repair |
| A2 | Empirical strict endpoint availability | PENDING / NOT YET APPLICABLE | No canonical episodes exist yet |
| B1 | Statistical validity and independent standard KM/RMST validation | NO-GO | Local synthetic regression passes, but lifelines/scikit-survival/R survival could not be executed in `cac` or `cac_clean` |
| B2 | Empirical survival statistics | PENDING / NOT YET APPLICABLE | No canonical episodes exist yet |
| H | Historical checkpoint/evidence disposition | CLOSED — archival candidates recovered, canonical reproduction retired | `docs/HISTORICAL_CHECKPOINT_RECOVERY_CLOSURE.md`, `archival/provenance/recovered_checkpoint_candidates_v2.csv` |
| C0 | Canonical evidence contract and destination layout | PASS | `docs/CANONICAL_CONFIRMATORY_PROTOCOL_V2.md`, `results/canonical_v2/` contract |
| C1 | Empirical evidence completeness | NOT YET APPLICABLE | No canonical run is authorized |

## Phase 2G-1: historical evidence closure

The final bounded search covered the repository, sibling worktrees, the historical `e02a753` worktree, Git history/LFS, Downloads, OneDrive, Documents, Desktop, source archives, and project-related Codex artifact archives. It found two archival 5-seed/update-60 checkpoint families:

1. `param_matched_single_graph_5seed_bottleneck_strict_update60_formal_candidate`, seeds 0–4, 1,590,846 bytes each;
2. `true_no_role_identity_hardened_5seed_strict_update60_formal_candidate`, seeds 0–4, 1,591,534 bytes each.

All ten candidate SHA256 values are recorded in `archival/provenance/recovered_checkpoint_candidates_v2.csv`. They remain external archival candidates. The recovered directories do not provide a complete v2 strict-endpoint evidence package bound to each checkpoint, so they cannot be declared historical reproduction or canonical evidence. Historical 5-seed Gate-1 remains legacy descriptive evidence; historical 3-seed/10,800 survival remains legacy survival evidence. Future confirmatory training is new evidence.

## Phase 2G-2: endpoint and protocol freeze

The strict primary endpoint is frozen as:

```text
pre_failure_chain_established AND chain_lost_after_failure
AND post_failure_chain_recovered_after_loss
```

The primary duration is `t_recovery - t_loss`; onset-to-first-establishment is secondary. The schema and cohort rules are in `docs/RECOVERY_ENDPOINT_PROTOCOL_V2.md`. The canonical method set, five-seed plan, validation-only checkpoint selection, tau schedule, bootstrap hierarchy, and artifact contract are in `docs/CANONICAL_CONFIRMATORY_PROTOCOL_V2.md`.

## Phase 2G-3: statistical gate

The v2 local implementation and synthetic regression suite are retained. A fail-closed harness is provided at `analysis/survival_v2/validate_standard_reference.py`. It requires `lifelines` and records its version and tolerance when executed.

Observed environment facts:

- `cac`: numpy/pandas/scipy available; no lifelines, scikit-survival, or Rscript.
- `cac_clean`: isolated Python environment; no standard survival package.
- Normal SSL installation attempts failed; SSL security was not lowered.

Consequently, KM/RMST are not yet trusted for headline empirical claims. Gate B1 stays NO-GO until the full synthetic matrix (including censor/event ties and all taus) plus the empirical dataset pass a standard reference with the frozen `1e-10` absolute tolerance.

## Phase 2G-4/5: canonical readiness

`results/canonical_v2/` contains the required empty destination structure: protocol, configs, manifests, checkpoints, validation, raw episodes, survival, mechanism, figures, tables, and `SHA256SUMS`. It contains no formal outputs and no checkpoint bytes. This is intentional.

The evidence contract is ready but empirical completeness is not applicable. A future run may start only after Gate B1 is PASS and the final readiness gate is re-issued.

## What can proceed without training

- Install/execute a standard survival reference in a clean environment without changing SSL policy.
- Complete the v2 numerical cross-validation report and package/version record.
- Perform non-mutating review of the recovered archival candidate metadata.
- Prepare scripts and manifests against the frozen protocol.

## What cannot proceed yet

- No formal canonical training.
- No confirmatory seed expansion.
- No new headline survival result.
- No historical result relabeling as v2 reproduction.
- No endpoint, tau, censor, reward, failure timing, or checkpoint-selection changes.

## Final GO / NO-GO

**Current decision: NO-GO for Phase 3A.**

The project is scientifically protocol-ready and has a clean canonical evidence destination, but it is not statistically gate-ready. Phase 3A becomes **GO** only after B1 passes independently and the readiness report is updated without altering the frozen protocol. If the recovered checkpoint candidates later pass complete provenance binding, they may be evaluated as archival evidence; that evaluation must remain explicitly separate from new canonical confirmatory training.
