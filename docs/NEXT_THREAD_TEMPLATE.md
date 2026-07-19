# Next Thread Template

Use this when starting a new Codex conversation for this project.

```text
Please first read:

- AGENTS.md
- README.md
- docs/PROJECT_STATE.md
- docs/DECISIONS.md
- docs/ROADMAP.md
- docs/CURRENT_REQUIREMENTS.md
- docs/Q1_EXECUTION_PLAN.md

Then inspect the current relevant code and continue from the repository state, not from chat memory.

Task:
<one concrete, testable task>

Relevant files:
- <path>
- <path>

Constraints:
- Do not break the existing 2D evidence chain.
- Preserve the standard environment interface.
- Keep rules/masks/ELO/self-play auxiliary unless explicitly requested.

Completion standard:
- Relevant smoke tests or gates pass.
- Update docs/PROJECT_STATE.md if the milestone state changes.
- Summarize changed files, verification commands, and remaining risks.
```

## Recommended Next Task

```text
Task:
Run a PDF-readiness and baseline-credibility pass on the active 3D manuscript.

Relevant files:
- algorithms/ri_gmappo/simple_ri_gmappo.py
- scripts/evaluate_ri_gmappo_3d.py
- scripts/evaluate_3d_checkpoint_sweep.py
- scripts/build_gate1_safety_fx60_paper_tables.py
- scripts/analyze_3d_failure_aligned_mechanism.py
- scripts/replay_3d_relay_failure_case.py
- envs/uav_intercept_3d_env.py
- tests/
- docs/Q1_EXECUTION_PLAN.md
- docs/gate1_communication_feasibility_audit.md
- docs/actor_critic_observation_boundary.md
- docs/bottleneck_dropout030_relay_frozen_protocol.md
- docs/intercept_3d_gate1_hardened_60update_3seed_dev_summary.md
- docs/intercept_3d_gate1_hardened_60update_collision_audit.md
- docs/intercept_3d_gate1_hardened_60update_collision_replay.md
- docs/intercept_3d_gate1_hardened_60update_safety_diag_summary.md
- docs/intercept_3d_gate1_hardened_safety_5seed_fixed_update60_summary.md
- docs/gate1_safety_fx60_paper_tables.md
- docs/gate1_safety_fx60_no_curriculum_decision.md
- docs/gate1_safety_fx60_manuscript_consistency_audit.md
- docs/gate1_safety_fx60_contribution_evidence_alignment.md
- docs/gate1_safety_fx60_method_component_audit.md
- docs/gate1_safety_fx60_pdf_readiness_audit.md
- docs/gate1_safety_fx60_failure_timing_generalization_protocol.md
- docs/gate1_safety_fx60_failure_timing_generalization_formal_evidence.md
- paper_latex_3d_en/main.tex
- paper_latex_3d_en/references.bib
- paper_latex_3d_en/sections/01_introduction.tex
- paper_latex_3d_en/sections/02_related_work.tex
- paper_latex_3d_en/sections/03_problem.tex
- paper_latex_3d_en/sections/04_method.tex
- paper_latex_3d_en/sections/05_experiments.tex
- paper_latex_3d_en/sections/06_discussion.tex
- paper_latex_3d_en/sections/07_conclusion.tex
- docs/gate1_safety_fx60_model_cost_report.md
- results/gate1_safety_fx60_model_costs/model_costs.csv
- docs/PROJECT_STATE.md
- docs/ROADMAP.md

Constraints:
- Do not change the existing default 2D training behavior.
- Treat the fixed-update-60 safety-enabled result as a frozen fixed-budget candidate unless the repository records a replacement protocol before any new test evaluation.
- Do not tune on the completed five-seed fixed-update-60 test split.
- Treat completed five-seed bottleneck results as pre-hardening development evidence until P0 fixes are complete and rerun.
- Treat `results/intercept_3d_gate1_hardened_20update_3seed_dev/` as a development diagnostic only. Its relaxed-selection result is not final paper evidence.
- Treat `results/intercept_3d_gate1_hardened_60update_safety_diag/` as three-seed development evidence; the current stronger candidate is the five-seed fixed-update-60 safety result.
- Preserve the standard environment interface.
- Existing actor-side tests must keep enforcing communication-feasible information flow.
- Task-support edges may gate delivered messages but must not transmit target information by themselves.
- Use graph direction convention `A[receiver, sender] = 1`.
- Keep centralized critic access separate from decentralized actor access.
- Actor observation must remain decentralized: no team-level aggregate shortcuts.
- Stale or low-confidence target cache entries must remain invalid.
- `info["step"]`, node-failure activation, and delayed message delivery use post-step timing.
- Strict-bottleneck graph target node must not expose stale global target state when no agent currently detects the target.

Completion standard:
- Use the hardened code path; do not reuse old pre-hardening results as final evidence.
- Use the completed collision replay as the safety-flaw evidence.
- Use `docs/intercept_3d_gate1_hardened_safety_5seed_fixed_update60_summary.md` as the current five-seed fixed-budget evidence summary.
- Main fixed result: recovery `no_graph=21.8%`, `single=53.2%`, `multi_relation=88.6%`; `multi_relation` zero collisions; seed-aware `multi_relation - single` recovery delta `+35.4 pp`, 95% CI `[+1.2, +73.0] pp`.
- Use `docs/gate1_safety_fx60_mechanism/failure_aligned_mechanism_summary.md` as the current mechanism-evidence summary.
- `no_task_support` is complete and documented in `docs/intercept_3d_gate1_hardened_safety_no_task_support_5seed_fixed_update60_summary.md`.
- `no_role_pair_gate` is complete and documented in `docs/intercept_3d_gate1_hardened_safety_no_role_pair_gate_5seed_fixed_update60_summary.md`.
- Paper-facing result tables are complete in `docs/gate1_safety_fx60_paper_tables.md` and `results/gate1_safety_fx60_paper_tables/`.
- `no_curriculum` is deferred in `docs/gate1_safety_fx60_no_curriculum_decision.md`; the current paper claim emphasizes graph/message mechanisms more than training-curriculum causality.
- The fixed-update-60 experiment section is integrated into `paper_latex_3d_en/sections/05_experiments.tex`.
- The abstract in `paper_latex_3d_en/main.tex` has been updated to match the five-seed fixed-budget evidence.
- Discussion and conclusion have been updated to avoid overclaiming curriculum causality, 4v2 red-blue capability, missile closure, or 6DOF validation.
- Contribution-to-evidence alignment is complete in `docs/gate1_safety_fx60_contribution_evidence_alignment.md`.
- Manuscript consistency audit is complete in `docs/gate1_safety_fx60_manuscript_consistency_audit.md`.
- Method-component audit is complete in `docs/gate1_safety_fx60_method_component_audit.md`.
- Related-work and bibliography coverage has been expanded and citation audit currently has no missing or unused BibTeX keys.
- Baseline-credibility model-cost reporting is available in `docs/gate1_safety_fx60_model_cost_report.md` and `results/gate1_safety_fx60_model_costs/model_costs.csv`.
- The model-cost LaTeX table is integrated into the experiment section, and recursive static manuscript checks currently pass.
- PDF-readiness static audit is recorded in `docs/gate1_safety_fx60_pdf_readiness_audit.md`; all five paper-facing tables have page-width resize protection.
- Failure-timing generalization scenarios are registered and smoke-tested; the protocol is recorded in `docs/gate1_safety_fx60_failure_timing_generalization_protocol.md`.
- A 5-episode-per-seed diagnostic found early relay failure valid and delayed/late relay failure metric-limited because many full-method episodes end before the delayed failure window.
- The fixed-checkpoint early-vs-nominal failure-timing generalization formal evaluation is complete under `results/gate1_safety_fx60_failure_timing_generalization_formal_merged/`.
- The timing-generalization result is integrated into the active experiment section and passes recursive static LaTeX checks.
- Next, refresh paper-facing table documentation and compile the PDF if a LaTeX compiler is available.
- Run relevant Gate 1 tests before and after the development run.
- Current frozen 3v1 bottleneck dropout-relay protocol remains documented as a regression target.
- `docs/PROJECT_STATE.md` and `docs/ROADMAP.md` are updated with the result and next decision.
```
