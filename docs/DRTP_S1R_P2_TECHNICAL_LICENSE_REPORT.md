# DRTP S1-R P2 Technical License Report

## Decision: `P2_TECHNICAL_LICENSE_PASS`

This report is technical-only. No scientific G/B reference, intervention, evaluator, held-out run, or canonical run was started.

- Technical env steps: `516` (limit `20000`).
- Scientific env steps: `0`.
- Frozen asset integrity: `True`.
- RNG tuple construction: `True`.
- Runtime RNG isolation: `True`.
- Telemetry schema/readback: `True`.
- Failure-relative r=0..39: `True`.
- Risk-set semantics: `{'protocol': 'DRTP-S1R-P2-RISK-SET-V1', 'scheduled_onset': 44, 'episode_id': 910244, 'alive_immediately_before_onset': True, 'pre_onset_rows_retained': True, 'pre_onset_termination_removed': False, 'failure_triggered': True, 'pass': True}`.
- Precursor reconstruction: `{'protocol': 'DRTP-S1R-P2-PRECURSOR-V1', 'milestone': 'scratch_1', 'window': 'failure_relative_step 0..39', 'values_first': {'P1_progress_rate_40': 0.003749999999999999, 'P2_quality_negative_stagnation_fraction_40': 0.0, 'P3_stage_advance_40': 0}, 'values_second': {'P1_progress_rate_40': 0.003749999999999999, 'P2_quality_negative_stagnation_fraction_40': 0.0, 'P3_stage_advance_40': 0}, 'deterministic_reconstruction': True, 'pass': True}`.
- Checkpoint persistence/reload: `{'protocol': 'DRTP-S1R-P2-CHECKPOINT-V1', 'technical_only': True, 'runtime_path': 'results\\development\\drtp_s1r_p2_technical_only\\actor_critic_runtime_state_latest.pt', 'model_path': 'results\\development\\drtp_s1r_p2_technical_only\\actor_critic_latest.pt', 'runtime_sha256': '8568598c85a6df4f0043f82836cd89842af72d3e7ab56d45069d16252845f7ff', 'model_sha256': '6cbdc354dc8ced2d62938f63a0bee1bcccc71757e535d416df4c41f420e00bcf', 'required_runtime_keys': ['drtp_sampler_state', 'environment_states', 'episode_counts', 'graph_obs', 'model_state', 'obs', 'optimizer_state', 'rng_state', 'share_obs', 'update'], 'required_keys_present': True, 'update': 1, 'probe_output': {'probe_id': 'P2_reload_probe', 'output': [0.0, 1.0, 0.0]}, 'reload_process': 'independent child process loaded runtime checkpoint from disk', 'parameter_checksum_exact': True, 'probe_reproduced': True, 'pass': True}`.
- Probe legality: `{'protocol': 'DRTP-S1R-P2-PROBE-V1', 'classification': 'actor_legal', 'source': 'telemetry_native_t0 actor_view obs/share_obs/graph', 'privileged_simulator_state_in_probe': False, 'input_fields': ['obs', 'share_obs', 'graph_node_feat', 'graph_edge_feat', 'graph_adj', 'graph_relation_adj', 'graph_role'], 'output_reloaded': {'probe_id': 'P2_reload_probe', 'output': [0.0, 1.0, 0.0]}, 'pass': True}`.

`P3 G/B REFERENCE STARTED = NO`

`STOP CONFIRMED`
