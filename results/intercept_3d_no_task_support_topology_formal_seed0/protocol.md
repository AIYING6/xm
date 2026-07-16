# 3DOF Topology Curriculum Protocol

Generated: 2026-07-16T13:57:08

```text
seeds = [0]
graph_encoders = ['multi_relation']
graph_relation_ablation = no_task_support
updates = 20
num_envs = 4
rollout_steps = 64
lr = 5e-05
entropy_coef = 0.001
communication_range_random = [0.65, 1.0]
communication_dropout_random = [0.0, 0.25]
message_delay_random = [0, 3]
radar_dropout_random = [0.0, 0.15]
failed_blue_agent = -1
node_failure_random_prob = 0.5
node_failure_start_random = [30, 70]
node_failure_duration_random = [40, 100]
eval_episodes = 30
eval_scenarios = ['relay_failure', 'scout_failure']
```

Boundary:

```text
This protocol fine-tunes already trained straight-target checkpoints under topology-domain randomization.
It is the first matched topology-curriculum experiment chain; final paper evidence still requires completed seeds and fixed evaluation budgets.
```
