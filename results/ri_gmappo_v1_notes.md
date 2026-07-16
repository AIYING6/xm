# RI-GMAPPO v1 Notes

Date: 2026-07-13

## Implementation

RI-GMAPPO v1 has been implemented as an extension of hybrid GAT-MAPPO.

New files:

```text
algorithms/ri_gmappo/__init__.py
algorithms/ri_gmappo/simple_ri_gmappo.py
scripts/train_ri_gmappo.py
scripts/evaluate_ri_gmappo.py
```

Updated files:

```text
envs/uav_pursuit_env.py
envs/__init__.py
```

Environment update:

- `graph_obs` now includes `intent_label`.
- Intent classes:
  - `0`: straight
  - `1`: escape nearest pursuer
  - `2`: turn left
  - `3`: turn right
  - `4`: unknown

Model update:

```text
policy_input = concat(local_obs_embedding, graph_agent_embedding, predicted_intent_embedding)
```

Training objective:

```text
loss = ppo_loss + value_coef * value_loss - entropy_coef * entropy + intent_coef * intent_ce_loss
```

The loader supports warm starting from a hybrid GAT-MAPPO checkpoint. For the first policy layer, it copies the existing GAT weights and initializes the additional intent-input columns to zero. This avoids destroying the pretrained GAT policy when adding the intent embedding.

## Smoke Tests

RI-GMAPPO smoke training:

```bash
python scripts/train_ri_gmappo.py --updates 2 --num-envs 2 --rollout-steps 16 --eval-episodes 2 --eval-interval 1 --target-policy mixed --target-speed 0.75 --lr 0.0001 --intent-coef 0.1 --out-dir results/ri_gmappo_smoke
```

Result:

- training runs successfully;
- `actor_critic_best.pt` and `actor_critic_latest.pt` are saved;
- `train_log.csv` contains `intent_loss`, `intent_acc`, and `eval_intent_acc`.

Resume smoke from GAT checkpoint:

```bash
python scripts/train_ri_gmappo.py --updates 1 --num-envs 2 --rollout-steps 16 --eval-episodes 5 --eval-interval 1 --target-policy mixed --target-speed 0.75 --lr 0.0001 --intent-coef 0.1 --resume results/gat_mappo_hybrid_slow_60_plus90/actor_critic_latest.pt --out-dir results/ri_gmappo_resume_smoke_v2
```

Result:

```text
loaded 18 matching tensors and 1 partial tensors; skipped 0
eval_success_rate = 0.80
eval_collision_rate = 0.20
eval_timeout_rate = 0.20
```

This confirms that RI-GMAPPO can inherit the pretrained GAT policy without randomizing the policy head.

## First Quick Experiments

Setting:

```text
target_policy = mixed
target_speed  = 0.75
updates       = 30
num_envs      = 8
rollout_steps = 64
eval_episodes = 20 during training
independent evaluation = 100 episodes
resume checkpoint = results/gat_mappo_hybrid_slow_60_plus90/actor_critic_latest.pt
lr = 1e-4
```

### RI-GMAPPO v1 with intent loss

Command:

```bash
python scripts/train_ri_gmappo.py --updates 30 --num-envs 8 --rollout-steps 64 --eval-episodes 20 --eval-interval 5 --target-policy mixed --target-speed 0.75 --lr 0.0001 --intent-coef 0.1 --resume results/gat_mappo_hybrid_slow_60_plus90/actor_critic_latest.pt --out-dir results/ri_gmappo_v1_mixed_lr1e4_30
```

Best 100-episode evaluation:

```text
success_rate    = 0.86
collision_rate  = 0.11
timeout_rate    = 0.03
avg_steps       = 50.38
intent_accuracy = 0.58
```

Latest 100-episode evaluation:

```text
success_rate    = 0.74
collision_rate  = 0.15
timeout_rate    = 0.11
intent_accuracy = 0.58
```

### RI-GMAPPO ablation without intent loss

Command:

```bash
python scripts/train_ri_gmappo.py --updates 30 --num-envs 8 --rollout-steps 64 --eval-episodes 20 --eval-interval 5 --target-policy mixed --target-speed 0.75 --lr 0.0001 --intent-coef 0.0 --resume results/gat_mappo_hybrid_slow_60_plus90/actor_critic_latest.pt --out-dir results/ri_gmappo_no_intent_loss_mixed_lr1e4_30
```

Best 100-episode evaluation:

```text
success_rate    = 0.88
collision_rate  = 0.10
timeout_rate    = 0.02
avg_steps       = 53.65
intent_accuracy = 0.08
```

Latest 100-episode evaluation:

```text
success_rate    = 0.80
collision_rate  = 0.16
timeout_rate    = 0.04
intent_accuracy = 0.05
```

## Comparison With Existing Baselines

All rows below use 100 independent mixed/0.75 evaluation episodes.

| Method | Checkpoint | Success | Collision | Timeout | Avg steps | Intent acc |
|---|---|---:|---:|---:|---:|---:|
| MAPPO | curriculum slow checkpoint | 0.87 | 0.12 | 0.01 | 51.99 | n/a |
| Hybrid GAT-MAPPO | curriculum slow checkpoint | 0.82 | 0.14 | 0.05 | 54.94 | n/a |
| MAPPO | conservative FT best | 0.86 | 0.10 | 0.04 | 56.17 | n/a |
| Hybrid GAT-MAPPO | conservative FT best | 0.83 | 0.11 | 0.06 | 54.06 | n/a |
| RI-GMAPPO v1 | intent_coef=0.1, best | 0.86 | 0.11 | 0.03 | 50.38 | 0.58 |
| RI-GMAPPO ablation | intent_coef=0.0, best | 0.88 | 0.10 | 0.02 | 53.65 | 0.08 |

## Current Interpretation

Do not claim that target intent prediction improves policy performance yet.

What the current result supports:

1. RI-GMAPPO v1 is implemented and trainable.
2. Warm starting from hybrid GAT-MAPPO works.
3. The intent head can learn a meaningful target-intent signal when supervised.
4. Current `intent_coef=0.1` improves interpretability but does not outperform MAPPO.
5. The no-intent-loss ablation has the best quick-test success rate, but its intent prediction is nearly random. This suggests the extra intent branch may help as a policy-side representation, while the current supervised intent loss may be too strong or not aligned with the control objective.

## Next Steps

The next experiment should not be a long training run with the same settings. More useful next steps:

1. Run an intent-loss sweep:

```text
intent_coef = 0.01, 0.03, 0.05, 0.1
```

2. Add a stop-gradient option for the predicted intent embedding:

```text
policy uses detach(softmax(intent_logits))
intent head trained only by CE loss
```

3. Add an oracle-intent diagnostic:

```text
policy receives ground-truth intent embedding during training/evaluation
```

This will answer whether target intent is actually useful for control. If oracle intent does not improve performance, the current intent definition is not useful enough.

4. If intent proves useful, proceed to relative edge features and communication masks.

5. If intent still does not help, revise intent labels:

- distinguish escape direction relative to pursuers;
- predict future target heading sector instead of behavior category;
- predict short-horizon target displacement.

## Diagnostic Update: Detach and Oracle Intent

Date: 2026-07-13

Two diagnostic switches were added:

```text
--detach-intent
--oracle-intent
```

Meaning:

- `--detach-intent`: the policy uses predicted intent probabilities, but PPO gradients do not flow back through the intent probabilities. The intent head is mainly trained by CE loss.
- `--oracle-intent`: the policy receives ground-truth intent embedding. This is not a deployable method; it is a diagnostic for whether intent information is useful for control.

Code changes:

```text
algorithms/ri_gmappo/simple_ri_gmappo.py
scripts/train_ri_gmappo.py
scripts/evaluate_ri_gmappo.py
```

### New 30-update diagnostic runs

All runs:

```text
target_policy = mixed
target_speed  = 0.75
updates       = 30
num_envs      = 8
rollout_steps = 64
lr            = 1e-4
resume        = results/gat_mappo_hybrid_slow_60_plus90/actor_critic_latest.pt
evaluation    = 100 independent episodes
```

| Method | Success | Collision | Timeout | Avg steps | Intent acc |
|---|---:|---:|---:|---:|---:|
| RI-GMAPPO, intent_coef=0.03 | 0.83 | 0.13 | 0.04 | 59.75 | 0.59 |
| RI-GMAPPO, detach_intent, intent_coef=0.05 | 0.90 | 0.07 | 0.04 | 51.18 | 0.58 |
| RI-GMAPPO, oracle_intent | 0.89 | 0.09 | 0.03 | 49.05 | 0.06 |

Comparison with earlier baselines:

| Method | Success | Collision | Timeout | Avg steps |
|---|---:|---:|---:|---:|
| MAPPO curriculum checkpoint | 0.87 | 0.12 | 0.01 | 51.99 |
| Hybrid GAT-MAPPO curriculum checkpoint | 0.82 | 0.14 | 0.05 | 54.94 |
| RI-GMAPPO v1, intent_coef=0.1 | 0.86 | 0.11 | 0.03 | 50.38 |
| RI-GMAPPO, detach_intent, intent_coef=0.05 | 0.90 | 0.07 | 0.04 | 51.18 |

### Interpretation

This is the first result where an RI-GMAPPO variant clearly improves over the MAPPO curriculum checkpoint in both success rate and collision rate:

```text
MAPPO:                    success 0.87, collision 0.12
RI-GMAPPO detach 0.05:    success 0.90, collision 0.07
```

The result is promising but not yet paper-grade. It is still a single-seed, 100-episode quick experiment.

Current technical judgment:

1. Target intent information is likely useful, because oracle intent reaches 0.89 success and the detach variant reaches 0.90.
2. Directly allowing PPO gradients to flow through intent probabilities is unstable.
3. `detach_intent + CE intent supervision` is a better design than the original RI-GMAPPO v1.
4. The current intent category definition is useful enough for a first result, but it may not be optimal.

### Next Required Experiments

Do not move to LAG yet. The next step should strengthen this result:

1. Repeat `detach_intent, intent_coef=0.05` with at least 3 seeds.
2. Run communication-stress evaluation:

```text
communication_radius = 4, 6, 8, 10
```

3. Compare the following on the same seeds:

```text
MAPPO
Hybrid GAT-MAPPO
RI-GMAPPO without intent loss
RI-GMAPPO with detach_intent
Oracle intent diagnostic
```

4. If the 3-seed result remains positive, implement relative edge features.

## Detach-Intent 3-Seed Update

The `detach_intent + intent_coef=0.05` variant was repeated with seeds 0, 1, and 2.

Per-seed 100-episode mixed/0.75 evaluation:

| Seed | Success | Collision | Timeout | Avg steps | Intent acc |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.90 | 0.07 | 0.04 | 51.18 | 0.58 |
| 1 | 0.94 | 0.05 | 0.01 | 56.16 | 0.59 |
| 2 | 0.84 | 0.11 | 0.05 | 55.81 | 0.38 |

Mean ± std:

```text
success_rate    = 0.893 ± 0.050
collision_rate  = 0.077 ± 0.031
timeout_rate    = 0.033 ± 0.021
avg_steps       = 54.38 ± 2.78
intent_accuracy = 0.516 ± 0.115
```

Updated judgment:

```text
The detach-intent variant is promising and improves the mean result over MAPPO,
but seed 2 is weaker than the MAPPO single-checkpoint baseline. Stability is not yet sufficient.
```

Detailed record:

```text
results/ri_gmappo_detach_seed_summary.md
```
