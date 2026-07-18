# Fair Staged Source Protocol Run

Generated: 2026-07-17T02:09:39

This run prepares comparable source checkpoints before strict-sensing fine-tuning.

```text
seeds = [0]
graph_encoders = ['no_graph', 'single', 'multi_relation']
bc_episodes = 4
bc_epochs = 1
nominal_updates = 1
curriculum_updates = 1
strict_updates = 1
num_envs = 1
rollout_steps = 8
skip_strict_smoke = False
```

Directory layout:

```text
stage1_bc/<graph_encoder>/seed<seed>/actor_critic_best.pt
stage2_nominal/runs/<graph_encoder>/bc_ppo_seed<seed>/actor_critic_best.pt
stage3_curriculum/runs/<graph_encoder>/bc_ppo_seed<seed>/actor_critic_best.pt
stage4_strict_smoke/...
```
