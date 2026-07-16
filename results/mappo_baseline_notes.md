# MAPPO Baseline Notes

## Environment

Python environment:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe
torch 2.4.1+cu124
cuda available: True
```

## Smoke Run

Command:

```bash
python scripts/train_mappo.py --updates 2 --num-envs 2 --rollout-steps 16 --eval-episodes 2 --eval-interval 1 --out-dir results/mappo_smoke
```

Result:

- Training pipeline runs successfully.
- Model checkpoint and `train_log.csv` are generated.

## Short Mixed-Target Run

Command:

```bash
python scripts/train_mappo.py --updates 30 --num-envs 8 --rollout-steps 64 --eval-episodes 10 --eval-interval 5 --target-policy mixed --out-dir results/mappo_short
```

Observation:

- Baseline runs, but success rate remains unstable and low.
- Collision spikes occur in some evaluations.

## Reward Shaping Update

The environment reward was adjusted from mostly team-level progress to:

- team progress;
- individual target-distance progress;
- dense distance potential;
- target-heading alignment;
- proximity penalty;
- terminal success/collision rewards.

This improves the reward signal but does not fully solve MAPPO learning within 50 updates.

## Straight-Target Curriculum Test

Command:

```bash
python scripts/train_mappo.py --updates 80 --num-envs 8 --rollout-steps 64 --eval-episodes 20 --eval-interval 10 --target-policy straight --out-dir results/mappo_straight_80
```

Observation:

- Evaluation success rate fluctuates around 0.25-0.45.
- This is better than random policy, but not yet a strong baseline.

Higher learning rate test:

```bash
python scripts/train_mappo.py --updates 50 --num-envs 8 --rollout-steps 64 --eval-episodes 20 --eval-interval 10 --target-policy straight --lr 0.001 --out-dir results/mappo_straight_lr1e3_50
```

Observation:

- Entropy decreases, indicating the policy is updating.
- Success rate remains around 0.15-0.35.
- Stochastic evaluation is not better than deterministic evaluation.

## Current Judgment

The MAPPO code path is valid, but the baseline is not yet reliable enough for paper experiments.

Do not implement GAT-MAPPO or RI-GMAPPO until the MAPPO baseline reaches a stable success rate on the straight-target curriculum task.

## Next Debugging Steps

1. Increase training horizon:

```bash
python scripts/train_mappo.py --updates 300 --num-envs 16 --rollout-steps 128 --eval-episodes 30 --eval-interval 20 --target-policy straight
```

2. Add explicit curriculum levels:

- Level 1: slower straight target.
- Level 2: normal straight target.
- Level 3: random target.
- Level 4: mixed target.

3. Consider rule-policy behavior cloning warm start for all methods, but only if clearly reported as a common pretraining step.

4. Add trajectory rendering for trained policies to understand failure modes:

- all agents chase the same point;
- agents circle away from target;
- agents collide;
- agents timeout near the boundary.

5. Once MAPPO reaches stable performance, implement GAT-MAPPO.

## Curriculum Run Update

A slower straight-target curriculum was added through `--target-speed`.

Command:

```bash
python scripts/train_mappo.py --updates 150 --num-envs 16 --rollout-steps 128 --eval-episodes 30 --eval-interval 15 --target-policy straight --target-speed 0.45 --lr 0.001 --out-dir results/mappo_curriculum_slow_150
```

Final evaluation at update 150:

```text
success_rate = 1.0
collision_rate = 0.0
timeout_rate = 0.0
avg_steps = 37.47
```

Transfer evaluation of the trained model:

```text
straight, speed 0.45: success 1.00, collision 0.00
straight, speed 0.75: success 0.80, collision 0.20
random,   speed 0.75: success 0.97, collision 0.03
mixed,    speed 0.75: success 0.83, collision 0.13
```

Current judgment:

- MAPPO baseline is now valid after curriculum training.
- The next implementation step can be `GAT-MAPPO`.
- Keep the curriculum setup as a common training protocol for MAPPO, GAT-MAPPO and RI-GMAPPO to ensure fair comparison.

## 2026-07-13 Multi-Seed Communication Baseline

MAPPO seed 1 and seed 2 were trained with the same curriculum protocol as seed 0.

Seed 1:

```bash
python scripts/train_mappo.py --seed 1 --updates 150 --num-envs 16 --rollout-steps 128 --eval-episodes 30 --eval-interval 15 --target-policy straight --target-speed 0.45 --lr 0.001 --out-dir results/mappo_curriculum_slow_seed1_150
```

Seed 2:

```bash
python scripts/train_mappo.py --seed 2 --updates 150 --num-envs 16 --rollout-steps 128 --eval-episodes 30 --eval-interval 15 --target-policy straight --target-speed 0.45 --lr 0.001 --out-dir results/mappo_curriculum_slow_seed2_150
```

Training-stage final evaluations:

| Run | Final success | Final collision | Final timeout | Avg steps |
|---|---:|---:|---:|---:|
| seed0 latest | 1.00 | 0.00 | 0.00 | 37.47 |
| seed1 latest | 1.00 | 0.00 | 0.00 | 24.87 |
| seed2 latest | 0.967 | 0.033 | 0.00 | 35.43 |

Communication-stress evaluation:

```bash
python scripts/evaluate_mappo_runs.py --run-dirs results/mappo_curriculum_slow_150 results/mappo_curriculum_slow_seed1_150 results/mappo_curriculum_slow_seed2_150 --episodes 100 --target-policy mixed --target-speed 0.75 --radii 4 6 8 10 --checkpoint latest --out-csv results/mappo_comm_multi_seed_eval.csv
```

3-seed mean and std:

| Radius | Success | Collision | Timeout | Avg steps |
|---:|---:|---:|---:|---:|
| 4 | 0.690 ± 0.212 | 0.240 ± 0.135 | 0.073 ± 0.083 | 85.40 ± 30.28 |
| 6 | 0.777 ± 0.158 | 0.217 ± 0.141 | 0.013 ± 0.019 | 68.69 ± 29.24 |
| 8 | 0.800 ± 0.167 | 0.180 ± 0.151 | 0.023 ± 0.021 | 62.21 ± 24.59 |
| 10 | 0.850 ± 0.054 | 0.143 ± 0.046 | 0.007 ± 0.009 | 58.90 ± 17.53 |

Judgment:

```text
The old single-seed MAPPO row underestimated MAPPO.
MAPPO can become strong under some seeds, but its communication-stress variance is large.
RI-GMAPPO should therefore be framed as improving limited-communication stability and collision reduction,
not as simply beating a weak MAPPO baseline.
```

Generated artifacts:

```text
scripts/evaluate_mappo_runs.py
results/mappo_comm_multi_seed_eval.csv
results/mappo_comm_multi_seed_summary.csv
```
