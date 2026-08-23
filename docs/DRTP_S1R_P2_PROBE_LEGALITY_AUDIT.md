# DRTP S1-R P2 Probe Legality Audit

{
  "protocol": "DRTP-S1R-P2-PROBE-V1",
  "classification": "actor_legal",
  "source": "telemetry_native_t0 actor_view obs/share_obs/graph",
  "privileged_simulator_state_in_probe": false,
  "input_fields": [
    "obs",
    "share_obs",
    "graph_node_feat",
    "graph_edge_feat",
    "graph_adj",
    "graph_relation_adj",
    "graph_role"
  ],
  "output_reloaded": {
    "probe_id": "P2_reload_probe",
    "output": [
      0.0,
      1.0,
      0.0
    ]
  },
  "pass": true
}
