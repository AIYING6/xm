# Gate 1 Finish-Mode Consistency Audit

Last updated: 2026-07-22

## Purpose

Freeze the current Gate 1 evidence package around the defensible claim:

> Under strict intermittent sensing, target-information bottleneck, communication dropout, and relay-node failure, the multi-relation role graph with role-pair-conditioned message passing improves heterogeneous UAV kill-chain recovery reliability.

This audit prevents the manuscript and project state from drifting back toward unproven claims such as curriculum as a main contribution, full 4v2 red-blue validity, JSBSim validation, or online missile engagement.

## Findings

- `docs/PROJECT_STATE.md` still described staged topology curriculum as part of the main method and retained older statements that treated the 3DOF work as a straight-target curriculum baseline.
- `paper_latex_3d_en/sections/05_experiments.tex` still said the no-curriculum ablation was deferred, although the three-seed no-curriculum diagnostic is complete.
- The current evidence supports a strong Gate 1 mechanism package, not a broad full-system air-combat claim.

## Actions Taken

- Updated `docs/PROJECT_STATE.md` to mark the current milestone as fixed-update-60 Gate 1 evidence/package finishing.
- Rewrote the stable research direction so the primary method is the multi-relation role graph and role-pair-conditioned message passing.
- Explicitly moved topology curriculum, rules, reward shaping, ELO, self-play, and JSBSim replay into auxiliary or future-extension status.
- Updated the known-issues section to reflect the real remaining limitations: 3v1 scope, relay-failure claim boundary, unfinished formal maneuvering-target evidence, and missing local PDF rendering.
- Updated the experiment section to state that the three-seed no-curriculum diagnostic does not justify claiming curriculum as an independent contribution.
- Added a short contribution-boundary diagnostic note for the delayed scout-failure stressor: useful supplemental screen, not a main-table claim.
- Updated the English manuscript readiness audit to inspect `paper_latex_3d_en/` instead of the older `paper_latex_en/` path.
- Updated the submission package manifest generator so the English route and shared table/figure list point to the current 3D Gate 1 manuscript artifacts.

## Current Decision

Stop adding small stressors or new system components for now. The next work should be:

- reproducibility package audit;
- manuscript static consistency checks;
- figure/table reference verification;
- final result-summary polishing;
- only then decide whether a single formal maneuvering-target scenario-depth extension is worth the compute.

## Validation

Passed on 2026-07-22:

- `python scripts/check_latex_project.py`
- `python scripts/check_paper_claim_consistency.py`
- `python scripts/check_paper_text_risk.py`
- `python scripts/check_reproducibility_artifacts.py`
- `python scripts/audit_english_manuscript_readiness.py`
- `python scripts/write_submission_package_manifest.py`
- `python scripts/write_submission_action_register.py`
- `python scripts/write_submission_readiness_report.py`
- `python -m py_compile scripts/evaluate_3d_topology_robustness.py scripts/evaluate_3d_checkpoint_sweep.py scripts/analyze_3d_strict_sensing_seed_aware_stats.py`
- `python -m py_compile scripts/audit_english_manuscript_readiness.py scripts/write_submission_package_manifest.py`
- `python -m pytest tests/test_gate1_communication_feasibility.py -q`

Latest Gate 1 regression result: `20 passed`.

Remaining submission-action register status:

- `open`: 7, mostly journal/template/metadata/declaration/supplement/manual-review tasks.
- `blocked`: 2, PDF rendering due to missing LaTeX toolchain and real LAG/JSBSim validation due to missing JSBSim data/submodule.
- `deferred`: 1, optional extra seed expansion only if the target venue/adviser requires it.
