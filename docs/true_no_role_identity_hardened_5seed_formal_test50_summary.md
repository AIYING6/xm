# Hardened True No-Role-Identity Five-Seed Formal Test50 Summary

Last updated: 2026-07-22

## Purpose

Promote `no_role_identity` from a three-seed development diagnostic to a paper-facing formal candidate because role identity is now treated as a main mechanism contribution.

This experiment asks whether explicit symbolic role identity helps recovery after relay failure, beyond physical capability heterogeneity.

## Ablation Semantics

`graph_input_ablation = no_role_identity` removes explicit symbolic role identity from:

- actor local observation role one-hot fields;
- graph node role one-hot fields;
- actor role embeddings;
- role-pair message-gate role inputs.

Physical heterogeneity remains available through dynamics, sensing, communication, and weapon/capability features.

## Protocol

Source training:

```text
source root = results/true_no_role_identity_hardened_5seed_formal_source
seeds = 0, 1, 2, 3, 4
graph_encoder = multi_relation
graph_input_ablation = no_role_identity
hidden_dim = 128
BC episodes = 120
BC epochs = 20
nominal PPO updates = 20
topology curriculum updates = 10
```

Strict bottleneck continuation:

```text
strict root = results/true_no_role_identity_hardened_5seed_strict_update60_formal_candidate
updates = 60
save interval = 10
validation episodes = 20 per seed
validation base seed = 390000
scenario = dropout030_relay_failure
strict_target_sensing = True
agent_target_info_bottleneck = True
```

Final test:

```text
test root = results/true_no_role_identity_hardened_5seed_update60_formal_test50
test episodes = 50 per seed
test base seed = 391000
matched full reference = full multi-relation actor_critic_update_0060.pt
```

## Selected No-Role Checkpoints

| Train seed | Selected update | Validation recovery | Validation collision | Constraint violation |
|---:|---:|---:|---:|---:|
| 0 | 10 | 55.0% | 0.0% | 0.0% |
| 1 | 60 | 80.0% | 0.0% | 0.0% |
| 2 | 60 | 0.0% | 0.0% | 40.0% |
| 3 | 20 | 100.0% | 0.0% | 0.0% |
| 4 | 40 | 80.0% | 0.0% | 0.0% |

## Seed-Level Test Result

| Variant | Train seed | Recovery | Timeout | Collision | Constraint violation | Steps | Tracking during failure | Chain during failure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| No role identity | 0 | 40.0% | 60.0% | 0.0% | 0.0% | 174.4 | 27.3% | 5.8% |
| No role identity | 1 | 66.0% | 32.0% | 0.0% | 2.0% | 118.6 | 22.4% | 10.0% |
| No role identity | 2 | 2.0% | 60.0% | 0.0% | 38.0% | 254.2 | 1.0% | 0.3% |
| No role identity | 3 | 88.0% | 12.0% | 0.0% | 0.0% | 71.3 | 45.9% | 13.7% |
| No role identity | 4 | 88.0% | 12.0% | 0.0% | 0.0% | 71.5 | 87.2% | 13.7% |
| Full multi-relation | 0 | 50.0% | 50.0% | 0.0% | 0.0% | 152.7 | 57.8% | 8.1% |
| Full multi-relation | 1 | 92.0% | 8.0% | 0.0% | 0.0% | 63.2 | 93.2% | 13.6% |
| Full multi-relation | 2 | 98.0% | 2.0% | 0.0% | 0.0% | 49.8 | 98.3% | 15.6% |
| Full multi-relation | 3 | 96.0% | 4.0% | 0.0% | 0.0% | 78.2 | 70.6% | 11.8% |
| Full multi-relation | 4 | 100.0% | 0.0% | 0.0% | 0.0% | 45.7 | 62.2% | 15.5% |

## Aggregate Test Result

| Variant | Recovery | Timeout | Collision | Constraint violation | Steps | Tracking during failure | Chain during failure | Connectivity during failure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| No role identity | 56.8% | 35.2% | 0.0% | 8.0% | 138.0 | 36.8% | 8.7% | 15.1% |
| Full multi-relation | 87.2% | 12.8% | 0.0% | 0.0% | 77.9 | 76.4% | 12.9% | 21.9% |

## Seed-Aware Statistics

Hierarchical bootstrap statistics are recorded in:

```text
results/true_no_role_identity_hardened_5seed_update60_formal_test50/seed_aware_stats/
docs/true_no_role_identity_hardened_5seed_seed_aware_stats/
```

| Metric | No-role | Full | Delta full - no-role | 95% CI |
|---|---:|---:|---:|---:|
| Recovery | 56.8% | 87.2% | +30.4 pp | [+7.2, +64.4] pp |
| Timeout | 35.2% | 12.8% | -22.4 pp | [-41.6, -7.2] pp |
| Restricted mean recovery steps | 97.99 | 37.93 | -60.06 | [-135.92, -6.15] |
| Tracking during failure | 36.8% | 76.4% | +39.7 pp | [+3.1, +75.5] pp |
| Connectivity during failure | 15.1% | 21.9% | +6.8 pp | [+1.3, +13.4] pp |
| Chain closure during failure | 8.7% | 12.9% | +4.2 pp | [-0.2, +10.1] pp |

## Interpretation

- Explicit symbolic role identity improves post-failure recovery under strict sensing and relay failure.
- The formal result is more nuanced than the dev20 diagnostic: no-role can solve some seeds, especially seeds 3 and 4, but it is less reliable and much weaker on seed 2.
- The strongest claims are recovery probability, timeout reduction, restricted recovery time, tracking during failure, and connectivity during failure.
- Chain-closure rate improves in mean but its confidence interval slightly crosses zero, so it should be reported as supportive rather than decisive.
- Because the no-role ablation preserves physical heterogeneity, this supports the value of symbolic role conditioning and role-aware message passing rather than merely showing that heterogeneous platforms matter.

## Paper Use

Recommended use:

- Main or supplemental mechanism table for the role-identity contribution.
- Report seed-level scatter; do not show only mean bars.
- Phrase the claim as improved reliability and recovery probability, not as absolute necessity of role identity.

Recommended wording:

> Removing explicit role identity while preserving platform heterogeneity reduces post-failure recovery from `87.2%` to `56.8%`; the seed-aware recovery delta is `+30.4 pp` with 95% CI `[+7.2, +64.4] pp`.

## Artifacts

- Formal source root: `results/true_no_role_identity_hardened_5seed_formal_source/`
- Strict update60 checkpoints: `results/true_no_role_identity_hardened_5seed_strict_update60_formal_candidate/`
- Test50 no-role output: `results/true_no_role_identity_hardened_5seed_update60_formal_test50/no_role_identity/`
- Test50 full reference: `results/true_no_role_identity_hardened_5seed_update60_formal_test50/full_multi_reference/`
- Combined summary: `results/true_no_role_identity_hardened_5seed_update60_formal_test50/combined_summary/`
- Seed-aware stats: `results/true_no_role_identity_hardened_5seed_update60_formal_test50/seed_aware_stats/`
