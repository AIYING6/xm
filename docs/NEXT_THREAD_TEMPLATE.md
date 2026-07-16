# Next Thread Template

Use this when starting a new Codex conversation for this project.

```text
Please first read:

- AGENTS.md
- README.md
- docs/PROJECT_STATE.md
- docs/DECISIONS.md
- docs/ROADMAP.md

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
Draft the 3DOF experiment section around the finalized evidence stack.

Relevant files:
- algorithms/ri_gmappo/simple_ri_gmappo.py
- scripts/train_ri_gmappo.py
- scripts/pretrain_ri_gmappo_3d_bc.py
- scripts/evaluate_ri_gmappo_3d.py
- scripts/evaluate_3d_topology_robustness.py
- scripts/run_3d_topology_curriculum_protocol.py
- scripts/build_3d_paper_tables.py
- envs/uav_intercept_3d_env.py
- docs/intercept_3d_paper_main_table.md
- docs/intercept_3d_strict_sensing_curriculum_seed0_pilot_formal_eval_summary.md
- results/intercept_3d_strict_sensing_curriculum_seed0_pilot/formal_eval/episode_metrics.csv

Constraints:
- Do not change the existing default 2D training behavior.
- Keep the current relay-failure recovery claim and task-support ablation as the strongest manuscript evidence.
- Keep the current straight-target protocol reproducible; add strict sensing as an opt-in switch first.
- Do not promote oracle geometric pursuit as a fair decentralized baseline; it uses simulator target state.
- Do not promote zero-shot maneuvering-target results to main-table evidence yet; absolute success is too low.
- Do not spend formal three-seed budget on `no_edge_features` unless the manuscript later specifically needs that diagnostic.
- Do not treat `no_role_identity` as a primary mechanism claim; formal results are relay-positive but scout-mixed.
- Use `--strict-target-sensing`.
- The existing strict-sensing evidence uses 10 PPO fine-tuning updates; label it honestly if integrating it into paper-facing tables.
- Relay failure is separated and paper-useful; scout failure is positive but non-separated.
- Do not rewrite the claim as a general strict-sensing superiority claim across all node failures.
- Use three layers of evidence: main relay-failure recovery, mechanism ablations (`no_task_support`, `no_role_pair_gate`), and strict-sensing scenario depth.
- Clearly label the strict-sensing result as a 10-update fine-tuning pilot if used in manuscript text.

Completion standard:
- 3DOF environment smoke test passes.
- `scripts/smoke_test_strict_target_sensing.py` passes.
- Draft/update the experiment narrative without overstating scout failure or strict-sensing generality.
- Run the lightweight paper asset gate after any table integration.
- `docs/PROJECT_STATE.md` is updated with the result and any remaining failure mode.
```
