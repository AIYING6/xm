# Gate 1 Safety Fixed-Update-60 No-Curriculum Three-Seed Diagnostic

Last updated: 2026-07-22

## Purpose

This diagnostic tests whether topology curriculum has enough independent evidence to be promoted from a training protocol to a paper contribution.

The answer from the current three-seed development run is no. The curriculum-trained policy remains valid as the main frozen evidence source, but the curriculum itself should not be claimed as a proven contribution.

## Protocol

Method:

- `multi_relation` only
- training seeds: `0, 1, 2`
- source checkpoints: `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed*/actor_critic_latest.pt`
- continuation budget: `60` PPO updates
- strict target sensing: enabled
- agent target-information bottleneck: enabled
- safety proximity auxiliary: `distance=1000`, `weight=0.3`

No-curriculum training setting:

- communication range fixed at `1.0`
- communication dropout fixed at `0.30`
- message delay fixed at `0`
- radar dropout fixed at `0`
- relay failure probability fixed at `1.0`
- relay failure starts at step `40`
- failure duration fixed at `80`

Matched comparison:

- original topology-curriculum checkpoints from `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/`
- same validation base seed: `340000`
- same checkpoint sweep: updates `10, 20, 30, 40, 50, 60`
- same diagnostic budget: `30` episodes per checkpoint and seed

## Validation-Selected Result

Each seed selects the checkpoint with the standard validation score.

| Protocol | Recovery | Seed recovery | Selected updates | Tracking | Chain closed | Timeout | Collision |
|---|---:|---:|---:|---:|---:|---:|---:|
| No curriculum | 88.9% +/- 16.4 | [70.0, 96.7, 100.0] | [50, 50, 50] | 90.6% | 14.3% | 11.1% | 0.0% |
| Topology curriculum | 87.8% +/- 21.2 | [63.3, 100.0, 100.0] | [60, 50, 60] | 89.4% | 14.2% | 12.2% | 0.0% |

No-curriculum minus curriculum:

- recovery: `+1.1 pp`
- tracking: `+1.2 pp`
- chain closure: `+0.1 pp`
- timeout: `-1.1 pp`

## Fixed-Update-60 Result

| Protocol | Recovery | Seed recovery | Tracking | Chain closed | Timeout | Collision |
|---|---:|---:|---:|---:|---:|---:|
| No curriculum | 85.6% +/- 15.0 | [70.0, 86.7, 100.0] | 87.7% | 13.6% | 14.4% | 0.0% |
| Topology curriculum | 87.8% +/- 21.2 | [63.3, 100.0, 100.0] | 89.4% | 14.2% | 12.2% | 0.0% |

No-curriculum minus curriculum:

- recovery: `-2.2 pp`
- tracking: `-1.7 pp`
- chain closure: `-0.6 pp`
- timeout: `+2.2 pp`

## Interpretation

The three-seed diagnostic does not justify promoting topology curriculum to a primary contribution:

- validation-selected performance is essentially tied;
- fixed-update-60 performance slightly favors curriculum, but the effect is small;
- both protocols have zero diagnostic collisions;
- the outcome is dominated by seed-level saturation on seeds `1` and `2`.

This is a useful negative result. It prevents an overclaim. The current manuscript should keep the contribution focused on:

1. strict-sensing relay-failure kill-chain recovery task;
2. multi-relation role graph;
3. role-pair-conditioned message passing.

Topology curriculum should be described as training support or implementation protocol unless a larger and more discriminative no-curriculum study is explicitly planned.

## Decision

Do not spend the five-seed formal budget on no-curriculum right now. The likely return is low because the three-seed diagnostic shows no clear independent curriculum benefit.

Recommended next experiment:

Strengthen the core method evidence instead:

- keep the fixed-update-60 main table frozen;
- add or improve mechanism visualizations and seed-level scatter for the existing graph/message ablations;
- if adding new training, prefer a harder graph-relation stressor that separates full multi-relation from single graph, rather than continuing to test curriculum in the same saturated setting.

## Artifacts

- No-curriculum runs: `results/gate1_safety_fx60_no_curriculum_3seed_dev60/runs/multi_relation/`
- Checkpoint sweeps: `results/gate1_safety_fx60_no_curriculum_3seed_dev60_sweep_eval30/`
- Aggregate CSV: `results/gate1_safety_fx60_no_curriculum_3seed_dev60_summary/aggregate_summary.csv`
- Aggregate JSON: `results/gate1_safety_fx60_no_curriculum_3seed_dev60_summary/aggregate_summary.json`
