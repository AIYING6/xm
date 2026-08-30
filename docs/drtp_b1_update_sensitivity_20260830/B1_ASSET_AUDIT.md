# B1 source-asset audit

The local archives contain the required paired runtime checkpoints:

| cohort | archive | seeds | frozen runtime checkpoint |
| --- | --- | --- | --- |
| formal positive | `drtp_utr_q2_paired_5seed_cloud_10way.tar.gz` | 2301--2305 | 500k |
| independent reversal | `drtp_snr_q2_mechanism_comparator_10way_results.tar.gz` | 2401--2405 | 500k |
| Stable-R1 mixed | `drtp_stable_r1_1m_results.tar.gz` | 3001--3005 | 500k |
| B5 mixed | `drtp_b5_observational.tar.gz` | 3601--3605 | 500k |

For every seed, both `utr_sg` and `drtp_sg` provide strict runtime state,
including model, optimizer, environment, sampler, observation, and RNG state.
The cloud asset package should contain only these 40 runtime checkpoints,
source manifests, and frozen endpoint labels; raw telemetry and redundant
checkpoints need not be uploaded.

The 0.5M choice is uniform across cohorts and avoids checkpoint selection.
It is before the clear 3001 collapse at 0.75M and before the final B5 3605
failure. It is diagnostic, not checkpoint promotion.
