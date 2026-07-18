# Roadmap

## Q1 Target Overlay

Status: Active

The current target is a Q1-level submission attempt with a Q2 fallback path. The governing plan is `docs/Q1_EXECUTION_PLAN.md`.

Execution order:

- Gate 1: information realism and communication-feasibility tests;
- Gate 2: five-seed 3v1 mechanism evidence;
- Gate 3: strong baseline and method hardening;
- Gate 4: 5v2 rule-jammer main scenario family;
- Gate 5: formal Q1-scale experiments and OOD tests;
- Gate 6: LAG/JSBSim 6DOF replay validation.

Do not start 5v2 formal training before Gate 1 passes.

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
- Next item: convert the result into paper-grade evidence by adding five-seed mechanism ablations and baseline fairness diagnostics.

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

- Run five-seed ablations for `no_task_support` and `no_role_pair_gate` under the same frozen validation/test protocol.
- Report parameter counts, inference time, communication load, and seed-level scatter for baseline credibility.
- Add one controlled scenario-depth extension only after mechanism ablations and fairness diagnostics are finished.
- Keep `scout_failure` as supporting evidence unless a later formal run separates it; do not let it distract from relay-failure recovery.
- Remove role information.
- Remove edge features.
- Remove multi-relation edge indicators.
- Train and ablate staged topology curriculum.
- Test unseen communication radius, dropout, delay, radar perturbation, node failure, target maneuver changes, and strict intermittent sensing.

## Milestone 5: 4v2 Enhancement

Status: Planned

- Add interceptor UAV and rule-based escort.
- Use 4v2 as an enhancement experiment after 3v1 is trainable.
- Keep red-blue self-play and ELO optional.

## Milestone 6: LAG/JSBSim Replay

Status: Deferred

- Use final policies for replay and feasibility checks only.
- Do not train all baselines in JSBSim for the first Q2-targeted paper.
