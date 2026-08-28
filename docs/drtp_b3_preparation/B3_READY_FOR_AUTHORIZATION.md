# B3 readiness report

Status: `B3_READY_FOR_AUTHORIZATION`.

This is a preparation decision, not a training authorization. No B3 training,
evaluation, checkpoint, or algorithm variant has been launched locally or in
the cloud.

The source freeze is commit `79b0f5cc30dd74f042e3a2c7c5961c5095c09b01`.

## Readiness checklist

| Requirement | Evidence | Status |
|---|---|---|
| New paired seeds | 2701–2703 have no scientific-result, debug, smoke, manifest, path, or Git-history seed-semantic hit | PASS |
| Historical time scale | first persistent paired training-return proxy cohort separation ends at 0.384M steps | PASS: 1M is a meaningful falsification horizon |
| Read-only telemetry | OFF/ON exact 256-transition action/reward/termination/PPO/sampler/model equivalence | PASS |
| RNG and resume | telemetry writer does not consume training RNG; mid-window save/resume is exact | PASS |
| Development tape | five fixed diagnostic conditions, IDs 520000–520099, logical hash `e01c905b04257fd6b373dbbe3ca25cf5f0dece0864e89b6713bd7647107ce9ed` | PASS |
| Scientific contract | original UTR/DRTP only; fixed 1M budget and predeclared 1M/3M gates | PASS |
| Cloud launch guard | manifest is declarative and `NOT_AUTHORIZED` | PASS |

## Recommended execution envelope after separate authorization

- **First-stage budget:** 6 runs × 1,000,192 = **6,001,152 environment
  steps**. There is no 2M stage.
- **Conditional extension:** only a `MECHANISM_CANDIDATE` permits strict
  continuation of the same six states to 3M; incremental cost would be
  12,002,304 steps. A 10M run is not authorized.
- **Development evaluation:** 3,000 episodes at each frozen diagnostic
  evaluation sweep (2 methods × 3 seeds × 5 conditions × 100 episodes).
- **Maximum safe parallelism:** **6** on one 12-GB RTX 3080 Ti with roughly
  20 CPU cores and 30 GB RAM. This limit is deliberately lower than
  GPU-memory-only concurrency: B3 emits JSONL behavior telemetry and must not
  starve CPU scheduling or disk I/O.
- **Disk estimate:** B2 measured 681,111 bytes for 212 event rows, about
  3.21 KB per row. A conservative 1M-step upper envelope is about 0.32M
  event rows per run (81 logged steps in a 260-step episode), or roughly
  1.0 GB event JSONL per run. Budget **at least 20 GB free** for six runs,
  episode summaries, PPO/sampler logs, runtime checkpoints, diagnostics, and
  margin; 50 GB cloud data storage is adequate.

## Remaining blockers

There is **no technical blocker**. The only blocker is the required explicit
human authorization to start six cloud-only B3 development trajectories.

## Frozen decision boundary

At 1M, absence of a repeatable candidate chain is
`MECHANISM_HYPOTHESIS_NO_GO`, not a reason to tune or extend by default. B3
cannot alter A-line results, delete cohorts, or delay A-line submission.
