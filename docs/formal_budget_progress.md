# Formal Budget Progress

Last updated: 2026-07-29

## Current Stage

Formal budget study had started under the frozen protocol in
`docs/formal_protocol_freeze.md`, but the protocol has now been interrupted by
a P0 actor information-boundary hardening: actor-visible attack-window inputs
were separated from evaluation-only true attack-window variables on 2026-07-29.

Therefore, the completed seed0 run below is preserved as development evidence
only. It must not be mixed into formal validation/test evidence unless the run
is repeated or the protocol explicitly allows pre-hardening checkpoints.

Protocol audit on 2026-07-29 confirmed the hardened code path:

- Actor observations use `local_attack_window`.
- Actor graph node features use `local_attack_window`.
- Attack edges and attacker-originated task-support edges use
  `local_attack_window`.
- `RIGMAPPOConfig`, BC, PPO training, single-checkpoint evaluation, and
  checkpoint-sweep evaluation now explicitly pass `attack_hold_steps`.
- HAPPO BC and HAPPO PPO training also explicitly pass `attack_hold_steps`;
  HAPPO evaluation paths already had the same pass-through.

Validation commands passed:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe -m py_compile algorithms/ri_gmappo/simple_ri_gmappo.py scripts/train_ri_gmappo.py scripts/pretrain_ri_gmappo_3d_bc.py scripts/evaluate_ri_gmappo_3d.py scripts/evaluate_3d_checkpoint_sweep.py scripts/train_happo_baseline.py scripts/pretrain_happo_3d_bc.py scripts/evaluate_happo_3d.py scripts/evaluate_happo_checkpoint_sweep.py tests/test_gate1_communication_feasibility.py
D:/Anaconda/envs/.conda/envs/cac/python.exe -m pytest -q tests/test_gate1_communication_feasibility.py
33 passed
```

A one-update strict-sensing training smoke with `attack_hold_steps=4` also
passed under `results/protocol_hardening_smoke/`. Minimal HAPPO BC and HAPPO
training smoke tests also passed under the same smoke directory.

The first method being run is:

- EA-RG-MAPPO-S with role-gate prior.
- Method directory:
  `results/paper_config_runs/formal_budget/ea_rg_mappo_s_gate_prior/`

Fourth-review metric audit on 2026-07-29 added a stricter recovery distinction:
ordinary post-failure closure is split into `post_failure_fresh_info_recovered`
and `post_failure_stale_cache_recovered`. Fresh-information recovery requires
the attacker-side target information used at recovery to be generated or
delivered no earlier than the relay-failure start. This prevents a checkpoint
from being selected mainly because it preserved pre-failure target cache. All
future budget sweeps should use `--selection-metric fresh_info_recovery`;
delayed recovery and stale-cache recovery remain diagnostic metrics only.

Fourth-review actor-graph masking audit later on 2026-07-29 changed the strict
bottleneck actor graph itself: the shared target node is now fixed to public
prior plus zero velocity and no longer exposes true target state or an
`any_detected` flag. This is a protocol-changing hardening. Consequently, the
clean post-audit seed0 PPO progress below remains useful as a training health
artifact, but it must not be treated as formal budget evidence unless rerun
from BC under the new graph-mask code.

Fifth-review FreshRec audit on 2026-07-30 changed the primary validation metric
again. `fresh_info_recovery` is now generation-based, after-loss, and requires
a full `attack_hold_steps` continuous window supported by the currently
effective attacker cache. A pre-failure observation delivered after failure is
reported separately and is not FreshRec. Therefore any checkpoint sweep or
selection produced before this metric hardening is development evidence only.

## Completed

### Clean Post-Audit Seed 0 BC

Completed after the 2026-07-29 protocol audit:

- Directory:
  `results/paper_config_runs/formal_budget_post_audit/ea_rg_mappo_s_gate_prior/bc_seed0/`
- Final BC action accuracy: about `0.496`.
- Demonstration success rate: about `0.908`.
- Explicit formal protocol flags include `strict_target_sensing`,
  `agent_target_info_bottleneck`, `communication_dropout_prob=0.30`,
  `message_delay_steps=2`, randomized relay-failure start in `[25, 70]`,
  `node_failure_duration_steps=80`, `attack_hold_steps=4`, and
  `min_success_step=80`.

### Clean Post-Audit Seed 0 PPO 1M

Started from the clean post-audit BC checkpoint:

- Directory:
  `results/paper_config_runs/formal_budget_post_audit/ea_rg_mappo_s_gate_prior/ppo_seed0_1m/`
- Current progress: `200 / 977` updates.
- Save interval: `20`.
- Saved training states: `actor_critic_training_state_update_0020.pt`,
  `actor_critic_training_state_update_0040.pt`,
  `actor_critic_training_state_update_0060.pt`, and
  `actor_critic_training_state_update_0080.pt`,
  `actor_critic_training_state_update_0100.pt`, and
  `actor_critic_training_state_update_0120.pt`,
  `actor_critic_training_state_update_0140.pt`,
  `actor_critic_training_state_update_0160.pt`,
  `actor_critic_training_state_update_0180.pt`, and
  `actor_critic_training_state_update_0200.pt`.
- First formal budget candidate checkpoint generated:
  `actor_critic_update_0200.pt`.

Online monitor, not final selection:

| Update | Eval success | Collision | Timeout |
|---:|---:|---:|---:|
| 20 | 1.0 | 0.0 | 0.0 |
| 40 | 1.0 | 0.0 | 0.0 |
| 60 | 1.0 | 0.0 | 0.0 |
| 80 | 1.0 | 0.0 | 0.0 |
| 100 | 0.8 | 0.0 | 0.2 |
| 120 | 1.0 | 0.0 | 0.0 |
| 140 | 1.0 | 0.0 | 0.0 |
| 160 | 1.0 | 0.0 | 0.0 |
| 180 | 1.0 | 0.0 | 0.0 |
| 200 | 0.8 | 0.0 | 0.2 |

These 5-episode online checks only indicate that the hardened protocol can train
and should not be used for checkpoint selection.

### Seed 0 BC

Completed:

- Directory:
  `results/paper_config_runs/formal_budget/ea_rg_mappo_s_gate_prior/bc_seed0/`
- Final BC action accuracy: about `0.511`.
- Demonstration success rate: about `0.908`.

### Seed 0 PPO 1M

The first attempt used `save_interval=80` and was killed by the 300-second tool
guard before a training-state checkpoint was saved. That partial run is not used
as formal evidence.

Seed0 PPO was restarted with safer chunking:

- Save interval: `20`.
- Chunk size: `40` updates.
- Output directory:
  `results/paper_config_runs/formal_budget/ea_rg_mappo_s_gate_prior/ppo_seed0_1m/`

Seed0 1M is complete under the pre-`local_attack_window` actor-input protocol.

```text
977 / 977
```

Saved formal candidate checkpoints:

- `actor_critic_update_0200.pt`
- `actor_critic_update_0400.pt`
- `actor_critic_update_0600.pt`
- `actor_critic_update_0800.pt`
- `actor_critic_update_0977.pt`

Online monitor, not final selection:

| Update | Eval success | Collision | Timeout |
|---:|---:|---:|---:|
| 200 | 0.8 | 0.0 | 0.2 |
| 300 | 1.0 | 0.0 | 0.0 |
| 400 | 0.8 | 0.0 | 0.2 |
| 500 | 0.8 | 0.0 | 0.2 |
| 600 | 0.8 | 0.0 | 0.2 |
| 700 | 0.8 | 0.0 | 0.2 |
| 800 | 0.8 | 0.0 | 0.2 |
| 900 | 1.0 | 0.0 | 0.0 |

These online monitor episodes use only 5 episodes and are not checkpoint
selection evidence. Because the actor information boundary changed after this
run, these checkpoints should be treated as pre-hardening development artifacts.

### Seed 1 BC and Partial PPO

Seed1 BC and a partial PPO continuation were started before the protocol audit
was completed. They are preserved only as development/continuity artifacts:

- BC directory:
  `results/paper_config_runs/formal_budget/ea_rg_mappo_s_gate_prior/bc_seed1/`
- PPO directory:
  `results/paper_config_runs/formal_budget/ea_rg_mappo_s_gate_prior/ppo_seed1_1m/`
- Partial PPO progress observed: `400 / 977` updates.

Do not mix these partial seed1 artifacts with the clean post-audit formal
budget study.

## Next Step

Restart clean seed0 formal-budget PPO from the matching BC checkpoint under the
new graph-mask code, or explicitly create a new directory such as:

```text
results/paper_config_runs/formal_budget_post_graph_mask/ea_rg_mappo_s_gate_prior/
```

Candidate checkpoints for the budget decision remain:

```text
200 400 600 800 977
```

Do not continue `actor_critic_training_state_update_0200.pt` as formal
evidence, because that checkpoint was created before the stricter shared graph
target mask. Do not run held-out test at this stage. Do not mix pre-mask seed0
with post-mask seed1/2 in the same formal comparison.

After checkpoints 400, 600, 800, and 977 are produced, rerun fixed validation
checkpoint sweeps with `selection_metric=fresh_info_recovery`. Any sweep results
computed before the fresh/stale-cache metric split should be treated as
development diagnostics, not final checkpoint-selection evidence.
