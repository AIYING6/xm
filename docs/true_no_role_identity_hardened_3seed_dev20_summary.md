# Hardened True No-Role-Identity Three-Seed Dev20 Summary

Last updated: 2026-07-22

## Purpose

Rerun the `no_role_identity` ablation after implementation hardening.

The old no-role checkpoints were trained before explicit actor-side role identity was fully removed. They can only support a diagnostic. This run verifies that the hardened no-role setting is trainable and checks whether removing explicit role labels degrades strict relay-failure recovery.

## Hardened Ablation Semantics

`graph_input_ablation = no_role_identity` removes explicit role labels from:

- local actor observation role one-hot fields;
- graph node role one-hot fields;
- actor role embeddings;
- role-pair message-gate role inputs.

Physical capability heterogeneity is preserved. This means the ablation removes symbolic role identity, not aircraft dynamics or sensor/communication capability differences.

## Protocol

Source training:

```text
out_dir = results/true_no_role_identity_hardened_3seed_dev_source
seeds = 0, 1, 2
graph_encoder = multi_relation
graph_input_ablation = no_role_identity
hidden_dim = 128
BC episodes = 120
BC epochs = 20
nominal PPO updates = 20
topology curriculum updates = 10
num_envs = 4
rollout_steps = 64
```

Strict bottleneck continuation:

```text
out_dir = results/true_no_role_identity_hardened_3seed_strict_dev20
updates = 20
save interval = 5
validation episodes = 10 per seed
test episodes = 10 per seed
scenario = dropout030_relay_failure
strict_target_sensing = True
agent_target_info_bottleneck = True
```

Full reference:

```text
out_dir = results/true_no_role_identity_hardened_3seed_dev20_full_reference_same_split
checkpoint = full multi-relation actor_critic_update_0060.pt
test episodes = 10 per seed
same test base seed = 385000
```

## Selected Checkpoints

| Train seed | Selected update | Validation recovery | Validation collision | Constraint violation |
|---:|---:|---:|---:|---:|
| 0 | 15 | 60.0% | 0.0% | 0.0% |
| 1 | 20 | 10.0% | 0.0% | 20.0% |
| 2 | 20 | 0.0% | 0.0% | 70.0% |

## Seed-Level Test Result

| Variant | Train seed | Recovery | Timeout | Collision | Steps | Tracking during failure | Chain during failure |
|---|---:|---:|---:|---:|---:|---:|---:|
| Hardened no-role-identity | 0 | 60.0% | 40.0% | 0.0% | 131.2 | 42.6% | 9.9% |
| Hardened no-role-identity | 1 | 0.0% | 90.0% | 0.0% | 259.6 | 1.3% | 0.0% |
| Hardened no-role-identity | 2 | 0.0% | 10.0% | 10.0% | 233.4 | 5.6% | 0.0% |
| Full multi-relation reference | 0 | 80.0% | 20.0% | 0.0% | 88.0 | 83.0% | 13.7% |
| Full multi-relation reference | 1 | 100.0% | 0.0% | 0.0% | 45.6 | 99.2% | 16.1% |
| Full multi-relation reference | 2 | 100.0% | 0.0% | 0.0% | 45.1 | 100.0% | 17.0% |

## Aggregate Test Result

| Variant | Recovery | Timeout | Collision | Steps | Tracking during failure | Chain during failure | Connectivity during failure |
|---|---:|---:|---:|---:|---:|---:|---:|
| Hardened no-role-identity | 20.0% | 46.7% | 3.3% | 208.1 | 16.5% | 3.3% | 7.3% |
| Full multi-relation reference | 93.3% | 6.7% | 0.0% | 59.6 | 94.1% | 15.6% | 22.9% |

Seed-level full-minus-no-role deltas:

```text
recovery: +20.0 pp, +100.0 pp, +100.0 pp
timeout:  -20.0 pp, -90.0 pp, -10.0 pp
steps:    -43.2, -214.0, -188.3
tracking during failure: +40.4 pp, +97.9 pp, +94.4 pp
chain during failure: +3.8 pp, +16.1 pp, +17.0 pp
```

## Metric Boundary Fix

During this run, one no-role episode ended by collision before the relay-failure start step. The evaluator previously returned `-1.0` for failure-window rates when no `node_failure_active` samples existed. This was corrected so configured-but-unreached failure windows report `0.0` for:

- `chain_closed_during_failure_rate`;
- `tracking_during_failure_rate`;
- `connectivity_during_failure`.

A regression test was added in `tests/test_gate1_communication_feasibility.py`.

## Interpretation

- The hardened no-role ablation is trainable end-to-end through BC, nominal PPO, topology curriculum, strict bottleneck continuation, validation selection, and test evaluation.
- Removing explicit symbolic role identity strongly degrades recovery in this development run.
- The result supports promoting hardened no-role to a five-seed formal ablation if the manuscript needs a stronger role-identity mechanism claim.
- Seed 0 retains moderate recovery, so the final paper should describe this as a reliability and generalization degradation rather than claiming no-role never works.

## Boundary

This is still development evidence:

- only three seeds;
- only ten test episodes per seed;
- full reference uses the existing fixed-update-60 checkpoint;
- no seed-aware bootstrap was run because this is not yet a formal table.

Recommended next step:

- If role identity is a main mechanism claim, run a five-seed fixed-budget hardened no-role formal ablation with at least 50 test episodes per seed.
- If page or runtime budget is tight, keep this as a development justification and prioritize scenario-depth experiments.

## Artifacts

- Source training: `results/true_no_role_identity_hardened_3seed_dev_source/`
- Strict run: `results/true_no_role_identity_hardened_3seed_strict_dev20/`
- Full same-split reference: `results/true_no_role_identity_hardened_3seed_dev20_full_reference_same_split/`
- Combined summary: `results/true_no_role_identity_hardened_3seed_dev20_summary/`
