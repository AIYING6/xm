# 3DOF Topology Curriculum Protocol

Generated: 2026-07-16T12:05:28

```text
seeds = [0, 1, 2]
graph_encoders = ['single', 'multi_relation']
updates = 20
num_envs = 4
rollout_steps = 64
lr = 5e-05
entropy_coef = 0.001
communication_range_random = [0.5, 1.0]
communication_dropout_random = [0.0, 0.25]
message_delay_random = [0, 3]
radar_dropout_random = [0.0, 0.15]
failed_blue_agent = -1
eval_episodes = 5
eval_scenarios = ['nominal', 'range_075', 'range_050', 'dropout_015', 'dropout_030', 'delay_2', 'delay_5', 'radar_010', 'radar_025', 'relay_failure', 'scout_failure']
```

Boundary:

```text
This protocol fine-tunes already trained straight-target checkpoints under topology-domain randomization.
It is the first matched topology-curriculum experiment chain; final paper evidence still requires completed seeds and fixed evaluation budgets.
```
