# 3DOF Manuscript Figure Assets

Generated: 2026-08-02T01:40:47

These figures are generated from existing 3DOF result files and schematic task definitions. They do not retrain or re-evaluate policies.

| Figure | File | Manuscript use |
| --- | --- | --- |
| Task scene | `results/figures/intercept_3d_task_scene.png` | Introduce the 3DOF scout-relay-attacker kill-chain task. |
| Multi-relation graph | `results/figures/intercept_3d_multi_relation_graph.png` | Explain perception, communication, task-support, and role-pair-conditioned messages. |
| Main recovery evidence | `results/figures/intercept_3d_recovery_evidence_summary.png` | Show relay/scout recovery and relay-failure mechanism ablations. |
| Strict sensing pilot | `results/figures/intercept_3d_strict_sensing_summary.png` | Show the no-target-fallback scenario-depth result with an honest budget label. |

## Claim Boundary

- Use relay-failure recovery as the main statistical figure.
- Use task-support and role-pair-gate ablation deltas as mechanism evidence.
- Label strict sensing as a 10-update scenario-depth pilot, not as a full-budget universal claim.
- Keep the existing relay-failure replay figure as the qualitative timeline/case figure.

Existing qualitative figure:

- `results/figures/intercept_3d_relay_failure_case_replay.png`