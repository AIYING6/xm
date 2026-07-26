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
- docs/Q1_THREE_STAGE_EXECUTION_PLAN.md
- docs/FINAL_SINGLE_PAPER_SCOPE.md
- docs/FINAL_Q1_SINGLE_PAPER_PLAN.md
- docs/p0_scientific_validity_hardening_update.md
- docs/p1_training_protocol_standardization.md
- docs/dev1m_launch_plan.md

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
Start P1 training-protocol standardization under the final Q1 single-paper plan.

Relevant files:
- algorithms/ri_gmappo/simple_ri_gmappo.py
- scripts/run_3d_strict_sensing_formal_protocol.py
- scripts/evaluate_3d_checkpoint_sweep.py
- scripts/report_3d_model_costs.py
- scripts/analyze_3d_maneuver_reachability.py
- scripts/analyze_3d_geometric_oracle_reachability.py
- scripts/pretrain_ri_gmappo_3d_bc.py
- scripts/train_ri_gmappo.py
- scripts/run_3d_nominal_weaving_mild_formal_protocol.py
- envs/uav_intercept_3d_env.py
- tests/
- docs/Q1_EXECUTION_PLAN.md
- docs/Q1_THREE_STAGE_EXECUTION_PLAN.md
- docs/FINAL_SINGLE_PAPER_SCOPE.md
- docs/FINAL_Q1_SINGLE_PAPER_PLAN.md
- docs/p0_scientific_validity_hardening_update.md
- docs/p1_training_protocol_standardization.md
- docs/ACCELERATED_FINISH_PLAN.md
- docs/actor_critic_observation_boundary.md
- docs/gate1_communication_feasibility_audit.md
- docs/intercept_3d_gate1_hardened_safety_5seed_fixed_update60_summary.md
- docs/gate1_safety_fx60_model_cost_report.md
- docs/parameter_matched_single_graph_baseline_plan.md
- docs/parameter_matched_single_graph_seed0_dev_summary.md
- docs/parameter_matched_single_graph_3seed_dev_summary.md
- docs/parameter_matched_single_graph_update60_dev_summary.md
- docs/parameter_matched_single_graph_5seed_test50_candidate_summary.md
- docs/parameter_matched_single_graph_5seed_test50_seed_aware_stats/intercept_3d_strict_sensing_seed_aware_bootstrap.md
- results/param_matched_single_graph_5seed_update60_candidate_test50/seed_aware_stats/
- results/param_matched_single_graph_5seed_update60_candidate_test50/combined_summary/
- docs/true_no_role_identity_ablation_audit.md
- docs/true_no_role_identity_post_hardening_diag10_summary.md
- docs/true_no_role_identity_hardened_3seed_dev20_summary.md
- docs/true_no_role_identity_hardened_5seed_formal_test50_summary.md
- results/true_no_role_identity_hardened_5seed_update60_formal_test50/combined_summary/
- results/true_no_role_identity_hardened_5seed_update60_formal_test50/seed_aware_stats/
- docs/gate1_safety_fx60_paper_tables.md
- docs/gate1_safety_fx60_no_curriculum_decision.md
- docs/gate1_safety_fx60_no_curriculum_3seed_dev60_summary.md
- docs/gate1_safety_fx60_seed_mechanism_summary.md
- docs/gate1_safety_fx60_dropout030_scout_failure_diag20_summary.md
- docs/gate1_safety_fx60_dropout030_delay2_scout_failure_diag20_summary.md
- docs/gate1_safety_fx60_weaving_mild_fixed_checkpoint_diag20_summary.md
- docs/nominal_weaving_mild_frozen_protocol.md
- docs/nominal_weaving_mild_formal_protocol_smoke_summary.md
- docs/nominal_weaving_mild_formal_protocol_3seed_summary.md
- results/gate1_safety_fx60_weaving_mild_fixed_checkpoint_diag20/
- docs/PROJECT_STATE.md
- docs/ROADMAP.md

Constraints:
- Do not change the existing default 2D training behavior.
- Preserve the standard environment interface.
- Use the hardened communication-feasible code path only.
- Follow `docs/FINAL_Q1_SINGLE_PAPER_PLAN.md` if older docs conflict.
- Do not launch million-step training before P0 information-boundary tests pass.
- Do not tune on the completed five-seed fixed-update-60 test split.
- Actor observation must remain decentralized: no team-level aggregate shortcuts.
- Task-support edges may gate delivered messages but must not transmit target information by themselves.
- Use graph direction convention A[receiver, sender] = 1.
- Keep centralized critic access separate from decentralized actor access.
- Stale or low-confidence target cache entries must remain invalid.
- Strict-bottleneck graph target node must not expose stale global target state when no agent currently detects the target.
- Treat the current five-seed test50 parameter-matched single-graph result as a capacity-control credibility result.
- Report seed-level scatter because parameter-matched single-graph is competitive on seeds 0 and 4 but weak on seeds 1, 2, and 3.
- Treat old no-role-identity checkpoints as pre-hardening and not manuscript-level evidence.
- Treat all pre-2026-07-24 3DOF checkpoints with 18 edge features as pre-hardening because actor graph edge features now exclude global `attack_hold`.
- P0 actor information-boundary tests passed at 24 tests; continue with P1 unless new leakage is found.
- `configs/paper/` and `scripts/audit_paper_configs.py` now exist; use them as the P1 source of truth for formal training protocol.
- `scripts/generate_paper_commands.py` generated and executed one-update smoke commands for mappo/single_graph/ea_rg_mappo.
- `scripts/generate_paper_commands.py --include-sweeps` now generates validation/test checkpoint sweep commands; test sweeps require validation selection CSVs.
- `scripts/write_paper_run_provenance.py` generated hashes for paper configs and critical code.
- `configs/paper/checkpoint_selection_schema.yaml` and `scripts/audit_checkpoint_selection_schema.py` fix the validation/test selection schema.
- `scripts/train_happo_baseline.py` HAPPO training smoke passed; `scripts/evaluate_happo_checkpoint_sweep.py` validation/test sweep smoke also passed.
- Treat the hardened no-role dev20 result as development evidence only: three seeds and ten test episodes per seed.
- Treat the hardened no-role five-seed test50 result as paper-facing mechanism evidence, but report seed scatter.
- The role-identity result has already been integrated into the paper table package.
- The fixed-checkpoint `weaving_mild` diagnostic is too hard for a main table: full recovery is only `11.0%`.
- Direct strict relay-failure `weaving_mild` fine-tuning for 20 updates failed: both `single` and `multi_relation` recovered `0.0%`.
- Nominal `weaving_mild` without strict sensing or node failure is weakly feasible for `multi_relation` at `21.7%` success, while `single` remains at `0.0%`.
- From-scratch nominal weaving BC/PPO was unstable and should not be the next route.
- Checkpoint-compatible `hidden_dim=64` fine-tuning from mature straight-target policies reached `multi_relation=26.7%` and `single=0.0%`; it is promising but below the Stage 2 gate.
- The 60-update `weaving_mild` extension stayed weak: `multi_relation=24.7%`, with seed 1 still `0.0%`.
- `weaving_tiny` exists as an opt-in lower-amplitude curriculum entry and has regression coverage. Zero-shot `weaving_tiny` gives `multi_relation=28.9%` and `single=0.0%`, but seed 1 still fails.
- `scripts/run_3d_target_policy_curriculum.py` exists and passed a smoke for `straight source -> weaving_tiny -> weaving_mild`.
- The three-seed `weaving_tiny -> weaving_mild` diagnostic reached only `27.3%` success and seed 1 stayed at `0.0%`.
- Opt-in `attack_geometry_reward_weight` exists and is tested, but `0.15` did not unstick seed 1.
- Learned-policy reachability analysis shows the seed-1 blocker is attack-geometry conversion, not basic approach: seed 1 reduces range by about `11.9 km` but has no attack-window episodes and no geometry score above `0.25`.
- Geometric-oracle reachability shows nominal `weaving_mild` is feasible: lead/offset oracle reaches `100%` success and `0%` collision on matched 30-episode diagnostics. Direct pursuit is less safe (`66.7%` success, `36.7%` collision), so the useful signal is lead/offset attack-geometry behavior.
- Oracle-BC support now exists. Seed-1 attacker-weighted offset BC gives the first nonzero learned-policy signal on nominal `weaving_mild` (`3.3%` success, zero collision), but pure BC remains far below the acceptance gate.
- Seed-1 oracle-BC + PPO dev10 improves nominal `weaving_mild` success to `13.3%` with zero collision. This is promising but still below the scenario-depth acceptance gate.
- Seed-1 oracle-BC + PPO continuation reaches `40.0%` success and `0.0%` collision on matched nominal `weaving_mild` test episodes, clearing the seed-1 development threshold.
- Three-seed `multi_relation` oracle-assisted nominal `weaving_mild` development reaches `62.2%` aggregate success and `0.0%` collision, improving over the previous curriculum-only `27.3%`.
- The fair `single` graph seed-1 control remains at `0.0%` success under the same oracle-assisted route, while `multi_relation` seed 1 reaches `40.0%`.
- The three-seed equal-budget comparison is complete: `multi_relation` reaches `62.2%` success versus `single` `11.1%`, with zero collisions for both.
- Validation-selected/test-evaluated protocol hardening is complete: `multi_relation` reaches `63.3%` success versus `single` `11.1%` on the frozen test split, with zero collisions.
- The `no_graph` oracle-assisted control is complete and fails at `0.0%` success. The nominal `weaving_mild` hierarchy is `no_graph 0.0% < single 11.1% < multi_relation 63.3%`.
- The three-seed no-curriculum diagnostic is complete and does not support claiming topology curriculum as an independent main contribution: validation-selected recovery is `88.9%` for no-curriculum versus `87.8%` for topology curriculum, and fixed-update-60 recovery is `85.6%` versus `87.8%`, both with zero collision.
- The `dropout030_scout_failure` stressor diagnostic keeps the expected method ordering but does not cleanly separate full from single under seed-aware bootstrap. Use it as a scenario-design hint, not a paper table.
- The `dropout030_delay2_scout_failure` accelerated stressor improves the screen but still does not cleanly separate full from single on recovery. It separates tracking and supports the story as supplemental evidence. Stop adding small stressors and move to finish mode.
- The finish-mode consistency audit is recorded in `docs/gate1_finish_mode_consistency_audit.md`.
- The governing staged route is: Gate 1 package closure -> formal `nominal weaving_mild` scenario-depth -> one small realism supplement.
- Stage 2 frozen protocol, smoke, and three-seed run are complete. The run preserves `no_graph < single < multi_relation` but only reaches `42.7%` success for `multi_relation`, so it is diagnostic evidence and should not be expanded to five seeds yet.
- The final decision is one paper only. The paper must center on Gate 1 strict-sensing relay-failure recovery; new experiments are optional supplements, not new project goals.

Completion standard:
- Do not tune further on the `409000` maneuvering-target test split.
- Treat nominal `weaving_mild` as frozen supporting scenario-depth evidence unless a new formal budget is explicitly planned.
- Keep topology curriculum as training support unless a future harder curriculum-specific stressor proves an independent benefit.
- Inspect the main strict-sensing relay-failure evidence package and fix manuscript/document inconsistencies before adding experiments.
- Follow `docs/ACCELERATED_FINISH_PLAN.md`: freeze evidence, package figures/tables, run consistency checks, and avoid new experiments unless a reviewer-critical gap remains.
- Prefer seed-aware statistics, fixed protocol tables, and mechanism figures over adding new environment complexity.
- Do not spend any new five-seed formal budget unless the missing claim cannot be defended from the frozen package.
- Do not modify the frozen `nominal_weaving_mild` validation/test seeds or selection score unless a new protocol revision is explicitly documented before running experiments.
- Do not tune on the `609000` Stage 2 test split.
- Do not expand Stage 2 to five seeds unless a validation-only revision first clears the acceptance gate.
- Do not start full 4v2/5v2, self-play/ELO, online missile/radar, or full JSBSim baseline training for this paper.
- Prioritize manuscript quality, final evidence audit, figure/table polish, PDF compilation, and target-journal preparation.
- Preserve the evaluator fix for pre-failure episode termination; failure-window rates must not be negative.
- Run relevant Gate 1 tests after manuscript/docs or code changes.
- Update docs/PROJECT_STATE.md and docs/ROADMAP.md with the result and next decision.
```
