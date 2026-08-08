# Fair baseline information protocol v1.8 (R2)

**Status:** protocol design for author review; no training authorized.

## Two comparison questions

### System-level comparison

Standard MAPPO and HAPPO retain their legal local-observation actor paths. They
answer whether a complete EA-RG system is competitive with standard MARL
baselines in the same environment. These are not pure graph-architecture
comparisons unless their actor information set is matched.

### Matched-information architecture comparison

Corrected EA-RG and corrected wider single-graph must receive identical
recipient-specific (G_i) views, packet payloads, validity masks, cache rules,
edge features and relation-independent raw information. Only the encoder or
relation representation may differ. This is the primary route for attributing
an effect to multi-relational representation.

An optional matched-information non-graph MLP/MAPPO baseline should be decided
before implementation. It would receive the same legal recipient features via
fixed pooling/vectorization and would separate information advantage from graph
inductive bias. It is recommended for a strong architecture claim but is not
authorized in this stage.

## Method status under the new protocol

| Method | New-paper role | Information rule |
|---|---|---|
| Corrected EA-RG | Matched-information graph method | Recipient-specific legal graph |
| Corrected wider single-graph | Primary matched architecture baseline | Exactly the same recipient-specific raw views |
| Standard MAPPO | System-level baseline | Existing legal local observation; not a pure architecture comparator |
| Standard HAPPO | System-level baseline | Existing legal local observation; not a pure architecture comparator |
| w/o Gate Prior | Matched-input component ablation | Same corrected views as Full; initialization only changes |
| w/o Task-Support | Controlled representation-removal ablation | Same legal raw source, task-support channel deliberately removed |
| w/o Role-Pair | Matched-input component ablation | Same legal views; gate mechanism removed/replaced |

## Evidence disposition

- All v1.6 raw measurements remain `legacy implemented-policy evidence`.
- EA-RG vs MAPPO/HAPPO remains numerically valid but descriptive under
  asymmetric actor information.
- EA-RG vs wider single-graph remains the relevant matched-information legacy
  comparison, subject to the R4 implementation proving view equivalence.
- Full vs Gate Prior and Full vs Role-Pair remain matched-input component
  measurements; Full vs Task-Support is a controlled representation removal.
- The old 11.81 vs 15.51 RMST80 contrast cannot be promoted to corrected
  architecture evidence.

## Training-matrix proposals (not authorization)

### Minimal matrix

1. Corrected EA-RG Full: seeds 0, 1, 2 under a newly frozen confirmatory
   protocol.
2. Corrected wider single-graph: seeds 0, 1, 2 under the identical protocol.
3. Reuse MAPPO/HAPPO frozen checkpoints only if local observation, physics,
   budget, selection rule and evaluation protocol remain identical; otherwise
   classify them as legacy/system-level evidence and propose retraining
   separately.

### Full matrix

Minimal matrix plus corrected w/o Gate Prior, w/o Task-Support and w/o Role-Pair
with the same seeds, budget and checkpoint-selection rule. Add a matched-input
non-graph baseline only if explicitly authorized before R4.

No matrix is started at R2. Any corrected graph actor whose input distribution
changes must be retrained; its old checkpoint cannot be new fair evidence.

## Selection and held-out rules

Before any new training, freeze actor contract, packet schema, graph views,
seeds, budget, validation selection, evaluation seed/anchor, tau values,
bootstrap hierarchy and stopping rules. If training or checkpoint selection is
repeated, old repeatedly inspected held-out data must not be silently called a
new confirmatory test; a new deterministic held-out generation rule or frozen
evaluation anchor is required.
