# Post-Gate-1 Seed 3/4 Source Generation Summary

Last updated: 2026-07-18

## Purpose

This run closes the five-seed blocker identified in `docs/post_gate1_five_seed_launch_plan.md`.

Before this step, `no_graph`, `single`, and `multi_relation` had post-Gate-1 60-update checkpoint snapshots for seeds `0, 1, 2`, but seeds `3` and `4` were missing.

## Source Generation Policy

Seeds `3` and `4` were generated with the same predefined staged source budget:

```text
BC episodes = 200
BC epochs = 80
nominal PPO updates = 60
topology curriculum updates = 20
post-Gate-1 continuation updates = 60
save interval = 10
target policy = straight
strict target sensing = true
agent target-information bottleneck = true
communication dropout random = [0.00, 0.30]
message delay random = [0, 2]
node failure probability = 1.0
node failure start = 40
node failure duration = 80
```

Generated staged sources:

```text
results/intercept_3d_formal_seed34_source_generation/
```

Generated post-Gate-1 checkpoint snapshots:

```text
results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/
```

## Current Five-Seed Snapshot Inventory

| Method | Seed 0 | Seed 1 | Seed 2 | Seed 3 | Seed 4 |
|---|---|---|---|---|---|
| `no_graph` | 6 snapshots | 6 snapshots | 6 snapshots | 6 snapshots | 6 snapshots |
| `single` | 6 snapshots | 6 snapshots | 6 snapshots | 6 snapshots | 6 snapshots |
| `multi_relation` | 6 snapshots | 6 snapshots | 6 snapshots | 6 snapshots | 6 snapshots |

Each method/seed directory contains:

```text
actor_critic_update_0010.pt
actor_critic_update_0020.pt
actor_critic_update_0030.pt
actor_critic_update_0040.pt
actor_critic_update_0050.pt
actor_critic_update_0060.pt
actor_critic_best.pt
actor_critic_latest.pt
```

## Quality Notes

- `single` and `multi_relation` seed `3/4` showed normal online smoke behavior during source and post-Gate continuation.
- `no_graph` seed `3/4` remains weak and seed-sensitive under strict sensing, matching earlier `no_graph` diagnostics. This should be reported as baseline variance, not repaired seed-by-seed.
- The source policy is now frozen for the first five-seed formal attempt unless all methods/seeds are regenerated under a new predefined policy.

## Decision

The missing seed `3/4` checkpoint blocker is closed.

Next step:

Run a five-seed checkpoint-sweep integration diagnostic, then launch the formal validation/test split if the sweep path and safety selection pass.

