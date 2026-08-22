# DRTP-DIV-A0 — Optimization Timeline

## Frozen windows

The audit uses the predeclared windows 0–0.25M, 0.25–0.5M, 0.5–1M, 1–2M,
2–3M, and 3–10M. It reports every available update in each window; no update
or seed is removed.

## Findings

There is no common PPO failure signature unique to weak DRTP seeds before their
later weak final performance.

* In 0–0.25M, weak-seed KL was 0.0009 and 0.0010, within the strong-seed range
  0.0009–0.0011. Weak-seed clip fraction was 0.0047 and 0.0072, also within
  the strong range 0.0035–0.0067.
* In 0.5–1M, weak-seed gradient norms were 2.92 and 2.48; strong seeds were
  2.93, 2.76, and 2.86. Explained variance was similarly high for both classes.
* In 1–2M, strong seeds had *larger* gradient norms (4.34–5.69) than weak
  seeds (3.25–3.74), while weak seeds were not distinguished by KL, clipping,
  value loss, or explained variance.
* The first broad separation in logged internal reward occurs by 0.5–1M:
  weak DRTP seeds average 0.1105 and 0.0942, versus 0.1218–0.1314 for the
  three strong seeds. This is a learning-outcome separation, not a diagnostic
  proof of a PPO instability mechanism.

Figure A and `optimization_timeline.csv` provide the full descriptive trace.

## H1 assessment

**H1 — optimization divergence first: not supported.** The available PPO
telemetry does not identify a repeated KL, clip, entropy, gradient, value-loss,
or explained-variance abnormality that temporally precedes weak performance in
both weak seeds.

