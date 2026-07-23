# Gate 1 Safety Fixed-Update-60 No-Curriculum Seed-0 Diagnostic

Last updated: 2026-07-22

## Purpose

This diagnostic checks whether the topology curriculum can be claimed as an independent mechanism contribution in the hardened strict-sensing relay-failure package.

The run is development evidence only. It uses one training seed and a 30-episode validation diagnostic, so it must not be promoted to a paper table.

## Protocol

Source checkpoint:

- `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed0/actor_critic_latest.pt`

No-curriculum continuation:

- method: `multi_relation`
- seed: `0`
- updates: `60`
- strict target sensing: enabled
- agent target-information bottleneck: enabled
- safety proximity auxiliary: `distance=1000`, `weight=0.3`
- communication range randomization: fixed to `1.0`
- communication dropout randomization: fixed to `0.30`
- message delay randomization: fixed to `0`
- radar dropout randomization: fixed to `0`
- node failure probability: `1.0`
- node failure start: fixed to step `40`
- node failure duration: fixed to `80`

Evaluation:

- scenario: `dropout030_relay_failure`
- validation base seed: `340000`
- episodes per checkpoint: `30`
- checkpoints: updates `10, 20, 30, 40, 50, 60`
- matched comparison: original curriculum-trained seed-0 checkpoints from `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/`

## Result

| Protocol | Best update | Recovery | Tracking | Chain closed | Timeout | Collision |
|---|---:|---:|---:|---:|---:|---:|
| No curriculum, fixed full difficulty | 50 | 70.0% | 75.0% | 11.4% | 30.0% | 0.0% |
| Original topology curriculum | 60 | 63.3% | 68.8% | 10.5% | 36.7% | 0.0% |

Fixed update-60 comparison on the same 30 episodes:

| Protocol | Recovery | Tracking | Chain closed | Timeout | Collision |
|---|---:|---:|---:|---:|---:|
| No curriculum, fixed full difficulty | 70.0% | 74.6% | 11.4% | 30.0% | 0.0% |
| Original topology curriculum | 63.3% | 68.8% | 10.5% | 36.7% | 0.0% |

## Interpretation

The seed-0 diagnostic does not support claiming topology curriculum as an independently proven main contribution. Under this seed and diagnostic split, the fixed-difficulty no-curriculum run is at least competitive with the original curriculum run.

This is not enough to conclude that curriculum is useless, because:

- only one training seed was tested;
- the no-curriculum setting is matched to the final test scenario rather than broad topology randomization;
- the diagnostic evaluates only 30 matched episodes per checkpoint.

However, it is enough to set the paper boundary:

- keep the main contribution centered on multi-relation role graphs and role-pair-conditioned message passing;
- describe topology curriculum as a training protocol unless a three-seed and then five-seed no-curriculum ablation proves an independent benefit;
- do not list curriculum as a primary contribution in the current manuscript without the stronger ablation.

## Artifacts

- Training run: `results/gate1_safety_fx60_no_curriculum_seed0_dev60/runs/multi_relation/bc_ppo_seed0/`
- No-curriculum sweep: `results/gate1_safety_fx60_no_curriculum_seed0_dev60_sweep_eval30/no_curriculum/validation_checkpoint_summary.csv`
- Curriculum matched sweep: `results/gate1_safety_fx60_no_curriculum_seed0_dev60_sweep_eval30/curriculum/validation_checkpoint_summary.csv`

## Next Decision

Recommended next experimental step:

Run a three-seed development no-curriculum comparison for `multi_relation` only, using the same fixed full-difficulty setting and the same checkpoint-sweep diagnostic. If the three-seed result still shows no clear curriculum advantage, remove topology curriculum from the paper contribution list and keep it as training support.
