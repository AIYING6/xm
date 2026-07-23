# 3DOF Target-Policy Curriculum Run

Generated: 2026-07-22T15:48:50

This run performs nominal target-policy curriculum fine-tuning only.
It intentionally does not enable strict sensing, target-information bottlenecks, or node failure.

```text
seeds = [1]
graph_encoders = ['multi_relation']
stage_policies = ['weaving_tiny', 'weaving_mild']
stage_updates = [30, 30]
source_checkpoint_kind = actor_critic_update_0060.pt
hidden_dim = 64
lr = 1e-05
entropy_coef = 0.001
num_envs = 4
rollout_steps = 64
eval_episodes = 4
save_interval = 10
graph_relation_ablation = none
graph_message_ablation = none
graph_input_ablation = none
safety_proximity_distance = 0.0
safety_proximity_penalty_weight = 0.0
attack_geometry_reward_weight = 0.15
```
