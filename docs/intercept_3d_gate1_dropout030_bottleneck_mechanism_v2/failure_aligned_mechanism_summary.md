# Failure-Aligned Mechanism Evidence

Generated: 2026-07-18T22:09:39

## Inputs

- Episode CSV: `results/intercept_3d_gate1_dropout030_bottleneck_5seed_formal/checkpoint_sweep/test_episode_metrics.csv`
- Selection CSV: `results/intercept_3d_gate1_dropout030_bottleneck_5seed_formal/checkpoint_sweep/validation_selected_checkpoints.csv`

## Representative Case Rule

The case is selected automatically from matched `single` and `multi_relation` test episodes.
The script computes a positive case score from recovery-probability gain and capped recovery-step gain, then chooses the candidate closest to the median positive score. This avoids hand-picking the largest gap.

```text
positive_candidates = 285
median_positive_case_score = 314
selected_case_score = 314
```

## Selected Episode

- `single` seed 0 episode 11: recovered=0.0, recovery_steps=220.0, success=0.0, timeout=1.0
- `multi_relation` seed 0 episode 11: recovered=1.0, recovery_steps=6.0, success=1.0, timeout=0.0

## Outputs

- Curves CSV: `results/intercept_3d_gate1_dropout030_bottleneck_mechanism_v2/failure_aligned_curves.csv`
- Case CSV: `results/intercept_3d_gate1_dropout030_bottleneck_mechanism_v2/representative_case_replay.csv`
- Curves figure: `results/intercept_3d_gate1_dropout030_bottleneck_mechanism_v2/failure_aligned_mechanism_curves.png`
- Case figure: `results/intercept_3d_gate1_dropout030_bottleneck_mechanism_v2/representative_case_timeline.png`

## Curve Interpretation

- `recovery_cdf` uses all 500 test episodes per method and carries recovery state forward after episode termination.
- `tracking_rate_mean`, `connectivity_mean`, and `chain_closed_mean` are instantaneous means over episodes that still have per-step data at that relative time; use `n_available` to interpret late-time values.
- At failure time `relative_step=0`, all methods have `n_episode=500`.
- By `relative_step=220`, recovery CDF matches the formal test result: `no_graph=0.342`, `single=0.518`, and `multi_relation=0.962`.
- The mechanism signal is therefore not only a higher final recovery rate; the multi-relation policy recovers much earlier after relay failure.

## Use Boundary

Use these figures to explain the completed five-seed formal result. They are not a new training result and should not be used to tune model checkpoints.
