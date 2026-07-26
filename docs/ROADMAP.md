# Roadmap

## Q1 Target Overlay

Status: Active

The current target is one Q1-level submission attempt with a Q2 fallback path. The controlling final plan is `docs/FINAL_Q1_SINGLE_PAPER_PLAN.md`.

Final single-paper scope is now fixed in `docs/FINAL_Q1_SINGLE_PAPER_PLAN.md`. The project will produce one paper centered on the 3DOF 3v1 strict-sensing relay-failure kill-chain recovery evidence, with controlled Q1 supplements rather than uncontrolled system expansion.

Current execution route:

1. P0 scientific-validity hardening: observation schema, role-identity correctness, actor/critic boundary, and information-boundary tests.
2. P1 unified training protocol: environment-step budgets, validation checkpoint selection, metric schema, and paper configs.
3. P2 development training: MAPPO, Single-Graph, HAPPO, and EA-RG-MAPPO at 1M steps first.
4. P3 formal 3v1 evidence: five seeds, key ablations, parameter-matched baseline, seed-aware statistics.
5. P4 Q1 supplements: mild maneuver target, 4v2/5v2 rule-red extension, and LAG/JSBSim replay.
6. P5 paper package: figures, tables, reproducibility, manuscript, and PDF-ready review.

Do not launch million-step formal training or Q1 supplements before P0 passes.

P0 first pass status:

- role-identity slice bug fixed by exporting the 3DOF observation/node role slices;
- `attack_hold` removed from actor graph edge features;
- `EDGE3D_FEAT_DIM` is now 17;
- P0 tests now include direct actor-logit invariance for global `attack_hold` and unreachable target-cache changes;
- P0 tests and 3DOF smoke passed;
- details are recorded in `docs/p0_scientific_validity_hardening_update.md`.

Remaining P0 work: freeze the P0 environment/config state at commit time, then move to P1 training-protocol standardization.

P1 first pass status:

- `configs/paper/` exists with the main Gate 1 scenario, method, strong-baseline, and ablation configs;
- HAPPO is recorded as a priority Q1 external baseline attempt with a 3-5 engineering-day stop rule;
- `scripts/audit_paper_configs.py` passed and validates the environment-step budget convention.
- `scripts/generate_paper_commands.py` now generates smoke/dev/formal command manifests from `configs/paper/`;
- config-driven smoke training passed for MAPPO, Single-Graph, and EA-RG-MAPPO.
- `dev_1m` command generation now includes validation/test checkpoint sweeps, with test sweeps requiring validation `selected_checkpoints.csv`.
- HAPPO training smoke passed through `scripts/train_happo_baseline.py`; HAPPO validation/test checkpoint-sweep smoke also passed through `scripts/evaluate_happo_checkpoint_sweep.py`.
- `scripts/write_paper_run_provenance.py` now records hashes for paper configs and critical code.
- checkpoint-selection schema is now fixed by `configs/paper/checkpoint_selection_schema.yaml` and audited by `scripts/audit_checkpoint_selection_schema.py`.

Next P1 work: review the generated development-budget commands, then launch MAPPO/Single-Graph/EA-RG-MAPPO/HAPPO `dev_1m` training.

Gate 1 progress:

- Completed first pass: receiver-sender task-support convention, task-support no-bypass, 3DOF intent-context broadcast disabled, and first communication-feasibility tests.
- Completed second pass: scalar delay semantics were replaced with a pending-message queue.
- Packet-dropout and communication-subsystem failure tests now cover the delayed-message queue.
- Target-message caches and one-hop-per-step multi-hop causality tests are now in place.
- Actor-vs-critic observation boundaries are documented.
- One existing multi-relation checkpoint passed a 5-episode post-change compatibility evaluation under the frozen dropout-relay bottleneck settings.
- A tiny seed-0 three-method post-change diagnostic preserved the expected ordering: `no_graph < single < multi_relation`.
- A three-seed checkpoint-reuse post-change diagnostic preserved strong separation between `multi_relation` and `single`.
- A tiny seed-0 post-change retraining smoke confirmed that PPO continuation remains executable.
- A three-seed post-change retraining diagnostic preserved strong separation between `multi_relation` and `single` after 3 continuation PPO updates.
- Completed a 20-update post-Gate-1 retraining diagnostic with validation checkpoint selection and disjoint test episodes. Under strict sensing plus the target-information bottleneck, `multi_relation` recovered `93.3%` versus `single` `33.3%`; seed-aware recovery delta was `+60.0 pp` with 95% CI `[+16.7, +91.7] pp`.
- Completed a 60-update post-Gate-1 retraining diagnostic with validation checkpoint selection and disjoint test episodes. Under strict sensing plus the target-information bottleneck, `multi_relation` recovered `93.3%` versus `single` `43.3%`; seed-aware recovery delta was `+50.0 pp` with 95% CI `[+15.0, +80.0] pp`.
- Gate 2 core five-seed formal result is complete for `dropout030_relay_failure + strict_target_sensing + agent_target_info_bottleneck`: `multi_relation` recovers `96.2%` versus `single` `51.8%` and `no_graph` `34.2%` on a disjoint 1500-episode test set. The result is recorded in `docs/intercept_3d_gate1_dropout030_bottleneck_5seed_formal_summary.md`.
- Failure-aligned mechanism curves and a predefined median-difference representative case are complete under `results/intercept_3d_gate1_dropout030_bottleneck_mechanism_v2/` and documented in `docs/intercept_3d_gate1_dropout030_bottleneck_mechanism_v2/failure_aligned_mechanism_summary.md`.
- Higher-standard Gate 1 review downgraded the completed five-seed result to pre-hardening development evidence. P0-1 actor-localization first pass is complete: actor observation now uses local inbound connectivity, local inbound message age, local target-cache age, and local target-cache confidence instead of team-level aggregate shortcuts; Gate 1 tests now cover this.
- Target-message TTL/confidence freshness is implemented across environment, training, evaluation, protocol, replay, and mechanism-analysis paths. Gate 1 tests now verify stale and low-confidence target caches cannot keep the kill chain valid.
- Step/failure/message timing semantics now use a post-step convention, and post-failure metrics distinguish maintained, recovered-after-loss, and unrecovered outcomes.
- Graph-information hardening now prevents stale global last-detected target state from appearing in the strict-bottleneck graph target node when no agent currently detects the target.
- A hardened 20-update three-method, three-seed development rerun completed under `results/intercept_3d_gate1_hardened_20update_3seed_dev/`. The strict zero-collision validation gate failed for `single` seed `1`; the relaxed diagnostic preserved the expected ordering (`no_graph < single < multi_relation`) but must not be used as final paper evidence.
- A hardened 60-update three-method, three-seed development rerun completed under `results/intercept_3d_gate1_hardened_60update_3seed_dev/`. Strict zero-collision validation selection passed. Disjoint test recovery was `no_graph 0.267 +/- 0.411`, `single 0.613 +/- 0.473`, and `multi_relation 0.853 +/- 0.070`. The remaining blocker for formal promotion is test-time collision inspection and seed-aware statistical reporting.
- Seed-aware statistics and collision-case audit are complete for the hardened 60-update run. `multi_relation` is separated from `no_graph` but not yet from `single`; three collision episodes remain to replay and diagnose.
- Recovery-time reporting was clarified in the evaluator with explicit censored and recovered-only output fields.
- Collision replay is complete for the hardened 60-update run. It found one `multi_relation` blue-blue collision and two `single` blue-target collisions, all during relay failure, with sustained unsafe approach before termination.
- A light proximity safety auxiliary has been implemented and smoke-tested. A three-method, three-seed hardened 60-update safety diagnostic completed under `results/intercept_3d_gate1_hardened_60update_safety_diag/`: recovery was `no_graph 28.0%`, `single 53.3%`, and `multi_relation 86.7%`; `multi_relation` had zero test collisions. The result supports the safety-enabled route versus `no_graph`, but `multi_relation - single` still needs five-seed confirmation or a stronger frozen safety protocol because the three-seed CI touches zero.
- Minimum-distance metrics have been added to the 3DOF evaluator and checkpoint sweep. The safety diagnostic was re-evaluated without retraining under `results/intercept_3d_gate1_hardened_60update_safety_diag_min_distance_eval/`; `multi_relation` kept zero collisions with mean episode-min distances of `3290.2 m` blue-red and `2334.4 m` blue-blue.
- A five-seed safety-enabled hardened formal candidate completed all training runs under `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/`. It uses the post-Gate-1 60-update checkpoints as a uniform five-seed source and applies 60 additional safety-continuation updates.
- Full validation checkpoint selection for the five-seed safety candidate repeatedly stalled, so a fixed-update-60 test diagnostic was completed as the practical route.
- `scripts/merge_checkpoint_sweep_shards.py` now supports merging validation/test shards and regenerating selected-checkpoint CSVs.
- Batched episode evaluation is now available through `--eval-batch-size` in the policy evaluator and checkpoint sweep.
- The fixed-update-60 five-seed safety diagnostic is recorded in `docs/intercept_3d_gate1_hardened_safety_5seed_fixed_update60_summary.md`: recovery is `no_graph=21.8%`, `single=53.2%`, and `multi_relation=88.6%`; `multi_relation` has zero collisions; seed-aware `multi_relation - single` recovery delta is `+35.4 pp` with 95% CI `[+1.2, +73.0] pp`.
- Fixed-protocol mechanism evidence is complete under `results/gate1_safety_fx60_mechanism/` and documented in `docs/gate1_safety_fx60_mechanism/failure_aligned_mechanism_summary.md`.
- The fixed-protocol `no_task_support` ablation is complete and documented in `docs/intercept_3d_gate1_hardened_safety_no_task_support_5seed_fixed_update60_summary.md`. Recovery drops from `88.6%` to `64.8%`, but the seed-aware CI crosses zero, so it is supportive rather than decisive mechanism evidence.
- The fixed-protocol `no_role_pair_gate` ablation is complete and documented in `docs/intercept_3d_gate1_hardened_safety_no_role_pair_gate_5seed_fixed_update60_summary.md`. Recovery drops from `88.6%` to `64.8%`, and the seed-aware recovery CI `[+2.8, +59.2] pp` separates in favor of the full method.
- Paper-facing result tables are complete in `docs/gate1_safety_fx60_paper_tables.md` and `results/gate1_safety_fx60_paper_tables/`.
- The three-seed `no_curriculum` diagnostic is complete and does not support claiming topology curriculum as an independent main contribution. Keep curriculum as training support.
- A paper-facing fixed-update-60 experiment-section draft is complete in `docs/gate1_safety_fx60_experiment_section_draft.md`.
- The fixed-update-60 experiment section and abstract are integrated into the 3D English manuscript path under `paper_latex_3d_en/`.
- The active manuscript consistency audit is recorded in `docs/gate1_safety_fx60_manuscript_consistency_audit.md`.
- Contribution-to-evidence alignment is recorded in `docs/gate1_safety_fx60_contribution_evidence_alignment.md`.
- Method-component audit is recorded in `docs/gate1_safety_fx60_method_component_audit.md`; problem metrics and method equations have been added to the active manuscript.
- External project-content review accepted the current direction but raised several hardening requirements before Q1-scale claims: critic/reward consistency, true role-removal ablation, parameter-matched strong graph baselines, explicit masked-global-graph wording, and documentation cleanup.
- Critic/reward consistency first pass is complete: the centralized critic now conditions on each blue agent's role one-hot while keeping the decentralized actor boundary unchanged. Audit: `docs/critic_role_conditioning_audit.md`.
- True `no_role_identity` implementation hardening is complete: the actor now removes explicit role labels from local observation fields, graph node fields, role embeddings, and role-pair message inputs while preserving physical capability heterogeneity. Audit: `docs/true_no_role_identity_ablation_audit.md`.
- A small post-hardening `no_role_identity` diagnostic is complete in `docs/true_no_role_identity_post_hardening_diag10_summary.md`. It shows clear degradation under hardened no-role inference, but the no-role checkpoints were trained before hardening, so this is not manuscript-level evidence.
- Parameter-matched single-graph baseline planning is complete in `docs/parameter_matched_single_graph_baseline_plan.md`. The target capacity-control baseline is `graph_encoder=single, hidden_dim=240`, with `394913` total parameters versus full EA-RG-MAPPO-S at `390385`.
- Seed-0 parameter-matched single-graph development is complete in `docs/parameter_matched_single_graph_seed0_dev_summary.md`. It confirms the capacity-control baseline is runnable and remains far below the full method on the small matched strict bottleneck test split.
- Three-seed parameter-matched single-graph development is complete in `docs/parameter_matched_single_graph_3seed_dev_summary.md`. Full multi-relation remains far above parameter-matched single-graph on the small strict bottleneck diagnostic, but the result is not yet formal because the strict-stage budget and test episode count are still development-level.
- A fairer three-seed parameter-matched single-graph update-60 development extension is complete in `docs/parameter_matched_single_graph_update60_dev_summary.md`. The capacity-control baseline improves compared with the ten-update diagnostic, but full multi-relation still recovers `88.3%` versus parameter-matched single-graph `18.3%` on the same small matched test split.
- A five-seed parameter-matched single-graph test50 formal candidate is complete in `docs/parameter_matched_single_graph_5seed_test50_candidate_summary.md`. Full multi-relation recovers `89.2%` versus parameter-matched single-graph `33.2%`; the single-graph baseline is high-variance across seeds.
- Seed-aware hierarchical bootstrap is complete for the five-seed capacity-control candidate. Recovery delta is `+56.0 pp` with 95% CI `[+11.2, +98.8] pp`, supporting use as a parameter-count credibility result while still requiring seed-level scatter reporting.
- The capacity-control result is integrated into the paper table package as a separate supplemental table and delta table.
- Hardened true `no_role_identity` staged-source training is enabled by passing `--graph-input-ablation` through the fair staged source protocol.
- Hardened true `no_role_identity` three-seed dev20 rerun is complete in `docs/true_no_role_identity_hardened_3seed_dev20_summary.md`. It shows a large recovery drop (`20.0%` versus full same-split `93.3%`) and supports formalization if role identity is kept as a main mechanism claim.
- Evaluation metrics now handle pre-failure episode termination without negative failure-window rates.
- Hardened true `no_role_identity` five-seed formal test50 candidate is complete in `docs/true_no_role_identity_hardened_5seed_formal_test50_summary.md`. Full multi-relation recovers `87.2%` versus no-role `56.8%`; the seed-aware recovery delta is `+30.4 pp` with 95% CI `[+7.2, +64.4] pp`.
- The hardened role-identity formal result is integrated into the paper table package as a standalone mechanism table and delta table.
- First fixed-checkpoint `weaving_mild` scenario-depth diagnostic is complete in `docs/gate1_safety_fx60_weaving_mild_fixed_checkpoint_diag20_summary.md`. Zero-shot transfer is too hard for the current straight-trained checkpoints; full recovery is only `11.0%`.
- Finish-mode next item: return to Gate 1 manuscript packaging under the final single-paper scope. Treat Stage 2 `nominal weaving_mild` as diagnostic unless a separate validation-only revision later passes its gate.

## Milestone 1: Preserve 2D Evidence Chain

Status: Done

- Maintain 2D pursuit results, checkpoints, figures, tables, and audits.
- Keep the reproducibility gate passing.
- Use 2D experiments as prototype, ablation, and appendix evidence.

## Milestone 2: Build 3DOF Interception Environment

Status: Done

Done:

- Add `envs/uav_intercept_3d_env.py`.
- Add `scripts/smoke_test_intercept_3d_env.py`.
- Validate 3v1 heterogeneous interception interface and graph observations.

The environment selection, training smoke tests, and maintained 3DOF evaluation CSVs are complete.

## Milestone 3: 3DOF Main Learning Results

Status: In progress

- Completed matched 3DOF straight-target baseline protocol: geometric controller, from-scratch RI-GMAPPO, BC-only RI-GMAPPO, and BC-to-PPO RI-GMAPPO across three replicates.
- Implement perception, communication, and task-support relations for EA-RG-MAPPO-S in 3DOF 3v1.
- Add MAPPO/GAT-MAPPO/EA-RG-MAPPO baselines.
- Report task success, chain closure, attack-window formation, tracking, communication connectivity, message age, collision, and constraint violations.

## Milestone 4: Ablation and Robustness

Status: In progress

Done:

- Add 3DOF communication range scaling, dropout, delay, radar dropout, and temporary communication-node failure controls.
- Add zero-shot robustness screening for existing single-graph and multi-relation checkpoints.
- Add matched topology-curriculum fine-tuning protocol and complete an initial three-seed 20-update pilot.
- Add random temporary blue-node communication failure curriculum hooks.
- Complete formal relay/scout node-failure evaluation and selected robustness evaluation.
- Add paired bootstrap summaries, paper-facing 3DOF main table, and relay-failure case candidates.
- Add relay-failure per-step replay data and timeline/trajectory case figure.
- Add and smoke-test `no_task_support` graph-relation ablation, then run a seed-0 diagnostic pilot.
- Complete formal three-seed `no_task_support` task-support ablation for relay/scout failure.
- Complete formal three-seed scale-matched `no_role_pair_gate` message ablation for relay/scout failure.
- Add and smoke-test `no_edge_features` graph-input ablation through training, evaluation, and protocol entry points.
- Complete seed-0 `no_edge_features` diagnostic and decide not to promote it because the signal is weak.
- Add `no_role_identity`, complete seed-0 diagnostic, then complete formal three-seed relay/scout evaluation; keep it as auxiliary because the formal result is mixed.
- Add `break_turn` and `weaving` target policies, then complete a zero-shot break-turn relay/scout node-failure pilot.
- Add `weaving_mild`, complete maneuvering-target pilots, and decide not to promote them until staged maneuvering curriculum improves absolute success.
- Complete the compact straight-target node-failure baseline table with oracle geometric pursuit, single-graph MAPPO, and EA-RG-MAPPO-S.
- Add opt-in strict intermittent sensing for local observations, shared observations, and graph target state; complete smoke validation and a small zero-shot relay/scout node-failure screen.
- Complete a three-seed 10-update strict-sensing topology-curriculum pilot and 30-episode relay/scout node-failure evaluation. Relay failure shows separated multi-relation recovery improvement; scout failure remains a trend.
- Integrate the strict-sensing relay/scout pilot into the paper-facing 3DOF evidence table as a budget-labeled scenario-depth section.
- Add a formal strict-sensing protocol with 120-update checkpoint snapshots, fixed validation/test splits, validation-based checkpoint selection, and a smoke-validated end-to-end command path.
- Complete a three-seed strict-sensing relay-failure development run. Validation-selected multi-relation checkpoints reached 100% recovery on all three test seeds, while single-graph averaged 92.7% recovery and also solved one selected seed.
- Complete seed-aware hierarchical bootstrap statistics for the strict-sensing relay-failure development run. The result supports a recovery-probability and timeout-reduction claim, while recovery speed should be reported as restricted mean recovery time rather than recovered-only speed.
- Add `no_graph` MAPPO-style actor support and smoke-validate a fair strict-sensing baseline protocol for `no_graph`, `single`, and `multi_relation` using the same BC, topology curriculum, validation selection, and disjoint test structure.
- Complete a two-seed tiny fair-baseline development run. It validated the end-to-end protocol but did not produce usable validation recovery because the BC/PPO budget was intentionally very small.
- Complete a seed-0 BC-strength diagnostic for `single` and `multi_relation`. BC accuracy improved, but relay-failure validation recovery stayed at zero, indicating that fair baselines should follow the staged source-checkpoint path rather than jumping directly from nominal BC into strict relay-failure.
- Add and smoke-validate `scripts/run_3d_fair_staged_source_protocol.py`. The smoke run produced BC, nominal, topology/node-failure curriculum, and strict-sensing checkpoint-sweep outputs for `no_graph`, `single`, and `multi_relation`.
- Complete a seed-0 staged source development run and a 20-update nominal source budget diagnostic. Both showed zero nominal success, so strict-sensing fair baseline work must start from a known-learnable source budget or existing successful source checkpoints.
- Inventory fair source checkpoints and confirm that `single` / `multi_relation` source checkpoints exist for seeds `0, 1, 2`, while `no_graph` sources are missing.
- Train `no_graph` seed-0 source with a known-learnable budget and run a mixed-source strict-sensing diagnostic. The diagnostic restored nonzero recovery and showed the expected ordering signal: `multi_relation` and `single` strong, `no_graph` weaker.
- Train missing `no_graph` source checkpoints for seeds `1` and `2`, then complete the first three-seed strict-sensing fair diagnostic with `no_graph`, `single`, and `multi_relation` under shared validation selection and disjoint test episodes. Test recovery was `40.0%`, `93.3%`, and `100.0%`, respectively. Treat this as a development-budget result, not a final paper table.
- Generate seed-aware hierarchical bootstrap reports for the strict-sensing fair diagnostic. The result clearly separates `multi_relation` from `no_graph`, but only weakly separates `multi_relation` from `single`, so the paper claim should emphasize recovery robustness and graph-structure necessity rather than recovered-only speed.
- Audit `no_graph` source checkpoint quality with 50-episode nominal and strict relay-failure evaluations. Seed 2 is genuinely weak, so formal comparisons must avoid selective seed replacement.
- Add a formal source policy for fair baselines. The next 30-update development diagnostic keeps all current `no_graph` seeds; any formal replacement must retrain all `no_graph` sources under a fixed budget before final test evaluation.
- Complete a 30-update strict-sensing fair checkpoint-budget diagnostic. It preserves the strong `multi_relation` vs `no_graph` separation, but `single` remains close to `multi_relation`; therefore the current straight relay-failure setup is useful for graph-structure necessity, not yet sufficient for a strong multi-relation-vs-single claim.
- Probe harder variants with the selected 30-update checkpoints. `weaving_mild` is too hard, `range0.75` is still saturated for graph methods, and `radar_dropout0.10` does not favor multi-relation over single. Do not promote these probes as paper main results.
- Identify `communication_dropout0.30 + relay_failure + strict_target_sensing` as the strongest next scenario candidate. In a checkpoint-only probe, `multi_relation` reached `98.3%` recovery, `single` `76.7%`, and `no_graph` `28.3%`, with seed-aware `multi_relation - single` recovery delta `+21.7 pp` and 95% CI `[+3.3, +41.7] pp`.
- Add the `dropout030_relay_failure` scenario to the shared evaluation scenario registry and smoke-test it through checkpoint sweep.
- Complete a first dropout-relay formal development diagnostic with validation selection on dropout-relay episodes. The result still separates `multi_relation` from `no_graph`, but no longer clearly separates `multi_relation` from `single`; therefore it is not ready for five-seed formal reporting.
- Complete a 60-update dropout-relay diagnostic for `single` and `multi_relation`. It modestly improves the recovery delta to `+8.3 pp`, but the seed-aware interval still crosses zero, so longer training alone has not solved the evidence gap.
- Add an opt-in agent target-information bottleneck and complete a checkpoint-only probe. The probe gives the strongest current `multi_relation` vs `single` separation: `+16.7 pp` recovery with 95% CI `[+3.3, +33.3] pp`.
- Complete bottleneck-enabled validation selection and disjoint testing. The result remains separated: `multi_relation` recovery `95.0%`, `single` `78.3%`, seed-aware delta `+16.7 pp` with 95% CI `[+6.7, +28.3] pp`.
- Add `no_graph` to the same bottleneck-enabled protocol. The three-method ordering is now clear on the development diagnostic: `no_graph 25.0% < single 78.3% < multi_relation 95.0%`.
- Freeze the bottleneck-enabled dropout-relay protocol in `docs/bottleneck_dropout030_relay_frozen_protocol.md` before any five-seed expansion.
- Complete a 20-update post-Gate-1 communication-feasible retraining diagnostic for `single` and `multi_relation`. Validation-selected test recovery is `33.3%` for `single` and `93.3%` for `multi_relation`; seed-aware recovery delta is `+60.0 pp` with 95% CI `[+16.7, +91.7] pp`. This supports longer post-Gate-1 training, but it is not final paper evidence.
- Complete a 60-update post-Gate-1 communication-feasible retraining diagnostic for `single` and `multi_relation`. Validation-selected test recovery is `43.3%` for `single` and `93.3%` for `multi_relation`; seed-aware recovery delta is `+50.0 pp` with 95% CI `[+15.0, +80.0] pp`. The protocol remains stable enough to plan formal expansion, but collision handling must be fixed before final reporting.
- Add `--max-selection-collision-rate` to checkpoint sweep so formal validation can reject unsafe checkpoints before final testing. A smoke checkpoint sweep passed with `--max-selection-collision-rate 0.0`.
- Forward `--max-selection-collision-rate` through the formal strict-sensing protocol script and validate it with a one-update formal-protocol smoke.
- Complete a post-Gate-1 three-method safety-selected diagnostic for `no_graph`, `single`, and `multi_relation`. Recovery ordering is `no_graph 31.7% < single 38.3% < multi_relation 98.3%`; seed-aware `multi_relation - single` recovery delta is `+60.0 pp` with 95% CI `[+26.7, +86.7] pp`.
- Add the five-seed launch plan in `docs/post_gate1_five_seed_launch_plan.md` and identify missing seed `3` / `4` source checkpoints as the current blocker.
- Generate seed `3` and `4` staged sources plus post-Gate-1 60-update snapshots for `no_graph`, `single`, and `multi_relation`; record the inventory in `docs/post_gate1_seed34_source_generation_summary.md`.
- Complete a five-seed checkpoint-sweep integration diagnostic with small validation/test budgets. The evaluation chain passed and kept the expected ordering: `no_graph 26.0% < single 46.0% < multi_relation 94.0%` recovery.
- Complete the five-seed formal checkpoint sweep and disjoint final test for the frozen bottleneck dropout-relay protocol. Test recovery is `no_graph 34.2% < single 51.8% < multi_relation 96.2%`; seed-aware hierarchical bootstrap gives `multi_relation - single = +44.4 pp` with 95% CI `[+16.2, +74.4] pp` and `multi_relation - no_graph = +62.0 pp` with 95% CI `[+27.8, +95.2] pp`.

Next:

- Treat the fixed-update-60 safety-enabled result as the current practical formal candidate unless a new protocol is explicitly recorded before any new test evaluation.
- Paper-facing table documentation is now reproducible: `scripts/build_gate1_safety_fx60_paper_tables.py` regenerates the timing-generalization section and artifact links in `docs/gate1_safety_fx60_paper_tables.md`.
- Submission readiness reporting has been migrated to the active 3DOF Gate 1 package. `docs/submission_readiness_report.md` now states the 3DOF strict-sensing relay-failure recovery claim rather than the obsolete 2D claim.
- Compile the active English manuscript when a LaTeX compiler is available, then check PDF table widths, figure placement, captions, and bibliography rendering.
- Static PDF-readiness audit is complete in `docs/gate1_safety_fx60_pdf_readiness_audit.md`; all five paper-facing tables now have page-width resize protection. Full visual inspection still requires a LaTeX compiler.
- Polish the fixed-update-60 mechanism figures and captions from the compiled PDF perspective once PDF rendering is available.
- Parameter-count, inference-time, and communication-load reporting now exists in `docs/gate1_safety_fx60_model_cost_report.md` and is integrated as a compact experiment subsection.
- A seed-0 no-curriculum fixed full-difficulty diagnostic is complete and recorded in `docs/gate1_safety_fx60_no_curriculum_seed0_dev60_summary.md`. It did not show a curriculum advantage on the matched 30-episode diagnostic, so topology curriculum must remain a training protocol rather than a main contribution unless stronger multi-seed evidence reverses this.
- The three-seed no-curriculum development comparison is complete and recorded in `docs/gate1_safety_fx60_no_curriculum_3seed_dev60_summary.md`. Validation-selected recovery is tied within development noise (`88.9%` no-curriculum versus `87.8%` topology curriculum), and fixed-update-60 only slightly favors curriculum (`85.6%` versus `87.8%`). Decision: do not spend five-seed formal compute on no-curriculum now, and keep curriculum out of the primary contribution list.
- Seed-level mechanism figures are complete under `results/gate1_safety_fx60_seed_mechanism/` and documented in `docs/gate1_safety_fx60_seed_mechanism_summary.md`. These figures package the frozen fixed-update-60 evidence as seed scatter, paired mechanism-ablation deltas, and seed-aware bootstrap intervals.
- A small opt-in graph-relation stressor, `dropout030_scout_failure`, is registered and screened in `docs/gate1_safety_fx60_dropout030_scout_failure_diag20_summary.md`. It keeps the expected ordering (`no_graph 24.0% < single 51.0% < multi_relation 76.0%`) but does not cleanly separate full from single under seed-aware bootstrap, so it is a scenario-design hint rather than paper evidence.
- The accelerated delayed scout-failure stressor, `dropout030_delay2_scout_failure`, is screened in `docs/gate1_safety_fx60_dropout030_delay2_scout_failure_diag20_summary.md`. It improves the screen (`no_graph 37.0% < single 56.0% < multi_relation 85.0%`) and separates full from single on tracking, but recovery CI still crosses zero. Decision: stop adding small stressors and move to finish mode.

Finish-mode boundary:

- Freeze the current evidence package.
- Do not add more scenario variants unless tied to a specific reviewer-critical gap.
- Prioritize manuscript consistency, figure/table packaging, reproducibility, and final claim discipline.
- If using validation selection, finish the per-seed validation shards and merge them with `scripts/merge_checkpoint_sweep_shards.py`, then run the selected-checkpoint test split from the merged validation CSV.
- Fixed-checkpoint early-vs-nominal failure-timing generalization is complete, recorded in `docs/gate1_safety_fx60_failure_timing_generalization_formal_evidence.md`, and integrated into the active experiment section. Early relay failure is valid and discriminative; delayed/late failure remains deferred because pre-window episode termination makes failure-window metrics invalid.
- Keep `scout_failure` as supporting evidence unless a later formal run separates it; do not let it distract from relay-failure recovery.
- Scenario-depth diagnostics show that fixed straight-target checkpoints transfer poorly to `weaving_mild`, and direct strict relay-failure weaving fine-tuning remains at zero recovery. Nominal weaving is weakly feasible for `multi_relation` but not for `single`. The next scenario-depth route is staged weaving curriculum: nominal weaving first, strict sensing second, relay failure third.
- Stage 1 nominal weaving fine-tuning from correctly matched `hidden_dim=64` straight-target checkpoints improves `multi_relation` to `26.7%` success versus `single` at `0.0%`, but this is below the acceptance gate for Stage 2. Continue Stage 1 with longer checkpoint-compatible fine-tuning before adding strict sensing or relay failure.
- The 60-update `weaving_mild` Stage 1 extension did not improve the aggregate result (`24.7%` success, seed 1 still `0.0%`). A new opt-in `weaving_tiny` curriculum entry improves the entry difficulty slightly but still leaves seed 1 at zero. The next route is a target-policy curriculum and/or maneuver-aware reward shaping, not more direct `weaving_mild` updates.
- `scripts/run_3d_target_policy_curriculum.py` now provides the target-policy curriculum route and has passed a two-stage smoke. Next run: a small `multi_relation` three-seed diagnostic with `weaving_tiny -> weaving_mild` before considering any strict-sensing maneuvering-target experiment.
- The three-seed `weaving_tiny -> weaving_mild` diagnostic completed but remained weak (`27.3%` success, seed 1 `0.0%`). Opt-in attack-geometry shaping also failed to unstick seed 1.
- Maneuvering-target reachability analysis shows that seed 1 can reduce range similarly to other seeds but cannot convert approach into attack geometry: no attack-window episodes and no geometry score above `0.25`. The next maneuvering-target step is a deterministic geometric-oracle reachability check, not larger formal PPO training.
- Geometric-oracle reachability is complete. Lead/offset geometric policies solve matched nominal `weaving_mild` evaluations with `100%` success and `0%` collision, while direct pursuit is less safe (`66.7%` success, `36.7%` collision). This confirms scenario feasibility. Next: use oracle traces for BC warm start or auxiliary imitation in Stage 1 maneuvering-target training, then compare against the current curriculum-only baseline.
- Oracle-BC support is now available in the existing 3DOF BC script. Seed-1 attacker-weighted offset BC produces the first nonzero learned-policy signal on nominal `weaving_mild` (`3.3%` success, zero collision), but pure BC remains far below the acceptance gate. Next: run a short PPO fine-tune from this oracle-BC checkpoint before expanding to three seeds.
- Seed-1 oracle-BC + PPO dev10 improved the nominal `weaving_mild` learned-policy signal to `13.3%` success with zero collision. This is not yet enough for scenario-depth reporting, but it validates oracle-assisted training as the right next development route. Continue only seed 1 for 20-40 updates with checkpoint evaluation before spending three-seed budget.
- Seed-1 oracle-BC + PPO continuation reached `40.0%` success and `0.0%` collision on matched nominal `weaving_mild` test episodes. This clears the seed-1 development threshold. Next: repeat the same oracle-assisted protocol for seeds 0 and 2, then compare the three-seed aggregate against the curriculum-only `27.3%` baseline.
- Three-seed oracle-assisted nominal `weaving_mild` development reached `62.2%` success and zero collision, versus the previous curriculum-only `27.3%`. This passes the maneuvering-target Stage 1 development gate. Next: run fair oracle-assisted `single` graph controls before promoting this route toward paper-facing evidence.
- The first fair `single` graph control is complete for seed 1. Under the same oracle-assisted route, `single` stays at `0.0%` while `multi_relation` reaches `40.0%`. Next: run `single` controls for seeds 0 and 2 to establish a three-seed fairness comparison.
- The three-seed oracle-assisted `multi_relation` versus `single` comparison is complete. `multi_relation` reaches `62.2%` success versus `single` `11.1%`, both with zero collision. This is strong development evidence for maneuvering-target scenario depth. Next: harden validation/test protocol before treating it as paper-facing evidence.
- Validation-selected nominal `weaving_mild` protocol hardening is complete. Frozen validation-selected checkpoints reach `63.3%` success for `multi_relation`, `11.1%` for `single`, and `0.0%` for `no_graph` on the development test split, all with zero collision. The formal protocol is now frozen in `docs/nominal_weaving_mild_frozen_protocol.md`, and the orchestration smoke passed in `docs/nominal_weaving_mild_formal_protocol_smoke_summary.md`.
- The frozen Stage 2 three-seed run with a new `609000` test split is complete in `docs/nominal_weaving_mild_formal_protocol_3seed_summary.md`. It preserves the method hierarchy but does not reach the paper-facing success gate, so it remains diagnostic scenario-depth evidence.
- The `no_graph` oracle-assisted control is complete and fails at `0.0%` success under the same validation-selected protocol. The maneuvering-target method hierarchy is now `no_graph 0.0% < single 11.1% < multi_relation 63.3%`. Freeze this branch as supporting scenario-depth evidence and return to the main strict-sensing relay-failure package.

## Milestone 5: 4v2 Enhancement

Status: Planned

- Add interceptor UAV and rule-based escort.
- Use 4v2 as an enhancement experiment after 3v1 is trainable.
- Keep red-blue self-play and ELO optional.

## Milestone 6: LAG/JSBSim Replay

Status: Deferred

- Use final policies for replay and feasibility checks only.
- Do not train all baselines in JSBSim for the first Q2-targeted paper.
