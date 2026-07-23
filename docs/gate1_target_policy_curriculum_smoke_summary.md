# Target-Policy Curriculum Smoke Summary

Date: 2026-07-22

## Purpose

This smoke validates the new nominal maneuvering-target curriculum entry point.

The script is intended for scenario-depth development only. It does not enable strict sensing, target-information bottlenecks, or node failure.

## New Script

- `scripts/run_3d_target_policy_curriculum.py`

The script chains multiple target-policy fine-tuning stages, for example:

```text
straight source checkpoint -> weaving_tiny -> weaving_mild
```

Each stage resumes from the previous stage's final snapshot and writes separate stage directories:

```text
stage01_weaving_tiny/
stage02_weaving_mild/
```

## Smoke Protocol

- Method: `multi_relation`
- Seed: `0`
- Source checkpoint: mature straight-target safety fixed-update-60 checkpoint
- Stage policies: `weaving_tiny`, `weaving_mild`
- Stage updates: `1, 1`
- Hidden dimension: `64`
- Evaluation: final `weaving_mild` checkpoint, 2 episodes

Outputs:

- `results/gate1_target_policy_curriculum_smoke/`

## Result

The smoke passed:

- stage 1 loaded the mature straight-target source checkpoint;
- stage 2 loaded the stage-1 checkpoint with all tensors matched;
- the final stage-2 checkpoint was readable by `scripts/evaluate_ri_gmappo_3d.py`.

This validates the curriculum plumbing. It is not a performance result.

## Next Use

The next development run should use this script for a real but still small diagnostic:

```text
stage_policies = weaving_tiny, weaving_mild
stage_updates = 30,30 or 60,30
seeds = 0,1,2
graph_encoders = multi_relation
```

Only if `multi_relation` reaches robust nominal maneuvering-target success should the project add strict sensing and relay failure to the maneuvering-target route.
