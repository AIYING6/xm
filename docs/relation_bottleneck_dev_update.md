# Relation-Bottleneck Development Update

Last updated: 2026-07-29

## Purpose

This note records the follow-up after the early stress validation showed:

- EA-RG-MAPPO beats no-graph MAPPO under `dropout030_delay2_relay_failure_early`.
- EA-RG-MAPPO does not beat Single-Graph MAPPO.
- Existing role-pair gates remain nearly neutral in diagnostics.

The goal is to harden the claimed mechanism before any further formal training.

## Selected-Checkpoint Ablation

Protocol:

```text
scenario = dropout030_delay2_relay_failure_early
target_policy = straight
strict_target_sensing = true
agent_target_info_bottleneck = true
communication_dropout_prob = 0.30
message_delay_steps = 2
failed_blue_agent = 1
node_failure_start_step = 25
node_failure_duration_steps = 80
base_seed = 140000
episodes = 50 per selected checkpoint
selected EA checkpoints = seed0 update100, seed1 update1200, seed2 update2900
```

Mean over 3 training seeds:

| Variant | Success | Recovery | Recovery steps | Tracking during failure | Connectivity during failure | Timeout |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| EA original selected | 0.4733 | 0.4733 | 34.4233 | 0.3458 | 0.1805 | 0.5267 |
| EA no task-support | 0.4667 | 0.4667 | 33.3397 | 0.3494 | 0.1814 | 0.5333 |
| EA no role-pair gate | 0.4867 | 0.4867 | 34.4988 | 0.3508 | 0.1807 | 0.5133 |

Interpretation:

- Task-support removal produces almost no degradation.
- Disabling role-pair gates slightly improves selected-checkpoint evaluation.
- Therefore the current implementation cannot support a strong causal claim
  that task-support relation or role-pair gate is the main source of recovery.

## Code Change

Added `multi_relation_global_residual_weight`:

- default = `1.0`, preserving old behavior and old checkpoint compatibility;
- `0.0` disables the union-graph residual contribution while keeping parameter
  shapes stable;
- the reported global attention channel is multiplied by the same weight so
  diagnostics reflect whether the global path is active.

Files touched:

- `algorithms/ri_gmappo/simple_ri_gmappo.py`
- `scripts/train_ri_gmappo.py`
- `scripts/evaluate_ri_gmappo_3d.py`
- `scripts/evaluate_3d_checkpoint_sweep.py`
- `scripts/pretrain_ri_gmappo_3d_bc.py`
- `scripts/diagnose_role_graph_usage.py`
- `configs/paper/ea_rg_mappo_relation_bottleneck.yaml`
- `tests/test_gate1_communication_feasibility.py`

Also fixed a BC protocol gap: `pretrain_ri_gmappo_3d_bc.py` now exposes
`--agent-target-info-bottleneck` so BC initialization can match the strict
PPO protocol.

## Verification

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe -m pytest tests/test_gate1_communication_feasibility.py tests/test_happo_policy_loss.py -q
27 passed

D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/audit_paper_configs.py
paper config audit passed: 14 configs
```

Relation-bottleneck smoke:

```text
BC smoke: 20 episodes, 3 epochs, strict sensing, target-info bottleneck,
dropout 0.30, delay 2, global residual weight 0.0

PPO smoke: 20 updates, seed 0, dropout030_delay2_relay_failure_early,
global residual weight 0.0
```

Result:

- training ran without tensor or checkpoint-load errors;
- online success remained `0.0` at updates 1, 10, and 20;
- role-graph diagnostic confirmed `Global Attention = 0.0000`;
- task-support attention remained weak (`0.0174`) and role-pair gates remained
  nearly neutral (`mean abs delta from 0.5 = 0.000113`).

This is a wiring smoke only. It is not a positive algorithm result.

## Seed-0 100-Update Development Run

A stronger BC initialization was generated before PPO:

```text
BC episodes = 200
BC epochs = 12
samples = 9074
demo_success_rate = 1.0
final action_accuracy = 0.2970
final attacker_action_accuracy = 0.1558
final support_action_accuracy = 0.3676
```

Then PPO was run for 100 updates under the same early stress protocol with
`multi_relation_global_residual_weight = 0.0`.

Online evaluation result:

| Update | Success | Timeout | Avg steps |
| ---: | ---: | ---: | ---: |
| 1 | 0.0 | 1.0 | 260 |
| 10 | 0.0 | 1.0 | 260 |
| 20 | 0.0 | 1.0 | 260 |
| 30 | 0.0 | 1.0 | 260 |
| 40 | 0.0 | 1.0 | 260 |
| 50 | 0.0 | 1.0 | 260 |
| 60 | 0.0 | 1.0 | 260 |
| 70 | 0.0 | 1.0 | 260 |
| 80 | 0.0 | 1.0 | 260 |
| 90 | 0.0 | 1.0 | 260 |
| 100 | 0.0 | 1.0 | 260 |

Latest-checkpoint role-graph diagnostic over 10 matched episodes:

| Group | Episodes | Success | Task-support attention | Communication attention | Perception attention | Global attention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 10 | 0.0000 | 0.0082 | 0.7500 | 0.0043 | 0.0000 |

Gate summary:

```text
mean abs gate deviation from 0.5 = 0.001640
max abs gate deviation from 0.5 = 0.015268
```

Interpretation:

- The global residual was successfully disabled.
- Disabling it did not make task-support or perception channels more useful.
- The policy did not recover learning performance under the 100-update budget.
- This candidate should not be scaled to 1M/2M training in its current form.

## BC Loss Diagnostic

Geometric oracle reachability under the same early stress scenario:

| Oracle mode | Success | Collision | Attack-window episodes | Tracking |
| --- | ---: | ---: | ---: | ---: |
| direct | 1.000 | 0.000 | 1.000 | 0.433 |
| lead | 0.967 | 0.033 | 1.000 | 0.430 |
| offset | 1.000 | 0.000 | 1.000 | 0.430 |

This confirms the scenario is reachable. The weak learning result is not caused
by an impossible task.

Balanced BC was the main immediate weakness:

| BC source | Balanced loss | Action acc. | Attacker acc. | BC-only success |
| --- | ---: | ---: | ---: | ---: |
| direct | yes | 0.2970 | 0.1558 | 0.0000 |
| offset | yes | 0.2074 | 0.1538 | 0.0333 |
| direct | no | 0.7253 | 0.7217 | 0.3000 |

The unbalanced direct BC checkpoint was then used for a 100-update PPO run with
`multi_relation_global_residual_weight = 0.0`.

Selected 50-episode validation:

| Checkpoint | Success | Recovery | Recovery steps censored | Tracking during failure | Connectivity during failure | Timeout |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| original EA seed0 update100 | 0.2800 | 0.2800 | 26.0000 | 0.3337 | 0.1412 | 0.7200 |
| relation-bottleneck unbalanced update70 | 0.2600 | 0.2600 | 178.9600 | 0.4053 | 0.1125 | 0.7400 |
| relation-bottleneck unbalanced update80 | 0.2600 | 0.2600 | 178.9600 | 0.4030 | 0.1124 | 0.7400 |
| relation-bottleneck unbalanced update100 | 0.2600 | 0.2600 | 178.9600 | 0.4054 | 0.1121 | 0.7400 |

Interpretation:

- `--no-balanced-loss` is a useful protocol fix for BC quality.
- The relation-bottleneck architecture still does not outperform original EA.
- Higher tracking without faster recovery means the learned behavior tracks but
  does not close the post-failure task chain efficiently.

## Decision

Do not promote the relation-bottleneck candidate.

Next decision gate:

- Do not spend 1M/2M budget on `global_residual_weight = 0.0`.
- Promote `--no-balanced-loss` as the next BC default candidate for future
  development runs; it must be applied fairly to Single-Graph and no-graph
  baselines if used in formal experiments.
- Before adding another network module, inspect reward scale, action
  distribution, and whether strict target-information bottleneck makes some
  relation channels uninformative.
- If a new candidate is tried, it must first beat this 100-update negative
  control and show measurable mechanism activation.

If it still fails, stop trying to rescue role-pair gates and narrow the paper
claim to multi-relation graph robustness over no-graph, with Single-Graph as a
hard baseline that may remain competitive.
