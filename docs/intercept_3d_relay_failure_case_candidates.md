# Relay-Failure Case Candidates

Generated: 2026-07-16T21:05:02

These matched episodes are candidates for later trajectory and timeline plots. They are not new experiments; they are selected from the formal relay-failure evaluation CSV.

| Rank | Train seed | Episode | Single recovered | Multi recovered | Recovery steps single/multi | Step gain | Tracking during failure single/multi | Connectivity during failure single/multi |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0 | 0 | 0 | 1 | 220.0 / 8.0 | 212.0 | 0.158 / 1.000 | 0.329 / 0.407 |
| 2 | 0 | 3 | 0 | 1 | 220.0 / 8.0 | 212.0 | 0.150 / 1.000 | 0.342 / 0.407 |
| 3 | 2 | 0 | 0 | 1 | 220.0 / 8.0 | 212.0 | 0.167 / 1.000 | 0.275 / 0.407 |
| 4 | 2 | 3 | 0 | 1 | 220.0 / 8.0 | 212.0 | 0.154 / 1.000 | 0.338 / 0.407 |
| 5 | 1 | 10 | 0 | 1 | 220.0 / 9.0 | 211.0 | 0.154 / 1.000 | 0.342 / 0.400 |
| 6 | 1 | 0 | 0 | 1 | 220.0 / 10.0 | 210.0 | 0.154 / 0.970 | 0.342 / 0.394 |
| 7 | 1 | 3 | 0 | 1 | 220.0 / 11.0 | 209.0 | 0.154 / 1.000 | 0.342 / 0.389 |
| 8 | 0 | 25 | 1 | 1 | 8.0 / 7.0 | 1.0 | 1.000 / 1.000 | 0.407 / 0.417 |
| 9 | 2 | 10 | 1 | 1 | 8.0 / 7.0 | 1.0 | 1.000 / 1.000 | 0.407 / 0.417 |
| 10 | 2 | 25 | 1 | 1 | 8.0 / 7.0 | 1.0 | 1.000 / 1.000 | 0.407 / 0.417 |

## Next Use

Use the top candidates to replay both checkpoints with per-step logging, then draw a timeline of node failure, tracking loss/recovery, communication connectivity, and kill-chain closure.
