# Formal Post-Sixth Freeze v1 (frozen baseline)

- protocol_version: post-sixth-freeze-v1
- git_tag: formal-post-sixth-freeze-v1
- freeze_commit_sha: 8b13e26ed4944340d803dc0f5f628fb3521a0424
- branch: main
- python_version: 3.8.20
- torch_version: 2.4.1+cu124
- cuda_version: 12.4
- device: cpu
- hostname: AIYING
- target_updates: 977
- num_envs: 8
- rollout_steps: 128
- total_transitions_per_update: 1024
- P0 env fix: zero/mask target prior + union-graph attack-edge removal

Training-start invariant (each ppo_seed*_1m before any training):
- train_log.csv must NOT exist
- *_training_state_latest.pt must NOT exist
- actor_critic_update_*.pt / happo_update_*.pt must NOT exist
- selected_checkpoints.csv must NOT exist
- bc_checkpoint exists and loadable, bc_manifest commit == freeze_commit_sha

Resume rule:
- resume_start_update = training_checkpoint_update (authoritative)
- train_log.csv is audit-only; never decides resume start alone
- gate states: FRESH / READY / COMPLETE / BLOCKED

Evidence separation:
- pre-sixth_development = DEVELOPMENT EVIDENCE ONLY (pre-freeze 20-29 updates)
- post_sixth_freeze_v1_preflight = PREFLIGHT EVIDENCE ONLY (pre-tag BC + 0->2)
- this directory = the only formal 1M budget target
