# Fair Staged Source Protocol Run

Generated: 2026-07-18T18:05:43

This run prepares comparable source checkpoints before strict-sensing fine-tuning.

```text
seeds = [4]
graph_encoders = ['multi_relation']
bc_episodes = 200
bc_epochs = 80
nominal_updates = 60
curriculum_updates = 20
strict_updates = 1
num_envs = 1
rollout_steps = 32
skip_strict_smoke = False
```

Directory layout:

```text
stage1_bc/<graph_encoder>/seed<seed>/actor_critic_best.pt
stage2_nominal/runs/<graph_encoder>/bc_ppo_seed<seed>/actor_critic_best.pt
stage3_curriculum/runs/<graph_encoder>/bc_ppo_seed<seed>/actor_critic_best.pt
stage4_strict_smoke/...
```
