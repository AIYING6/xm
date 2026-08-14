# Phase RSG-TC-0 Report

## Decision

> **RSG-TC-0 PASS — RSG-1 DEVELOPMENT SMOKE AUTHORIZED**

This authorization does not start RSG-1 automatically. Formal development
training remains stopped until separately launched.

## What was frozen

The only new candidate is `RSG-TC`: a shared two-layer Single-Graph encoder
with a local topology-conditioned attention-score bias. The implementation
uses:

- relation multi-hot `[perception, communication, task-support]`;
- normalized distance, sensing validity, communication validity, task-support
  validity, message age, and confidence from the frozen local `edge_feat`
  schema;
- a small shared relation-state MLP that produces an additive attention-score
  bias;
- zero initialization of the bias MLP's final projection;
- no relation branches, Role-Gate, union residual, consistency loss, or
  robustness auxiliary loss.

Forbidden global/path information was not added. RSG-TC requires
`relation_adj`; it does not silently replace relation semantics with an
`argmax` category.

## Parameter matching

| Method | Hidden size | Parameters |
|---|---:|---:|
| Matched Single-Graph | 115 | 116,728 |
| RSG-TC | 114 | 117,424 |

Relative difference: **0.5927%**, below the frozen 1% target.

## Contract checks

All checks passed:

- non-canonical development seeds `1501/1502/1503`;
- shared evaluation tape `340000–340099`;
- relation count and multi-hot representation;
- frozen local feature indices;
- forbidden-input source audit;
- zero-bias initialization;
- relation tensor shape and required-input behavior;
- parameter matching below 1%.

## One-update smoke

The allowed integration smoke completed for matched Single-Graph and RSG-TC.
Both produced finite checkpoints and training logs. This smoke used only one
tiny update and is not evidence of performance or robustness.

Artifacts:

- `results/development/phase_rsg_tc0_smoke/RSG_TC0_CONTRACT_RESULT.json`
- `results/development/phase_rsg_tc0_smoke/matched_single_graph/`
- `results/development/phase_rsg_tc0_smoke/rsg_tc/`

The smoke result records `formal_training_started=false` and
`formal_training_authorized=false`; `smoke_training_started=true` refers only
to the permitted one-update integration check.

## RSG-1 frozen decision gates

The next development stage must use MAPPO, matched Single-Graph, and RSG-TC;
seeds `1501/1502/1503`; 200,192 environment steps per method and seed; fixed
final checkpoints; and the shared paired tape. No resume, checkpoint
promotion, seed removal, protocol changes, or auxiliary robustness loss is
allowed.

RSG-TC must satisfy all of the following to continue:

1. Mean nominal score ratio to SG at least `0.90`.
2. Mean failure score at least `0.90` of SG.
3. Mean `ΔJ = J_N - J_F` lower than SG.
4. At least two of three seeds have lower `ΔJ`, with the pooled direction the
   same.
5. Collision, timeout, and constraint-violation rates no more than 0.05
   absolute above SG.
6. Relation/topology bias telemetry shows non-zero, state-stratified use.

Failure of any mandatory gate produces `RSG-1 NO-GO` and ends new-network
screening. No formal 5-seed experiment is authorized before all development
gates pass.

