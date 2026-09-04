# Current Project State

## Deliverable

This repository is the focused EA-RG-MAPPO-S 3DOF heterogeneous UAV interception project.

- Environment: lightweight 3DOF, 3v1 scout-relay-attacker interception.
- Main result: early post-relay-failure recovery under the locked nominal held-out protocol.
- Manuscript: `paper_latex_3d_en/`.
- Selected evidence: `results/`.

## Scope boundary

The project does not claim complete 6DOF combat, JSBSim/LAG validation, radar/missile closure, universal baseline superiority, or unrestricted OOD generalization.

## Validation

The active checks are:

```text
scripts/smoke_test_env.py
scripts/smoke_test_intercept_3d_env.py
tests/test_gate1_communication_feasibility.py
tests/test_happo_policy_loss.py
```

Failed alternative algorithm lines, old manuscript routes, raw development runs, and migration experiments have been removed from the deliverable repository.

## Research-line update — 2026-09-04

- The A-line Original DRTP manuscript/evidence remains frozen; the new work does not rewrite its claims or results.
- EGTR's fresh 10M double-cohort programme ended `EGTR_DOUBLE_COHORT_REPLICATION_NO_GO`: it improved Original DRTP broadly but did not establish repeatable superiority/reliability versus UTR in both cohorts.
- PVF is an engineering fallback only, not the primary algorithm line.
- The current single-model research candidate is **TGTR-PPO** (Topology-Group Trust-Region PPO): fixed synchronized topology exposure, ordinary-PPO anchor, minimal active-group actor correction, held-stream training certificate, and per-group full-policy KL.
- P0 status: `TGTR_P0_FEASIBLE_FOR_C1`.
- The separately authorized C1 implementation and five-state exact same-rollout audit completed with `TGTR_C1_NO_GO`. Ordinary PPO exposed group harm in 4/5 source states, but the frozen design/certificate rule rejected every TGTR actor epoch (20/20 zero steps), and overall surrogate retention passed in only 1/5 states.
- TGTR fresh-seed development and cloud repetition are not authorized. The frozen candidate is closed; see `docs/tgtr_ppo_c1_20260904/TGTR_C1_FINAL_RESULT.md`.
- Post-TGTR design work now targets **RACG-PPO** (Reliability-Adaptive Cross-fitted Group-Gradient PPO): fixed synchronized exposure, cross-fitted training-only group-gradient agreement, a soft average-oriented conflict correction, and an exact ordinary-PPO fallback. P0 mechanically verified the non-freezing bound and interface design as `RACG_P0_FEASIBLE_FOR_C1_DESIGN_ONLY`; it authorizes no implementation, rollout, update, cloud run, or fresh-seed training. See `docs/racg_ppo_p0_20260904/`.
- RACG C0.5 froze the only permitted formula: continuous split agreement with no trigger threshold, reliability-shrunk group gradients, one seven-dimensional average-anchored CAGrad solve, a correction capped at 0.5 of the complete ordinary actor direction, and exact ordinary fallback on disagreement or numerical failure. Its pre-execution status was `RACG_C05_FORMULA_FROZEN_FOR_C1_IMPLEMENTATION`.
- RACG C1 was subsequently authorized and completed as `RACG_C1_NO_GO`. The method eliminated TGTR's actor-freezing failure and retained the overall local surrogate in 4/5 source states, but improved the worst topology-group harm in only 2/5 states (4/5 required) and cost 6.84--11.05 times ordinary PPO on the measured CPU path (4x maximum). RACG is closed; no fresh-seed or cloud training is authorized. See `docs/racg_ppo_c1_20260904/`.
- **CAPD** (Consensus-Anchored Policy Distillation) passed its static P0 but closed at P0.5 as `CAPD_P05_NO_CANDIDATE_CONSENSUS_SIGNAL`. After cloud recovery, all 20 frozen 10M UTR/EGTR checkpoints passed SHA256, manifest and exact-architecture checks. On 168 newly frozen outcome-free training states, the ten predeclared three-EGTR groups had zero qualifying consensus units; median pairwise EGTR JS was 0.451 in Cohort A and 0.625 in Cohort B. The teachers represent incompatible policy modes rather than a repeated consensus direction, so no student implementation or training is authorized. See `docs/capd_p05_signal_20260904/`.
- A new algorithm project, **TATG-MAPPO**, is now limited to a zero-training P0 semantic and novelty audit. It asks whether a single current legal graph snapshot is information-sufficient during dynamic relay-topology transition; it is not a DRTP stabilization or training-seed precursor project. A generic GNN+GRU is excluded as a contribution. P1 must first show a repeatable, policy-neutral and outcome-free legal-history information gap in two disjoint state cohorts before any architecture implementation is considered. See `docs/tatg_mappo_p0_20260904/`.
- **TATG-MAPPO P1** completed as `TATG_P1_INFORMATION_GAP_PRESENT`. In each of two disjoint, scripted, non-learning state cohorts, the current actor-legal structural topology code (including the present edge-age proxy) mapped to more than one transition label, while a one-step legal topology history had no mixed-label code. This is a narrow topology-representation result only: no policy, reward, return, evaluation tape, checkpoint or PPO update was used. See `docs/tatg_mappo_p1_20260904/`.
- **TATG-MAPPO P1.5** froze the only CETM formula, the local receiver-row input boundary, an exact parameter-matched generic current-snapshot GRU control, the zero-residual ablation and the three-tensor runtime-state contract. Its static result is `TATG_P15_FORMULA_FROZEN_FOR_C1_IMPLEMENTATION_AUDIT`; see `docs/tatg_mappo_p15_20260904/`.
- **TATG-MAPPO C1** completed as `TATG_C1_IMPLEMENTATION_SERIALIZATION_PASS`. The isolated CETM implementation reads only each actor's local blue-blue communication/task-support/message-age rows; exact zero-residual identity, reset state, capacity matching (1,617 added parameters per temporal module) and post-serialization continuation all passed. It used synthetic tensors only: 0 environment steps, 0 PPO updates and no change to the legacy snapshot actor or critic. It authorizes only a separately frozen policy-integration audit, not training. See `docs/tatg_mappo_c1_20260904/`.
- **TATG-MAPPO C1.5** completed as `TATG_C15_ACTOR_INTEGRATION_PASS`. An isolated wrapper connected CETM to the snapshot actor's policy-input boundary. At reset its logits are bit-identical to the legacy snapshot actor; a legal transition reaches logits, the generic snapshot-GRU control has identical added capacity (3,899 parameters), and wrapper runtime restoration is exact. The wrapper is audit-only because it retains the copied legacy head to expose that boundary; no PPO runner was altered. It used synthetic tensors only: 0 environment steps and 0 PPO updates. A separately frozen runner/rollout-state preflight remains required before training. See `docs/tatg_mappo_c15_20260904/`.
- **TATG-MAPPO C2** completed as `TATG_C2_RUNTIME_BANK_PASS`. The runner-neutral state bank keeps one CETM state per vectorized environment, resets completed slots only, preserves unfinished slots exactly, and restores exact next-call behavior. It stores only the frozen three tensors under `tatg_memory_state`; the existing runner's explicit done/reset and runtime-checkpoint lifecycle sites were verified but not modified or executed. It used synthetic tensors only: 0 environment steps and 0 PPO updates. It authorizes only a separately frozen runner-integration preflight, not training. See `docs/tatg_mappo_c2_20260904/`.
- **TATG-MAPPO C2.5** completed as `TATG_C25_SEQUENCE_PPO_RUNNER_REQUIRED`. The current snapshot PPO runner preserves `[time, environment]` during collection but flattens and randomly permutes it for actor updates, which is invalid for CETM state replay. The frozen resolution requires exact state-before-rollout persistence and chronological full-sequence replay in every actor PPO epoch; the snapshot critic remains ordinary and the CETM, generic-GRU and delta-zero controls must share the same sequence runner. It used source inspection only: 0 environment steps and 0 PPO updates. It authorizes only a separately frozen runner implementation and same-rollout correctness audit, not training. See `docs/tatg_mappo_c25_20260904/`.
- **TATG-MAPPO C3** completed as `TATG_C3_SEQUENCE_PPO_CORRECTNESS_PASS`. On a synthetic chronological `[time, environment]` rollout, replay from the saved CETM state exactly reproduced collected action log-probabilities, reset only the completed environment slot, retained a finite ordinary clipped actor objective, and connected gradients first to the new temporal policy head and then to CETM's GRUCell after a deterministic unit-level activation check. CETM, the capacity-matched snapshot-GRU control and the zero-residual control shared the same replay route and 3,899 added actor parameters. No environment, evaluation tape, cloud process, selected checkpoint or formal PPO update was used. It authorizes only a separately frozen runner integration and exact-continuation audit, not training. See `docs/tatg_mappo_c3_20260904/`.
