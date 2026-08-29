# S0 S1 cloud resource estimate

Status: `ESTIMATE_ONLY — NO CLOUD JOB CREATED`

## Frozen S1 workload

`UTR / original DRTP / DRTP-TR × 2901/2902/2903 × 499,968 steps` equals nine
trajectories and `4,499,712` environment steps. All runs retain the 0.25M and
0.5M milestones and read-only sampler/telemetry logs.

## Conservative cloud recommendation

For a single RTX 3080 Ti (12 GB) with 12--20 CPU cores:

- maximum safe initial concurrency: **9** processes (all nine trajectories);
- `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, and training CPU thread budget 12;
- reserve at least **8 GB** free data-disk capacity before launch; expected
  outputs are approximately 1--3 GB before archival compression, based on the
  existing 6×1M B3 archive (0.82 GB compressed) and 10×0.5M H2 archive
  (0.69 GB compressed);
- monitor the first five minutes for OOM, worker crashes, and seed/config
  provenance. Any technical interruption is a technical event, not a result
  reason to change constants.

Concurrency is a scheduling setting only. It must not alter seeds, the frozen
method, tape, budget, evaluator, or decision thresholds.
