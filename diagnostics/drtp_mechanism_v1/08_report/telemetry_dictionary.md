# DRTP Mechanism V1 telemetry dictionary

Telemetry is an evidence sink only. `episode_summary.jsonl` contains one row per terminal episode; `failure_event_window.jsonl` contains rows for `tau=-20..+60` around scheduled or matched pseudo onset.

| Field family | Required fields |
|---|---|
| provenance | `protocol`, `method`, `seed`, `update`, `env_index`, `episode_id`, `env_step` |
| scenario | `scenario_group`, `scenario_member`, `failure_onset`, `failure_duration`, `failure_active`, `failure_relative_time` |
| outcome | `success`, `timeout`, `collision`, `constraint_violation`, `termination_reason`, `terminal_step`, `total_return` |
| geometry | per-UAV position, velocity, heading, pairwise geometry |
| information path | legal communication edges, direct/relay/no-path state, relay status, path switch |
| task support | scout detection, attacker valid target information, cache source/freshness, attack-window and task-support state |
| policy | action and policy entropy when available |
| reward | total reward and environment-provided reward components |

Missing values are represented as JSON `null`, never as fabricated zeros. The writer records a schema manifest and is restored from runtime checkpoints; it never supplies an input tensor to the policy or critic.
