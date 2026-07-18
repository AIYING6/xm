# Failure-Aligned Mechanism Evidence

Generated: 2026-07-18T21:18:54

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

- Curves CSV: `results/intercept_3d_gate1_mechanism_benchmark_one_ep/failure_aligned_curves.csv`
- Case CSV: `results/intercept_3d_gate1_mechanism_benchmark_one_ep/representative_case_replay.csv`
- Curves figure: `results/intercept_3d_gate1_mechanism_benchmark_one_ep/failure_aligned_mechanism_curves.png`
- Case figure: `results/intercept_3d_gate1_mechanism_benchmark_one_ep/representative_case_timeline.png`

## Use Boundary

Use these figures to explain the completed five-seed formal result. They are not a new training result and should not be used to tune model checkpoints.
