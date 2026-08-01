# Baseline Fairness Protocol

Last updated: 2026-08-02

## Purpose

This protocol fixes the fairness rules for comparing EA-RG-MAPPO against graph
and non-graph baselines. It must be satisfied before any result is used as a
paper-facing method comparison.

## Main Methods

Formal comparison candidates:

```text
MAPPO / no_graph
Single-Graph GAT-MAPPO
Parameter-Matched Single Graph
HAPPO
EA-RG-MAPPO
```

Main proposed method:

```text
EA-RG-MAPPO
```

Non-promoted development candidates:

```text
chain auxiliary learning
role_gate_prior_strength = 0.4
multi_relation_global_residual_weight = 0.0 relation-bottleneck candidate
```

These candidates may be discussed as development findings only unless they pass
the same freeze and fairness protocol as all baselines.

## Shared Scenario

All formal methods must use the same scenario from:

```text
configs/paper/main_gate1.yaml
```

Required shared settings:

- `env_name = 3d_intercept`;
- `strict_target_sensing = true`;
- `agent_target_info_bottleneck = true`;
- same target policy;
- same target prior position;
- same communication dropout and delay;
- same failed blue agent;
- same node-failure start and duration;
- same message age and confidence thresholds;
- same reward, termination, safety, and success definitions.

## Shared Training Budget

All formal methods must use the same environment-step budget:

```text
num_envs * rollout_steps * updates
```

The current 1M approximation is defined in:

```text
configs/paper/main_gate1.yaml
```

No method may receive additional updates, extra fine-tuning, different early
stopping, or different checkpoint frequency unless the same rule is applied to
all methods.

## Shared Seeds

Training seeds, validation base seed, test base seed, validation episodes, and
test episodes must come from `configs/paper/main_gate1.yaml`.

Rules:

- validation episodes select checkpoints;
- test episodes are used once after checkpoint selection;
- test results must not change checkpoint selection;
- extra seeds can be added only by extending the protocol for all methods.

## BC Initialization Fairness

If BC initialization is used:

- BC data source must be identical across methods where architecturally possible;
- BC budget must be identical;
- BC manifest must record method, seed, checkpoint path, freeze tag, freeze
  commit, architecture, and SHA256;
- unusable BC is `BC_INVALID`, not a valid start point;
- any change such as no-balanced BC must be applied to all comparable methods.

BC protocol improvements are training-protocol choices, not method
contributions.

## Hyperparameter Fairness

Allowed:

- a predeclared candidate grid in method configs;
- same candidate grid across comparable MAPPO-family methods;
- validation-only selection.

Forbidden:

- choosing hyperparameters from test results;
- giving EA-RG-MAPPO a larger search budget;
- dropping failed EA seeds while keeping failed baseline seeds;
- running extra recovery fine-tuning only for the proposed method.

## Architecture Fairness

The comparison must separate two questions:

1. Does graph information help?
2. Does multi-relation role-conditioned graph information help beyond a normal graph?

Therefore the minimum fair set is:

- MAPPO/no-graph for CTDE baseline;
- Single-Graph for graph baseline;
- Parameter-Matched Single Graph if parameter count differs materially;
- EA-RG-MAPPO for proposed multi-relation role graph;
- HAPPO for heterogeneous-policy external baseline when the implementation passes
  smoke and checkpoint-sweep checks.

## Ablation Fairness

Core ablations must reuse the selected EA-RG-MAPPO checkpoint where the ablation
is evaluation-time only, or retrain with the same budget where the ablation
changes the learned model.

Required ablations:

- no task-support relation;
- no role-pair gate;
- no edge features;
- no role identity;
- single graph instead of multi-relation graph.

No ablation may be claimed as causal if disabling it improves performance.

## Reporting Rules

Report all of:

- seed-level results;
- selected checkpoint updates;
- validation selection metrics;
- final test metrics;
- confidence intervals;
- failure modes;
- collision and flight-envelope violations;
- communication and message-age metrics.

Do not report only reward or only best-case success.

## Freeze Pass Criteria

Before formal comparison starts:

- `scripts/audit_paper_configs.py` passes;
- `scripts/audit_checkpoint_selection_schema.py` passes;
- all method configs exist;
- HAPPO status is explicitly either included or documented as failed/deferred;
- no method has unique extra training budget;
- validation/test split is fixed;
- checkpoint-selection schema is fixed.

