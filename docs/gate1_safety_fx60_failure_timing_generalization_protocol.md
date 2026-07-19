# Gate 1 Safety Fixed-Update-60 Failure-Timing Generalization Protocol

Last updated: 2026-07-19

## Purpose

This protocol tests whether the current fixed-update-60 policy package only works for the trained relay-failure timing, or whether the multi-relation role graph remains robust when relay failure starts earlier or later.

This is a controlled scenario-depth extension. It does not add 4v2 red-blue self-play, missiles, JSBSim, or new target policies.

## Frozen Policy Rule

Use the existing fixed-update-60 safety-enabled checkpoints:

- `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed*/actor_critic_update_0060.pt`
- `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed*/actor_critic_update_0060.pt`
- `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed*/actor_critic_update_0060.pt`

Do not tune checkpoints or hyperparameters on the timing-generalization test scenarios.

## Scenarios

The scenario registry now includes:

| Scenario | Communication dropout | Failed node | Failure start | Duration | Purpose |
|---|---:|---:|---:|---:|---|
| `dropout030_relay_failure_early` | 0.30 | relay `1` | 25 | 80 | OOD early failure |
| `dropout030_relay_failure` | 0.30 | relay `1` | 40 | 80 | current fixed-budget main scenario |
| `dropout030_relay_failure_delayed` | 0.30 | relay `1` | 55 | 80 | OOD delayed failure |
| `dropout030_relay_failure_late` | 0.30 | relay `1` | 70 | 80 | late stress diagnostic only |

Optional non-dropout counterparts are also registered:

- `relay_failure_early`
- `relay_failure`
- `relay_failure_delayed`
- `relay_failure_late`

The paper-facing timing-generalization claim should prioritize the dropout scenarios because they match the current strict-sensing communication bottleneck.

## Recommended Evaluation Command

Run the full fixed-checkpoint timing-generalization evaluation for the currently valid primary timing scenarios:

```bash
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/evaluate_3d_checkpoint_sweep.py \
  --split test \
  --seeds 0 1 2 3 4 \
  --graph-encoders no_graph single multi_relation \
  --scenarios dropout030_relay_failure_early dropout030_relay_failure \
  --episodes 100 \
  --base-seed 260000 \
  --checkpoint-glob actor_critic_update_0060.pt \
  --no-graph-root results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph \
  --single-root results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single \
  --multi-root results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation \
  --strict-target-sensing \
  --agent-target-info-bottleneck \
  --out-dir results/gate1_safety_fx60_failure_timing_generalization \
  --device cpu
```

This evaluates:

- 3 methods;
- 5 training seeds;
- 2 timing scenarios;
- 100 matched episodes per seed-scenario-method;
- 3000 total episodes.

## Statistics

Use seed-aware paired statistics, not raw episode-level bootstrap.

For each timing scenario, compare:

- `multi_relation` vs `single`;
- `multi_relation` vs `no_graph`.

Primary metrics:

- post-failure chain recovery;
- restricted mean recovery steps;
- tracking during failure;
- chain-closed rate during failure;
- timeout;
- collision.

Recommended interpretation:

- If `multi_relation` stays above `single` on both early and nominal failure starts, the result supports limited timing robustness against earlier-than-nominal relay loss.
- If only the nominal scenario separates, keep the current main claim and report timing generalization as mixed.
- If the late stress diagnostic has many episodes ending before the failure window, do not use its failure-window tracking or chain-rate averages as primary evidence.

## Smoke Validation

A one-episode smoke run passed for:

- method: `multi_relation`;
- seed: `0`;
- scenario: `dropout030_relay_failure_early`;
- checkpoint: `actor_critic_update_0060.pt`;
- output: `results/gate1_safety_fx60_failure_timing_generalization_smoke/`.

The smoke result is interface validation only and must not be used as paper evidence.

A 5-episode-per-seed diagnostic with `late` start step 70 showed that many episodes terminate before the failure window contributes valid tracking/chain measurements. Therefore, `dropout030_relay_failure_delayed` with start step 55 is the preferred formal delayed-failure scenario, while start step 70 is retained only as a stress diagnostic.

After a second 5-episode-per-seed diagnostic, start step 55 showed the same metric-validity issue for the full method: many successful episodes ended before the delayed failure window. Therefore, the current formal timing-generalization candidate should use only `dropout030_relay_failure_early` and `dropout030_relay_failure`. Delayed or late failure should be revisited only if the environment later supports an evaluation mode that keeps episodes alive after early chain closure.

## Paper Use

This experiment can become a compact scenario-depth subsection if it gives a clear result:

> The learned multi-relation policy is evaluated without retraining under early, nominal, and late relay-failure onset times. This tests whether the recovery mechanism generalizes beyond the fixed failure time used in the main evidence package.

Do not present this as a new algorithmic contribution.
