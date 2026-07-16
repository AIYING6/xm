# 3DOF Topology Curriculum Protocol

Generated: 2026-07-16T20:45:32

```text
seeds = [0, 1, 2]
graph_encoders = ['single', 'multi_relation']
graph_relation_ablation = none
graph_message_ablation = none
graph_input_ablation = none
strict_target_sensing = True
updates = 10
num_envs = 4
rollout_steps = 64
lr = 5e-05
entropy_coef = 0.001
communication_range_random = [0.65, 1.0]
communication_dropout_random = [0.0, 0.15]
message_delay_random = [0, 2]
radar_dropout_random = [0.0, 0.1]
failed_blue_agent = -1
node_failure_random_prob = 0.5
node_failure_start_random = [None, None]
node_failure_duration_random = [None, None]
eval_episodes = 5
eval_scenarios = ['relay_failure', 'scout_failure']
```

Boundary:

```text
This protocol fine-tunes already trained straight-target checkpoints under topology-domain randomization.
It is the first matched topology-curriculum experiment chain; final paper evidence still requires completed seeds and fixed evaluation budgets.
```
