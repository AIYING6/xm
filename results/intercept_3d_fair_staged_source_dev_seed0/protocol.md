# Fair Staged Source Protocol Run

Generated: 2026-07-17T10:02:31

This run prepares comparable source checkpoints before strict-sensing fine-tuning.

```text
seeds = [0]
graph_encoders = ['single', 'multi_relation']
bc_episodes = 40
bc_epochs = 10
nominal_updates = 5
curriculum_updates = 5
strict_updates = 3
num_envs = 2
rollout_steps = 16
skip_strict_smoke = False
```

Directory layout:

```text
stage1_bc/<graph_encoder>/seed<seed>/actor_critic_best.pt
stage2_nominal/runs/<graph_encoder>/bc_ppo_seed<seed>/actor_critic_best.pt
stage3_curriculum/runs/<graph_encoder>/bc_ppo_seed<seed>/actor_critic_best.pt
stage4_strict_smoke/...
```
