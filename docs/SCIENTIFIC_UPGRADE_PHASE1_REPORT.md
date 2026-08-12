# Scientific Upgrade Phase 1 Report

Generated: 2026-08-12

Scope: Phase 0 freeze and Phase 1 audit only. **No new training was started. No scientific protocol was modified.**

## 1. Frozen baseline

- Branch: `scientific_recovery_v2`
- Baseline tag: `upgrade-baseline-20260812`
- Frozen pre-audit commit: `4122f6dd3748fb10a6aa91a60e38332b68cc0c12`
- Phase-0 snapshot commit: `43e24e1`
- Current working changes are audit artifacts only.

## 2. Confirmed problems

### P0 scientific definition

The retained episode CSV contains `post_failure_chain_recovered_after_loss`, but lacks `pre_failure_chain_established`. It therefore cannot prove the strict cohort:

```text
pre-failure chain established → post-failure chain loss → post-loss re-closure
```

The current primary endpoint must not be called strict recovery/re-establishment until those fields are available.

### P0 statistical implementation

The historical survival v1.1 implementation:

- subtracts events but not censorings from the risk set at tied times;
- writes a fixed primary-tau observed delta for every sensitivity tau.

The old outputs are legacy evidence, not canonical v2 statistics.

### P0 paper-code equivalence

The method text describes independent query/key projections and edge features entering the message payload. The code uses a shared node projection, edge features as an additive attention-score bias, role-pair message modulation, and a union/global residual branch. The method section is not equation-level equivalent.

### P0 result provenance

The current retained Gate-1 episode CSV has 3,000 rows, five training seeds, three graph variants, and two scenarios. The paper claims a different 10,800-episode, three-seed package. Checkpoint bytes are absent even though CSV paths point to historical checkpoints.

### Baseline identity

The config distinction between No-Graph internal ablation and canonical MAPPO is reasonable, but the retained episode CSV labels all graph variants as `EA-RG-MAPPO-S`. This prevents independent verification of baseline identity from the result file alone.

## 3. Completed repairs/audits

- Created frozen branch and baseline tag.
- Added `docs/UPGRADE_BASELINE_SNAPSHOT.md`.
- Added read-only recovery endpoint inventory script and report.
- Added independent survival v2 implementation with six synthetic tests; all six pass.
- Added `analysis/survival_v2/survival_validation_report.md`.
- Added paper-code equivalence audit.
- Added baseline fairness audit.
- Added result provenance audit.
- Confirmed no training process was launched.

These are audit and infrastructure repairs, not scientific-protocol changes.

## 4. Recommended recovery endpoint

Primary endpoint for the upgraded project:

```text
pre_failure_chain_established
AND chain_lost_after_failure
AND post_failure_chain_recovered_after_loss
```

Recommended time origin and estimand:

```text
t = failure onset
T_loss = first post-failure loss after a pre-established chain
T_recovery = first stable closure after T_loss
ΔT = T_recovery - T_loss
```

If the strict cohort is too small, rename the current endpoint to `post-failure chain establishment/closure` and retain strict recovery as a secondary endpoint. Do not change the definition to improve results.

## 5. Is survival/RMST trustworthy?

**Not yet.** The v2 implementation is independently implemented and synthetic-tested, but the historical numerical outputs are not yet validated against a standard third-party survival library. The configured environment lacks `lifelines`, `scikit-survival`, `statsmodels`, and R; installing `lifelines` failed due to the package mirror SSL error. Gate B remains NO-GO.

## 6. Are paper formulas and code fully consistent?

**No.** High-level graph semantics are aligned, but the attention formula, edge-feature role, shared projection structure, and global residual branch require correction. See `docs/PAPER_CODE_EQUIVALENCE_AUDIT.md`.

## 7. Missing evidence package content

- Final checkpoint bytes and hashes;
- raw episode fields needed to reconstruct strict endpoint cohort and loss time;
- canonical v2 survival outputs;
- a consistent method/baseline identity manifest;
- a single release whose raw CSV, configs, checkpoints, derived tables, and figures agree on seed count and episode count;
- PDF-verified manuscript after the scientific corrections.

## 8. Reuse / re-evaluation / retraining decision

### Can be directly re-statistically analyzed

- Terminal success, collision, timeout, and descriptive closure summaries from retained raw/summary CSVs, after label verification.
- Existing seed-level descriptive tables, if their source CSV and method identity are re-bound.
- Legacy OOD/robustness summaries only as provisional diagnostics, not final claims.

### Requires re-evaluation, not automatically retraining

- Strict recovery endpoint, if the selected checkpoint bytes can be restored from external storage or Git LFS/backup and evaluation protocol is frozen first.
- Canonical KM/RMST and tau sensitivity after the endpoint fields are emitted.
- Mechanism trajectories and checkpoint-selection provenance.

### Requires retraining only if checkpoints cannot be restored

- Any confirmatory evaluation that depends on missing final checkpoints.
- New five-seed confirmatory training beyond the recoverable evidence.
- Union/global-residual ablation, Gate Prior sensitivity, random failure timing/node, scalability, or higher-fidelity extensions.

The current evidence does **not** justify automatic retraining during Phase 1.

## 9. Recommended Phase 2/3 protocols

### Phase 2: statistics and evidence repair

1. Restore/locate checkpoint bytes and original richer episode CSVs.
2. Freeze endpoint schema and emit explicit `pre_failure_chain_established`, `chain_lost_after_failure`, `t_loss`, `t_recovery`, `event`, and `censor_time` fields.
3. Install/use a standard survival reference implementation in a reproducible environment.
4. Run v2 KM/RMST and hierarchical bootstrap over pre-registered taus; verify tau-specific observed deltas.
5. Regenerate tables, figures, claim matrix, and paper metrics from canonical outputs.
6. Repair method equations and baseline labels.

### Phase 3: confirmatory experiments after Gate A–C pass

Freeze a protocol before training with:

- five or more independent training seeds;
- Full versus canonical MAPPO plus single-graph comparator;
- fixed training budget and validation-only checkpoint selection;
- strict primary endpoint and tau chosen before results;
- union/global residual ablation;
- Gate Prior sensitivity;
- failure-aligned mechanism measurements;
- raw episode output and checkpoint hash for every method/seed.

Only after this gate consider random failure timing/node or 4/5-UAV scalability.

## 10. Final GO / NO-GO

**Phase 1 audit status: NO-GO for training and NO-GO for submission-level headline survival claims.**

The project is **GO for Phase 2 evidence repair** and **GO for selective restoration of existing raw data/checkpoints**. It is **NO-GO for any new training** until Gate A (endpoint/paper-code correctness), Gate B (standard survival validation), and Gate C (evidence completeness) pass.
