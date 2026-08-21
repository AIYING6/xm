# EDR-D1 Implementation Report

**Status:** `IMPLEMENTED — pending frozen five-seed development result`  
**Base commit before implementation:** `22e4b89`

## Exact architectural difference

The unchanged matched SG uses two `GraphAttentionLayer` aggregations with
neighbour-softmax weights.  EDR adds the explicit `graph_encoder="edr"`
option, leaving `graph_encoder="single"` untouched.  Its two replacement
layers retain the same `proj`, `attn`, and `edge_score` trainable tensors, but
compute

\[
\gamma_{ij}=A_{ij}\sigma(\operatorname{LeakyReLU}(a([h_i,h_j])+b(e_{ij}))),
\qquad c_i=\frac14\sum_j\gamma_{ij}h_j.
\]

The existing identity-edge mask remains part of the graph convention.

## Files

- `algorithms/ri_gmappo/simple_ri_gmappo.py`: EDR aggregation and isolated encoder switch.
- `scripts/telemetry_native_t1.py`: graph-family checkpoint adapter, now explicitly supports `single` and `edr`.
- `scripts/run_edr_d1_single.py`: frozen EDR-only development runner.
- `scripts/run_edr_d1_evaluation.py`: frozen-T1-tape final-checkpoint evaluator.
- `scripts/aggregate_edr_d1.py`: raw-evidence-only seed and paired aggregation.
- `scripts/run_edr_d1_technical_audit.py`, `tests/test_edr_sg.py`: technical audit and regression coverage.

## Isolation and boundary

The SG baseline code path, task, reward, PPO, critic, sampler, actor gradient
mode, and evaluator semantics are unchanged.  EDR uses only the existing
actor-side `obs`, `node_feat`, `edge_feat`, role and adjacency tensors; it
receives no failure label, global route, simulator diagnostic, future topology
or critic-only state.  No loss, memory, curriculum, adaptive sampler, or
additional parameter is introduced.

## Parameter fairness

Both matched SG and EDR instantiate exactly **116,728** trainable parameters.

