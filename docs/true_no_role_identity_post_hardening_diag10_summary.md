# True No-Role-Identity Post-Hardening Diagnostic

Last updated: 2026-07-22

## Purpose

After the 2026-07-19 `no_role_identity` hardening, the actor now removes explicit role indicators from:

- local observation role fields;
- graph-node role fields;
- role embeddings;
- role-pair message inputs.

This diagnostic checks whether the hardened no-role semantics create a meaningful performance difference before spending resources on a formal retraining run.

## Protocol

This is a small diagnostic only.

Common evaluation settings:

```text
training seeds = [0, 1, 2]
episodes per seed/scenario = 10
base seed = 260000
target policy = straight
strict_target_sensing = True
agent_target_info_bottleneck = True
scenarios = [dropout030_relay_failure, scout_failure]
```

Compared variants:

```text
full_update60:
  checkpoint = results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed*/actor_critic_update_0060.pt
  graph_input_ablation = none

true_no_role_identity_old_ckpt:
  checkpoint = results/intercept_3d_no_role_identity_topology_formal/runs/multi_relation/bc_ppo_seed*/actor_critic_best.pt
  graph_input_ablation = no_role_identity
```

Important boundary:

```text
The no-role checkpoints were trained before the 2026-07-19 hardening.
This diagnostic evaluates them under the new hardened no-role inference semantics.
It is not a formal paper result and does not replace retraining the no-role ablation under the hardened semantics.
```

## Results

| Scenario | Variant | Recovery | Timeout | Collision | Steps | Tracking during failure | Chain during failure |
|---|---|---:|---:|---:|---:|---:|---:|
| dropout030_relay_failure | full_update60 | 76.7% | 23.3% | 0.0% | 95.7 | 80.3% | 11.6% |
| dropout030_relay_failure | true_no_role_identity_old_ckpt | 50.0% | 50.0% | 0.0% | 153.2 | 56.9% | 7.0% |
| scout_failure | full_update60 | 86.7% | 13.3% | 0.0% | 74.4 | 88.8% | 13.0% |
| scout_failure | true_no_role_identity_old_ckpt | 50.0% | 50.0% | 0.0% | 153.3 | 56.7% | 6.9% |

Seed-mean full-minus-no-role recovery deltas:

```text
dropout030_relay_failure: +26.7 pp
scout_failure: +36.7 pp
```

## Interpretation

- The hardened no-role semantics produce a clear diagnostic degradation under both relay and scout failure.
- The result supports promoting true `no_role_identity` to a formal retraining ablation if the manuscript needs a stronger role-identity mechanism claim.
- Because the no-role checkpoints were trained before the hardening, this result should be treated as a go/no-go diagnostic, not manuscript-level evidence.

## Artifacts

- No-role diagnostic episodes: `results/true_no_role_identity_post_hardening_eval_diag10/episode_metrics.csv`
- No-role diagnostic summary: `results/true_no_role_identity_post_hardening_eval_diag10/summary.md`
- Full reference checkpoint summary: `results/true_no_role_identity_post_hardening_full_reference_diag10/test_checkpoint_summary.csv`
- Full reference selected checkpoints: `results/true_no_role_identity_post_hardening_full_reference_diag10/test_selected_checkpoints.csv`
