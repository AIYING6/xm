# Roadmap

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

Next:

- Decide whether to rerun a longer strict-sensing fine-tuning protocol for polish or keep the current budget-labeled scenario-depth result.
- If keeping the current result, draft the 3DOF experiment section and align text claims with the paper-facing table statuses.
- Decide whether to extend `scout_failure` with more seeds or keep it as supporting trend evidence.
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
