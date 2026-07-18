# Gate 1 Post-Change Retraining Smoke Summary

Last updated: 2026-07-18

## Purpose

Check whether training remains executable after the Gate 1 communication-feasibility changes.

This is a tiny retraining smoke, not paper evidence.

## Protocol

Training:

- methods: `single`, `multi_relation`;
- seed: `0`;
- resume checkpoints: existing 60-update dropout-relay diagnostic checkpoints;
- updates: `3`;
- num envs: `1`;
- rollout steps: `16`;
- strict target sensing: enabled;
- agent target-information bottleneck: enabled;
- communication dropout training randomization: `0.00` to `0.30`;
- message delay training randomization: `0` to `2`;
- node-failure curriculum: enabled.

Output:

```text
results/intercept_3d_gate1_post_change_retrain_smoke/
```

Evaluation:

- scenario: `dropout030_relay_failure`;
- seed: `0`;
- episodes: `10`;
- checkpoint: `actor_critic_update_0003.pt`.

## Result

| Method | Success | Recovery | Timeout |
|---|---:|---:|---:|
| `single` | `90.0%` | `90.0%` | `10.0%` |
| `multi_relation` | `100.0%` | `100.0%` | `0.0%` |

## Interpretation

The new communication-feasible semantics do not break short PPO continuation training from existing checkpoints.

Because this smoke uses only one seed and three PPO updates, it must not be used as paper evidence. Its only decision value is that a larger post-Gate-1 retraining diagnostic is worth running.

## Next Decision

Run a small three-seed retraining diagnostic:

- methods: `single`, `multi_relation`;
- seeds: `0, 1, 2`;
- short budget first, then increase only if training remains stable;
- use validation checkpoint selection before any formal test expansion.
