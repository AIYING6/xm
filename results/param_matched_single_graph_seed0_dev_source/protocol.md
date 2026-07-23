# Fair Staged Source Protocol Run

Generated: 2026-07-22T03:16:17

This run prepares comparable source checkpoints before strict-sensing fine-tuning.

```text
seeds = [0]
graph_encoders = ['single']
bc_episodes = 120
bc_epochs = 20
nominal_updates = 20
curriculum_updates = 10
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
