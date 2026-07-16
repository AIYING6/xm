# Current Project State

Last updated: 2026-07-16

## Current Milestone

Upgrade the project from a 2D limited-communication pursuit prototype to a 3DOF heterogeneous UAV cooperative interception platform suitable for stronger Q2-level experiments.

## Stable Research Direction

`EA-RG-MAPPO-S` is the main method:

- edge-aware role graph policy;
- limited-communication graph attention;
- staged random-radius / topology curriculum training.

Current safe paper claim:

> EA-RG-MAPPO-S improves limited-communication cooperative pursuit stability and reduces collision in the existing simplified 2D heterogeneous UAV setting.

Target next-stage claim:

> Multi-relation edge-aware role graph learning improves 3DOF heterogeneous UAV cooperative interception under intermittent sensing and limited communication.

## Completed

- 2D heterogeneous UAV pursuit environment and MAPPO/GAT-MAPPO/EA-RG-MAPPO-S training/evaluation chain.
- Final 2D main evaluation with 3 seeds and 300 evaluation episodes per seed.
- Communication dropout, radius interpolation, speed robustness, and edge-feature diagnostic evaluations.
- Chinese/English manuscript drafts, LaTeX projects, figures, tables, and evidence audits.
- Reproducibility checksum manifest and checksum verification.
- LAG-like role graph adapter/wrapper tests for future 6DOF migration.
- First 3DOF 3v1 heterogeneous interception environment smoke test.
- Maintained 3DOF EA-RG-MAPPO-S checkpoint evaluation script and diagnostic CSV schema.
- First non-smoke 3DOF learnability diagnostic under a straight-target curriculum.
- Low-level altitude and horizontal-boundary flight-envelope protection in the 3DOF environment.
- Geometric-demonstration behavior-cloning warm start and BC-to-PPO fine-tuning path.
- Matched three-replicate 3DOF straight-target baseline protocol with 360 independently evaluated episodes.
- Perception, communication, and dynamic task-support relation adjacencies in the 3DOF graph observation.
- Role-pair-conditioned multi-relation graph encoder with a union-graph residual path.
- Matched three-seed single-graph vs multi-relation BC-to-PPO straight-target comparison.
- Stage-configurable 3DOF communication range scaling, dropout, delay, radar dropout, and temporary communication-node failure.
- Zero-shot topology robustness screening script for existing 3DOF checkpoints.
- Episode-level 3DOF topology domain randomization hooks for range scale, communication dropout, message delay, and radar dropout during PPO training.
- Matched topology-curriculum protocol script for continuing nominal checkpoints under randomized communication topology and evaluating the same robustness suite.
- Random temporary blue-node communication failure curriculum hooks for PPO training.
- Paper-facing 3DOF robustness main table for the current evidence triage.
- Relay-failure matched episode candidate list for later trajectory/timeline case visualization.
- Relay-failure per-step replay CSV, qualitative summary, and timeline/trajectory figure for the top matched case.
- `no_task_support` graph-relation ablation switch across 3DOF environment, BC pretraining, PPO training, robustness evaluation, and replay.
- Seed-0 diagnostic task-support ablation pilot comparing full multi-relation against no-task-support under relay/scout failure.
- Formal three-seed `no_task_support` task-support ablation under relay/scout node-failure evaluation.
- Formal three-seed scale-matched `no_role_pair_gate` message ablation under relay/scout node-failure evaluation.
- `graph_input_ablation=no_edge_features` switch across 3DOF training, BC pretraining, policy evaluation, topology robustness evaluation, and baseline/topology protocols; compile, 3DOF smoke, one-update training smoke, evaluation smoke, and the full lightweight build gate passed.
- Seed-0 `no_edge_features` diagnostic through BC-to-PPO baseline, node-failure topology curriculum, relay/scout robustness evaluation, and paired diagnostic analysis.
- `graph_input_ablation=no_role_identity` switch across 3DOF training/evaluation paths, with smoke validation, seed-0 diagnostic, and formal three-seed relay/scout node-failure evaluation.
- `target_policy=break_turn` and `target_policy=weaving` maneuvering target policies in the 3DOF environment, including red-side altitude and boundary protection.
- Zero-shot break-turn node-failure scenario-depth pilot using existing straight-target topology-curriculum checkpoints.
- `target_policy=weaving_mild` reduced-amplitude maneuvering target policy and maneuvering-target pilot summary.
- Oracle geometric node-failure diagnostic and compact straight-target node-failure baseline table comparing oracle geometric pursuit, single-graph MAPPO, and EA-RG-MAPPO-S.
- Opt-in strict intermittent-sensing switch for the 3DOF environment, plus a strict-sensing smoke test and a small relay/scout node-failure screening evaluation.

## In Progress

- Consolidate strict-sensing curriculum evidence. A 10-update three-seed strict-sensing pilot restored a strong relay-failure multi-relation advantage; decide whether to integrate it as a paper-facing scenario-depth table or rerun with a longer strict-sensing fine-tuning budget.

## Known Issues

- The 3DOF environment and training chain are executable, but the current 3DOF evidence is still a straight-target curriculum baseline.
- The learned 3DOF policy has not yet been compared with R-MAPPO, GAT-MAPPO, or EA-RG-MAPPO under matched seeds and budgets.
- The current 3DOF baseline only uses a straight high-value target and nominal communication during training.
- The straight-target node-failure protocol is not hard enough to separate an oracle geometric demonstrator from learned policies; it is useful for recovery timing and mechanism ablations, not as a complete Q2-level scenario by itself.
- The current 3DOF observation uses a target estimate that falls back to true target position when no target has been detected, so a stricter intermittent-sensing setting is needed before claiming realistic partial observability.
- Strict sensing is now implemented as an opt-in switch, but existing checkpoints were not trained for it. A small screening run shows a reversal against multi-relation, so strict-sensing evidence must be generated through a matched curriculum rather than zero-shot evaluation.
- Under nominal straight-target training, the multi-relation and single-graph success intervals overlap; no nominal-condition superiority claim is supported.
- Zero-shot topology robustness screening is small-sample and currently does not support a multi-relation robustness claim; matched topology-curriculum retraining is required.
- LAG/JSBSim is currently interface-level only; no real JSBSim reset/step evaluation has passed.
- Intent prediction diagnostics are weak and must not be used as a main contribution.
- Full 4v2 red-blue self-play, ELO, missile online simulation, and human-UAV teaming are out of scope for the immediate paper.

## Current Maintained Gate

Latest full lightweight build passed with:

```text
required files checked: 144
required scripts checked: 50
checksum rows: 184
schema audit rows: 32
provenance audit rows: 56
```

## Repository State

- Local Git repository initialized on branch `main`.
- GitHub remote configured as `origin = https://github.com/AIYING6/xm.git`.
- Initial local commit: `7a037f3 chore: initialize UAV research project`.
- Latest manuscript skeleton commit before proxy-push workflow update: `4aab7a8 docs: draft 3d manuscript skeleton`.
- Heavy model checkpoints (`*.pt`, `*.pth`, `*.ckpt`, `*.onnx`) are ignored by `.gitignore`; the local Git object store is about 3.15 MiB after the initial commit.
- Push from this Codex environment should use the local proxy: `HTTPS_PROXY=http://127.0.0.1:7897 git push -u origin main`.

## Latest Integration Check

- `train_ri_gmappo.py` now supports `--env-name 2d_pursuit` (default) and `--env-name 3d_intercept`.
- The role embedding size is inferred from the selected environment graph, so the 3DOF target role is supported.
- The 3DOF graph supplies a neutral placeholder for the legacy intent context but marks it unsupervised; no intent auxiliary loss is applied.
- One-update smoke runs completed for both 2D and 3DOF and wrote logs plus latest/best checkpoints under `results/ri_gmappo_2d_smoke/` and `results/ri_gmappo_3d_smoke/`.
- `scripts/evaluate_ri_gmappo_3d.py` evaluates saved 3DOF checkpoints and writes task-chain metrics to `results/intercept_3d_policy_eval.csv`.
- A from-scratch 30-update PPO diagnostic failed through low-altitude constraint termination. Flight-envelope protection removes this invalid failure mode: the same policy then times out rather than violating constraints.
- The geometric 3DOF controller solves 0.8 of five smoke episodes, so the environment is task-solvable. Under the straight-target curriculum, an 80-epoch unweighted behavior-cloning warm start reaches 0.70 success over 20 independent evaluation episodes; a 60-update PPO fine-tune reaches 0.967 success over 30 independent episodes, with zero collisions and zero constraint violations.
- A 20-episode light-stress check (0.15 communication dropout, two-step delay, 0.1 radar dropout) did not fail, but the sample is too small and the policy was not trained with topology randomization. Treat this only as an integration check.
- The supported training entry for the next stage is `scripts/pretrain_ri_gmappo_3d_bc.py` followed by `scripts/train_ri_gmappo.py --resume <bc_checkpoint>`.
- The matched baseline protocol in `scripts/run_3d_baseline_protocol.py` completed with three training/evaluation replicates and 30 independent evaluation episodes per replicate. In the 3DOF straight-target task, geometric control reached `1.000 +/- 0.000` success, RI-GMAPPO from scratch reached `0.000 +/- 0.000`, BC-only reached `0.844 +/- 0.077`, and BC-to-PPO reached `0.967 +/- 0.033`. BC-to-PPO had zero collisions and zero constraint violations; this establishes a learnable curriculum baseline, not a main-method comparison.
- `relation_adj` now carries separate perception, communication, and dynamic task-support adjacencies while the old `adj` remains the union graph for a strict single-graph ablation. `graph_encoder=multi_relation` applies role-pair-conditioned messages over each relation plus a union-graph residual path. A one-seed diagnostic with 200 BC episodes, 80 BC epochs, and conservative PPO fine-tuning (60 updates, learning rate `5e-5`, entropy coefficient `0.001`) reached `1.000` success over 30 independent straight-target episodes with zero collisions, timeouts, and constraint violations. This is an integration/learnability result only.
- The matched three-seed comparison is complete with 30 independent episodes per seed. Single-graph BC-only/BC-to-PPO reached `0.844 +/- 0.051` and `0.900 +/- 0.033` success, respectively; multi-relation BC-only/BC-to-PPO reached `0.933 +/- 0.115` and `0.922 +/- 0.107`. All variants had zero collision and constraint-violation rates. The mean multi-relation result is slightly higher but its interval overlaps the single-graph result, so nominal-condition performance is a feasibility baseline rather than the main method claim.
- `UAVIntercept3DConfig` now exposes `communication_range_scale`, `failed_blue_agent`, `node_failure_start_step`, and `node_failure_duration_steps`. `train_ri_gmappo.py` also supports fixed or randomized 3DOF communication range scaling for staged topology curriculum training.
- `scripts/evaluate_3d_topology_robustness.py` reuses existing single-graph and multi-relation checkpoints and evaluates matched disruption scenarios. A screening run with 3 training seeds, 11 scenarios, and 5 episodes per checkpoint-scenario produced 330 episodes under `results/intercept_3d_topology_robustness_screen/`.
- The screening result shows that nominally trained multi-relation checkpoints do not yet outperform the single-graph checkpoints under the tested disruptions. Treat this as evidence that topology-curriculum retraining is necessary, not as a negative final result.
- A one-update multi-relation topology-curriculum training smoke passed from an existing seed-0 checkpoint using randomized range scale, dropout, delay, and radar dropout. This validates the training interface only; it is not a result.
- `scripts/run_3d_topology_curriculum_protocol.py` completed an initial three-seed 20-update pilot with single-graph and multi-relation checkpoints, followed by 330 robustness evaluation episodes under `results/intercept_3d_topology_curriculum_protocol_seed0_pilot/`. The directory name is historical from the first seed-0 run; it now contains seeds 0, 1, and 2.
- In the 20-update pilot, multi-relation and single-graph are mostly tied on nominal, dropout, delay, and range-0.75 scenarios. Multi-relation has a positive signal on `radar_025`, `relay_failure`, and `scout_failure`, while `range_050` remains too severe and favors single-graph. Treat this as scenario-selection evidence, not a final robustness claim.
- Random node-failure curriculum parameters are now available (`--node-failure-random-prob`, start-step range, and duration range). A one-update smoke run passed under `results/intercept_3d_node_failure_curriculum_smoke/`.
- A focused three-seed node-failure curriculum pilot also completed under `results/intercept_3d_node_failure_curriculum_pilot_seed0/` with 20 fine-tuning updates and 330 evaluation episodes. It used a milder range curriculum (`0.65--1.0`) plus random temporary blue-node failures. Multi-relation outperformed single-graph on most non-extreme scenarios in this pilot, including nominal, range-0.75, dropout, delay-2, radar perturbations, relay failure, and scout failure. `range_050` remains an extreme out-of-training stress case where single-graph performs better.
- A formal-budget node-failure evaluation completed under `results/intercept_3d_node_failure_curriculum_formal_node_failure_eval/` with 3 seeds, 30 episodes per checkpoint-scenario, and 360 total episodes. Under relay failure, multi-relation reached `1.000 +/- 0.000` success versus single-graph `0.922 +/- 0.016`; under scout failure, multi-relation reached `0.967 +/- 0.047` versus single-graph `0.944 +/- 0.016`. Multi-relation also used fewer steps on both scenarios. This is the first usable 3DOF robustness evidence, though more selected scenarios are still needed.
- A second formal-budget selected robustness evaluation completed under `results/intercept_3d_node_failure_curriculum_formal_selected_eval/` with 720 total episodes. Multi-relation is ahead on `delay_2` (`0.967 +/- 0.047` vs `0.944 +/- 0.016`), `dropout_030` (`0.967 +/- 0.027` vs `0.933 +/- 0.027`), and `radar_025` (`0.944 +/- 0.079` vs `0.922 +/- 0.031`), with fewer average steps. Single-graph is ahead on `range_075` (`0.967 +/- 0.027` vs `0.944 +/- 0.079`), so range compression should be treated as a mixed stress case rather than the main positive claim.
- `scripts/analyze_3d_topology_curriculum_statistics.py` now consolidates the formal node-failure and selected robustness evaluations into `results/intercept_3d_topology_curriculum_formal_summary.csv` and `docs/intercept_3d_topology_curriculum_formal_summary.md`. The current delta table favors multi-relation in 5 of 6 formal scenarios: `delay_2`, `dropout_030`, `radar_025`, `relay_failure`, and `scout_failure`; `range_075` favors single-graph.
- The formal summary now includes paired episode bootstrap confidence intervals. Only `relay_failure` currently has a success-rate CI fully above zero (`+0.078`, 95% CI `[+0.022, +0.133]`) and a steps CI fully below zero (`-16.2`, 95% CI `[-28.0, -6.7]`). Other positive scenarios should be described as trends until more seeds or stronger evaluation settings are added.
- 3DOF evaluation rows now include kill-chain timing and node-failure recovery metrics: first attack-window step, first chain-close step, post-failure recovery indicator, post-failure recovery steps, chain-closed rate during failure, tracking during failure, and connectivity during failure.
- `scripts/analyze_3d_node_failure_recovery.py` produces `results/intercept_3d_node_failure_recovery_summary.csv` and `docs/intercept_3d_node_failure_recovery_summary.md`. In `relay_failure`, multi-relation improves post-failure chain recovery probability by `+0.078` with 95% CI `[+0.022, +0.133]`, and reduces recovery steps by `-16.2` with 95% CI `[-28.0, -4.5]`. This directly supports the “kill-chain recovery after relay failure” paper claim. `scout_failure` remains a positive but non-separated trend.

- `scripts/build_3d_paper_tables.py` now produces `results/intercept_3d_paper_main_table.csv`, `docs/intercept_3d_paper_main_table.md`, and `docs/intercept_3d_paper_main_table.tex`. The table separates the current evidence into a defensible main claim (`relay_failure`), supporting trends (`scout_failure`, dropout, delay, radar), and a mixed stress case (`range_075`).
- `scripts/find_3d_relay_failure_case_candidates.py` now produces `results/intercept_3d_relay_failure_case_candidates.csv` and `docs/intercept_3d_relay_failure_case_candidates.md`. The top candidate is train seed `0`, episode `0`, where the single-graph checkpoint does not recover after relay failure while the multi-relation checkpoint recovers in `8` steps.
- `scripts/replay_3d_relay_failure_case.py` now replays the top relay-failure candidate and produces `results/intercept_3d_relay_failure_case_replay.csv`, `docs/intercept_3d_relay_failure_case_replay.md`, and `results/figures/intercept_3d_relay_failure_case_replay.png`. In the replay, the single-graph policy times out at `260` steps without chain closure while the multi-relation policy closes the chain at step `48`.
- The full lightweight paper asset gate passed after adding the 3DOF paper table, relay-failure case-candidate, and relay-failure replay scripts.
- `graph_relation_ablation=no_task_support` removes the dynamic task-support relation from the 3DOF graph and is now exposed through `scripts/train_ri_gmappo.py`, `scripts/pretrain_ri_gmappo_3d_bc.py`, `scripts/evaluate_ri_gmappo_3d.py`, `scripts/evaluate_3d_topology_robustness.py`, `scripts/run_3d_baseline_protocol.py`, `scripts/run_3d_topology_curriculum_protocol.py`, and `scripts/replay_3d_relay_failure_case.py`.
- A seed-0 diagnostic pilot completed under `results/intercept_3d_no_task_support_baseline_seed0_pilot/` and `results/intercept_3d_no_task_support_topology_seed0_pilot/`. Compared with the full multi-relation seed-0 checkpoint on the same relay/scout evaluation seeds, full multi-relation reached `1.000` success while no-task-support reached `0.300`, with average steps `45.9` versus `195.5`. This is strong diagnostic support for a formal task-support ablation, but it is not yet paper-level statistical evidence.
- `scripts/analyze_3d_task_support_ablation_pilot.py` produces `results/intercept_3d_task_support_ablation_seed0_pilot_summary.csv` and `docs/intercept_3d_task_support_ablation_seed0_pilot_summary.md`.
- `scripts/run_3d_task_support_ablation_protocol.py` now defines the formal no-task-support ablation protocol. The formal run completed for seeds `0, 1, 2` under `results/intercept_3d_no_task_support_baseline_formal/` and `results/intercept_3d_no_task_support_topology_formal/`, with 30 evaluation episodes per checkpoint-scenario for `relay_failure` and `scout_failure`.
- `scripts/analyze_3d_task_support_ablation_formal.py` produces `results/intercept_3d_task_support_ablation_formal_summary.csv` and `docs/intercept_3d_task_support_ablation_formal_summary.md`. On matched evaluation episodes, full multi-relation outperforms no-task-support on `relay_failure` success by `+0.111` with 95% CI `[+0.056, +0.178]` and reduces recovery steps by `-23.5` with 95% CI `[-37.7, -11.6]`. On `scout_failure`, success improves by `+0.089` with 95% CI `[+0.033, +0.156]` and recovery steps improve by `-18.8` with 95% CI `[-32.9, -7.0]`. This is now manuscript-level evidence for the dynamic task-support relation.
- `graph_message_ablation=no_role_pair_gate` disables learned role-pair-conditioned message gates while preserving the perception, communication, and task-support relation channels. The disabled gate uses a scale-matched constant value of `0.5`, matching the full model's zero-initialized sigmoid gate scale.
- `scripts/run_3d_role_pair_gate_ablation_protocol.py` completed the formal scale-matched no-role-pair-gate ablation for seeds `0, 1, 2` under `results/intercept_3d_no_role_pair_gate_baseline_formal_scale_matched/` and `results/intercept_3d_no_role_pair_gate_topology_formal_scale_matched/`, with 30 evaluation episodes per checkpoint-scenario for `relay_failure` and `scout_failure`.
- `scripts/analyze_3d_role_pair_gate_ablation_formal.py` produces `results/intercept_3d_role_pair_gate_ablation_formal_scale_matched_summary.csv` and `docs/intercept_3d_role_pair_gate_ablation_formal_scale_matched_summary.md`. On `relay_failure`, the full model improves success/recovery over no-role-pair-gate by `+0.044` with 95% CI `[+0.011, +0.089]` and reduces recovery steps by `-9.8` with 95% CI `[-19.2, -2.7]`. On `scout_failure`, the effect is positive but non-separated, so it should be used as supporting trend evidence only.
- `scripts/build_3d_paper_tables.py` now appends both formal task-support and formal role-pair-gate ablation sections to `docs/intercept_3d_paper_main_table.md`.
- `graph_input_ablation=no_edge_features` zeros edge features inside the actor while preserving graph dimensions and relation channels. It is now wired through 3DOF BC pretraining, PPO training, policy evaluation, topology robustness evaluation, baseline protocol, and topology protocol. The current validation is only smoke-scale: compile checks, 3DOF environment smoke, one-update no-edge training smoke, no-edge checkpoint evaluation smoke, and the full lightweight build gate all pass. No paper claim should use this ablation until a matched diagnostic or formal run is complete.
- The seed-0 no-edge diagnostic completed under `results/intercept_3d_no_edge_features_baseline_seed0_diagnostic/` and `results/intercept_3d_no_edge_features_topology_seed0_diagnostic/`. The paired diagnostic summary in `docs/intercept_3d_no_edge_features_ablation_seed0_diagnostic_summary.md` shows only a weak relay-failure degradation (`+0.033` full-minus-no-edge success delta, CI `[+0.000, +0.100]`) and no scout-failure success difference. Do not promote this to a formal three-seed ablation unless a later manuscript review specifically needs an edge-feature diagnostic.
- `graph_input_ablation=no_role_identity` maps every role ID to the same neutral role inside the actor while preserving relation channels and edge features. A seed-0 diagnostic showed stronger recovery-step degradation, so it was promoted to a formal three-seed run.
- The formal no-role-identity ablation completed under `results/intercept_3d_no_role_identity_baseline_formal/` and `results/intercept_3d_no_role_identity_topology_formal/`. The summary in `docs/intercept_3d_no_role_identity_ablation_formal_summary.md` shows a modest relay-failure recovery-speed benefit for the full model (`-4.86` recovery-step delta, CI `[-11.94, -0.10]`) but mixed scout-failure results (`+2.22` recovery-step delta, CI `[-7.24, +13.86]`). Treat this as auxiliary diagnostic evidence only; the stronger mechanism evidence remains `no_task_support` and `no_role_pair_gate`.
- `target_policy=break_turn` adds defensive maneuvering when a blue UAV enters the target's threat zone: the target performs lateral break turns relative to the nearest pursuer and altitude changes while preserving world-boundary and altitude safety. `target_policy=weaving` adds lower-intensity sinusoidal lateral/altitude maneuvering.
- The zero-shot break-turn pilot completed under `results/intercept_3d_break_turn_node_failure_pilot/`, with paired summary in `docs/intercept_3d_break_turn_node_failure_pilot_summary.md`. Existing straight-target checkpoints were evaluated under break-turn plus relay/scout node failure. Single-graph timed out in every tested episode, while multi-relation retained nonzero success: relay failure `0.244` vs `0.000` and scout failure `0.144` vs `0.000`. Paired success deltas were `+0.244` with CI `[+0.156, +0.333]` for relay failure and `+0.144` with CI `[+0.078, +0.222]` for scout failure. This is strong scenario-depth evidence that the harder target policy has discriminative value, but the absolute success rate is too low for a main result without break-turn curriculum fine-tuning.
- A 20-update seed-0 break-turn fine-tuning pilot completed under `results/intercept_3d_break_turn_curriculum_seed0_pilot/`, but did not raise absolute success enough: multi-relation reached `0.267` on relay failure and `0.000` on scout failure; single-graph stayed at `0.000` on both.
- The zero-shot weaving pilot completed under `results/intercept_3d_weaving_node_failure_pilot/`, with paired summary in `docs/intercept_3d_weaving_node_failure_pilot_summary.md`. It behaved similarly to break-turn: multi-relation reached `0.267` relay and `0.144` scout success, while single-graph stayed at `0.000`.
- A seed-0 `weaving_mild` pilot completed under `results/intercept_3d_weaving_mild_node_failure_seed0_pilot/`. It still did not produce paper-ready absolute success: multi-relation reached `0.267` relay and `0.000` scout success; single-graph stayed at `0.000`.
- `docs/intercept_3d_maneuvering_target_pilot_summary.md` consolidates the maneuvering-target pilots. Current decision: keep maneuvering target results as scenario-depth diagnostics only. Do not promote them to the main table until a staged target-policy curriculum raises absolute success.
- `scripts/evaluate_3d_geometric_node_failure.py` evaluates the deterministic geometric pursuit demonstrator under the same relay/scout node-failure protocol. The formal run under `results/intercept_3d_geometric_node_failure_eval/` produced 180 episodes. It reached 100% success and 100% post-failure recovery in both relay and scout failure, with about `5.2` recovery steps. Because this controller uses simulator target state, it is an oracle-style demonstrator/reference rather than a fair decentralized baseline.
- `scripts/analyze_3d_compact_node_failure_baselines.py` produces `results/intercept_3d_compact_node_failure_baselines.csv` and `docs/intercept_3d_compact_node_failure_baselines.md`. The compact table places oracle geometric pursuit, single-graph MAPPO, and EA-RG-MAPPO-S under the same straight-target node-failure table. It documents baseline coverage and task difficulty, while explicitly preserving the paired single-vs-multi recovery analysis and formal ablations as the real method evidence.
- The new compact-baseline scripts compile successfully, and the full lightweight paper asset gate passed after the compact-baseline additions.
- `UAVIntercept3DConfig(strict_target_sensing=True)` now prevents local observations, shared observations, and graph target nodes/edges from falling back to true target state before a valid detection. Before first detection it uses a fixed search prior; after detection it uses the last detected target position/velocity. The default remains `False`, so all existing straight-target evidence is reproducible.
- `scripts/smoke_test_strict_target_sensing.py` verifies that forced radar dropout keeps legacy observations on true target state but strict-sensing observations and graph target nodes on the fixed prior.
- `scripts/evaluate_3d_topology_robustness.py`, `scripts/evaluate_ri_gmappo_3d.py`, `scripts/train_ri_gmappo.py`, `scripts/pretrain_ri_gmappo_3d_bc.py`, `scripts/run_3d_baseline_protocol.py`, and `scripts/run_3d_topology_curriculum_protocol.py` now expose `--strict-target-sensing`.
- A small strict-sensing node-failure screen completed under `results/intercept_3d_strict_sensing_node_failure_screen/` with 3 seeds, relay/scout failure, and 5 episodes per checkpoint-scenario. Existing topology-curriculum checkpoints remain task-capable, but single-graph reached `1.000` success on both relay/scout while multi-relation reached `0.867`. Treat this as a diagnostic showing that strict sensing needs matched retraining, not as a paper claim.
- A strict-sensing topology-curriculum pilot completed under `results/intercept_3d_strict_sensing_curriculum_seed0_pilot/`. It reused the existing node-failure curriculum checkpoints, enabled `--strict-target-sensing`, and fine-tuned single/multi checkpoints for 10 PPO updates across seeds `0, 1, 2`. The 30-episode-per-checkpoint-scenario evaluation produced 360 episodes under `formal_eval/`.
- `docs/intercept_3d_strict_sensing_curriculum_seed0_pilot_formal_eval_summary.md` summarizes the strict-sensing pilot checkpoint evaluation. Under `relay_failure`, multi-relation recovered in `0.967` of episodes versus single-graph `0.711`, giving a paired recovery delta of `+0.256` with 95% CI `[+0.156, +0.367]`, and reduced recovery steps by `-53.9` with 95% CI `[-75.3, -32.6]`. Under `scout_failure`, the result is positive but non-separated (`+0.067`, CI `[-0.056, +0.189]`). This is now a strong candidate scenario-depth result for Q2-level quality, especially because strict sensing removes target-state leakage from observations.
- `scripts/build_3d_paper_tables.py` now appends a strict-sensing scenario-depth section to `docs/intercept_3d_paper_main_table.md`. The section labels the result as a 10-update strict-sensing fine-tuning pilot, promotes only the separated relay-failure row, and keeps scout failure as a supporting trend.
- `docs/english_3d_experiments_draft.md` now converts the current 3DOF evidence stack into manuscript-ready experimental narrative. It covers the 3DOF scenario, training protocol, relay-failure recovery result, communication/sensing robustness trends, formal mechanism ablations, strict-sensing scenario-depth experiment, qualitative replay case, and claim boundaries.
- `docs/english_3d_manuscript_draft.md` now provides a full next-stage English manuscript skeleton around the 3DOF claim, including title, abstract, contributions, claim boundary, introduction, related work placeholders, problem formulation, method, experiments, discussion, conclusion, and revision checklist.
- `scripts/replay_3d_relay_failure_case.py` was updated with a default `strict_target_sensing=False` compatibility field after `evaluate_ri_gmappo_3d.build_config()` gained the new option. The relay-failure replay and the full lightweight paper asset gate both pass after the strict-sensing changes.

## Next Recommended Task

Next, prepare manuscript-quality 3DOF figures and LaTeX migration. Highest priority figures are: task scenario/kill-chain diagram, multi-relation role graph diagram, relay-failure recovery timeline, and strict-sensing scenario-depth result table/figure.
