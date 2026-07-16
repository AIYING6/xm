# GAT-MAPPO Notes

## First GAT Version

The first GAT actor used only graph node features and role embeddings.

Result after 150 updates on the slow straight curriculum:

```text
success_rate = 0.30
collision_rate = 0.00
timeout_rate = 0.70
```

Judgment:

- This version is not valid.
- Reason: replacing local observations with absolute graph node features removes useful ego-relative information.

## Hybrid GAT Version

The actor was changed to:

```text
policy_input = concat(local_obs_embedding, graph_agent_embedding)
```

This keeps the MAPPO local observation pathway and uses graph attention as an additional coordination representation.

## Hybrid GAT Curriculum Training

Stage 1 command:

```bash
python scripts/train_gat_mappo.py --updates 60 --num-envs 16 --rollout-steps 128 --eval-episodes 30 --eval-interval 15 --target-policy straight --target-speed 0.45 --lr 0.001 --out-dir results/gat_mappo_hybrid_slow_60
```

Stage 1 final:

```text
success_rate = 0.70
collision_rate = 0.23
timeout_rate = 0.07
```

Stage 2 command:

```bash
python scripts/train_gat_mappo.py --updates 90 --num-envs 16 --rollout-steps 128 --eval-episodes 30 --eval-interval 15 --target-policy straight --target-speed 0.45 --lr 0.0005 --resume results/gat_mappo_hybrid_slow_60/actor_critic_latest.pt --out-dir results/gat_mappo_hybrid_slow_60_plus90
```

Best evaluation during stage 2:

```text
update 45:
success_rate = 1.00
collision_rate = 0.00
timeout_rate = 0.00
avg_steps = 32.50
```

Final evaluation during stage 2:

```text
update 90:
success_rate = 0.90
collision_rate = 0.10
timeout_rate = 0.00
avg_steps = 36.13
```

## Transfer Evaluation

Final hybrid GAT model:

```text
straight, speed 0.45: success 0.90, collision 0.10
straight, speed 0.75: success 0.77, collision 0.20
random,   speed 0.75: success 0.87, collision 0.13
mixed,    speed 0.75: success 0.67, collision 0.17
```

MAPPO curriculum model for comparison:

```text
straight, speed 0.45: success 1.00, collision 0.00
straight, speed 0.75: success 0.80, collision 0.20
random,   speed 0.75: success 0.97, collision 0.03
mixed,    speed 0.75: success 0.83, collision 0.13
```

## Current Judgment

Hybrid GAT-MAPPO can learn the slow straight curriculum task, but it does not yet outperform MAPPO on transfer to the mixed target.

Do not claim graph attention is effective yet.

## Next Step

Run fair mixed-target fine-tuning for both:

1. MAPPO curriculum checkpoint -> mixed target fine-tuning.
2. GAT-MAPPO curriculum checkpoint -> mixed target fine-tuning.

Only after this comparison should we decide whether GAT is useful in the current environment.

## 2026-07-13 Multi-Seed Communication Baseline

To make the RI-GMAPPO communication-stress comparison more defensible, GAT-MAPPO was repeated with seed 1 and seed 2 using the same two-stage curriculum as seed 0.

Seed 1:

```bash
python scripts/train_gat_mappo.py --seed 1 --updates 60 --num-envs 16 --rollout-steps 128 --eval-episodes 30 --eval-interval 15 --target-policy straight --target-speed 0.45 --lr 0.001 --out-dir results/gat_mappo_hybrid_slow_seed1_60
python scripts/train_gat_mappo.py --seed 1 --updates 90 --num-envs 16 --rollout-steps 128 --eval-episodes 30 --eval-interval 15 --target-policy straight --target-speed 0.45 --lr 0.0005 --resume results/gat_mappo_hybrid_slow_seed1_60/actor_critic_latest.pt --out-dir results/gat_mappo_hybrid_slow_seed1_60_plus90
```

Seed 2:

```bash
python scripts/train_gat_mappo.py --seed 2 --updates 60 --num-envs 16 --rollout-steps 128 --eval-episodes 30 --eval-interval 15 --target-policy straight --target-speed 0.45 --lr 0.001 --out-dir results/gat_mappo_hybrid_slow_seed2_60
python scripts/train_gat_mappo.py --seed 2 --updates 90 --num-envs 16 --rollout-steps 128 --eval-episodes 30 --eval-interval 15 --target-policy straight --target-speed 0.45 --lr 0.0005 --resume results/gat_mappo_hybrid_slow_seed2_60/actor_critic_latest.pt --out-dir results/gat_mappo_hybrid_slow_seed2_60_plus90
```

Training-stage final evaluations:

| Run | Final success | Final collision | Final timeout | Avg steps |
|---|---:|---:|---:|---:|
| seed0 stage2 latest | 0.90 | 0.10 | 0.00 | 36.13 |
| seed1 stage2 latest | 1.00 | 0.00 | 0.00 | 36.60 |
| seed2 stage2 latest | 1.00 | 0.00 | 0.00 | 30.33 |

Communication-stress evaluation:

```bash
python scripts/evaluate_gat_runs.py --run-dirs results/gat_mappo_hybrid_slow_60_plus90 results/gat_mappo_hybrid_slow_seed1_60_plus90 results/gat_mappo_hybrid_slow_seed2_60_plus90 --episodes 100 --target-policy mixed --target-speed 0.75 --radii 4 6 8 10 --checkpoint latest --out-csv results/gat_comm_multi_seed_eval.csv
```

3-seed mean and std:

| Radius | Success | Collision | Timeout | Avg steps |
|---:|---:|---:|---:|---:|
| 4 | 0.840 ± 0.037 | 0.127 ± 0.012 | 0.040 ± 0.042 | 70.21 ± 14.32 |
| 6 | 0.873 ± 0.045 | 0.097 ± 0.031 | 0.030 ± 0.022 | 64.53 ± 17.87 |
| 8 | 0.777 ± 0.052 | 0.183 ± 0.040 | 0.043 ± 0.048 | 67.52 ± 15.51 |
| 10 | 0.797 ± 0.029 | 0.170 ± 0.033 | 0.033 ± 0.029 | 69.51 ± 11.50 |

Judgment:

```text
GAT-MAPPO is now a stronger and fairer baseline than the earlier single-seed row.
It performs well at radius 4/6, but still degrades at radius 8/10 compared with RI-GMAPPO variants.
The key remaining baseline gap is MAPPO multi-seed communication stress.
```

Generated artifacts:

```text
scripts/evaluate_gat_runs.py
results/gat_comm_multi_seed_eval.csv
results/gat_comm_multi_seed_summary.csv
```
