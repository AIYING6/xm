# Fair Baseline Staged Source Protocol

The direct path

```text
BC -> strict-sensing relay-failure PPO
```

has been smoke-validated but is not strong enough: the seed-0 BC-strength diagnostic with 40 BC episodes and 10 BC epochs still produced zero validation recovery for `single` and `multi_relation`.

The stronger and fairer path is staged:

```text
nominal BC
  -> nominal BC-to-PPO
  -> topology / node-failure curriculum
  -> strict-sensing fine-tuning with checkpoint snapshots
  -> validation checkpoint selection
  -> disjoint final test
```

This mirrors the path that produced the existing positive strict-sensing `single` / `multi_relation` development result.

## Methods

Use the same staged path for:

- `no_graph`: MAPPO-style no-graph baseline;
- `single`: single union-graph GAT-MAPPO baseline;
- `multi_relation`: proposed EA-RG-MAPPO-S method.

## Stage 1: Nominal BC-To-PPO Source

Purpose:

```text
Learn basic 3DOF target approach and attack-window formation before adding node failures.
```

Recommended development budget:

```text
seeds = 0 1
bc_episodes = 100--200
bc_epochs = 40--80
ppo_updates = 40--60
```

Formal budget should only be chosen after the development budget avoids persistent timeout.

## Stage 2: Topology / Node-Failure Curriculum Source

Purpose:

```text
Teach the policy to survive communication range variation, dropout, delay, radar dropout, and temporary blue-node failure.
```

Use the same curriculum bounds as the current successful strict-sensing source runs unless a single major hyperparameter is being tested.

Checkpoint output should be organized as:

```text
results/<source_protocol>/runs/<graph_encoder>/bc_ppo_seed<seed>/actor_critic_best.pt
```

This path is directly consumable by `scripts/run_3d_strict_sensing_formal_protocol.py`.

## Stage 3: Strict-Sensing Fine-Tuning

Purpose:

```text
Remove target-state leakage and select checkpoints on strict-sensing relay-failure validation episodes.
```

Use:

```text
--strict-target-sensing
--save-snapshots
validation episodes for checkpoint selection
disjoint test episodes for final reporting
```

Do not use test rows for hyperparameter decisions.

## Decision Rules

- If Stage 1 cannot solve nominal 3DOF interception, do not enter Stage 2.
- If Stage 2 cannot produce nonzero relay-failure recovery under non-strict sensing, do not enter Stage 3.
- If Stage 3 validation recovery is zero for both `single` and `multi_relation`, tune the staged curriculum before increasing to 300/1000 updates.
- If validation recovery is nonzero and training curves are stable, run a 300-update long diagnostic before five-seed formal training.

## Q1 Upgrade Hook

After the staged 3v1 line is stable, add adversarial pressure through a rule-based escort or jammer. This should be treated as a scenario-depth extension, not as a replacement for the fair 3v1 main evidence.
