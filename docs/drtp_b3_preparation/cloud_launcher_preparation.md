# B3 cloud-launch preparation

No launcher is executable at this stage. The declarative launch manifest is
`configs/drtp_b3_cloud_launch_manifest.json` and remains
`launch_status: NOT_AUTHORIZED`.

On explicit authorization only, the cloud job must launch the frozen original
`utr_sg` and `drtp_sg` runs for the three paired seeds with:

- six total 1,000,192-step trajectories;
- milestones only at updates 976, 1953, 2930, and 3907;
- B2 read-only telemetry enabled;
- strict seed assertions covering requested seed, `cfg.seed`, sampler RNG,
  runtime RNG, and telemetry seed;
- a new output root; no reuse of A-line or prior B-line run directories;
- development-only tape `e01c905b…7107ce9ed` for diagnostic evaluation;
- an automatic shutdown only after the authorized training, evaluation, and
  aggregation all return zero.

No command in this document starts a process.
