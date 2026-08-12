# Scientific Upgrade Baseline Snapshot

Generated: 2026-08-12

## Frozen state

This snapshot freezes the project before the scientific upgrade Phase 1 audit. No new training has been started and no scientific protocol has been changed in this phase.

- Branch: `scientific_recovery_v2`
- Baseline tag: `upgrade-baseline-20260812`
- Frozen commit: `4122f6dd3748fb10a6aa91a60e38332b68cc0c12`
- Parent commit: `a843bbd2272bca8172d8f5d4dfde54bb6a9c75f536`
- Tracked files at freeze: 258
- Tracked result files at freeze: 99
- Tracked paper files at freeze: 40
- Tracked documentation files at freeze: 16

## Scope of the freeze

The following are frozen for audit purposes:

- source code under `algorithms/`, `baselines/`, `configs/`, `envs/`, `scripts/`, and `tests/`;
- the English manuscript under `paper_latex_3d_en/`;
- tracked CSV, figure, table, and report artifacts under `results/` and `docs/`;
- current configuration and evaluation conventions.

## Phase 1 restrictions

- No training may be started.
- No checkpoint may be overwritten.
- No observation, communication, failure timing, reward, recovery endpoint, survival horizon, tau, checkpoint-selection, or evaluation-protocol change may be implemented without a separate design note and commit.
- Existing raw results must be preferred over new evaluation or training.

## Known baseline limitations

- The current tracked release contains derived result artifacts but no training checkpoint files.
- The current manuscript contains an author placeholder and has not been PDF-verified in this runtime.
- Recovery endpoint semantics, survival/RMST implementation, paper-code equivalence, baseline fairness, and result provenance require the Phase 1 audit.

This file records the baseline only; it does not certify the current evidence as scientifically final.
