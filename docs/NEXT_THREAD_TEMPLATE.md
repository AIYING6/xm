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
Run the next five-seed mechanism ablation under the frozen bottleneck dropout-relay protocol.

Relevant files:
- algorithms/ri_gmappo/simple_ri_gmappo.py
- algorithms/ri_gmappo/role_graph.py
- scripts/train_ri_gmappo.py
- scripts/evaluate_ri_gmappo_3d.py
- scripts/evaluate_3d_topology_robustness.py
- scripts/evaluate_3d_checkpoint_sweep.py
- scripts/run_3d_strict_sensing_formal_protocol.py
- envs/uav_intercept_3d_env.py
- tests/
- docs/Q1_EXECUTION_PLAN.md
- docs/gate1_communication_feasibility_audit.md
- docs/actor_critic_observation_boundary.md
- docs/bottleneck_dropout030_relay_frozen_protocol.md
- docs/intercept_3d_gate1_dropout030_bottleneck_5seed_formal_summary.md
- docs/intercept_3d_gate1_dropout030_bottleneck_mechanism_v2/failure_aligned_mechanism_summary.md
- docs/PROJECT_STATE.md
- docs/ROADMAP.md

Constraints:
- Do not change the existing default 2D training behavior.
- Do not rerun or tune the completed five-seed formal test split unless a new frozen protocol is explicitly defined first.
- Preserve the standard environment interface.
- Existing actor-side tests must keep enforcing communication-feasible information flow.
- Task-support edges may gate delivered messages but must not transmit target information by themselves.
- Use graph direction convention `A[receiver, sender] = 1`.
- Keep centralized critic access separate from decentralized actor access.

Completion standard:
- Run the relevant Gate 1 tests.
- Use the documented validation-time collision rejection rule if any new checkpoint selection is needed: `--max-selection-collision-rate 0.0`.
- Do not selectively repair weak seeds.
- Compare against the completed post-Gate-1 diagnostics and formal result:
  - `docs/intercept_3d_gate1_post_change_retrain_20update_diag_summary.md`
  - `docs/intercept_3d_gate1_post_change_retrain_60update_diag_summary.md`
  - `docs/intercept_3d_gate1_post_change_retrain_60update_three_method_safety_selected_diag_summary.md`
  - `docs/intercept_3d_gate1_post_change_retrain_60update_5seed_integration_diag_summary.md`
  - `docs/intercept_3d_gate1_dropout030_bottleneck_5seed_formal_summary.md`
- Start with `no_task_support`; then run `no_role_pair_gate` if the first ablation is stable.
- Use the same frozen validation/test split structure and report seed-aware bootstrap deltas against `multi_relation`.
- Save generated data/figures under a new result directory and document the method.
- Relevant tests pass.
- Current frozen 3v1 bottleneck dropout-relay protocol remains documented as a regression target.
- `docs/PROJECT_STATE.md` and `docs/ROADMAP.md` are updated with the result and next decision.
```
