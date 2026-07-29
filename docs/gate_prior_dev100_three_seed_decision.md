# Gate-Prior Dev100 Three-Seed Decision

Last updated: 2026-07-29

## Purpose

This document completes the gate-prior development decision. The question is not
whether to keep tuning gates indefinitely, but whether the current
`role_gate_prior_strength=0.4` candidate is strong enough to replace the
original EA-RG-MAPPO candidate for the next formal-budget study.

## Protocol

Both original EA and gate-prior EA use:

- Strong post-loss recovery protocol.
- Balanced offset BC initialization.
- Dropout `0.30`, message delay `2`.
- Strict target sensing and target-info bottleneck.
- Relay failure agent `1`.
- Random failure start `[25, 70]`, duration `80`.
- `min_success_step=80`.
- Post-loss chain reclosure reward `0.5`.
- Safety proximity distance `2500`, penalty `0.5`.
- PPO candidates from checkpoints 20/40/60/80/100.
- Suite-level checkpoint selection over four failure-timing scenarios.
- Selection metric: delayed recovery with `delayed_recovery_min_step=80`,
  success weight `0`.

## Selected-Checkpoint Results

| Method | Seed | Update | Success | Post-loss recovery | Delayed recovery | Collision |
|---|---:|---:|---:|---:|---:|---:|
| Original EA | 0 | 40 | 0.525 | 0.675 | 0.200 | 0.000 |
| Original EA | 1 | 20 | 0.725 | 0.825 | 0.325 | 0.100 |
| Original EA | 2 | 100 | 0.625 | 0.675 | 0.425 | 0.000 |
| Original EA mean | - | - | 0.625 | 0.725 | 0.317 | 0.033 |
| Gate-prior EA | 0 | 60 | 0.925 | 0.950 | 0.525 | 0.000 |
| Gate-prior EA | 1 | 60 | 0.750 | 0.825 | 0.425 | 0.000 |
| Gate-prior EA | 2 | 20 | 0.675 | 0.775 | 0.300 | 0.000 |
| Gate-prior EA mean | - | - | 0.783 | 0.850 | 0.417 | 0.000 |

## Differences

Gate-prior versus original EA:

- Success: `+0.158`.
- Post-loss recovery: `+0.125`.
- Delayed recovery: `+0.100`.
- Collision: `-0.033`.

Seed-level caveat:

- Gate-prior improves success and recovery on all three seeds.
- Gate-prior improves delayed recovery on seeds 0 and 1.
- Original EA has higher delayed recovery on seed2 (`0.425` versus `0.300`), but
  gate-prior still has higher success and post-loss recovery on seed2.

## Mechanism Evidence

Seed0 diagnostics show that gate-prior also strengthens the role-pair mechanism:

- Original EA gate mean/max absolute deviation from 0.5:
  `0.005914 / 0.060720`.
- Gate-prior gate mean/max absolute deviation from 0.5:
  `0.025573 / 0.121487`.

Gate-prior also increases task-support and perception relation attention in the
diagnostic episodes:

- Task-support attention: `0.0111 -> 0.0228`.
- Perception attention: `0.0382 -> 0.0628`.
- Diagnostic success episodes: `12/20 -> 18/20`.

## Decision

Promote gate-prior EA as the current main EA-RG-MAPPO-S candidate for the next
formal-budget study.

Stop further gate-parameter optimization. The current candidate is good enough
to move forward, but the seed2 delayed-recovery caveat means it should still be
validated under the formal five-seed budget before making final paper claims.

## Frozen Candidate

Current main candidate:

- `graph_encoder=multi_relation`
- `role_gate_prior_strength=0.4`
- `graph_relation_ablation=none`
- `graph_message_ablation=none`
- `graph_input_ablation=none`
- `chain_aux_coef=0.0`

The next step is not to tune this candidate again. The next step is to freeze
the common protocol and start the formal budget study.
