# 3DOF Target-Policy Curriculum Run

Generated: 2026-07-22T15:11:46

This run performs nominal target-policy curriculum fine-tuning only.
It intentionally does not enable strict sensing, target-information bottlenecks, or node failure.

```text
seeds = [0]
graph_encoders = ['multi_relation']
stage_policies = ['weaving_tiny', 'weaving_mild']
stage_updates = [1, 1]
source_checkpoint_kind = actor_critic_update_0060.pt
hidden_dim = 64
lr = 1e-05
entropy_coef = 0.001
num_envs = 1
rollout_steps = 8
eval_episodes = 1
save_interval = 1
graph_relation_ablation = none
graph_message_ablation = none
graph_input_ablation = none
```
