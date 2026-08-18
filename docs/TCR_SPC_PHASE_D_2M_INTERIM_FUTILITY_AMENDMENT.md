# TCR/SPC Phase-D 2M Interim Stop-Loss Amendment

Status: **prospective execution amendment; no training result has been inspected**  
Applies to: `TCR_SPC_PHASE_D_3M_CONTINUATION`  
Historical Phase-C v1: `TECHNICAL_INVALID` (unchanged and immutable)

## 1. Purpose and boundary

This amendment adds one pre-registered stop-loss checkpoint to the already
authorized strict-continuous Phase-D `1M -> 3M` continuation. It does not
change TCR, SPC, UTR, the Single-Graph backbone, PPO, environment, reward,
failure semantics, actor information boundary, seeds, or evaluation tape.

All 15 trajectories remain paired and symmetric:

- UTR/SPC/TCR × seeds `2002, 2101, 2102, 2103, 2104`;
- all four methods/seeds use the same 2M decision point;
- no seed may be removed, replaced, or given a different budget;
- no checkpoint is promoted as a performance result.

The 2M checkpoint is an interim futility/stop-loss audit only. If the gate
passes, each trajectory continues strictly from its 2M runtime state to the
common 3M endpoint. If the gate fails, all 15 trajectories stop at 2M and no
3M continuation is started. A stop at 2M is not a new algorithmic result.

## 2. Strict continuation stages

The first stage resumes the verified Phase-C 1M runtime states:

| stage | source update | endpoint update | environment steps | runtime boundary |
|---|---:|---:|---:|---|
| Phase-D 2M interim | 3907 | 7813 | 2,000,128 | Phase-C 1M runtime state |
| Phase-D 3M final | 7813 | 11719 | 3,000,064 | Phase-D 2M runtime state |

The 2M-to-3M transition is strict runtime continuation, not a warm restart.
The second stage must restore the complete 2M runtime state and pass the same
save→reload→next-update contract. If a continuation chain is technically
invalid, the result is `TECHNICAL INVALID`; the executor must not silently
restart or substitute a checkpoint.

## 3. Fixed 2M milestones

The 2M stage saves `1.5M` and `2M` milestones. They are for learning-curve
and stop-loss auditing only. The 2M final checkpoint is not promoted over the
3M final checkpoint, and no intermediate score may be selected as the final
method result.

## 4. Pre-registered stop-loss gate

The 2M evaluation uses the same development tape and the same v2 scientific
validity definition as Phase D. Technical validity is checked first using
risk-set trigger validity; all raw episodes, including pre-trigger collision,
remain in the metrics.

The decision is `STOP_AT_2M` if **any** of the following is true:

1. Any TCR seed satisfies the frozen catastrophic-seed rule against its
   same-seed UTR reference.
2. Stress seed `2002` is catastrophic for TCR.
3. The frozen cross-seed bifurcation rule is triggered.
4. The frozen systemic safety-deterioration rule is triggered.
5. TCR is systematically below UTR on OOD robustness: pooled `J_OOD_mean`
   and pooled `J_OOD_worst` are both lower, and fewer than `3/5` TCR seeds
   have positive `J_OOD_worst` direction versus UTR.
6. TCR is systematically below SPC on OOD-worst: at least `4/5` paired
   TCR-minus-SPC OOD-worst differences are negative and their mean is
   negative.

If none of these conditions is true, the decision is
`CONTINUE_TO_3M`. This is only a continuation authorization under the
already approved Phase-D contract; it is not a GO claim and does not alter
the 3M decision criteria.

## 5. Reporting and stop behavior

The 2M audit must write:

- `PHASE_D_2M_INTERIM_DECISION.json`;
- `docs/TCR_SPC_PHASE_D_2M_INTERIM_STOP_LOSS_REPORT.md`;
- per-seed and pooled nominal/F0/OOD metrics;
- catastrophic, safety, exposure, risk-set validity, and pre-trigger metrics;
- explicit stop reasons, or an explicit empty stop-reason list.

If `STOP_AT_2M`, the launcher exits successfully after preserving the 2M
results. It does not launch 3M, 5M, held-out, canonical, ablation, or any
new training. If `CONTINUE_TO_3M`, it launches only the symmetric 2M→3M
strict continuation and the already authorized final Phase-D evaluation.

Automatic shutdown, if requested in the cloud wrapper, is permitted only
after the selected stop-at-2M or completed-3M outputs and hashes are safely
written. A training/evaluation/aggregation error must not be treated as a
successful stop-loss decision.

## 6. Immutable exclusions

This amendment does not authorize:

- 3M→5M or any later extension;
- held-out or canonical seeds;
- algorithm, PPO, reward, environment, projection, threshold, or tape
  changes;
- best-checkpoint selection, early stopping, or seed exclusion;
- rewriting Phase-C v1 `TECHNICAL_INVALID`.
