# DRTP runtime and complexity plan

## Analytic complexity

For \(G=6\) non-nominal groups, reset selection is \(O(G)\); adaptation every 32 updates is \(O(G)\) plus the size of the completed-episode windows. The bounded-simplex projection uses a fixed 100-iteration bisection over six coordinates. DRTP adds no actor/critic parameters and does not change the PPO tensor graph.

## Measurement protocol

Do not benchmark the aborted 6-UAV run. After the final PLR and 6-UAV jobs finish, use completed run logs and one short, separately labelled implementation benchmark only if a timing field is absent. The benchmark must:

1. use the frozen environment and same GPU/CPU setting for UTR and DRTP;
2. execute a fixed short budget without evaluation or checkpoint selection;
3. report median wall-clock across repeated process launches, peak GPU memory, and the same policy parameter count;
4. label timing as implementation overhead, not task-performance evidence.

## Extraction checklist

| Quantity | Preferred source | Fallback |
|---|---|---|
| Policy parameters | model state dictionary | deterministic parameter-count script |
| Wall-clock / 1M steps | launcher/process timestamps | short matched benchmark |
| Peak GPU memory | `nvidia-smi` sampling or launcher telemetry | matched benchmark sampler |
| Sampler-update cost | sampler log timestamps/profiler | instrumented microbenchmark |
| Memory overhead | runtime state and sampler-state sizes | file-size audit |

The final manuscript should report the ratio to UTR on the same machine; it should not compare absolute timings across rented cards.

