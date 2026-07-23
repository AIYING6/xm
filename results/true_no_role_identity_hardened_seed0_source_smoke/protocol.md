# Fair Staged Source Protocol Run

Generated: 2026-07-22T05:07:24

This run prepares comparable source checkpoints before strict-sensing fine-tuning.

```text
seeds = [0]
graph_encoders = ['multi_relation']
graph_input_ablation = no_role_identity
bc_episodes = 40
bc_epochs = 5
nominal_updates = 5
curriculum_updates = 3
strict_updates = 1
num_envs = 2
rollout_steps = 32
skip_strict_smoke = True
```

Directory layout:

```text
stage1_bc/<graph_encoder>/seed<seed>/actor_critic_best.pt
stage2_nominal/runs/<graph_encoder>/bc_ppo_seed<seed>/actor_critic_best.pt
stage3_curriculum/runs/<graph_encoder>/bc_ppo_seed<seed>/actor_critic_best.pt
stage4_strict_smoke/...
```
