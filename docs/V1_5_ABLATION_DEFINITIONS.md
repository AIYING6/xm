# v1.5 Formal Ablation Definitions (frozen)

**Freeze date:** 2026-08-04
**Base (Full):** `ea_rg_mappo_s_gate_prior` — `role_gate_prior_strength=0.4`,
task-support relation enabled, role-pair gate learnable, multi-relation
attention enabled.
**Rule:** every ablation inherits ONLY from Full and differs in exactly one
factor. No ablation inherits from the older `ea_rg_mappo` (prior=0) config.

## 1. w/o Gate Prior

```text
change only : role_gate_prior_strength 0.4 -> 0.0
```

- role-pair gate stays **learnable** (embedding still used, gradients flow);
- `role_gate_prior_strength` is an **initialization logit**:
  `initialize_role_pair_prior` fills `role_pair_gate.weight[pair_index]` with
  the strength (code `simple_ri_gmappo.py` line 231-239). At strength=0.0 the
  embedding stays zeros (initialized line 202) so the initial gate is
  sigmoid(0)=0.5, then trains freely.
- task-support relation, relation count, actor/critic dims, PPO, rewards,
  training budget: unchanged.

## 2. w/o Task-Support Relation

Goal: remove the task-support **information channel** without shrinking the
model. Env-level adjacency zeroing is insufficient because the graph layer adds
a self-loop (`mask = clamp(adj + eye)`, line 220) which still yields a
non-zero task-support output.

Required implementation (model level):

```python
# MultiRelationGraphEncoder gains disable_task_support: bool = False
# in _apply_layer, for relation_id == RELATION_TASK_SUPPORT:
#   output = torch.zeros_like(output)   when disable_task_support
```

- relation count stays 3; parameters of the task-support layers stay in the
  state dict (architecturally identical), only the output is zeroed;
- perception and communication relations unchanged;
- env `graph_relation_ablation="no_task_support"` may also stay (consistent
  double gate), but the model-level zeroing is the authoritative mechanism.

## 3. w/o Role-Pair Gate

Remove the differentiated role-pair gating while preserving message scale.

```text
all role pairs get the same fixed gate value = sigmoid(0.4) ~= 0.5987
no role_pair_gate embedding lookup, no gradient through it
```

- `RoleConditionedGraphAttentionLayer` gains `fixed_gate_value: float = 0.5`
  (default keeps current behaviour); when `use_role_pair_gate=False` the gate
  becomes `torch.full_like(hj, fixed_gate_value)` (line 227).
- Primary ablation uses `fixed_gate_value = sigmoid(0.4)`; `gate=1.0` and
  `gate=0.5` may be sensitivity analyses, not the primary ablation.
- state-dependent attention, edge-feature modulation, communication mask,
  relation projections, task-support relation: all unchanged.

## 4. Single-variable diff constraints

| Config | Allowed difference |
|---|---|
| w/o Gate Prior | only `role_gate_prior_strength` |
| w/o Task-Support | only task-support disable flag (model-level zeroing) |
| w/o Role-Pair Gate | only role-pair gate mode/fixed value |

Identical across all: env/scenarios, seeds 0/1/2, updates 977, checkpoint
nodes, BC data/budget, PPO hyperparams, rewards, actor/critic hidden dims,
attention dims, relation dims, obs/action space, RNG policy, device.

## 5. Code assertions (smoke, not experimental results)

- w/o Gate Prior: initial role-pair gate = 0.5 for all pairs; gate has gradients.
- w/o Task-Support: task-support relation output strictly zero; other relation
  outputs non-zero; self-loop does not bypass the flag.
- w/o Role-Pair Gate: all role pairs get identical constant gate; gate never
  updates; attention still input-dependent; other relations/mask normal.

## 6. Outputs (config audit)

```text
effective_config_sha256.csv
effective_config_diff_report.md
parameter_count_report.csv
state_dict_key_comparison.csv
```
