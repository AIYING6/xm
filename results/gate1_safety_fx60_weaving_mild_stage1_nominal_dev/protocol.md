# Fair Staged Source Protocol Run

Generated: 2026-07-22T13:13:56

This run prepares comparable source checkpoints before strict-sensing fine-tuning.

```text
seeds = [2]
graph_encoders = ['multi_relation']
graph_input_ablation = none
bc_episodes = 60
bc_epochs = 15
nominal_updates = 30
curriculum_updates = 1
strict_updates = 1
num_envs = 4
rollout_steps = 64
skip_strict_smoke = True
```

Directory layout:

```text
stage1_bc/<graph_encoder>/seed<seed>/actor_critic_best.pt
stage2_nominal/runs/<graph_encoder>/bc_ppo_seed<seed>/actor_critic_best.pt
stage3_curriculum/runs/<graph_encoder>/bc_ppo_seed<seed>/actor_critic_best.pt
stage4_strict_smoke/...
```
