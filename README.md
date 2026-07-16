# RI-GMAPPO UAV

This project is the phase-1 sandbox for heterogeneous UAV cooperative decision-making under limited communication.

Current scope:

- 2D multi-UAV pursuit environment.
- Heterogeneous pursuer dynamics.
- Rule-based policy for environment validation.
- Trajectory rendering and episode metrics.

Planned method:

- MAPPO baseline.
- GAT-MAPPO.
- RI-GMAPPO with role-aware graph encoding, intent prediction, and limited-communication attention.

## Quick Start

```bash
python scripts/render_episode.py
```

The script runs one rule-based episode and saves a trajectory image under `results/`.

If `matplotlib` is unavailable, it saves a trajectory CSV instead.

## Environment Validation

```bash
python scripts/smoke_test_env.py
python scripts/evaluate_policies.py --episodes 50 --target-policy mixed
```

The expected rough result before learning is:

- random policy: low success rate, high timeout rate.
- rule policy: high success rate, some collisions.

This gap indicates that the task is learnable but not trivial.

## MAPPO Baseline

Install dependencies in a PyTorch-enabled environment:

```bash
pip install -r requirements.txt
```

Train a compact MAPPO baseline:

```bash
python scripts/train_mappo.py --updates 200 --num-envs 8 --rollout-steps 128
```

For a quick smoke run:

```bash
python scripts/train_mappo.py --updates 2 --num-envs 2 --rollout-steps 16 --eval-episodes 2 --eval-interval 1
```

Training logs are saved to:

```text
results/mappo/train_log.csv
```

Current baseline scope:

- shared actor for all UAVs.
- centralized critic with global state.
- discrete 9-action maneuver set.
- no graph network yet.
- no intent prediction yet.

The next step after this baseline is stable is `GAT-MAPPO`.

## 3DOF Interception Smoke Run

The RI/EA-RG-MAPPO-S runner also supports the first 3DOF heterogeneous
interception environment. This command is an integration check only, not a
reported learning result:

```bash
python scripts/train_ri_gmappo.py --env-name 3d_intercept --updates 1 --num-envs 2 --rollout-steps 8 --eval-episodes 1 --eval-interval 1 --save-interval 1 --hidden-dim 32 --out-dir results/ri_gmappo_3d_smoke
```

Evaluate the saved 3DOF checkpoint and write the maintained diagnostic CSV:

```bash
python scripts/evaluate_ri_gmappo_3d.py
```

The output is diagnostic only until multi-seed 3DOF training is complete:

```text
results/intercept_3d_policy_eval.csv
docs/intercept_3d_policy_eval.md
```

## 3DOF Learnability Curriculum

The straight-target 3DOF task uses a geometric-controller demonstration warm
start before PPO fine-tuning. This is a training aid for sparse attack-window
exploration, not a paper contribution.

```bash
python scripts/pretrain_ri_gmappo_3d_bc.py --episodes 200 --epochs 80 --hidden-dim 64 --no-balanced-loss --out-dir results/ri_gmappo_3d_bc_straight_seed0

python scripts/train_ri_gmappo.py --env-name 3d_intercept --target-policy straight --updates 60 --num-envs 4 --rollout-steps 64 --eval-episodes 5 --eval-interval 10 --save-interval 10 --hidden-dim 64 --intent-coef 0.0 --lr 1e-4 --resume results/ri_gmappo_3d_bc_straight_seed0/actor_critic_latest.pt --out-dir results/ri_gmappo_3d_bc_ppo_straight_seed0

python scripts/evaluate_ri_gmappo_3d.py --checkpoint results/ri_gmappo_3d_bc_ppo_straight_seed0/actor_critic_best.pt --episodes 30 --target-policy straight --out-csv results/intercept_3d_policy_eval_bc_ppo_straight_seed0.csv --summary-md docs/intercept_3d_policy_eval_bc_ppo_straight_seed0.md
```

This curriculum has passed a single-seed learnability check. Use matched seeds
and independent evaluation seeds before treating any 3DOF result as evidence.

Run the matched 3DOF baseline protocol:

```bash
python scripts/run_3d_baseline_protocol.py --seeds 0 1 2 --eval-episodes 30
```

It writes per-seed checkpoints and evaluations under
`results/intercept_3d_baseline_protocol/`, plus `episode_metrics.csv` and a
mean-plus-standard-deviation `summary.csv`. The protocol is a curriculum
baseline only; it does not test the multi-relation graph contribution.

For the multi-relation graph diagnostic, use a separate result directory and
the conservative fine-tuning settings:

```bash
python scripts/run_3d_baseline_protocol.py --graph-encoder multi_relation --ppo-lr 5e-5 --entropy-coef 0.001 --seeds 0 1 2 --out-dir results/intercept_3d_multirelation_protocol
```

The multi-relation path separates perception, communication, and task-support
adjacencies, with role-pair-conditioned messages and a union-graph residual.

Run zero-shot communication-topology robustness screening over the matched
single-graph and multi-relation checkpoints:

```bash
python scripts/evaluate_3d_topology_robustness.py --episodes 5 --out-dir results/intercept_3d_topology_robustness_screen
```

This screening reuses nominally trained checkpoints. Use it to choose
non-trivial disruption levels before running topology-curriculum retraining and
formal 30+ episode evaluations.

Run a matched topology-curriculum pilot from the nominal BC-to-PPO checkpoints:

```bash
python scripts/run_3d_topology_curriculum_protocol.py --seeds 0 1 2 --updates 20 --eval-episodes 5 --out-dir results/intercept_3d_topology_curriculum_protocol_pilot
```

For a node-failure-focused curriculum, keep the communication range less severe
and randomize temporary failed blue nodes:

```bash
python scripts/run_3d_topology_curriculum_protocol.py --seeds 0 1 2 --updates 20 --eval-episodes 5 --communication-range-random-min 0.65 --communication-range-random-max 1.0 --node-failure-random-prob 0.5 --node-failure-start-random-min 30 --node-failure-start-random-max 80 --node-failure-duration-random-min 40 --node-failure-duration-random-max 100 --out-dir results/intercept_3d_node_failure_curriculum_pilot
```
