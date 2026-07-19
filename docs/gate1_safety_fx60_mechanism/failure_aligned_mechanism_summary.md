# Failure-Aligned Mechanism Evidence

Generated: 2026-07-19T06:01:45

## Inputs

- Episode CSV: `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/checkpoint_sweep_fixed_update60_test/merged/test_episode_metrics.csv`
- Selection CSV: `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/checkpoint_sweep_fixed_update60_test/merged/fixed_update60_selected_checkpoints.csv`

## Representative Case Rule

The case is selected automatically from matched `single` and `multi_relation` test episodes.
The script computes a positive case score from recovery-probability gain and capped recovery-step gain, then chooses the candidate closest to the median positive score. This avoids hand-picking the largest gap.

```text
positive_candidates = 245
median_positive_case_score = 315
selected_case_score = 315
```

## Selected Episode

- `single` seed 1 episode 16: recovered=0.0, recovery_steps=220.0, success=0.0, timeout=1.0
- `multi_relation` seed 1 episode 16: recovered=1.0, recovery_steps=5.0, success=1.0, timeout=0.0

## Outputs

- Curves CSV: `results/gate1_safety_fx60_mechanism/failure_aligned_curves.csv`
- Case CSV: `results/gate1_safety_fx60_mechanism/representative_case_replay.csv`
- Curves figure: `results/gate1_safety_fx60_mechanism/failure_aligned_mechanism_curves.png`
- Case figure: `results/gate1_safety_fx60_mechanism/representative_case_timeline.png`

## Use Boundary

Use these figures to explain the completed five-seed formal result. They are not a new training result and should not be used to tune model checkpoints.
